"""Large-parameter supersingular type-1 pairing backend.

Same construction as ``song2025_pairing``/``lihang2026_pairing`` (curve
``y^2 = x^3 + x`` over ``F_r`` with ``#E = r + 1 = 120*p*q``, embedding degree 2,
distortion-based reduced Tate pairing) but with the prime factors chosen in the
256-bit range, so that

* the composite-order subgroup has order ``N = p*q`` (~512 bits), and
* the prime-order subgroup has order ``p`` (~256 bits).

Its only purpose is to check that the reported conclusions do **not** depend on
the reduced parameters used elsewhere in this workspace.  Parameters are
deterministic and cached to JSON so repeated runs reuse them.

This file is deliberately separate from the frozen backends: those stay byte
identical so the earlier run records remain reproducible from the tree.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .common import digest
from .song2025_pairing import is_prime

COFACTOR = 120
DEFAULT_BITS = 256
CACHE_PATH = Path(__file__).resolve().parents[1] / "evidence" / "large_parameters" / "parameters.json"

FIELD: int = 0
ORDER: int = 0          # composite order p*q
PRIME_ORDER: int = 0    # prime order p
P_FACTOR: int = 0
Q_FACTOR: int = 0
CURVE_A = 1


def _random_prime(rng: random.Random, bits: int) -> int:
    while True:
        candidate = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(candidate):
            return candidate


def generate_parameters(bits: int = DEFAULT_BITS, seed: int = 0x5A17) -> dict:
    """Find primes p, q and a prime field r with ``r + 1 = 120*p*q``."""
    rng = random.Random(seed)
    p = _random_prime(rng, bits)
    attempts = 0
    while True:
        attempts += 1
        q = _random_prime(rng, bits)
        if q == p:
            continue
        field = COFACTOR * p * q - 1
        if is_prime(field):
            return {"bits": bits, "seed": seed, "attempts": attempts,
                    "p": p, "q": q, "field": field, "cofactor": COFACTOR,
                    "field_bits": field.bit_length(),
                    "composite_order_bits": (p * q).bit_length(),
                    "prime_order_bits": p.bit_length()}


def load_or_generate(bits: int = DEFAULT_BITS) -> dict:
    if CACHE_PATH.exists():
        cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if cached.get("bits") == bits:
            return cached
    parameters = generate_parameters(bits)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(parameters, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
    return parameters


def configure(bits: int = DEFAULT_BITS) -> dict:
    """Set the module-level parameters (generating and caching them if needed)."""
    global FIELD, ORDER, PRIME_ORDER, P_FACTOR, Q_FACTOR
    parameters = load_or_generate(bits)
    FIELD = parameters["field"]
    P_FACTOR = parameters["p"]
    Q_FACTOR = parameters["q"]
    ORDER = P_FACTOR * Q_FACTOR
    PRIME_ORDER = P_FACTOR
    return parameters


@dataclass(frozen=True)
class Fp2:
    a: int
    b: int = 0

    def __post_init__(self):
        object.__setattr__(self, "a", self.a % FIELD)
        object.__setattr__(self, "b", self.b % FIELD)

    def __add__(self, other: "Fp2") -> "Fp2":
        return Fp2(self.a + other.a, self.b + other.b)

    def __sub__(self, other: "Fp2") -> "Fp2":
        return Fp2(self.a - other.a, self.b - other.b)

    def __neg__(self) -> "Fp2":
        return Fp2(-self.a, -self.b)

    def __mul__(self, other: "Fp2") -> "Fp2":
        return Fp2(self.a * other.a - self.b * other.b,
                   self.a * other.b + self.b * other.a)

    def inverse(self) -> "Fp2":
        norm = (self.a * self.a + self.b * self.b) % FIELD
        if norm == 0:
            raise ZeroDivisionError("zero in Fp2")
        inv = pow(norm, -1, FIELD)
        return Fp2(self.a * inv, -self.b * inv)

    def __truediv__(self, other: "Fp2") -> "Fp2":
        return self * other.inverse()

    def __pow__(self, exponent: int) -> "Fp2":
        if exponent < 0:
            return self.inverse() ** -exponent
        result = Fp2(1)
        base = self
        while exponent:
            if exponent & 1:
                result = result * base
            base = base * base
            exponent >>= 1
        return result

    def to_dict(self) -> dict:
        return {"a": hex(self.a), "b": hex(self.b)}


@dataclass(frozen=True)
class Point:
    x: int | None = None
    y: int | None = None

    @property
    def infinity(self) -> bool:
        return self.x is None

    def to_dict(self) -> dict:
        if self.infinity:
            return {"infinity": True}
        return {"x": hex(int(self.x)), "y": hex(int(self.y))}

    @classmethod
    def from_dict(cls, value: dict) -> "Point":
        if value.get("infinity"):
            return cls()
        x, y = int(value["x"], 16), int(value["y"], 16)
        if not (0 <= x < FIELD and 0 <= y < FIELD):
            raise ValueError("non-canonical point coordinate")
        point = cls(x, y)
        if not on_curve(point):
            raise ValueError("point is not on curve")
        return point


INFINITY = Point()


def on_curve(point: Point) -> bool:
    if point.infinity:
        return True
    return (0 <= point.x < FIELD and 0 <= point.y < FIELD
            and (point.y * point.y - (point.x * point.x * point.x + CURVE_A * point.x))
            % FIELD == 0)


def negate(point: Point) -> Point:
    return point if point.infinity else Point(point.x, -point.y % FIELD)


def add(left: Point, right: Point) -> Point:
    if left.infinity:
        return right
    if right.infinity:
        return left
    if left.x == right.x and (left.y + right.y) % FIELD == 0:
        return INFINITY
    if left == right:
        if left.y == 0:
            return INFINITY
        slope = (3 * left.x * left.x + CURVE_A) * pow(2 * left.y, -1, FIELD) % FIELD
    else:
        slope = (right.y - left.y) * pow((right.x - left.x) % FIELD, -1, FIELD) % FIELD
    x3 = (slope * slope - left.x - right.x) % FIELD
    y3 = (slope * (left.x - x3) - left.y) % FIELD
    return Point(x3, y3)


def multiply_raw(point: Point, scalar: int) -> Point:
    if scalar < 0:
        return multiply_raw(negate(point), -scalar)
    result = INFINITY
    current = point
    while scalar:
        if scalar & 1:
            result = add(result, current)
        current = add(current, current)
        scalar >>= 1
    return result


def multiply(point: Point, scalar: int) -> Point:
    return multiply_raw(point, scalar % ORDER)


def _sqrt(value: int) -> int | None:
    root = pow(value % FIELD, (FIELD + 1) // 4, FIELD)
    return root if root * root % FIELD == value % FIELD else None


def _point_from_material(material: bytes, require_full_composite_order: bool) -> Point:
    counter = 0
    while True:
        x = int.from_bytes(digest(b"large-curve", material, counter.to_bytes(8, "big")),
                           "big") % FIELD
        y = _sqrt((x * x * x + CURVE_A * x) % FIELD)
        counter += 1
        if y is None:
            continue
        point = multiply_raw(Point(x, y), COFACTOR)
        if point.infinity:
            continue
        if not multiply_raw(point, ORDER).infinity:
            raise AssertionError("cofactor projection failed")
        if require_full_composite_order and (multiply_raw(point, P_FACTOR).infinity
                                             or multiply_raw(point, Q_FACTOR).infinity):
            continue
        return point


def hash_to_point(*parts: bytes) -> Point:
    return _point_from_material(digest(b"large-hash-to-point", *parts), False)


def _distort(point: Point) -> tuple[Fp2, Fp2]:
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


def _miller(left: Point, right: Point, loop_order: int) -> Fp2:
    target = _distort(right)
    bits = bin(loop_order)[3:]
    accumulator = Fp2(1)
    running = left
    for bit in bits:
        accumulator = accumulator * accumulator * _line_ratio(running, running, target)
        running = add(running, running)
        if bit == "1":
            accumulator = accumulator * _line_ratio(running, left, target)
            running = add(running, left)
    return accumulator


def pairing_composite(left: Point, right: Point) -> Fp2:
    if left.infinity or right.infinity:
        return Fp2(1)
    if not in_composite_subgroup(left) or not in_composite_subgroup(right):
        raise ValueError("pairing input outside the order-N subgroup")
    return _miller(left, right, ORDER) ** ((FIELD * FIELD - 1) // ORDER)


def pairing_prime(left: Point, right: Point) -> Fp2:
    if left.infinity or right.infinity:
        return Fp2(1)
    if not in_prime_subgroup(left) or not in_prime_subgroup(right):
        raise ValueError("pairing input outside the prime-order subgroup")
    return _miller(left, right, PRIME_ORDER) ** ((FIELD * FIELD - 1) // PRIME_ORDER)


def in_composite_subgroup(point: Point) -> bool:
    return on_curve(point) and not point.infinity and multiply_raw(point, ORDER).infinity


def in_prime_subgroup(point: Point) -> bool:
    return on_curve(point) and not point.infinity and multiply_raw(point, PRIME_ORDER).infinity


_COMPOSITE_GENERATOR: Point | None = None
_PRIME_GENERATOR: Point | None = None
_MU: Point | None = None


def composite_generator() -> Point:
    global _COMPOSITE_GENERATOR
    if _COMPOSITE_GENERATOR is None:
        _COMPOSITE_GENERATOR = _point_from_material(b"generator", True)
    return _COMPOSITE_GENERATOR


def prime_generator() -> Point:
    """A generator of the order-p subgroup, derived from the composite one."""
    global _PRIME_GENERATOR
    if _PRIME_GENERATOR is None:
        candidate = multiply_raw(composite_generator(), Q_FACTOR)
        if candidate.infinity or not multiply_raw(candidate, PRIME_ORDER).infinity:
            raise AssertionError("prime subgroup projection failed")
        _PRIME_GENERATOR = candidate
    return _PRIME_GENERATOR


def mu() -> Point:
    global _MU
    if _MU is None:
        _MU = _point_from_material(b"mu", True)
    return _MU


def parameters_summary() -> dict:
    return {"bits": P_FACTOR.bit_length(), "field": hex(FIELD),
            "field_bits": FIELD.bit_length(),
            "p": hex(P_FACTOR), "q": hex(Q_FACTOR),
            "composite_order_bits": ORDER.bit_length(),
            "prime_order_bits": PRIME_ORDER.bit_length(),
            "curve": "y^2=x^3+x", "embedding_degree": 2,
            "cofactor": COFACTOR}
