"""Reduced-parameter composite-order bilinear group for Song 2025.

This is a real elliptic-curve subgroup and reduced Tate pairing, not an
exponent-carrying simulation.  Parameters are intentionally small enough for
reproducible tests and provide no production security.
"""
from __future__ import annotations

from dataclasses import dataclass

from .common import digest

P_FACTOR = 2_147_483_647
Q_FACTOR = 2_147_483_629
ORDER = P_FACTOR * Q_FACTOR
COFACTOR = 120
FIELD = COFACTOR * ORDER - 1
CURVE_A = 1


def is_prime(value: int) -> bool:
    """Deterministic Miller-Rabin for the parameter sizes used here."""
    if value < 2:
        return False
    bases = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for base in bases:
        if value % base == 0:
            return value == base
    odd = value - 1
    power = 0
    while odd % 2 == 0:
        power += 1
        odd //= 2
    for base in bases:
        witness = pow(base, odd, value)
        if witness in (1, value - 1):
            continue
        for _ in range(power - 1):
            witness = witness * witness % value
            if witness == value - 1:
                break
        else:
            return False
    return True


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
            and (point.y * point.y - (point.x * point.x * point.x + CURVE_A * point.x)) % FIELD == 0)


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


def multiply(point: Point, scalar: int) -> Point:
    if scalar < 0:
        return multiply(negate(point), -scalar)
    result = INFINITY
    current = point
    scalar %= ORDER
    while scalar:
        if scalar & 1:
            result = add(result, current)
        current = add(current, current)
        scalar >>= 1
    return result


def _sqrt(value: int) -> int | None:
    root = pow(value % FIELD, (FIELD + 1) // 4, FIELD)
    return root if root * root % FIELD == value % FIELD else None


def _point_from_material(material: bytes, require_full_order: bool) -> Point:
    counter = 0
    while True:
        x = int.from_bytes(digest(b"song-curve", material, counter.to_bytes(8, "big")), "big") % FIELD
        y = _sqrt((x * x * x + CURVE_A * x) % FIELD)
        counter += 1
        if y is None:
            continue
        point = multiply_raw(Point(x, y), COFACTOR)
        if point.infinity:
            continue
        if not multiply_raw(point, ORDER).infinity:
            raise AssertionError("cofactor projection failed")
        if require_full_order and (multiply_raw(point, P_FACTOR).infinity
                                   or multiply_raw(point, Q_FACTOR).infinity):
            continue
        return point


def multiply_raw(point: Point, scalar: int) -> Point:
    """Scalar multiplication without reducing modulo subgroup order."""
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


GENERATOR = _point_from_material(b"generator", True)
MU = _point_from_material(b"mu", True)


def hash_to_point(*parts: bytes) -> Point:
    return _point_from_material(digest(b"hash-to-point", *parts), False)


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


def pairing(left: Point, right: Point) -> Fp2:
    if left.infinity or right.infinity:
        return Fp2(1)
    if not in_subgroup(left) or not in_subgroup(right):
        raise ValueError("pairing input outside order-N subgroup")
    target = _distort(right)
    bits = bin(ORDER)[3:]
    accumulator = Fp2(1)
    running = left
    for bit in bits:
        accumulator = accumulator * accumulator * _line_ratio(running, running, target)
        running = add(running, running)
        if bit == "1":
            accumulator = accumulator * _line_ratio(running, left, target)
            running = add(running, left)
    return accumulator ** ((FIELD * FIELD - 1) // ORDER)


def in_subgroup(point: Point) -> bool:
    return on_curve(point) and multiply_raw(point, ORDER).infinity


def parameters() -> dict:
    return {"field": FIELD, "order": ORDER, "p_factor": P_FACTOR,
            "q_factor": Q_FACTOR, "cofactor": COFACTOR,
            "curve": "y^2=x^3+x", "embedding_degree": 2,
            "generator": GENERATOR.to_dict(), "mu": MU.to_dict()}
