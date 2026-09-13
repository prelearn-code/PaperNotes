"""Song et al. 2025 L1 algebraic reproduction.

Elements carry exponents in an abstract composite-order bilinear group.  This
faithfully exercises Eqs. (2)--(10) and all eight protocol algorithms, but is
not an L2 cryptographic backend because discrete logarithms are represented.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .common import canonical, digest, hash_int, prf_int


P_FACTOR = 1_000_003
Q_FACTOR = 1_000_033
N = P_FACTOR * Q_FACTOR


@dataclass(frozen=True)
class G1:
    exponent: int

    def __mul__(self, other: "G1") -> "G1":
        return G1((self.exponent + other.exponent) % N)

    def __truediv__(self, other: "G1") -> "G1":
        return G1((self.exponent - other.exponent) % N)

    def __pow__(self, scalar: int) -> "G1":
        return G1(self.exponent * scalar % N)

    def encode(self) -> int:
        return self.exponent

    @classmethod
    def decode(cls, value: int) -> "G1":
        return cls(int(value) % N)


def pairing(left: G1, right: G1) -> int:
    return left.exponent * right.exponent % N


def h2(*parts: bytes) -> G1:
    return G1(hash_int(N, b"song-h2", *parts, nonzero=True))


def h3_int(state: int) -> int:
    return hash_int(N, b"song-h3", state.to_bytes(16, "big"))


def _token(mk: bytes, keyword: str) -> bytes:
    return digest(b"song-token", mk, keyword.encode())


def _index_key(token: bytes, state: int) -> str:
    return digest(b"song-index", token, state.to_bytes(16, "big")).hex()


def _pointer(state: int, previous: int) -> int:
    return previous ^ h3_int(state)


def _unpointer(state: int, pointer: int) -> int:
    return pointer ^ h3_int(state)


def pi(theta: bytes, file_id: str, index: int) -> int:
    return hash_int(N, b"song-pi", theta, file_id.encode(), index.to_bytes(8, "big"), nonzero=True)


def setup() -> dict:
    return {"model": "L1-exponent-carrying-composite-order", "p": P_FACTOR,
            "q": Q_FACTOR, "N": N, "g": G1(1).encode(), "mu": G1(7).encode()}


def keygen(seed: bytes = b"song-default") -> tuple[dict, dict]:
    sk = hash_int(N, seed, b"sk", nonzero=True)
    secret = {"sk": sk, "mk": digest(seed, b"mk").hex(), "ek": digest(seed, b"ek").hex()}
    return {"pk": (G1(1) ** sk).encode()}, secret


def file_identifier(sectors: list[list[int]]) -> str:
    return digest(b"song-file-id", canonical(sectors)).hex()


def authentication_tags(file_id: str, sectors: list[list[int]], sk: int) -> list[G1]:
    mu = G1(7)
    return [((h2(file_id.encode(), i.to_bytes(8, "big")) * (mu ** sum(row))) ** sk)
            for i, row in enumerate(sectors)]


def new_system(seed: bytes = b"song-default") -> dict:
    public, secret = keygen(seed)
    return {"pp": setup(), "public": public, "secret": secret, "states": {}, "db": {}, "files": {}}


def insert(system: dict, sectors: list[list[int]], keywords: Iterable[str], state_seed: bytes) -> str:
    if not sectors or not sectors[0] or any(len(row) != len(sectors[0]) for row in sectors):
        raise ValueError("sectors must be a non-empty rectangular matrix")
    sectors = [[int(x) % N for x in row] for row in sectors]
    file_id = file_identifier(sectors)
    if file_id in system["files"]:
        raise ValueError("duplicate file")
    sk = int(system["secret"]["sk"])
    tags = authentication_tags(file_id, sectors, sk)
    system["files"][file_id] = {"sectors": sectors, "tags": [x.encode() for x in tags]}
    mk = bytes.fromhex(system["secret"]["mk"])
    for ordinal, keyword in enumerate(keywords):
        token = _token(mk, keyword)
        previous = system["states"].get(keyword)
        state = prf_int(state_seed, keyword.encode(), ordinal, N, nonzero=True)
        while state == previous or _index_key(token, state) in system["db"]:
            state = (state + 1) % N or 1
        first = previous is None
        previous_for_pointer = state if first else int(previous)
        kt_base = h2(file_id.encode()) * h2(state.to_bytes(16, "big"), token)
        if not first:
            kt_base = kt_base / h2(int(previous).to_bytes(16, "big"), token)
        entry = {"pointer": _pointer(state, previous_for_pointer), "valid": True,
                 "kt": (kt_base ** sk).encode(), "file_id": file_id}
        system["db"][_index_key(token, state)] = entry
        system["states"][keyword] = state
    return file_id


def delete(system: dict, file_id: str) -> None:
    if file_id not in system["files"]:
        raise KeyError(file_id)
    del_tag = h2(file_id.encode()) ** int(system["secret"]["sk"])
    for entry in system["db"].values():
        if entry["file_id"] == file_id and entry["valid"]:
            entry["kt"] = (G1.decode(entry["kt"]) / del_tag).encode()
            entry["valid"] = False
    del system["files"][file_id]


def projection_state(system: dict) -> dict:
    files = {}
    for file_id, value in system["files"].items():
        files[file_id] = {"block_sums": [sum(row) % N for row in value["sectors"]],
                          "tags": value["tags"]}
    return {"schema": "song2025-projection-state-v1", "pp": system["pp"],
            "public": system["public"], "db": system["db"], "files": files}


def challenge(theta: bytes) -> dict:
    return {"theta": theta.hex()}


def proof_from_sectors(file_id: str, sectors: list[list[int]], tags: list[int], challenge_value: dict) -> dict:
    theta = bytes.fromhex(challenge_value["theta"])
    weights = [pi(theta, file_id, i) for i in range(len(sectors))]
    psi = sum(weight * sum(row) for weight, row in zip(weights, sectors)) % N
    phi = G1(0)
    for weight, tag in zip(weights, tags):
        phi = phi * (G1.decode(tag) ** weight)
    return {"file_id": file_id, "psi": psi, "phi": phi.encode()}


def proof_from_projection(file_id: str, value: dict, challenge_value: dict) -> dict:
    theta = bytes.fromhex(challenge_value["theta"])
    weights = [pi(theta, file_id, i) for i in range(len(value["block_sums"]))]
    psi = sum(weight * block_sum for weight, block_sum in zip(weights, value["block_sums"])) % N
    phi = G1(0)
    for weight, tag in zip(weights, value["tags"]):
        phi = phi * (G1.decode(tag) ** weight)
    return {"file_id": file_id, "psi": psi, "phi": phi.encode()}


def verify_audit(public: dict, expected_file_id: str, proof_value: dict,
                 challenge_value: dict, block_count: int) -> bool:
    try:
        file_id = proof_value["file_id"]
        if file_id != expected_file_id:
            return False
        theta = bytes.fromhex(challenge_value["theta"])
        zeta = G1(0)
        for i in range(block_count):
            zeta = zeta * (h2(file_id.encode(), i.to_bytes(8, "big")) ** pi(theta, file_id, i))
        left = pairing(G1.decode(proof_value["phi"]), G1(1))
        right = pairing(zeta * (G1(7) ** int(proof_value["psi"])), G1.decode(public["pk"]))
        return left == right
    except (KeyError, TypeError, ValueError):
        return False


def _search_entries(db: dict, token: bytes, latest_state: int) -> list[dict]:
    entries = []
    state = latest_state
    seen = set()
    while state not in seen:
        seen.add(state)
        entry = db.get(_index_key(token, state))
        if entry is None:
            raise ValueError("broken search chain")
        entries.append(entry)
        previous = _unpointer(state, int(entry["pointer"]))
        if previous == state:
            break
        state = previous
    else:
        raise ValueError("cyclic search chain")
    return entries


def search_request(system: dict, keyword: str, challenge_value: dict) -> dict:
    token = _token(bytes.fromhex(system["secret"]["mk"]), keyword)
    return {"token": token.hex(), "latest_state": system["states"].get(keyword),
            "challenge": challenge_value}


def search_from_projection(state: dict, token_hex: str, latest_state: int | None,
                           challenge_value: dict) -> dict:
    if latest_state is None:
        return {"token": token_hex, "latest_state": None,
                "results": [], "proofs": [], "keyword_phi": 0}
    token = bytes.fromhex(token_hex)
    entries = _search_entries(state["db"], token, int(latest_state))
    results, proofs = [], []
    keyword_phi = G1(0)
    for entry in entries:
        keyword_phi = keyword_phi * G1.decode(entry["kt"])
        if entry["valid"]:
            file_id = entry["file_id"]
            results.append(file_id)
            proofs.append(proof_from_projection(file_id, state["files"][file_id], challenge_value))
    return {"token": token.hex(), "latest_state": int(latest_state),
            "results": results, "proofs": proofs, "keyword_phi": keyword_phi.encode()}


def search_honest(system: dict, keyword: str, challenge_value: dict) -> dict:
    request = search_request(system, keyword, challenge_value)
    if request["latest_state"] is None:
        return {"token": request["token"], "latest_state": None,
                "results": [], "proofs": [], "keyword_phi": 0}
    entries = _search_entries(system["db"], bytes.fromhex(request["token"]), int(request["latest_state"]))
    results, proofs = [], []
    keyword_phi = G1(0)
    for entry in entries:
        keyword_phi = keyword_phi * G1.decode(entry["kt"])
        if entry["valid"]:
            file_id = entry["file_id"]
            value = system["files"][file_id]
            results.append(file_id)
            proofs.append(proof_from_sectors(file_id, value["sectors"], value["tags"], challenge_value))
    return {"token": request["token"], "latest_state": request["latest_state"],
            "results": results, "proofs": proofs, "keyword_phi": keyword_phi.encode()}


def verify_search(public: dict, expected_request: dict, response: dict,
                  challenge_value: dict, block_counts: dict[str, int]) -> bool:
    try:
        if (response["token"] != expected_request["token"]
                or response["latest_state"] != expected_request["latest_state"]):
            return False
        if response["latest_state"] is None:
            return response["results"] == [] and response["proofs"] == []
        results = response["results"]
        proofs = response["proofs"]
        if len(results) != len(proofs) or set(results) != {p["file_id"] for p in proofs}:
            return False
        theta = bytes.fromhex(challenge_value["theta"])
        zeta1 = G1(0)
        zeta2 = G1(0)
        zeta3 = G1.decode(response["keyword_phi"])
        rho = 0
        for proof_value in proofs:
            file_id = proof_value["file_id"]
            for i in range(block_counts[file_id]):
                zeta1 = zeta1 * (h2(file_id.encode(), i.to_bytes(8, "big")) ** pi(theta, file_id, i))
            zeta2 = zeta2 * h2(file_id.encode())
            zeta3 = zeta3 * G1.decode(proof_value["phi"])
            rho = (rho + int(proof_value["psi"])) % N
        token = bytes.fromhex(response["token"])
        endpoint = h2(int(response["latest_state"]).to_bytes(16, "big"), token)
        left = pairing(zeta3, G1(1))
        right = pairing(zeta1 * zeta2 * endpoint * (G1(7) ** rho), G1.decode(public["pk"]))
        return left == right
    except (KeyError, TypeError, ValueError):
        return False
