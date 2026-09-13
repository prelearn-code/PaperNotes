"""Yang 2026 (IEEE TNSM) key audit path — negative control for the analysis rule.

Paper: *Shared Data Integrity Audit Scheme Based on CP-ABE and Deduplication for
Cloud Storage*, DOI 10.1109/TNSM.2025.3650222.  See
``evidence/yang2026/protocol-map.md`` for the page-level mapping.

Only the critical audit path is implemented (Setup, KeyGen, TagGen, ProofGen,
ProofVerify); CP-ABE, deduplication, proof-of-ownership and the chain are out of
scope.

Two profiles exist and are never mixed:

``published``
    Exactly the paper: the sector weights ``a_j`` stay secret, only
    ``A_j = g^{a_j}`` is published, and the proof returns one aggregate per
    sector.  A cloud that kept only per-block sector sums **cannot** answer.

``weights_public``
    An explicitly marked *control variant* of this workspace, not a
    modification of the paper: the same construction with ``a_j`` revealed.  The
    cheating prover can then compute the weighted projection and answers
    successfully.  It exists only to show that the decision rule keys on whether
    the projection is server-computable.
"""
from __future__ import annotations

from .common import hash_int, prf_int
from .lihang2026_pairing import (
    GROUP_ORDER,
    Point,
    add,
    exponentiate,
    hash_to_group,
    in_group,
    multiply_raw,
    pairing,
)

PROFILES = ("published", "weights_public")


def h1(*parts: bytes) -> Point:
    return hash_to_group(b"yang-h1", *parts)


def h2(*parts: bytes) -> Point:
    return hash_to_group(b"yang-h2", *parts)


def h3(*parts: bytes) -> int:
    return hash_int(GROUP_ORDER, b"yang-h3", *parts, nonzero=True)


def h4(*parts: bytes) -> Point:
    return hash_to_group(b"yang-h4", *parts)


def setup(seed: bytes = b"yang2026-default") -> dict:
    master = hash_int(GROUP_ORDER, seed, b"msk", nonzero=True)
    return {"msk": master, "mpk": exponentiate(master).to_dict(),
            "profile": "published"}


def keygen(parameters: dict, identity: str, seed: bytes) -> dict:
    """KGC gives ``K_dos = H1(id)^s``; the owner keeps ``alpha_DO``."""
    alpha = hash_int(GROUP_ORDER, seed, b"alpha", nonzero=True)
    return {"identity": identity,
            "k_dos": multiply_raw(h1(identity.encode()), parameters["msk"]).to_dict(),
            "alpha": alpha,
            "k_dp": exponentiate(alpha).to_dict()}


def taggen(parameters: dict, owner: dict, k_l: int, blocks: list[list[int]],
           seed: bytes, *, profile: str = "published") -> dict:
    """Eq. (1).  Returns the tags, the published ``A_j`` and the DO's weights."""
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    sectors = len(blocks[0]) if blocks else 0
    weights = [hash_int(GROUP_ORDER, seed, b"a", j.to_bytes(4, "big"), nonzero=True)
               for j in range(sectors)]
    bases = [exponentiate(w) for w in weights]
    sk_f = h3(k_l.to_bytes(32, "big"))
    eta = h3(k_l.to_bytes(32, "big"), b"kc")
    k_dos = Point.from_dict(owner["k_dos"])
    tags = []
    for index, block in enumerate(blocks):
        projection = sum(w * value for w, value in zip(weights, block)) % GROUP_ORDER
        material = add(h4(eta.to_bytes(32, "big"), sk_f.to_bytes(32, "big"),
                          index.to_bytes(8, "big")),
                       exponentiate(projection))
        tags.append(_mul_pub(k_dos, multiply_raw(material, owner["alpha"])))
    return {"tags": [tag.to_dict() for tag in tags],
            "bases": [base.to_dict() for base in bases],
            "eta": eta, "sk_f": sk_f, "sectors": sectors,
            "profile": profile,
            "weights_if_revealed": weights if profile == "weights_public" else None}


def _mul_pub(left: Point, right: Point) -> Point:
    return add(left, right)


def challenge(blocks: int, size: int, seed: bytes) -> dict:
    if not 1 <= size <= blocks:
        raise ValueError("challenge size outside file")
    indices: list[int] = []
    cursor = 0
    while len(indices) < size:
        candidate = prf_int(seed, b"prp", cursor, blocks)
        cursor += 1
        if candidate not in indices:
            indices.append(candidate)
    coefficients = [prf_int(seed, b"prf", index, GROUP_ORDER, nonzero=True)
                    for index in indices]
    return {"indices": indices, "coefficients": coefficients}


def proof_from_data(tag_state: dict, blocks: list[list[int]], challenge_value: dict) -> dict:
    """Eq. (7) from the ciphertext."""
    sectors = tag_state["sectors"]
    sigma = Point()
    aggregates = [0] * sectors
    for index, coefficient in zip(challenge_value["indices"], challenge_value["coefficients"]):
        sigma = add(sigma, multiply_raw(Point.from_dict(tag_state["tags"][index]), coefficient))
        for j in range(sectors):
            aggregates[j] = (aggregates[j] + coefficient * blocks[index][j]) % GROUP_ORDER
    return {"sigma": sigma.to_dict(), "u": aggregates}


def proof_from_cached(tag_state: dict, cached: dict, challenge_value: dict) -> dict:
    """Prover that deleted the ciphertext and kept only a per-block statistic.

    ``cached`` carries either ``block_sums`` (what a real CSP can keep: the
    sector sums, since ``a_j`` is secret) or ``weighted_sums`` (only available in
    the control variant where ``a_j`` is public).
    """
    sigma = Point()
    for index, coefficient in zip(challenge_value["indices"], challenge_value["coefficients"]):
        sigma = add(sigma, multiply_raw(Point.from_dict(tag_state["tags"][index]), coefficient))
    sectors = tag_state["sectors"]
    if "weighted_sums" in cached:
        # Knows a_j, hence the true projection; places the whole total in one slot.
        total = sum(coefficient * cached["weighted_sums"][index]
                    for index, coefficient in zip(challenge_value["indices"],
                                                  challenge_value["coefficients"]))
        weights = tag_state["weights_if_revealed"]
        inverse = pow(weights[0], -1, GROUP_ORDER)
        aggregates = [0] * sectors
        aggregates[0] = total * inverse % GROUP_ORDER
    else:
        # Only the plain sector sums are known.  The verifier needs the
        # a-weighted total, which is not computable without a_j.
        total = sum(coefficient * cached["block_sums"][index]
                    for index, coefficient in zip(challenge_value["indices"],
                                                  challenge_value["coefficients"]))
        aggregates = [0] * sectors
        aggregates[0] = total % GROUP_ORDER
    return {"sigma": sigma.to_dict(), "u": aggregates}


def cached_state(blocks: list[list[int]], profile: str) -> dict:
    """What the cloud keeps: plain sector sums, or the weighted sums in the variant."""
    if profile == "published":
        return {"block_sums": [sum(block) % GROUP_ORDER for block in blocks],
                "note": "a_j is secret, so the weighted projection is not computable"}
    return {"block_sums": [sum(block) % GROUP_ORDER for block in blocks],
            "note": "control variant only"}


def with_revealed_weights(tag_state: dict, blocks: list[list[int]]) -> dict:
    """Control variant: the cloud computes the weighted projection before deleting."""
    weights = tag_state["weights_if_revealed"]
    return {"weighted_sums": [sum(w * value for w, value in zip(weights, block)) % GROUP_ORDER
                              for block in blocks]}


def verify_audit(parameters: dict, owner: dict, tag_state: dict,
                 challenge_value: dict, proof: dict) -> bool:
    """Eq. (8), written straight from the paper."""
    try:
        sigma = Point.from_dict(proof["sigma"])
        values = [int(value) % GROUP_ORDER for value in proof["u"]]
        if len(values) != tag_state["sectors"] or not in_group(sigma):
            return False
        bases = [Point.from_dict(value) for value in tag_state["bases"]]
        k_dp = Point.from_dict(owner["k_dp"])
        mpk = Point.from_dict(parameters["mpk"])
        weights_total = sum(challenge_value["coefficients"]) % GROUP_ORDER
        left = pairing(sigma, exponentiate(1))
        first = pairing(multiply_raw(h1(owner["identity"].encode()), weights_total), mpk)
        second = Point()
        for index, coefficient in zip(challenge_value["indices"], challenge_value["coefficients"]):
            second = add(second, multiply_raw(
                h4(tag_state["eta"].to_bytes(32, "big"), tag_state["sk_f"].to_bytes(32, "big"),
                   index.to_bytes(8, "big")), coefficient))
        for base, value in zip(bases, values):
            second = add(second, multiply_raw(base, value))
        return left == _pair_mul(first, pairing(second, k_dp))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def _pair_mul(left, right):
    return left * right


def verify_upload(parameters: dict, owner: dict, tag_state: dict,
                  blocks: list[list[int]], seed: bytes) -> bool:
    """The per-block tag check the paper prints next to Eq. (1) (PDF 7)."""
    try:
        mpk = Point.from_dict(parameters["mpk"])
        k_dp = Point.from_dict(owner["k_dp"])
        for index, block in enumerate(blocks):
            material = h4(tag_state["eta"].to_bytes(32, "big"), tag_state["sk_f"].to_bytes(32, "big"),
                          index.to_bytes(8, "big"))
            for base, value in zip([Point.from_dict(v) for v in tag_state["bases"]], block):
                material = add(material, multiply_raw(base, value))
            left = pairing(Point.from_dict(tag_state["tags"][index]), exponentiate(1))
            expected = _pair_mul(pairing(h1(owner["identity"].encode()), mpk),
                                 pairing(material, k_dp))
            if left != expected:
                return False
        return True
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False
