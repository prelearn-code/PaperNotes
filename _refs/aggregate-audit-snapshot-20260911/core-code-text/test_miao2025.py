from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.miao2025_protocol import (
    PROFILES,
    authgen,
    cached_state,
    challenge,
    keygen,
    proof_from_cached,
    proof_from_data,
    setup,
    verify,
    with_revealed_weights,
)

BLOCKS = 4
SECTORS = 3
KEYWORD_INDEX = 7


class Miao2025Tests(unittest.TestCase):
    """Miao 2025 is the second negative control: a real published scheme whose
    audit path must not be flagged by the analysis rule."""

    def setUp(self):
        self.parameters = setup(b"miao-tests")
        self.owner = keygen(self.parameters, "id-1", b"miao-owner")
        self.blocks = [[(index * 5 + k * 7) % 64 for k in range(SECTORS)]
                       for index in range(BLOCKS)]
        self.challenge = challenge(BLOCKS, 2, b"miao-chal")

    def state(self, profile: str = "published"):
        return authgen(self.parameters, self.owner, self.blocks, KEYWORD_INDEX,
                       b"miao-a", profile=profile)

    def test_honest_path_accepts(self):
        for profile in PROFILES:
            state = self.state(profile)
            proof = proof_from_data(state, self.blocks, self.challenge)
            self.assertTrue(verify(self.parameters, self.owner, state, self.challenge, proof),
                            profile)

    def test_published_profile_rejects_the_cached_projection_prover(self):
        """The negative control: with a_k secret the cloud cannot form prod_k A_k^{mu_k}."""
        state = self.state("published")
        cached = cached_state(self.blocks, "published")
        self.assertIn("block_sums", cached)
        self.assertIsNone(state["weights_if_revealed"])
        proof = proof_from_cached(state, cached, self.challenge)
        self.assertEqual(len(proof["mu"]), SECTORS)
        self.assertFalse(verify(self.parameters, self.owner, state, self.challenge, proof))

    def test_revealing_the_weights_breaks_the_same_construction(self):
        state = self.state("weights_public")
        proof = proof_from_cached(state, with_revealed_weights(state, self.blocks),
                                  self.challenge)
        self.assertTrue(verify(self.parameters, self.owner, state, self.challenge, proof))
        plain = proof_from_cached(state, cached_state(self.blocks, "published"), self.challenge)
        self.assertFalse(verify(self.parameters, self.owner, state, self.challenge, plain))

    def test_the_two_profiles_produce_identical_tags(self):
        published = self.state("published")
        revealed = self.state("weights_public")
        self.assertEqual(published["tags"], revealed["tags"])
        self.assertEqual(published["omega"], revealed["omega"])
        self.assertEqual(published["bases"], revealed["bases"])

    def test_tampering_and_misbinding_are_rejected(self):
        state = self.state("published")
        good = proof_from_data(state, self.blocks, self.challenge)
        self.assertTrue(verify(self.parameters, self.owner, state, self.challenge, good))
        broken_mu = copy.deepcopy(good)
        broken_mu["mu"][0] = (broken_mu["mu"][0] + 1) % (2 ** 31 - 1)
        self.assertFalse(verify(self.parameters, self.owner, state, self.challenge, broken_mu))
        broken_t = copy.deepcopy(good)
        broken_t["T"] = state["bases"][0]
        self.assertFalse(verify(self.parameters, self.owner, state, self.challenge, broken_t))
        other_challenge = challenge(BLOCKS, 3, b"other-chal")
        self.assertFalse(verify(self.parameters, self.owner, state, other_challenge, good))
        other_owner = keygen(self.parameters, "id-2", b"miao-owner-2")
        self.assertFalse(verify(self.parameters, other_owner, state, self.challenge, good))
        # Substituting another keyword's Omega while the verifier keeps THIS
        # keyword's H4 must fail.  (Replacing the whole state does not test
        # anything: Omega and H4 then cancel consistently, because T does not
        # depend on the keyword index.)
        other_keyword = authgen(self.parameters, self.owner, self.blocks, KEYWORD_INDEX + 1,
                                b"miao-a")
        mixed = copy.deepcopy(state)
        mixed["omega"] = other_keyword["omega"]
        self.assertFalse(verify(self.parameters, self.owner, mixed, self.challenge, good))

    def test_keyword_index_appears_only_in_the_cancelling_terms(self):
        """The tag set does not depend on the keyword index, so T is reusable
        across keywords; only Omega and H4 carry the keyword, and they cancel."""
        first = self.state("published")
        other_keyword = authgen(self.parameters, self.owner, self.blocks, KEYWORD_INDEX + 1,
                                b"miao-a")
        self.assertEqual(first["tags"], other_keyword["tags"])
        self.assertNotEqual(first["omega"], other_keyword["omega"])

    def test_corrupted_data_is_detected(self):
        state = self.state("published")
        damaged = list(self.blocks)
        damaged[self.challenge["indices"][0]] = [0] * SECTORS
        proof = proof_from_data(state, damaged, self.challenge)
        self.assertFalse(verify(self.parameters, self.owner, state, self.challenge, proof))


if __name__ == "__main__":
    unittest.main(verbosity=2)
