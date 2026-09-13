from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.authenticated_baseline import (
    ORDER,
    challenge,
    extract,
    extraction_rank,
    respond_from_block_sums,
    respond_from_data,
    sector_generators,
    setup,
    solve_mod,
    tags,
    verify,
)

BLOCKS = 4
SECTORS = 3


class AuthenticatedBaselineTests(unittest.TestCase):
    def setUp(self):
        self.public, self.secret = setup(b"baseline-tests")
        self.name = "f.bin"
        self.blocks = [[(index * 7 + sector * 11) % 64 for sector in range(SECTORS)]
                       for index in range(BLOCKS)]
        self.generators = sector_generators(SECTORS)
        self.challenges = [challenge(self.name, BLOCKS, f"seed-{k}".encode())
                           for k in range(BLOCKS + 2)]

    def responses(self, mode: str):
        tag_list = tags(self.name, self.blocks, self.secret["sk"], self.generators, mode)
        return tag_list, [respond_from_data(self.blocks, tag_list, c, mode) for c in self.challenges]

    def test_independent_baseline_honest_accepts(self):
        _, responses = self.responses("independent")
        self.assertTrue(all(verify(self.public, self.generators, c, r, "independent")
                            for c, r in zip(self.challenges, responses)))

    def test_independent_baseline_rejects_cached_block_sum_prover(self):
        tag_list = tags(self.name, self.blocks, self.secret["sk"], self.generators, "independent")
        block_sums = [sum(block) for block in self.blocks]
        accepted = sum(verify(self.public, self.generators, c,
                              respond_from_block_sums(block_sums, tag_list, c, "independent", SECTORS),
                              "independent") for c in self.challenges)
        self.assertEqual(accepted, 0)

    def test_independent_baseline_extracts_every_sector(self):
        _, responses = self.responses("independent")
        self.assertEqual(extraction_rank(self.challenges, BLOCKS), BLOCKS)
        recovered = extract(BLOCKS, SECTORS, self.challenges, responses)
        self.assertEqual(recovered, self.blocks)

    def test_shared_base_collapses_and_cached_prover_passes(self):
        tag_list = tags(self.name, self.blocks, self.secret["sk"], self.generators, "shared_base")
        block_sums = [sum(block) for block in self.blocks]
        accepted = sum(verify(self.public, self.generators, c,
                              respond_from_block_sums(block_sums, tag_list, c, "shared_base", SECTORS),
                              "shared_base") for c in self.challenges)
        self.assertEqual(accepted, len(self.challenges))
        responses = [respond_from_data(self.blocks, tag_list, c, "shared_base")
                     for c in self.challenges]
        self.assertTrue(all(len(r["mu"]) == 1 for r in responses))

    def test_shared_base_responses_are_not_injective_in_the_data(self):
        """Two different sector layouts with the same block sums are indistinguishable."""
        other = [[sum(block), 0, 0] for block in self.blocks]
        self.assertNotEqual(other, self.blocks)
        self.assertEqual([sum(block) for block in other], [sum(block) for block in self.blocks])
        tag_list = tags(self.name, self.blocks, self.secret["sk"], self.generators, "shared_base")
        other_tags = tags(self.name, other, self.secret["sk"], self.generators, "shared_base")
        self.assertEqual([t.to_dict() for t in tag_list], [t.to_dict() for t in other_tags])
        for c in self.challenges:
            self.assertEqual(respond_from_data(self.blocks, tag_list, c, "shared_base"),
                             respond_from_data(other, other_tags, c, "shared_base"))

    def test_tampered_and_misbound_responses_rejected(self):
        tag_list, responses = self.responses("independent")
        good = responses[0]
        for field, value in (("mu", [(good["mu"][0] + 1) % ORDER] + good["mu"][1:]),
                             ("sigma", self.generators[0].to_dict())):
            damaged = copy.deepcopy(good)
            damaged[field] = value
            self.assertFalse(verify(self.public, self.generators, self.challenges[0], damaged,
                                    "independent"))
        renamed = challenge("other.bin", BLOCKS, b"seed-0")
        self.assertFalse(verify(self.public, self.generators, renamed, good, "independent"))
        self.assertFalse(verify(self.public, self.generators, self.challenges[1], good, "independent"))
        self.assertFalse(verify(self.public, [self.generators[1], self.generators[0], self.generators[2]],
                                self.challenges[0], good, "independent"))

    def test_solve_mod_requires_invertible_pivot(self):
        with self.assertRaises(ValueError):
            solve_mod([[3, 0], [0, 1]], [3, 1], modulus=15)
        self.assertEqual(solve_mod([[3, 0], [0, 1]], [3, 1], modulus=7), [1, 1])

    def test_underdetermined_extraction_is_refused(self):
        _, responses = self.responses("independent")
        with self.assertRaises(ValueError):
            extract(BLOCKS, SECTORS, self.challenges[:2], responses[:2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
