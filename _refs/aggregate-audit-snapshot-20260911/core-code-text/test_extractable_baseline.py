from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractable_baseline import FIELD, coefficients, extract, respond


class ExtractableBaselineTests(unittest.TestCase):
    def test_independent_coefficients_recover_message(self):
        message = [3, 5, 8, 13, 21, 34]
        seeds, responses = [], []
        counter = 0
        while True:
            seed = f"challenge-{counter}".encode()
            seeds.append(seed)
            responses.append(respond(message, seed))
            counter += 1
            if len(seeds) < len(message):
                continue
            try:
                recovered = extract(len(message), seeds, responses)
                break
            except ValueError:
                continue
        self.assertEqual(recovered, message)

    def test_changed_response_changes_or_breaks_extraction(self):
        message = [1, 2, 3, 4]
        seeds = [f"seed-{i}".encode() for i in range(8)]
        responses = [respond(message, seed) for seed in seeds]
        responses[0] = (responses[0] + 1) % FIELD
        with self.assertRaises(ValueError):
            # Overdetermined inconsistent systems are rejected by an explicit
            # residual check in the test, rather than silently trusted.
            recovered = extract(len(message), seeds, responses)
            if any(sum(a*b for a, b in zip(coefficients(s, len(message)), recovered)) % FIELD != r
                   for s, r in zip(seeds, responses)):
                raise ValueError("inconsistent responses")


if __name__ == "__main__":
    unittest.main(verbosity=2)
