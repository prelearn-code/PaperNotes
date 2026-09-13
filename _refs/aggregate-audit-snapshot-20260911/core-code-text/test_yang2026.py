from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.yang2026_protocol import (
    PROFILES,
    cached_state,
    challenge,
    keygen,
    proof_from_cached,
    proof_from_data,
    setup,
    taggen,
    verify_audit,
    verify_upload,
    with_revealed_weights,
)

BLOCKS = 4
SECTORS = 3
K_L = 24680


class Yang2026Tests(unittest.TestCase):
    """Yang 2026 is the negative control: a real published scheme whose audit path
    must *not* be flagged by the analysis rule."""

    def setUp(self):
        self.parameters = setup(b"yang-tests")
        self.owner = keygen(self.parameters, "do-1", b"yang-owner")
        self.blocks = [[(index * 5 + j * 7) % 64 for j in range(SECTORS)]
                       for index in range(BLOCKS)]
        self.challenge = challenge(BLOCKS, 2, b"yang-chal")

    def state(self, profile: str = "published"):
        return taggen(self.parameters, self.owner, K_L, self.blocks, b"yang-a", profile=profile)

    def test_honest_path_accepts(self):
        for profile in PROFILES:
            state = self.state(profile)
            self.assertTrue(verify_upload(self.parameters, self.owner, state, self.blocks,
                                          b"upload"), profile)
            proof = proof_from_data(state, self.blocks, self.challenge)
            self.assertTrue(verify_audit(self.parameters, self.owner, state, self.challenge,
                                         proof), profile)

    def test_published_profile_rejects_the_cached_projection_prover(self):
        """The core negative control: with a_j secret the cloud cannot answer."""
        state = self.state("published")
        cached = cached_state(self.blocks, "published")
        self.assertIn("block_sums", cached)
        self.assertIsNone(state["weights_if_revealed"])
        proof = proof_from_cached(state, cached, self.challenge)
        self.assertEqual(len(proof["u"]), SECTORS)
        self.assertFalse(verify_audit(self.parameters, self.owner, state, self.challenge, proof))

    def test_revealing_the_weights_breaks_the_same_construction(self):
        """Sensitivity control: the rule must key on whether the projection is
        server-computable, not on the mere existence of a projection."""
        state = self.state("weights_public")
        cached = with_revealed_weights(state, self.blocks)
        proof = proof_from_cached(state, cached, self.challenge)
        self.assertTrue(verify_audit(self.parameters, self.owner, state, self.challenge, proof))
        # The same prover with only plain sector sums still fails, even in this variant.
        plain = proof_from_cached(state, cached_state(self.blocks, "published"), self.challenge)
        self.assertFalse(verify_audit(self.parameters, self.owner, state, self.challenge, plain))

    def test_the_two_profiles_produce_identical_tags(self):
        """Revealing a_j is the only difference, so the tags must coincide."""
        published = self.state("published")
        revealed = self.state("weights_public")
        self.assertEqual(published["tags"], revealed["tags"])
        self.assertEqual(published["bases"], revealed["bases"])

    def test_tampering_and_misbinding_are_rejected(self):
        state = self.state("published")
        good = proof_from_data(state, self.blocks, self.challenge)
        self.assertTrue(verify_audit(self.parameters, self.owner, state, self.challenge, good))
        broken = copy.deepcopy(good)
        broken["u"][0] = (broken["u"][0] + 1) % (2 ** 31 - 1)
        self.assertFalse(verify_audit(self.parameters, self.owner, state, self.challenge, broken))
        broken_sigma = copy.deepcopy(good)
        broken_sigma["sigma"] = state["bases"][0]
        self.assertFalse(verify_audit(self.parameters, self.owner, state, self.challenge,
                                      broken_sigma))
        other_challenge = challenge(BLOCKS, 3, b"other-chal")
        self.assertFalse(verify_audit(self.parameters, self.owner, state, other_challenge, good))
        other_owner = keygen(self.parameters, "do-2", b"yang-owner-2")
        self.assertFalse(verify_audit(self.parameters, other_owner, state, self.challenge, good))
        other_state = taggen(self.parameters, self.owner, K_L + 1, self.blocks, b"yang-a")
        self.assertFalse(verify_audit(self.parameters, self.owner, other_state,
                                      self.challenge, good))

    def test_corrupted_data_is_detected(self):
        state = self.state("published")
        damaged = list(self.blocks)
        damaged[self.challenge["indices"][0]] = [0] * SECTORS
        proof = proof_from_data(state, damaged, self.challenge)
        self.assertFalse(verify_audit(self.parameters, self.owner, state, self.challenge, proof))


if __name__ == "__main__":
    unittest.main(verbosity=2)
