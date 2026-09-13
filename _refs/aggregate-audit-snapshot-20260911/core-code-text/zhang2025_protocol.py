"""L2 reimplementation of Zhang et al. 2025 (IEEE Transactions on Computers).

Paper: *Blockchain-Based Privacy-Preserving Deduplication and Integrity Auditing
in Cloud Storage*, DOI 10.1109/TC.2025.3540670.

Equations reproduced from the paper (PDF page numbers in brackets):

* authentication tag, Eq. (1) [PDF 5]:
  ``tau_i = [ H4(c_i||i) * chi^{sum_j c_ij} ]^{H3(k_l)}``
* initial-upload check, Eq. (2) [PDF 5]
* ownership proof, Eq. (3)(4) [PDF 6]
* audit proof and verification, Eq. (7)(8) [PDF 7]:
  ``p_j = sum_i x_t b_i c_{a_i,j}``, ``Psi_hat = (prod tau^{b_i})^{s_t x_t}``,
  ``Gamma_hat = (prod H4(c_{a_i}||a_i)^{b_i})^{x_t}``, ``vartheta_hat = sum_j p_j``,
  ``e(Gamma_hat * chi^{vartheta_hat}, pk_{t,f}) = e(Psi_hat, g_1)``

Two profiles are implemented and never mixed:

``literal``
    Exactly the paper: one base ``chi`` shared by all sectors, and the verifier
    sums the per-sector aggregates before checking Eq. (8).

``sector_bound``
    An explicitly marked repair variant: one independent base ``chi_j`` per
    sector and a check that uses every per-sector aggregate directly.  It exists
    only to measure what the published equation does *not* bind.

The paper hands the audit key ``{x_t, s_t}`` to the CSP (PDF page 4), which the
cheating prover therefore legitimately holds.
"""
from __future__ import annotations

from .common import digest, hash_int, prf_int
from .lihang2026_pairing import (
    GROUP_ORDER,
    Point,
    add,
    exponentiate,
    hash_to_group,
    in_group,
    pairing,
)

MODES = ("literal", "sector_bound")
SHAPES = ("per_block", "per_sector")


def h1(*parts: bytes) -> int:
    return hash_int(GROUP_ORDER, b"zhang-h1", *parts, nonzero=True)


def h2(*parts: bytes) -> int:
    return hash_int(GROUP_ORDER, b"zhang-h2", *parts, nonzero=True)


def h3(*parts: bytes) -> int:
    return hash_int(GROUP_ORDER, b"zhang-h3", *parts, nonzero=True)


def h4(*parts: bytes) -> Point:
    return hash_to_group(b"zhang-h4", *parts)


def setup(seed: bytes = b"zhang2025-default", sectors: int = 3, mode: str = "literal",
          shape: str = "per_block") -> dict:
    """Public parameters.  ``chi`` is the base every sector shares in literal mode.

    ``shape`` records how the printed proof list is read.  Eq. (7) prints
    ``{p_{a_i}}_{1<=i<=l2}`` (one value per challenged block) while the
    verification prints ``vartheta_hat = sum_{j=1}^{s} p_{a_i}`` (a sum over the
    sector index of an ``i``-indexed value).  The paper's notation is therefore
    self-inconsistent; ``per_block`` follows the printed proof list and
    ``per_sector`` follows the printed sum.  Both readings give the same total
    and are both collapsed by Eq. (8).
    """
    if mode not in MODES:
        raise ValueError(f"unknown profile: {mode}")
    if shape not in SHAPES:
        raise ValueError(f"unknown proof shape: {shape}")
    if sectors < 1:
        raise ValueError("sector count must be positive")
    if mode == "literal":
        bases = [h4(b"chi", seed)]
    else:
        bases = [h4(b"chi", seed, j.to_bytes(4, "big")) for j in range(sectors)]
    return {
        "mode": mode,
        "shape": shape,
        "sectors": sectors,
        "group_order": GROUP_ORDER,
        "g": exponentiate(1).to_dict(),
        "bases": [base.to_dict() for base in bases],
    }


def bases_of(parameters: dict) -> list[Point]:
    return [Point.from_dict(value) for value in parameters["bases"]]


def audit_key(seed: bytes) -> dict:
    """The CSP receives this key in the clear (PDF page 4)."""
    return {"x_t": hash_int(GROUP_ORDER, seed, b"x", nonzero=True),
            "s_t": hash_int(GROUP_ORDER, seed, b"s", nonzero=True)}


def owner_key(seed: bytes) -> dict:
    """The uploader's own audit key; ``s_a`` appears in Eq. (2)."""
    return {"x_a": hash_int(GROUP_ORDER, seed, b"xa", nonzero=True),
            "s_a": hash_int(GROUP_ORDER, seed, b"sa", nonzero=True)}


def file_public_key(k_l: int, s_t: int) -> Point:
    return exponentiate(h3(k_l.to_bytes(32, "big")) * s_t % GROUP_ORDER)


def block_hash(index: int, block: list[int]) -> Point:
    material = b"".join(value.to_bytes(32, "big") for value in block)
    return h4(material, index.to_bytes(8, "big"))


def block_sum(block: list[int]) -> int:
    return sum(block) % GROUP_ORDER


def authentication_tags(parameters: dict, blocks: list[list[int]], k_l: int) -> list[Point]:
    """Eq. (1).  In literal mode the tag only sees the per-block sector sum."""
    exponent = h3(k_l.to_bytes(32, "big"))
    return [multiply_point(_combined_base(parameters, index, block), exponent)
            for index, block in enumerate(blocks)]


def multiply_point(point: Point, scalar: int) -> Point:
    from .lihang2026_pairing import multiply_raw

    return multiply_raw(point, scalar % GROUP_ORDER)


def _combined_base(parameters: dict, index: int, block: list[int]) -> Point:
    bases = bases_of(parameters)
    material = block_hash(index, block)
    if parameters["mode"] == "literal":
        return add(material, multiply_point(bases[0], block_sum(block)))
    combined = material
    for base, value in zip(bases, block):
        combined = add(combined, multiply_point(base, value))
    return combined


def verify_upload(parameters: dict, blocks: list[list[int]], tags: list[Point],
                  public_key: Point, s_a: int, seed: bytes) -> bool:
    """Eq. (2): the CSP checks the tags against the ciphertext at upload time."""
    try:
        count = len(blocks)
        coefficients = [prf_int(seed, b"upload", index, GROUP_ORDER, nonzero=True)
                        for index in range(count)]
        left = Point()
        for index, block in enumerate(blocks):
            left = add(left, multiply_point(_combined_base(parameters, index, block),
                                            coefficients[index]))
        right = Point()
        for coefficient, tag in zip(coefficients, tags):
            right = add(right, multiply_point(tag, coefficient))
        return pairing(left, public_key) == pairing(right, exponentiate(s_a))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def challenge(blocks: int, size: int, seed: bytes) -> dict:
    """Chal = {r3, r4, l2}; the index set is derived by pi_1 and the coefficients by pi_2."""
    if not 1 <= size <= blocks:
        raise ValueError("challenge size outside file")
    indices: list[int] = []
    cursor = 0
    while len(indices) < size:
        candidate = prf_int(seed, b"pi1", cursor, blocks)
        cursor += 1
        if candidate not in indices:
            indices.append(candidate)
    coefficients = [prf_int(seed, b"pi2", index, GROUP_ORDER, nonzero=True) for index in indices]
    return {"indices": indices, "coefficients": coefficients, "size": size}


def _proof_body(parameters: dict, challenge_value: dict, aggregates: list[int],
                gamma: Point, psi: Point) -> dict:
    return {"Gamma": gamma.to_dict(), "Psi": psi.to_dict(),
            "p": [value % GROUP_ORDER for value in aggregates],
            "mode": parameters["mode"]}


def proof_from_data(parameters: dict, blocks: list[list[int]], tags: list[Point],
                    challenge_value: dict, key: dict) -> dict:
    """Honest cloud server: reads the challenged ciphertext blocks (Eq. 7)."""
    indices = challenge_value["indices"]
    coefficients = challenge_value["coefficients"]
    sectors = parameters["sectors"]
    gamma = Point()
    psi = Point()
    for index, coefficient in zip(indices, coefficients):
        gamma = add(gamma, multiply_point(block_hash(index, blocks[index]), coefficient))
        psi = add(psi, multiply_point(tags[index], coefficient))
    gamma = multiply_point(gamma, key["x_t"])
    psi = multiply_point(psi, key["s_t"] * key["x_t"] % GROUP_ORDER)
    if parameters["mode"] == "literal":
        if parameters["shape"] == "per_block":
            aggregates = [key["x_t"] * coefficient * block_sum(blocks[index]) % GROUP_ORDER
                          for index, coefficient in zip(indices, coefficients)]
        else:
            aggregates = [key["x_t"] * sum(coefficient * blocks[index][j]
                                           for index, coefficient in zip(indices, coefficients))
                          % GROUP_ORDER for j in range(sectors)]
    else:
        aggregates = [key["x_t"] * sum(coefficient * blocks[index][j]
                                       for index, coefficient in zip(indices, coefficients))
                      % GROUP_ORDER for j in range(sectors)]
    return {"Gamma": gamma.to_dict(), "Psi": psi.to_dict(), "p": aggregates,
            "mode": parameters["mode"], "shape": parameters["shape"],
            "used_indices": list(indices)}


def proof_from_cache(parameters: dict, cached_hashes: list[Point], cached_sums: list[int],
                     tags: list[Point], challenge_value: dict, key: dict,
                     *, distribute: str = "first") -> dict:
    """Prover that deleted the ciphertext and kept one hash plus one sector sum per block.

    ``distribute`` controls how the cached total is placed into the response:
    ``first`` puts everything into the first aggregate (allowed because the
    literal verifier only sums them), ``zero`` returns all zeros.
    """
    pairs = list(zip(challenge_value["indices"], challenge_value["coefficients"]))
    return proof_from_pairs(parameters, cached_hashes, cached_sums, tags, pairs, key,
                            distribute=distribute)


def proof_from_pairs(parameters: dict, cached_hashes: list[Point], cached_sums: list[int],
                     tags: list[Point], pairs: list[tuple[int, int]], key: dict,
                     *, distribute: str = "first") -> dict:
    """Proof over an arbitrary set of (index, coefficient) pairs.

    The published verification (Eq. 8 / Algorithm 1) never checks which indices
    the server used, so ``pairs`` does not have to match the challenge.  That is
    what makes the single-block prover below possible.
    """
    sectors = parameters["sectors"]
    gamma = Point()
    psi = Point()
    for index, coefficient in pairs:
        gamma = add(gamma, multiply_point(cached_hashes[index], coefficient))
        psi = add(psi, multiply_point(tags[index], coefficient))
    gamma = multiply_point(gamma, key["x_t"])
    psi = multiply_point(psi, key["s_t"] * key["x_t"] % GROUP_ORDER)
    total = key["x_t"] * sum(coefficient * cached_sums[index] for index, coefficient in pairs) \
        % GROUP_ORDER
    if parameters["mode"] == "literal":
        if parameters["shape"] == "per_block":
            # One value per challenged block; each is exactly the cached sector sum.
            aggregates = [key["x_t"] * coefficient * cached_sums[index] % GROUP_ORDER
                          for index, coefficient in pairs]
        else:
            # Only the per-sector total is in the cache; Eq. (8) only uses its sum.
            aggregates = [total] if distribute == "first" else [0]
    else:
        # No sector detail is in the cache; a consistent split is unavailable.
        aggregates = [0] * sectors
    return {"Gamma": gamma.to_dict(), "Psi": psi.to_dict(), "p": aggregates,
            "mode": parameters["mode"], "shape": parameters["shape"],
            "used_indices": [index for index, _ in pairs]}


def proof_from_single_block(parameters: dict, index: int, coefficient: int,
                            cached_hash: Point, cached_sum: int, tag: Point,
                            key: dict) -> dict:
    """Prover that kept one block's hash, sector sum and tag, and nothing else."""
    return proof_from_pairs(parameters, [cached_hash], [cached_sum], [tag],
                            [(0, coefficient)], key, distribute="first") | {
        "used_indices": [index]}


def verify_audit(parameters: dict, public_key: Point, challenge_value: dict,
                 proof: dict) -> bool:
    """Eq. (8).  In literal mode every per-sector aggregate is summed first."""
    try:
        if proof.get("mode") != parameters["mode"]:
            return False
        sectors = parameters["sectors"]
        gamma = Point.from_dict(proof["Gamma"])
        psi = Point.from_dict(proof["Psi"])
        values = [int(value) % GROUP_ORDER for value in proof["p"]]
        bases = bases_of(parameters)
        if parameters["mode"] == "literal":
            # Eq. (8) only sees chi^{vartheta_hat}; the number and split of the
            # transmitted values are unconstrained, so every value is summed.
            left = gamma
            for value in values:
                left = add(left, multiply_point(bases[0], value))
        else:
            if len(values) != sectors or len(bases) != sectors:
                return False
            left = gamma
            for base, value in zip(bases, values):
                left = add(left, multiply_point(base, value))
        if not in_group(left) or not in_group(psi):
            return False
        return pairing(left, public_key) == pairing(psi, exponentiate(1))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def cached_state(parameters: dict, blocks: list[list[int]], tags: list[Point],
                 key: dict | None = None) -> dict:
    """State a cheating cloud keeps: one hash and one sector sum per block, plus tags.

    ``key`` is the audit key the paper hands to the CSP; it is recorded so the
    isolated prover has exactly what a real CSP would hold.
    """
    state = {
        "schema": "zhang2025-cached-state-v1",
        "mode": parameters["mode"],
        "sectors": parameters["sectors"],
        "parameters": parameters,
        "hashes": [block_hash(index, block).to_dict() for index, block in enumerate(blocks)],
        "sums": [block_sum(block) for block in blocks],
        "tags": [tag.to_dict() for tag in tags],
    }
    if key is not None:
        state["audit_key"] = {"x_t": key["x_t"], "s_t": key["s_t"]}
    return state


def minimal_state_bits(blocks: int, sectors: int, hash_bits: int, field_bits: int) -> dict:
    honest = blocks * sectors * field_bits
    cached = blocks * (hash_bits + field_bits)
    return {"blocks": blocks, "sectors": sectors,
            "honest_ciphertext_bits": honest, "cached_state_bits": cached,
            "compression_ratio": honest / cached if cached else None}
