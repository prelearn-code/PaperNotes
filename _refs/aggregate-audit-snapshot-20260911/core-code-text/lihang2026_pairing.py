"""Reduced-parameter prime-order type-1 bilinear group for Li Hang 2026.

Li Hang 2026 specifies a large prime ``q``, cyclic groups ``G``/``G_T`` of order
``q`` and a bilinear map ``e: G x G -> G_T``.  That is a symmetric (type-1)
prime-order pairing group.  This module instantiates it on the same
supersingular curve family already used for the Song case
(``y^2 = x^3 + x`` over ``F_r``, ``#E(F_r) = 120*p*q``, embedding degree 2) by
restricting to the prime-order subgroup of order ``p = 2^31 - 1``.

The distortion map plus reduced Tate pairing construction mirrors
``song2025_pairing``; the code is repeated here on purpose so that the Song
source fingerprint stays frozen and the two cases stay independently auditable.

Parameters are intentionally small enough for reproducible tests and provide no
production security.  A full security-parameter instantiation would need a
prime-order pairing-friendly curve such as BN/BLS, which is out of scope.
"""
from __future__ import annotations

from dataclasses import dataclass

from .song2025_pairing import (
    COFACTOR as _CURVE_COFACTOR,
    CURVE_A,
    FIELD,
    GENERATOR as FULL_ORDER_GENERATOR,
    Fp2,
    Point,
    add,
    is_prime,
    multiply_raw,
    on_curve,
)

# Subgroup used as Li Hang's group G.
GROUP_ORDER = 2_147_483_647  # 2^31 - 1, Mersenne prime
# The Song generator has order p*q; multiplying by q lands in the order-p subgroup.
COFACTOR_STEP = 2_147_483_629

INFINITY = Point()


def _distort(point: Point) -> tuple[Fp2, Fp2]:
    """Map a point into E(F_{r^2}) so that both pairing inputs can be in F_r."""
    if point.infinity:
        raise ValueError("cannot distort infinity")
    return Fp2(-point.x), Fp2(0, point.y)


def _line_ratio(left: Point, right: Point, target: tuple[Fp2, Fp2]) -> Fp2:
    if left.infinity or right.infinity:
        return Fp2(1)
    xq, yq = target
    if left.x == right.x and (left.y + right.y) % FIELD == 0:
        return xq - Fp2(left.x)
    if left == right:
        if left.y == 0:
            return xq - Fp2(left.x)
        slope = (3 * left.x * left.x + CURVE_A) * pow(2 * left.y, -1, FIELD) % FIELD
    else:
        slope = (right.y - left.y) * pow((right.x - left.x) % FIELD, -1, FIELD) % FIELD
    combined = add(left, right)
    numerator = yq - Fp2(left.y) - Fp2(slope) * (xq - Fp2(left.x))
    if combined.infinity:
        return numerator
    return numerator / (xq - Fp2(combined.x))


def pairing(left: Point, right: Point) -> Fp2:
    """Symmetric reduced Tate pairing on the order-GROUP_ORDER subgroup."""
    if left.infinity or right.infinity:
        return Fp2(1)
    if not in_group(left) or not in_group(right):
        raise ValueError("pairing input outside prime-order subgroup")
    target = _distort(right)
    bits = bin(GROUP_ORDER)[3:]
    accumulator = Fp2(1)
    running = left
    for bit in bits:
        accumulator = accumulator * accumulator * _line_ratio(running, running, target)
        running = add(running, running)
        if bit == "1":
            accumulator = accumulator * _line_ratio(running, left, target)
            running = add(running, left)
    return accumulator ** ((FIELD * FIELD - 1) // GROUP_ORDER)


def in_group(point: Point) -> bool:
    return on_curve(point) and not point.infinity and multiply_raw(point, GROUP_ORDER).infinity


def hash_to_group(*parts: bytes) -> Point:
    """Hash arbitrary bytes into the prime-order subgroup.

    Uses the same x-coordinate/cofactor derivation as the Song backend, then
    projects into the order-``GROUP_ORDER`` subgroup.  No discrete-log relation
    to GENERATOR is exposed.
    """
    from .common import digest

    counter = 0
    while True:
        x = int.from_bytes(digest(b"lihang-hash-to-group", *parts, counter.to_bytes(8, "big")),
                           "big") % FIELD
        y_squared = (x * x * x + CURVE_A * x) % FIELD
        y = pow(y_squared, (FIELD + 1) // 4, FIELD)
        counter += 1
        if y * y % FIELD != y_squared:
            continue
        candidate = multiply_raw(Point(x, y), _CURVE_COFACTOR)
        if candidate.infinity:
            continue
        candidate = multiply_raw(candidate, COFACTOR_STEP)
        if candidate.infinity:
            continue
        if not multiply_raw(candidate, GROUP_ORDER).infinity:
            raise AssertionError("subgroup projection failed")
        return candidate


def exponentiate(scalar: int) -> Point:
    """g^scalar for scalar in Z_q, without reducing modulo the curve group order."""
    return multiply_raw(GENERATOR, scalar % GROUP_ORDER)


def target_to_dict(value: Fp2) -> dict:
    return {"a": hex(value.a), "b": hex(value.b)}


def target_from_dict(value: dict) -> Fp2:
    return Fp2(int(value["a"], 16), int(value["b"], 16))


GENERATOR = multiply_raw(FULL_ORDER_GENERATOR, COFACTOR_STEP)
if GENERATOR.infinity or not multiply_raw(GENERATOR, GROUP_ORDER).infinity:
    raise AssertionError("prime-order subgroup projection failed")
if multiply_raw(GENERATOR, 1).infinity:
    raise AssertionError("degenerate generator")


def parameters() -> dict:
    return {
        "field": FIELD,
        "group_order": GROUP_ORDER,
        "group_order_bits": GROUP_ORDER.bit_length(),
        "group_order_is_prime": is_prime(GROUP_ORDER),
        "curve": "y^2=x^3+x",
        "embedding_degree": 2,
        "pairing": "distortion-based reduced Tate pairing, symmetric (type 1)",
        "generator": GENERATOR.to_dict(),
        "level": "L2-reduced-parameters",
        "security_note": "reduced functional parameters; not production security",
    }
