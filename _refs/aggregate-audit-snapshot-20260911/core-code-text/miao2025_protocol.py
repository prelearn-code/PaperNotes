"""Miao 2025 (IEEE TDSC) key audit path — second negative control.

Paper: *Blockchain-Assisted Searchable Integrity Auditing for Large-Scale
Similarity Data With Arbitration*, DOI 10.1109/TDSC.2024.3512345-style entry in
the local corpus (IEEE TDSC 22(6), 2025).  Equations reproduced from the parsed
text:

* authenticator (p. 6 of the parsed text, algorithm `AuthGen`):
  ``sigma_j = sk_ID * [ H3(ID_i||j) * g^{sum_k a_k b_jk} ]^x``
* keyword index authenticator:
  ``Omega_{w,ij} = [ H3(ID_i||j)^{-1} * H4(pi_o(w)||j) ]^x``
* proof: ``T = prod_j sigma_j^{v_j}``, ``mu_k = sum_j v_j * b_jk``
* verification Eq. (1):
  ``e(T * prod_j Omega_j^{v_j}, g)
    = e( prod_j H4(pi_o(w)||j)^{v_j} * prod_k A_k^{mu_k}, R )
      * e( H1(ID)^{sum_j v_j}, P_0 )``

Consistency of Eq. (1) forces ``sk_ID = H1(ID)^alpha`` (with ``P_0 = g^alpha``)
and ``R = g^x = P_1``; both are used here and are the only assignment that makes
the honest path verify.

Only the critical audit path is implemented; the searchable index structure,
arbitration, certificateless key derivation details and the chain are out of
scope.

Two profiles, never mixed:

``published``
    Exactly the paper: the sector weights ``a_k`` stay secret and only
    ``A_k = g^{a_k}`` is published, so a cloud that kept only per-block sector
    sums cannot produce the required ``prod_k A_k^{mu_k}``.
``weights_public``
    An explicitly marked control variant of this workspace (not a modification of
    the paper) with ``a_k`` revealed; the cheating prover then succeeds.  It
    exists only to show the rule keys on server-computability.
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
    return hash_to_group(b"miao-h1", *parts)


def h3(*parts: bytes) -> Point:
    return hash_to_group(b"miao-h3", *parts)


def h4(*parts: bytes) -> Point:
    return hash_to_group(b"miao-h4", *parts)


def setup(seed: bytes = b"miao2025-default") -> dict:
    alpha = hash_int(GROUP_ORDER, seed, b"msk", nonzero=True)
    return {"alpha": alpha, "p0": exponentiate(alpha).to_dict(),
            "g": exponentiate(1).to_dict()}


def keygen(parameters: dict, identity: str, seed: bytes) -> dict:
    """sk_ID = H1(ID)^alpha, x secret, P_1 = g^x (which plays the role of R)."""
    x = hash_int(GROUP_ORDER, seed, b"x", nonzero=True)
    return {"identity": identity,
            "sk_id": multiply_raw(h1(identity.encode()), parameters["alpha"]).to_dict(),
            "x": x,
            "p1": exponentiate(x).to_dict()}


def authgen(parameters: dict, owner: dict, blocks: list[list[int]], keyword_index: int,
            seed: bytes, *, profile: str = "published") -> dict:
    """Tags plus the keyword-index authenticators for one file."""
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    sectors = len(blocks[0]) if blocks else 0
    weights = [hash_int(GROUP_ORDER, seed, b"a", k.to_bytes(4, "big"), nonzero=True)
               for k in range(sectors)]
    bases = [exponentiate(w) for w in weights]
    sk_id = Point.from_dict(owner["sk_id"])
    identity = owner["identity"].encode()
    tags, omega = [], []
    for j, block in enumerate(blocks):
        projection = sum(w * value for w, value in zip(weights, block)) % GROUP_ORDER
        material = add(h3(identity, j.to_bytes(8, "big")), exponentiate(projection))
        tags.append(add(sk_id, multiply_raw(material, owner["x"])))
        omega_material = add(multiply_raw(h3(identity, j.to_bytes(8, "big")), -1),
                             h4(keyword_index.to_bytes(32, "big"), j.to_bytes(8, "big")))
        omega.append(multiply_raw(omega_material, owner["x"]))
    return {"tags": [tag.to_dict() for tag in tags],
            "omega": [value.to_dict() for value in omega],
            "bases": [base.to_dict() for base in bases],
            "sectors": sectors, "blocks": len(blocks),
            "keyword_index": keyword_index,
            "profile": profile,
            "weights_if_revealed": weights if profile == "weights_public" else None}


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


def proof_from_data(state: dict, blocks: list[list[int]], challenge_value: dict) -> dict:
    """T and the per-sector aggregates, computed from the ciphertext."""
    sectors = state["sectors"]
    aggregates = [0] * sectors
    for index, coefficient in zip(challenge_value["indices"], challenge_value["coefficients"]):
        for k in range(sectors):
            aggregates[k] = (aggregates[k] + coefficient * blocks[index][k]) % GROUP_ORDER
    return {"T": _tag_product(state, challenge_value), "mu": aggregates}


def _tag_product(state: dict, challenge_value: dict) -> dict:
    total = Point()
    for index, coefficient in zip(challenge_value["indices"], challenge_value["coefficients"]):
        total = add(total, multiply_raw(Point.from_dict(state["tags"][index]), coefficient))
    return total.to_dict()


def proof_from_cached(state: dict, cached: dict, challenge_value: dict) -> dict:
    """Prover that deleted the ciphertext.

    ``cached`` holds ``block_sums`` (the plain sector sums a real cloud can keep,
    since ``a_k`` is secret) or ``weighted_sums`` (available only in the control
    variant where ``a_k`` is public).
    """
    sectors = state["sectors"]
    indices = challenge_value["indices"]
    coefficients = challenge_value["coefficients"]
    aggregates = [0] * sectors
    if "weighted_sums" in cached:
        total = sum(coefficient * cached["weighted_sums"][index]
                    for index, coefficient in zip(indices, coefficients))
        weights = state["weights_if_revealed"]
        aggregates[0] = total * pow(weights[0], -1, GROUP_ORDER) % GROUP_ORDER
    else:
        total = sum(coefficient * cached["block_sums"][index]
                    for index, coefficient in zip(indices, coefficients))
        aggregates[0] = total % GROUP_ORDER
    return {"T": _tag_product(state, challenge_value), "mu": aggregates}


def cached_state(blocks: list[list[int]], profile: str) -> dict:
    if profile == "published":
        return {"block_sums": [sum(block) % GROUP_ORDER for block in blocks],
                "note": "a_k is secret, so the weighted projection is not computable"}
    return {"block_sums": [sum(block) % GROUP_ORDER for block in blocks],
            "note": "control variant only"}


def with_revealed_weights(state: dict, blocks: list[list[int]]) -> dict:
    weights = state["weights_if_revealed"]
    return {"weighted_sums": [sum(w * value for w, value in zip(weights, block)) % GROUP_ORDER
                              for block in blocks]}


def verify(parameters: dict, owner: dict, state: dict, challenge_value: dict,
           proof: dict) -> bool:
    """Eq. (1), written straight from the paper."""
    try:
        indices = challenge_value["indices"]
        coefficients = challenge_value["coefficients"]
        sectors = state["sectors"]
        mu = [int(value) % GROUP_ORDER for value in proof["mu"]]
        if len(mu) != sectors:
            return False
        t_value = Point.from_dict(proof["T"])
        keyword_index = state["keyword_index"]
        left = t_value
        for index, coefficient in zip(indices, coefficients):
            left = add(left, multiply_raw(Point.from_dict(state["omega"][index]), coefficient))
        if not in_group(left):
            return False
        weights_total = sum(coefficients) % GROUP_ORDER
        second = Point()
        for index, coefficient in zip(indices, coefficients):
            second = add(second, multiply_raw(
                h4(keyword_index.to_bytes(32, "big"), index.to_bytes(8, "big")), coefficient))
        for base, value in zip([Point.from_dict(v) for v in state["bases"]], mu):
            second = add(second, multiply_raw(base, value))
        r_point = Point.from_dict(owner["p1"])
        p0 = Point.from_dict(parameters["p0"])
        return (pairing(left, exponentiate(1))
                == pairing(second, r_point)
                * pairing(multiply_raw(h1(owner["identity"].encode()), weights_total), p0))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False
