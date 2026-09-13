"""L2 reimplementation of Li Hang 2026 (ICAIDE), lattice-hash auditing scheme.

Original equations follow the parsed paper text:

* initialization: ``Tag = (g^r, g^{r*H(c_1)}, ..., g^{r*H(c_n)})``
* challenge: ``chal = (fileID, Q, nonce, timestamp, AuditorSig)``
* proof: ``(g^s, g^{s*H_agg}, Q, timestamp_response, CSSig)`` with
  ``H_agg = sum_{i in Q} H(c_i)``
* verification: ``e(g^s, prod_{i in Q} g^{r*H(c_i)}) == e(g^r, g^{s*H_agg})``

Two profiles are implemented and never mixed:

``literal``
    Exactly the paper's specification: no ``s != 0`` requirement, no check that
    the proof is bound to the challenge nonce, no signature verification required
    by the verification equation.

``hardened``
    An explicitly marked variant that adds the checks a reviewer would ask for:
    ``g^s != 1``, proof bound to challenge nonce and index set, AuditorSig and
    CSSig verified.  This variant is used to show which problems a standard
    repair fixes and which it does not.

Explicit implementation choices (the paper leaves them open):

* Blocks are supplied as ciphertext bytes; no AES mode is invented.
* ``H`` is instantiated as a chunk-wise additive construction over ``Z_q``
  (``H(m) = sum_j F(chunk_j) mod q``), which satisfies the paper's stated
  homomorphism ``H(m1||m2) = H(m1) + H(m2)`` for equal-size blocks.  A
  non-additive ``plain`` hash variant is also provided to check whether the
  findings depend on the lattice-hash property.
* Signatures are Ed25519 with explicit domain separation.
"""
from __future__ import annotations

from typing import Callable, Iterable

from .common import (
    digest,
    hash_int,
    prf_int,
    private_bytes,
    public_bytes,
    sign,
    signing_key,
    verify_signature,
)
from .lihang2026_pairing import (
    GROUP_ORDER,
    Point,
    add,
    exponentiate,
    in_group,
    parameters as pairing_parameters,
    pairing,
)

CHUNK_BYTES = 16
NONCE_BYTES = 32
TIMESTAMP_WINDOW = 300
PAPER_BLOCK_BYTES = 128 * 1024

IDENTITY = Point()


# ---------------------------------------------------------------------------
# hash instantiations
# ---------------------------------------------------------------------------

def lattice_hash(block: bytes) -> int:
    """Additive (multiset) hash into Z_q, as the paper's lattice hash requires.

    Additivity holds across concatenation only on the chunk grid, which is the
    intended use: all ciphertext blocks have the same fixed size.
    """
    if not block or len(block) % CHUNK_BYTES:
        raise ValueError("block must be a non-empty multiple of the chunk size")
    total = 0
    for offset in range(0, len(block), CHUNK_BYTES):
        total += int.from_bytes(digest(b"lihang-lthash", block[offset:offset + CHUNK_BYTES]), "big")
    return total % GROUP_ORDER


def plain_hash(block: bytes) -> int:
    """Non-additive control hash: SHA-256 mapped into Z_q."""
    if not block:
        raise ValueError("block must be non-empty")
    return int.from_bytes(digest(b"lihang-plain", block), "big") % GROUP_ORDER


HASH_MODES: dict[str, Callable[[bytes], int]] = {"lattice": lattice_hash, "plain": plain_hash}


# ---------------------------------------------------------------------------
# profiles
# ---------------------------------------------------------------------------

PROFILES: dict[str, dict] = {
    "literal": {"require_nonzero_s": False, "bind_challenge": False,
                "verify_signatures": False, "require_indexset_binding": False},
    "hardened": {"require_nonzero_s": True, "bind_challenge": True,
                 "verify_signatures": True, "require_indexset_binding": True},
}


# ---------------------------------------------------------------------------
# initialization
# ---------------------------------------------------------------------------

def setup(seed: bytes = b"lihang2026-default") -> tuple[dict, dict]:
    auditor = signing_key(seed, b"auditor")
    cloud = signing_key(seed, b"cloud")
    public = {
        "pairing": pairing_parameters(),
        "auditor_verify_key": public_bytes(auditor.public_key()),
        "cloud_verify_key": public_bytes(cloud.public_key()),
    }
    secret = {
        "auditor_sign_key": private_bytes(auditor),
        "cloud_sign_key": private_bytes(cloud),
    }
    return public, secret


def initialization(file_id: str, blocks: list[bytes], hash_mode: str = "lattice",
                   seed: bytes = b"lihang2026-tag") -> dict:
    """Vehicle-side tag generation.

    Returns the auditor-facing tag set and the per-block digests that the honest
    cloud server derives from its own stored ciphertext.
    """
    if not blocks:
        raise ValueError("at least one block is required")
    hashes = HASH_MODES[hash_mode]
    r = hash_int(GROUP_ORDER, seed, b"r", nonzero=True)
    digests = [hashes(block) for block in blocks]
    return {
        "file_id": file_id,
        "hash_mode": hash_mode,
        "tag_set": {
            "basic": exponentiate(r).to_dict(),
            "per_block": [exponentiate(r * value % GROUP_ORDER).to_dict() for value in digests],
        },
        "digests": digests,
        "r": r,
    }


# ---------------------------------------------------------------------------
# challenge / proof / verify
# ---------------------------------------------------------------------------

def challenge(n: int, size: int, file_id: str, seed_indices: bytes, nonce: bytes,
              timestamp: int, auditor_sign_key: str) -> dict:
    if not 1 <= size <= n:
        raise ValueError("challenge size outside file")
    if len(nonce) != NONCE_BYTES:
        raise ValueError("nonce must be 32 bytes")
    indices: list[int] = []
    cursor = 0
    while len(indices) < size:
        candidate = prf_int(seed_indices, b"index", cursor, n)
        cursor += 1
        if candidate not in indices:
            indices.append(candidate)
    body = {"file_id": file_id, "Q": sorted(indices), "nonce": nonce.hex(), "timestamp": timestamp}
    return {"body": body, "signature": sign(auditor_sign_key, body)}


def proof_from_blocks(blocks: list[bytes], challenge_value: dict, hash_mode: str,
                      s: int, cloud_sign_key: str, *, hardened_binding: bool = False) -> dict:
    """Honest cloud server: reads the challenged ciphertext blocks."""
    hashes = HASH_MODES[hash_mode]
    aggregate = sum(hashes(blocks[index]) for index in challenge_value["body"]["Q"]) % GROUP_ORDER
    return _finalize(challenge_value, aggregate, s, cloud_sign_key, hardened_binding)


def proof_from_digests(digests: list[int], challenge_value: dict, s: int, cloud_sign_key: str,
                       *, hardened_binding: bool = False, indexset: Iterable[int] | None = None) -> dict:
    """Cheating cloud server: only per-block digests are available."""
    chosen = list(challenge_value["body"]["Q"]) if indexset is None else list(indexset)
    aggregate = sum(digests[index] for index in chosen) % GROUP_ORDER
    return _finalize(challenge_value, aggregate, s, cloud_sign_key, hardened_binding, indexset=chosen)


def proof_degenerate(challenge_value: dict, cloud_sign_key: str, *, hardened_binding: bool = False) -> dict:
    """Proof with s = 0: (g^0, g^0) = (identity, identity). Needs no state at all."""
    return _finalize(challenge_value, 0, 0, cloud_sign_key, hardened_binding)


def _finalize(challenge_value: dict, aggregate: int, s: int, cloud_sign_key: str,
              hardened_binding: bool, indexset: list[int] | None = None) -> dict:
    a_point = exponentiate(s)
    b_point = exponentiate(s * aggregate % GROUP_ORDER)
    announced = list(challenge_value["body"]["Q"]) if indexset is None else list(indexset)
    body = {
        "Q": announced,
        "A": a_point.to_dict(),
        "B": b_point.to_dict(),
        "timestamp_response": challenge_value["body"]["timestamp"],
    }
    if hardened_binding:
        body["nonce"] = challenge_value["body"]["nonce"]
    return {"body": body, "signature": sign(cloud_sign_key, body)}


def verify(public: dict, tag_set: dict, challenge_value: dict, proof: dict,
           profile: str = "literal", *, trust_proof_indexset: bool = False) -> bool:
    cfg = PROFILES[profile]
    try:
        challenge_body = challenge_value["body"]
        body = proof["body"]
        announced = body["Q"]
        if not isinstance(announced, list):
            return False
        if trust_proof_indexset:
            indices = list(announced)
        else:
            indices = list(challenge_body["Q"])

        if (not indices or len(set(indices)) != len(indices)
                or any(not isinstance(i, int) or i < 0 for i in indices)):
            return False
        if len(indices) != len(challenge_body["Q"]) and not trust_proof_indexset:
            return False

        if cfg["require_indexset_binding"] and list(announced) != list(challenge_body["Q"]):
            return False
        if cfg["bind_challenge"]:
            if body.get("nonce") != challenge_body["nonce"]:
                return False
            if body.get("timestamp_response") != challenge_body["timestamp"]:
                return False
        if cfg["verify_signatures"]:
            if not verify_signature(public["auditor_verify_key"], challenge_body,
                                    challenge_value["signature"]):
                return False
            if not verify_signature(public["cloud_verify_key"], body, proof["signature"]):
                return False

        a_point = Point.from_dict(body["A"])
        b_point = Point.from_dict(body["B"])
        if cfg["require_nonzero_s"]:
            if a_point.infinity or not in_group(a_point):
                return False
            if b_point.infinity or not in_group(b_point):
                return False
        else:
            if not a_point.infinity and not in_group(a_point):
                return False
            if not b_point.infinity and not in_group(b_point):
                return False

        per_block = tag_set["per_block"]
        if any(index >= len(per_block) for index in indices):
            return False
        product = IDENTITY
        for index in indices:
            product = add(product, Point.from_dict(per_block[index]))
        basic = Point.from_dict(tag_set["basic"])

        lhs = pairing(a_point, product)
        rhs = pairing(basic, b_point)
        return lhs == rhs
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


# ---------------------------------------------------------------------------
# accounting helpers
# ---------------------------------------------------------------------------

def digest_state_bits(block_count: int) -> int:
    """Minimal sufficient state for the digest-substitution strategy: n elements of Z_q."""
    return block_count * GROUP_ORDER.bit_length()


def honest_state_bits(block_count: int, block_bytes: int) -> int:
    """Honest cloud-server state: the ciphertext itself (tags live at the auditor)."""
    return block_count * block_bytes * 8


def state_summary(block_count: int, block_bytes: int, serialized_digest_state_bytes: int) -> dict:
    honest_bits = honest_state_bits(block_count, block_bytes)
    minimal_bits = digest_state_bits(block_count)
    return {
        "blocks": block_count,
        "block_bytes": block_bytes,
        "honest_server_state_bits": honest_bits,
        "minimal_digest_state_bits": minimal_bits,
        "serialized_digest_state_bytes": serialized_digest_state_bytes,
        "logical_compression_ratio": honest_bits / minimal_bits,
    }
