from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.song2025_pairing import (
    FIELD, GENERATOR, MU, ORDER, P_FACTOR, Q_FACTOR, Point, add,
    hash_to_point, in_subgroup, is_prime, multiply, multiply_raw, on_curve, pairing,
)


class SongPairingBackendTests(unittest.TestCase):
    def test_parameters_and_subgroup_order(self):
        self.assertTrue(is_prime(P_FACTOR))
        self.assertTrue(is_prime(Q_FACTOR))
        self.assertTrue(is_prime(FIELD))
        self.assertEqual(FIELD % 4, 3)
        self.assertTrue(in_subgroup(GENERATOR))
        self.assertTrue(multiply_raw(GENERATOR, ORDER).infinity)
        self.assertFalse(multiply_raw(GENERATOR, P_FACTOR).infinity)
        self.assertFalse(multiply_raw(GENERATOR, Q_FACTOR).infinity)

    def test_point_serialization_and_membership(self):
        point = hash_to_point(b"file", b"block-1")
        self.assertTrue(on_curve(point))
        self.assertTrue(in_subgroup(point))
        self.assertEqual(Point.from_dict(point.to_dict()), point)
        bad = dict(point.to_dict())
        bad["y"] = hex((int(bad["y"], 16) + 1) % FIELD)
        with self.assertRaises(ValueError):
            Point.from_dict(bad)
        noncanonical = point.to_dict()
        noncanonical["x"] = hex(int(noncanonical["x"], 16) + FIELD)
        with self.assertRaises(ValueError):
            Point.from_dict(noncanonical)

    def test_group_law(self):
        self.assertEqual(add(multiply(GENERATOR, 7), multiply(GENERATOR, 11)),
                         multiply(GENERATOR, 18))
        self.assertEqual(multiply(GENERATOR, ORDER), multiply(GENERATOR, 0))

    def test_pairing_bilinearity_and_nondegeneracy(self):
        base = pairing(GENERATOR, MU)
        self.assertNotEqual(base.a, 1)
        self.assertEqual(base ** ORDER, type(base)(1))
        self.assertNotEqual(base ** P_FACTOR, type(base)(1))
        self.assertNotEqual(base ** Q_FACTOR, type(base)(1))
        self.assertEqual(pairing(multiply(GENERATOR, 7), multiply(MU, 11)), base ** 77)
        self.assertEqual(pairing(multiply(GENERATOR, 3), MU),
                         pairing(GENERATOR, multiply(MU, 3)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
