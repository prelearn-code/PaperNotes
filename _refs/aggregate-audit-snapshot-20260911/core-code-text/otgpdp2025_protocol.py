"""OTGPDP 2025 reproduction.

The multiplicative group is a real prime-order subgroup of RFC 3526 group 14.
The paper does not specify its signature scheme; deterministic Ed25519 is the
documented implementation choice.  ``literal`` preserves the paper's CBF
threshold and missing signature checks. ``corrected`` applies only the
explicit repairs listed in the protocol map.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .common import (
    canonical,
    hash_int,
    private_bytes,
    prf_int,
    public_bytes,
    sign,
    signing_key,
    verify_signature,
)


P = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E08"
    "8A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B"
    "302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9"
    "A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE6"
    "49286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8"
    "FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C"
    "180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718"
    "3995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFF"
    "FFFFFFFF", 16
)
Q = (P - 1) // 2
G = 4


@dataclass(frozen=True)
class Profile:
    name: str
    cbf_minimum: int
    verify_signatures: bool
    correct_updates: bool
    cbf_initial: int = 0


# The paper's MetaVer requires the k positions of each tag to be "greater than 1"
# while MetaGen only "increments the value by one".  The counter initial value is
# never stated, so both conventions are made explicit:
#   * LITERAL:             counters start at 0 (the usual convention) -> fresh
#                          tags have count 1 and honest MetaVer always fails;
#   * LITERAL_INITIALIZED: counters start at 1 -> ">1" means "inserted at least
#                          once" and the literal flow is executable.
LITERAL = Profile("literal", cbf_minimum=2, verify_signatures=False, correct_updates=False,
                  cbf_initial=0)
LITERAL_INITIALIZED = Profile("literal_initialized", cbf_minimum=2, verify_signatures=False,
                              correct_updates=False, cbf_initial=1)
CORRECTED = Profile("corrected", cbf_minimum=1, verify_signatures=True, correct_updates=True,
                    cbf_initial=0)


def profile(name: str) -> Profile:
    if name == "literal":
        return LITERAL
    if name == "literal_initialized":
        return LITERAL_INITIALIZED
    if name == "corrected":
        return CORRECTED
    raise ValueError(f"unknown OTGPDP profile: {name}")


def h_group(filename: str, index: int) -> int:
    exponent = hash_int(Q, filename.encode(), index.to_bytes(8, "big"), nonzero=True)
    return pow(G, exponent, P)


def in_group(value: int) -> bool:
    return 1 <= value < P and pow(value, Q, P) == 1


class CountingBloomFilter:
    def __init__(self, size: int, hashes: int, counters: list[int] | None = None,
                 initial: int = 0):
        if size < 1 or hashes < 1:
            raise ValueError("CBF size and hash count must be positive")
        self.size = size
        self.hashes = hashes
        self.initial = initial
        self.counters = counters[:] if counters is not None else [initial] * size
        if len(self.counters) != size or any(x < 0 for x in self.counters):
            raise ValueError("invalid CBF counters")

    def positions(self, value: int) -> list[int]:
        raw = value.to_bytes((P.bit_length() + 7) // 8, "big")
        return [hash_int(self.size, b"otgpdp-cbf", j.to_bytes(4, "big"), raw) for j in range(self.hashes)]

    def add(self, value: int) -> None:
        for pos in self.positions(value):
            self.counters[pos] += 1

    def remove(self, value: int) -> None:
        positions = self.positions(value)
        if any(self.counters[pos] == 0 for pos in positions):
            raise ValueError("CBF underflow")
        for pos in positions:
            self.counters[pos] -= 1

    def contains(self, value: int, minimum: int) -> bool:
        return all(self.counters[pos] >= minimum for pos in self.positions(value))

    def to_dict(self) -> dict:
        return {"size": self.size, "hashes": self.hashes, "counters": self.counters}

    @classmethod
    def from_dict(cls, value: dict) -> "CountingBloomFilter":
        return cls(int(value["size"]), int(value["hashes"]), [int(x) for x in value["counters"]])


def setup(seed: bytes = b"otgpdp-default") -> tuple[dict, dict]:
    client = signing_key(seed, b"client")
    server = signing_key(seed, b"server")
    public = {
        "group": "RFC3526-group14-prime-order-subgroup",
        "p": hex(P), "q": hex(Q), "g": G,
        "client_verify_key": public_bytes(client.public_key()),
        "server_verify_key": public_bytes(server.public_key()),
    }
    secret = {
        "client_sign_key": private_bytes(client),
        "server_sign_key": private_bytes(server),
    }
    return public, secret


def data_process(blocks: Iterable[int], mask_seed: bytes | None = None) -> list[int]:
    values = [int(x) % Q for x in blocks]
    if mask_seed is None:
        return values
    return [(x + prf_int(mask_seed, b"mask", i, Q)) % Q for i, x in enumerate(values)]


def meta_gen(filename: str, data: list[int], *, cbf_size: int = 4096, hashes: int = 3,
             mode: str = "corrected") -> tuple[list[int], dict]:
    tags = [(h_group(filename, i) * pow(G, block, P)) % P for i, block in enumerate(data)]
    cbf = CountingBloomFilter(cbf_size, hashes, initial=profile(mode).cbf_initial)
    for tag in tags:
        cbf.add(tag)
    return tags, cbf.to_dict()


def meta_verify(filename: str, data: list[int], cbf_value: dict, mode: str) -> bool:
    tags, _ = meta_gen(filename, data, cbf_size=int(cbf_value["size"]), hashes=int(cbf_value["hashes"]))
    cbf = CountingBloomFilter.from_dict(cbf_value)
    return all(cbf.contains(tag, profile(mode).cbf_minimum) for tag in tags)


def challenge(n: int, count: int, seed_indices: bytes, seed_coefficients: bytes, client_sign_key: str) -> dict:
    if not 1 <= count <= n:
        raise ValueError("challenge count outside file")
    indices: list[int] = []
    cursor = 0
    while len(indices) < count:
        candidate = prf_int(seed_indices, b"index", cursor, n)
        cursor += 1
        if candidate not in indices:
            indices.append(candidate)
    coefficients = [prf_int(seed_coefficients, b"coefficient", i, Q, nonzero=True) for i in range(count)]
    body = {"count": count, "indices": indices, "coefficients": coefficients,
            "seed_indices": seed_indices.hex(), "seed_coefficients": seed_coefficients.hex()}
    return {"body": body, "signature": sign(client_sign_key, body)}


def _response_body(challenge_value: dict, p_value: int, tags: list[int]) -> dict:
    return {"challenge_digest": canonical(challenge_value["body"]).hex(), "P": hex(p_value),
            "tags": [hex(x) for x in tags]}


def proof_from_data(data: list[int], tags: list[int], challenge_value: dict, server_sign_key: str) -> dict:
    body = challenge_value["body"]
    p_value = pow(G, sum(a * data[i] for i, a in zip(body["indices"], body["coefficients"])) % Q, P)
    chosen = [tags[i] for i in body["indices"]]
    result = _response_body(challenge_value, p_value, chosen)
    return {"body": result, "signature": sign(server_sign_key, result)}


def proof_from_tags(filename: str, tags: list[int], challenge_value: dict, server_sign_key: str) -> dict:
    body = challenge_value["body"]
    chosen = [tags[i] for i in body["indices"]]
    p_value = 1
    for index, coefficient, tag in zip(body["indices"], body["coefficients"], chosen):
        encoded = tag * pow(h_group(filename, index), -1, P) % P
        p_value = p_value * pow(encoded, coefficient, P) % P
    result = _response_body(challenge_value, p_value, chosen)
    return {"body": result, "signature": sign(server_sign_key, result)}


def verify(public: dict, filename: str, cbf_value: dict, challenge_value: dict, response: dict, mode: str) -> bool:
    try:
        cfg = profile(mode)
        challenge_body = challenge_value["body"]
        response_body = response["body"]
        if cfg.verify_signatures:
            if not verify_signature(public["client_verify_key"], challenge_body, challenge_value["signature"]):
                return False
            if not verify_signature(public["server_verify_key"], response_body, response["signature"]):
                return False
        if response_body["challenge_digest"] != canonical(challenge_body).hex():
            return False
        indices = challenge_body["indices"]
        coefficients = challenge_body["coefficients"]
        tags = [int(x, 16) for x in response_body["tags"]]
        p_value = int(response_body["P"], 16)
        if (len(indices) != challenge_body["count"] or len(tags) != len(indices)
                or len(set(indices)) != len(indices) or any(not isinstance(i, int) or i < 0 for i in indices)
                or not in_group(p_value) or any(not in_group(tag) for tag in tags)):
            return False
        cbf = CountingBloomFilter.from_dict(cbf_value)
        if not all(cbf.contains(tag, cfg.cbf_minimum) for tag in tags):
            return False
        delta = 1
        expected_hashes = 1
        for index, coefficient, tag in zip(indices, coefficients, tags):
            delta = delta * pow(tag, coefficient, P) % P
            expected_hashes = expected_hashes * pow(h_group(filename, index), coefficient, P) % P
        return delta == expected_hashes * p_value % P
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def retained_state(filename: str, tags: list[int], public: dict, server_sign_key: str) -> dict:
    return {"schema": "otgpdp2025-tag-state-v1", "filename": filename,
            "tags": [hex(x) for x in tags], "public": public, "server_sign_key": server_sign_key}


def rebuild_corrected(filename: str, data: list[int], cbf_size: int,
                      hashes: int) -> tuple[list[int], dict]:
    """Regenerate every tag and the whole CBF from the current data list.

    Needed whenever a structural change renumbers positions, because tags bind
    their position through ``h_group(filename, i)``.  This is an explicit
    implementation-defined repair: the paper does not specify index renumbering.
    """
    tags = [h_group(filename, i) * pow(G, value % Q, P) % P for i, value in enumerate(data)]
    cbf = CountingBloomFilter(cbf_size, hashes)
    for tag in tags:
        cbf.add(tag)
    return tags, cbf.to_dict()


def insert(filename: str, index: int, value: int, tags: list[int], cbf_value: dict, mode: str,
           *, data: list[int]) -> tuple[list[int], dict]:
    """Insert a block at ``index``.

    ``literal`` DataUp only hashes ``d_update`` and increments a counter, so it
    cannot express a middle insertion.  The corrected profile renumbers and
    regenerates all following positions.
    """
    cfg = profile(mode)
    if not 0 <= index <= len(tags):
        raise IndexError(index)
    bloom = CountingBloomFilter.from_dict(cbf_value)
    if not cfg.correct_updates:
        if index != len(tags):
            raise ValueError("literal DataUp only supports appending, not middle insertion")
        bloom.add(value % P)
        appended = list(tags) + [h_group(filename, len(tags)) * pow(G, value % Q, P) % P]
        return appended, bloom.to_dict()
    new_data = list(data[:index]) + [int(value) % Q] + list(data[index:])
    return rebuild_corrected(filename, new_data, bloom.size, bloom.hashes)


def update(filename: str, index: int, old_data: int | None, new_data: int | None,
           tags: list[int], cbf_value: dict, mode: str, *,
           data: list[int] | None = None) -> tuple[list[int], dict]:
    """Modify, append or delete a block.

    Deleting the last block and overwriting/appending a block are position-safe
    and handled incrementally.  Deleting a middle block renumbers every later
    position; tags bind their position, so the retained tags become stale.  The
    paper does not specify renumbering, therefore a middle deletion raises
    unless the caller supplies the full post-deletion ``data`` list, in which
    case tags and CBF are regenerated by :func:`rebuild_corrected`.
    """
    cfg = profile(mode)
    updated = tags[:]
    cbf = CountingBloomFilter.from_dict(cbf_value)
    old_tag = updated[index] if index < len(updated) else None
    if new_data is None:
        if index >= len(updated):
            raise IndexError(index)
        shifting = index < len(updated) - 1
        if cfg.correct_updates and shifting:
            if data is None:
                raise ValueError(
                    "middle deletion renumbers later positions and the paper does not "
                    "specify index renumbering; pass the post-deletion data list to "
                    "regenerate tags explicitly")
            reduced = [value for position, value in enumerate(data) if position != index]
            return rebuild_corrected(filename, reduced, cbf.size, cbf.hashes)
        updated.pop(index)
        if cfg.correct_updates:
            cbf.remove(old_tag)
        else:
            cbf.add(0)
        return updated, cbf.to_dict()
    new_tag = h_group(filename, index) * pow(G, new_data % Q, P) % P
    if index == len(updated):
        updated.append(new_tag)
    else:
        updated[index] = new_tag
    if cfg.correct_updates:
        if old_tag is not None:
            cbf.remove(old_tag)
        cbf.add(updated[index])
    else:
        # Literal DataUp hashes d_update and increments for ADD/DEL/MOD.
        cbf.add(new_data % P)
    return updated, cbf.to_dict()
