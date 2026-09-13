"""Authenticated extractable audit baseline (positive control).

The workspace previously only contained a plain linear-algebra sanity check
(`extractable_baseline.py`), which has no authentication, no group structure and
no isolated prover.  It therefore could not serve as the "standard extractable
audit baseline" required by the test matrix.

This module implements a compact Shacham-Waters-style PoR over the real
composite-order pairing backend:

* ``independent`` (the baseline): every sector has its own generator
  ``g_1..g_s``, tags are ``sigma_i = (H(name||i) * prod_j g_j^{m_ij})^{sk}`` and
  the response returns one aggregate per sector, ``mu_j = sum_i v_i m_ij``.
* ``shared_base`` (the collapsed structure): all sectors use one base ``mu``, so
  tags only see ``z_i = sum_j m_ij`` and the response is a single aggregate.

The pair exists to test the analysis rule rather than to attack a paper:

* against ``independent``, a prover that only stored block sums cannot answer,
  and accepted responses determine every sector coordinate (extraction works);
* against ``shared_base``, the same cached prover answers every challenge.

Extraction is implemented over ``Z_N`` with a Gauss-Jordan pass that requires an
invertible pivot, matching the caveat that composite-order arithmetic cannot use
plain prime-field elimination without care.
"""
from __future__ import annotations

from .common import digest, hash_int
from .song2025_pairing import (
    GENERATOR,
    ORDER,
    Point,
    add,
    hash_to_point,
    in_subgroup,
    multiply,
    pairing,
)

MODES = ("independent", "shared_base")


def sector_generators(sectors: int) -> list[Point]:
    """Independent generators; no discrete-log relation to GENERATOR is known."""
    if sectors < 1:
        raise ValueError("sector count must be positive")
    return [hash_to_point(b"baseline-sector-generator", j.to_bytes(4, "big"))
            for j in range(sectors)]


def block_base(name: str, index: int) -> Point:
    return hash_to_point(b"baseline-block-base", name.encode(), index.to_bytes(8, "big"))


def setup(seed: bytes = b"baseline-default") -> tuple[dict, dict]:
    sk = hash_int(ORDER, seed, b"sk", nonzero=True)
    return {"pk": multiply(GENERATOR, sk).to_dict()}, {"sk": sk}


def tags(name: str, blocks: list[list[int]], sk: int, generators: list[Point],
         mode: str = "independent") -> list[Point]:
    if mode not in MODES:
        raise ValueError(f"unknown baseline mode: {mode}")
    result = []
    for index, block in enumerate(blocks):
        if len(block) != len(generators):
            raise ValueError("block width must match the sector generator count")
        base = block_base(name, index)
        if mode == "independent":
            for generator, value in zip(generators, block):
                base = add(base, multiply(generator, value))
        else:
            base = add(base, multiply(generators[0], sum(block)))
        result.append(multiply(base, sk))
    return result


def challenge(name: str, blocks: int, seed: bytes) -> dict:
    """Full-coverage challenge: every block carries an independent coefficient.

    Full coverage is a deliberate simplification of the baseline.  Real PoR
    samples a subset and relies on an erasure code; that refinement is not
    needed to test whether the analysis rule separates the two structures.
    """
    coefficients = [hash_int(ORDER, b"baseline-challenge", name.encode(), seed,
                             index.to_bytes(8, "big"), nonzero=True) for index in range(blocks)]
    return {"name": name, "coefficients": coefficients}


def respond_from_data(blocks: list[list[int]], tag_list: list[Point], challenge_value: dict,
                      mode: str = "independent") -> dict:
    coefficients = challenge_value["coefficients"]
    if len(blocks) != len(coefficients) or len(tag_list) != len(coefficients):
        raise ValueError("challenge does not match the file")
    sigma = Point()
    for coefficient, tag in zip(coefficients, tag_list):
        sigma = add(sigma, multiply(tag, coefficient))
    if mode == "independent":
        width = len(blocks[0])
        aggregates = [sum(coefficient * block[j] for coefficient, block in zip(coefficients, blocks))
                      % ORDER for j in range(width)]
    else:
        aggregates = [sum(coefficient * sum(block) for coefficient, block in zip(coefficients, blocks))
                      % ORDER]
    return {"name": challenge_value["name"], "mu": aggregates, "sigma": sigma.to_dict()}


def respond_from_block_sums(block_sums: list[int], tag_list: list[Point], challenge_value: dict,
                            mode: str, sectors: int) -> dict:
    """Prover that deleted the sector detail and kept only per-block sums."""
    coefficients = challenge_value["coefficients"]
    if len(block_sums) != len(coefficients) or len(tag_list) != len(coefficients):
        raise ValueError("challenge does not match the cached state")
    sigma = Point()
    for coefficient, tag in zip(coefficients, tag_list):
        sigma = add(sigma, multiply(tag, coefficient))
    total = sum(coefficient * value for coefficient, value in zip(coefficients, block_sums)) % ORDER
    if mode == "independent":
        # The cache only knows the sector total; it has to place it somewhere.
        aggregates = [total] + [0] * (sectors - 1)
    else:
        aggregates = [total]
    return {"name": challenge_value["name"], "mu": aggregates, "sigma": sigma.to_dict()}


def verify(public: dict, generators: list[Point], challenge_value: dict, response: dict,
           mode: str = "independent") -> bool:
    try:
        if response["name"] != challenge_value["name"]:
            return False
        coefficients = challenge_value["coefficients"]
        mu = [int(value) % ORDER for value in response["mu"]]
        expected_width = len(generators) if mode == "independent" else 1
        if len(mu) != expected_width:
            return False
        sigma = Point.from_dict(response["sigma"])
        if not in_subgroup(sigma):
            return False
        pk = Point.from_dict(public["pk"])
        left = Point()
        for index, coefficient in enumerate(coefficients):
            left = add(left, multiply(block_base(challenge_value["name"], index), coefficient))
        if mode == "independent":
            for generator, value in zip(generators, mu):
                left = add(left, multiply(generator, value))
        else:
            left = add(left, multiply(generators[0], mu[0]))
        return pairing(sigma, GENERATOR) == pairing(left, pk)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def solve_mod(matrix: list[list[int]], vector: list[int], modulus: int = ORDER) -> list[int]:
    """Gauss-Jordan over Z_N; every pivot must be invertible modulo N."""
    if not matrix or len(matrix) != len(vector) or any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError("invalid linear system")
    rows = [[value % modulus for value in row] + [value % modulus]
            for row, value in zip(matrix, vector)]
    height, width = len(rows), len(matrix[0])
    if height < width:
        raise ValueError("underdetermined system")
    pivot_row = 0
    pivots: list[int] = []
    for column in range(width):
        pivot = next((r for r in range(pivot_row, height)
                      if rows[r][column] and _invertible(rows[r][column], modulus)), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        inverse = pow(rows[pivot_row][column], -1, modulus)
        rows[pivot_row] = [value * inverse % modulus for value in rows[pivot_row]]
        for r in range(height):
            if r != pivot_row and rows[r][column]:
                factor = rows[r][column]
                rows[r] = [(x - factor * y) % modulus for x, y in zip(rows[r], rows[pivot_row])]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == height:
            break
    if len(pivots) < width:
        raise ValueError("rank-deficient or non-invertible system over Z_N")
    answer = [0] * width
    for r, column in enumerate(pivots[:width]):
        answer[column] = rows[r][-1]
    return answer


def _invertible(value: int, modulus: int) -> bool:
    from math import gcd

    return gcd(value % modulus, modulus) == 1


def extract(blocks: int, sectors: int, challenges: list[dict], responses: list[dict]) -> list[list[int]]:
    """Recover every sector coordinate from enough accepted responses.

    Only `independent` responses are extractable: each challenge contributes one
    equation per sector, and the coefficient matrix must reach rank `blocks`.
    """
    matrix = [list(challenge_value["coefficients"]) for challenge_value in challenges]
    recovered = [[0] * sectors for _ in range(blocks)]
    for sector in range(sectors):
        vector = [int(response["mu"][sector]) % ORDER for response in responses]
        solution = solve_mod(matrix, vector)
        for index in range(blocks):
            recovered[index][sector] = solution[index]
    return recovered


def extraction_rank(challenges: list[dict], blocks: int) -> int:
    """Rank of the coefficient matrix over Z_N, counting invertible pivots only."""
    rows = [[value % ORDER for value in challenge_value["coefficients"]] for challenge_value in challenges]
    rank = 0
    used = 0
    for column in range(blocks):
        pivot = next((r for r in range(used, len(rows))
                      if rows[r][column] and _invertible(rows[r][column], ORDER)), None)
        if pivot is None:
            continue
        rows[used], rows[pivot] = rows[pivot], rows[used]
        inverse = pow(rows[used][column], -1, ORDER)
        rows[used] = [value * inverse % ORDER for value in rows[used]]
        for r in range(len(rows)):
            if r != used and rows[r][column]:
                factor = rows[r][column]
                rows[r] = [(x - factor * y) % ORDER for x, y in zip(rows[r], rows[used])]
        rank += 1
        used += 1
    return rank
