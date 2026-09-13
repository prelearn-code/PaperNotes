"""Song 2025 L2 reproduction over a real composite-order pairing group."""
from __future__ import annotations

from typing import Iterable

from .common import canonical, digest, hash_int, prf_int
from .song2025_pairing import (
    GENERATOR, MU, ORDER, Point, add, hash_to_point, in_subgroup, multiply,
    pairing, parameters,
)


def _token(mk: bytes, keyword: str) -> bytes:
    return digest(b"song-l2-token", mk, keyword.encode())


def _index_key(token: bytes, state: int) -> str:
    return digest(b"song-l2-index", token, state.to_bytes(16, "big")).hex()


def _h3(state: int) -> int:
    return hash_int(ORDER, b"song-l2-h3", state.to_bytes(16, "big"))


def _pointer(state: int, previous: int) -> int:
    return previous ^ _h3(state)


def _unpointer(state: int, pointer: int) -> int:
    return pointer ^ _h3(state)


def pi(theta: bytes, file_id: str, index: int) -> int:
    return hash_int(ORDER, b"song-l2-pi", theta, file_id.encode(), index.to_bytes(8, "big"), nonzero=True)


def h2(*parts: bytes) -> Point:
    return hash_to_point(b"song-l2-h2", *parts)


def setup() -> dict:
    value = parameters()
    value["model"] = "L2-real-supersingular-composite-order-tate-pairing"
    return value


def keygen(seed: bytes = b"song-l2-default") -> tuple[dict, dict]:
    sk = hash_int(ORDER, seed, b"sk", nonzero=True)
    return {"pk": multiply(GENERATOR, sk).to_dict()}, {
        "sk": sk, "mk": digest(seed, b"mk").hex(), "ek": digest(seed, b"ek").hex()
    }


def file_identifier(sectors: list[list[int]]) -> str:
    return digest(b"song-l2-file-id", canonical(sectors)).hex()


def authentication_tags(file_id: str, sectors: list[list[int]], sk: int) -> list[Point]:
    return [multiply(add(h2(file_id.encode(), i.to_bytes(8, "big")), multiply(MU, sum(row))), sk)
            for i, row in enumerate(sectors)]


def new_system(seed: bytes = b"song-l2-default") -> dict:
    public, secret = keygen(seed)
    return {"pp": setup(), "public": public, "secret": secret, "states": {}, "db": {}, "files": {}}


def insert(system: dict, sectors: list[list[int]], keywords: Iterable[str], state_seed: bytes) -> str:
    if not sectors or not sectors[0] or any(len(row) != len(sectors[0]) for row in sectors):
        raise ValueError("sectors must be a non-empty rectangular matrix")
    sectors = [[int(x) % ORDER for x in row] for row in sectors]
    file_id = file_identifier(sectors)
    if file_id in system["files"]:
        raise ValueError("duplicate file")
    sk = int(system["secret"]["sk"])
    tags = authentication_tags(file_id, sectors, sk)
    system["files"][file_id] = {"sectors": sectors, "tags": [x.to_dict() for x in tags]}
    mk = bytes.fromhex(system["secret"]["mk"])
    for ordinal, keyword in enumerate(keywords):
        token = _token(mk, keyword)
        previous = system["states"].get(keyword)
        state = prf_int(state_seed, keyword.encode(), ordinal, ORDER, nonzero=True)
        while state == previous or _index_key(token, state) in system["db"]:
            state = (state + 1) % ORDER or 1
        first = previous is None
        previous_for_pointer = state if first else int(previous)
        base = add(h2(file_id.encode()), h2(state.to_bytes(16, "big"), token))
        if not first:
            base = add(base, multiply(h2(int(previous).to_bytes(16, "big"), token), -1))
        system["db"][_index_key(token, state)] = {
            "pointer": _pointer(state, previous_for_pointer), "valid": True,
            "kt": multiply(base, sk).to_dict(), "file_id": file_id,
        }
        system["states"][keyword] = state
    return file_id


def delete(system: dict, file_id: str) -> None:
    if file_id not in system["files"]:
        raise KeyError(file_id)
    deletion = multiply(h2(file_id.encode()), int(system["secret"]["sk"]))
    for entry in system["db"].values():
        if entry["file_id"] == file_id and entry["valid"]:
            entry["kt"] = add(Point.from_dict(entry["kt"]), multiply(deletion, -1)).to_dict()
            entry["valid"] = False
    del system["files"][file_id]


def retained_state(system: dict) -> dict:
    files = {}
    for file_id, value in system["files"].items():
        files[file_id] = {"block_sums": [sum(row) % ORDER for row in value["sectors"]],
                          "tags": value["tags"]}
    return {"schema": "song2025-l2-projection-state-v1", "pp": system["pp"],
            "public": system["public"], "db": system["db"], "files": files}


def challenge(theta: bytes) -> dict:
    return {"theta": theta.hex()}


def _aggregate(file_id: str, block_sums: list[int], tags: list[dict], challenge_value: dict) -> dict:
    theta = bytes.fromhex(challenge_value["theta"])
    weights = [pi(theta, file_id, i) for i in range(len(block_sums))]
    psi = sum(weight * block_sum for weight, block_sum in zip(weights, block_sums)) % ORDER
    phi = Point()
    for weight, tag in zip(weights, tags):
        phi = add(phi, multiply(Point.from_dict(tag), weight))
    return {"file_id": file_id, "psi": psi, "phi": phi.to_dict()}


def proof_from_sectors(file_id: str, sectors: list[list[int]], tags: list[dict], challenge_value: dict) -> dict:
    return _aggregate(file_id, [sum(row) % ORDER for row in sectors], tags, challenge_value)


def proof_from_projection(file_id: str, value: dict, challenge_value: dict) -> dict:
    return _aggregate(file_id, value["block_sums"], value["tags"], challenge_value)


def verify_audit(public: dict, expected_file_id: str, proof_value: dict,
                 challenge_value: dict, block_count: int) -> bool:
    try:
        if proof_value["file_id"] != expected_file_id or block_count < 1:
            return False
        pk = Point.from_dict(public["pk"])
        phi = Point.from_dict(proof_value["phi"])
        if not in_subgroup(pk) or not in_subgroup(phi):
            return False
        theta = bytes.fromhex(challenge_value["theta"])
        zeta = Point()
        for i in range(block_count):
            zeta = add(zeta, multiply(h2(expected_file_id.encode(), i.to_bytes(8, "big")),
                                        pi(theta, expected_file_id, i)))
        return pairing(phi, GENERATOR) == pairing(
            add(zeta, multiply(MU, int(proof_value["psi"]))), pk)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def search_request(system: dict, keyword: str, challenge_value: dict) -> dict:
    token = _token(bytes.fromhex(system["secret"]["mk"]), keyword)
    return {"token": token.hex(), "latest_state": system["states"].get(keyword),
            "challenge": challenge_value}


def _search_entries(db: dict, token: bytes, latest_state: int) -> list[dict]:
    entries, seen = [], set()
    state = latest_state
    while state not in seen:
        seen.add(state)
        entry = db.get(_index_key(token, state))
        if entry is None:
            raise ValueError("broken search chain")
        entries.append(entry)
        previous = _unpointer(state, int(entry["pointer"]))
        if previous == state:
            return entries
        state = previous
    raise ValueError("cyclic search chain")


def _search(state: dict, token_hex: str, latest_state: int | None,
            challenge_value: dict, *, honest_files: dict | None = None) -> dict:
    if latest_state is None:
        return {"token": token_hex, "latest_state": None, "results": [],
                "proofs": [], "keyword_phi": Point().to_dict()}
    entries = _search_entries(state["db"], bytes.fromhex(token_hex), int(latest_state))
    results, proofs = [], []
    keyword_phi = Point()
    for entry in entries:
        keyword_phi = add(keyword_phi, Point.from_dict(entry["kt"]))
        if entry["valid"]:
            file_id = entry["file_id"]
            results.append(file_id)
            if honest_files is None:
                proofs.append(proof_from_projection(file_id, state["files"][file_id], challenge_value))
            else:
                value = honest_files[file_id]
                proofs.append(proof_from_sectors(file_id, value["sectors"], value["tags"], challenge_value))
    return {"token": token_hex, "latest_state": int(latest_state), "results": results,
            "proofs": proofs, "keyword_phi": keyword_phi.to_dict()}


def search_from_projection(state: dict, token_hex: str, latest_state: int | None,
                           challenge_value: dict) -> dict:
    return _search(state, token_hex, latest_state, challenge_value)


def search_honest(system: dict, keyword: str, challenge_value: dict) -> dict:
    request = search_request(system, keyword, challenge_value)
    return _search(system, request["token"], request["latest_state"], challenge_value,
                   honest_files=system["files"])


def verify_search(public: dict, expected_request: dict, response: dict,
                  challenge_value: dict, block_counts: dict[str, int]) -> bool:
    try:
        if (response["token"] != expected_request["token"]
                or response["latest_state"] != expected_request["latest_state"]):
            return False
        if response["latest_state"] is None:
            return response["results"] == [] and response["proofs"] == []
        if len(response["results"]) != len(response["proofs"]):
            return False
        if set(response["results"]) != {item["file_id"] for item in response["proofs"]}:
            return False
        pk = Point.from_dict(public["pk"])
        zeta1, zeta2 = Point(), Point()
        zeta3 = Point.from_dict(response["keyword_phi"])
        rho = 0
        theta = bytes.fromhex(challenge_value["theta"])
        for proof_value in response["proofs"]:
            file_id = proof_value["file_id"]
            phi = Point.from_dict(proof_value["phi"])
            if file_id not in block_counts or not in_subgroup(phi):
                return False
            for i in range(block_counts[file_id]):
                zeta1 = add(zeta1, multiply(h2(file_id.encode(), i.to_bytes(8, "big")), pi(theta, file_id, i)))
            zeta2 = add(zeta2, h2(file_id.encode()))
            zeta3 = add(zeta3, phi)
            rho = (rho + int(proof_value["psi"])) % ORDER
        endpoint = h2(int(response["latest_state"]).to_bytes(16, "big"), bytes.fromhex(response["token"]))
        expected = add(add(add(zeta1, zeta2), endpoint), multiply(MU, rho))
        return pairing(zeta3, GENERATOR) == pairing(expected, pk)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False

