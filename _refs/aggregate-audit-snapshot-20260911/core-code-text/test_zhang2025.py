from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.common import dump_json, load_json
from scripts.lihang2026_pairing import GROUP_ORDER, Point, in_group
from scripts.zhang2025_protocol import (
    MODES,
    audit_key,
    authentication_tags,
    bases_of,
    block_hash,
    block_sum,
    cached_state,
    challenge,
    file_public_key,
    minimal_state_bits,
    owner_key,
    proof_from_cache,
    proof_from_data,
    proof_from_single_block,
    setup,
    verify_audit,
    verify_upload,
)

BLOCKS = 4
SECTORS = 3
K_L = 123456789


class ZhangProtocolTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [[(index * 7 + sector * 11) % 64 for sector in range(SECTORS)]
                       for index in range(BLOCKS)]
        self.challenge = challenge(BLOCKS, 2, b"zhang-tests")

    def system(self, mode: str):
        parameters = setup(b"zhang-tests", sectors=SECTORS, mode=mode)
        tags = authentication_tags(parameters, self.blocks, K_L)
        key = audit_key(b"zhang-audit-key")
        owner = owner_key(b"zhang-owner-key")
        return parameters, tags, key, owner

    def test_upload_check_passes_in_both_profiles(self):
        for mode in MODES:
            parameters, tags, key, owner = self.system(mode)
            public_key = file_public_key(K_L, owner["s_a"])
            self.assertTrue(verify_upload(parameters, self.blocks, tags, public_key,
                                          owner["s_a"], b"upload"))
            # A tag set for a different key must not verify.
            wrong = file_public_key(K_L + 1, owner["s_a"])
            self.assertFalse(verify_upload(parameters, self.blocks, tags, wrong,
                                           owner["s_a"], b"upload"))

    def test_honest_audit_passes_in_both_profiles(self):
        for mode in MODES:
            parameters, tags, key, _ = self.system(mode)
            public_key = file_public_key(K_L, key["s_t"])
            proof = proof_from_data(parameters, self.blocks, tags, self.challenge, key)
            self.assertTrue(verify_audit(parameters, public_key, self.challenge, proof), mode)

    def test_cached_state_reproduces_the_honest_proof(self):
        """In the literal profile the honest proof only needs hash, sum and tag."""
        parameters, tags, key, _ = self.system("literal")
        state = cached_state(parameters, self.blocks, tags, key)
        honest = proof_from_data(parameters, self.blocks, tags, self.challenge, key)
        cached = proof_from_cache(parameters,
                                  [Point.from_dict(value) for value in state["hashes"]],
                                  state["sums"], tags, self.challenge, key)
        self.assertEqual(honest["Gamma"], cached["Gamma"])
        self.assertEqual(honest["Psi"], cached["Psi"])
        self.assertEqual(honest["p"], cached["p"])

    def test_verification_does_not_bind_the_challenge(self):
        """Eq. (8) / Algorithm 1 take no challenge input, so any consistent proof passes."""
        parameters, tags, key, _ = self.system("literal")
        public_key = file_public_key(K_L, key["s_t"])
        other = challenge(BLOCKS, 3, b"a-completely-different-challenge")
        self.assertNotEqual(other["indices"], self.challenge["indices"])
        proof = proof_from_data(parameters, self.blocks, tags, other, key)
        self.assertTrue(verify_audit(parameters, public_key, self.challenge, proof))
        self.assertTrue(verify_audit(parameters, public_key, other, proof))

    def test_single_retained_block_answers_every_challenge(self):
        """One block's hash, sum and tag are enough: the minimal cheating state is O(1)."""
        parameters, tags, key, _ = self.system("literal")
        public_key = file_public_key(K_L, key["s_t"])
        state = cached_state(parameters, self.blocks, tags, key)
        kept = next(index for index in range(BLOCKS) if index not in self.challenge["indices"])
        kept_hash = Point.from_dict(state["hashes"][kept])
        kept_sum = state["sums"][kept]
        coefficient = self.challenge["coefficients"][0]
        proof = proof_from_single_block(parameters, kept, coefficient, kept_hash, kept_sum,
                                        tags[kept], key)
        self.assertEqual(proof["used_indices"], [kept])
        # The challenge it is verified against need not even contain the kept block.
        self.assertNotIn(kept, self.challenge["indices"])
        self.assertTrue(verify_audit(parameters, public_key, self.challenge, proof))
        for seed in (b"later-audit-1", b"later-audit-2", b"later-audit-3"):
            later = challenge(BLOCKS, 3, seed)
            self.assertTrue(verify_audit(parameters, public_key, later, proof), seed)

    def test_single_block_prover_fails_the_repaired_profile(self):
        parameters, tags, key, _ = self.system("sector_bound")
        public_key = file_public_key(K_L, key["s_t"])
        state = cached_state(parameters, self.blocks, tags, key)
        proof = proof_from_single_block(parameters, 1, self.challenge["coefficients"][0],
                                        Point.from_dict(state["hashes"][1]), state["sums"][1],
                                        tags[1], key)
        self.assertFalse(verify_audit(parameters, public_key, self.challenge, proof))

    def test_block_hash_depends_on_the_whole_block(self):
        """Same sector sum, different layout: the cached hash still differs, so a
        cheating server has to keep the hash as well as the sum."""
        other = [[block_sum(block), 0, 0] for block in self.blocks]
        self.assertNotEqual(other, self.blocks)
        parameters, tags, _, _ = self.system("literal")
        other_tags = authentication_tags(parameters, other, K_L)
        self.assertNotEqual([tag.to_dict() for tag in tags], [tag.to_dict() for tag in other_tags])

    def test_sector_bound_profile_distinguishes_the_same_layouts(self):
        other = [[block_sum(block), 0, 0] for block in self.blocks]
        parameters, tags, _, _ = self.system("sector_bound")
        other_tags = authentication_tags(parameters, other, K_L)
        self.assertNotEqual([tag.to_dict() for tag in tags], [tag.to_dict() for tag in other_tags])

    def test_cached_prover_passes_literal_and_fails_the_repair(self):
        for mode, expected in (("literal", True), ("sector_bound", False)):
            parameters, tags, key, _ = self.system(mode)
            public_key = file_public_key(K_L, key["s_t"])
            state = cached_state(parameters, self.blocks, tags, key)
            proof = proof_from_cache(parameters, [Point.from_dict(value) for value in state["hashes"]],
                                     state["sums"], tags, self.challenge, key)
            self.assertEqual(verify_audit(parameters, public_key, self.challenge, proof), expected,
                             mode)

    def test_both_readings_of_the_printed_proof_list_are_accepted(self):
        """Eq. (7) prints one value per block; the verification sums over s.  Both
        readings are accepted, and in both only the *total* is constrained."""
        for shape, expected in (("per_block", None), ("per_sector", SECTORS)):
            parameters = setup(b"zhang-tests", sectors=SECTORS, mode="literal", shape=shape)
            tags = authentication_tags(parameters, self.blocks, K_L)
            key = audit_key(b"zhang-audit-key")
            public_key = file_public_key(K_L, key["s_t"])
            honest = proof_from_data(parameters, self.blocks, tags, self.challenge, key)
            state = cached_state(parameters, self.blocks, tags, key)
            cached = proof_from_cache(parameters,
                                      [Point.from_dict(value) for value in state["hashes"]],
                                      state["sums"], tags, self.challenge, key)
            self.assertTrue(verify_audit(parameters, public_key, self.challenge, honest), shape)
            self.assertTrue(verify_audit(parameters, public_key, self.challenge, cached), shape)
            self.assertEqual(len(honest["p"]),
                             len(self.challenge["indices"]) if expected is None else expected, shape)
            zeroed = dict(honest, p=[0] * len(honest["p"]))
            self.assertFalse(verify_audit(parameters, public_key, self.challenge, zeroed), shape)
            collapsed = dict(honest, p=[sum(honest["p"]) % GROUP_ORDER])
            self.assertTrue(verify_audit(parameters, public_key, self.challenge, collapsed), shape)
            self.assertEqual(len(bases_of(parameters)), 1)

    def test_damage_and_tampering_are_rejected(self):
        parameters, tags, key, _ = self.system("literal")
        public_key = file_public_key(K_L, key["s_t"])
        damaged = list(self.blocks)
        damaged[self.challenge["indices"][0]] = [0] * SECTORS
        self.assertFalse(verify_audit(parameters, public_key, self.challenge,
                                      proof_from_data(parameters, damaged, tags, self.challenge, key)))
        good = proof_from_data(parameters, self.blocks, tags, self.challenge, key)
        for field, value in (("p", [(good["p"][0] + 1) % GROUP_ORDER]),
                             ("Gamma", bases_of(parameters)[0].to_dict()),
                             ("Psi", bases_of(parameters)[0].to_dict())):
            broken = copy.deepcopy(good)
            broken[field] = value
            self.assertFalse(verify_audit(parameters, public_key, self.challenge, broken), field)
        renamed = challenge(BLOCKS, 2, b"other-challenge")
        self.assertFalse(verify_audit(parameters, public_key, renamed, broken))
        self.assertFalse(verify_audit(parameters, file_public_key(K_L + 1, key["s_t"]),
                                      self.challenge, good))

    def test_minimal_state_accounting(self):
        """At paper scale one hash plus one field element per block beats s sectors.

        The saving needs ``s > 1 + |hash|/|Z_p|``; with equal 256-bit sizes that is
        ``s >= 3``.  Under this workspace's reduced parameters a group element is
        much larger than a field element, so the cached state would *not* be
        smaller -- the claim is therefore established by parameter analysis, not
        by the reduced-parameter run.
        """
        paper = minimal_state_bits(100, 3, 256, 256)
        self.assertEqual(paper["honest_ciphertext_bits"], 100 * 3 * 256)
        self.assertEqual(paper["cached_state_bits"], 100 * (256 + 256))
        self.assertLess(paper["cached_state_bits"], paper["honest_ciphertext_bits"])
        wide = minimal_state_bits(100, 100, 256, 256)
        self.assertGreater(wide["compression_ratio"], 40)
        reduced = minimal_state_bits(32, 3, 138, 31)
        self.assertGreater(reduced["cached_state_bits"], reduced["honest_ciphertext_bits"])
        self.assertEqual(minimal_state_bits(4, 5, 138, 31)["sectors"], 5)

    def test_isolated_process_uses_only_hash_sum_and_tag(self):
        parameters, tags, key, _ = self.system("literal")
        public_key = file_public_key(K_L, key["s_t"])
        state = cached_state(parameters, self.blocks, tags, key)
        encoded = json.dumps(state, sort_keys=True)
        for forbidden in ('"ciphertext"', '"blocks"', '"plaintext"', '"k_l"', '"decrypt"'):
            self.assertNotIn(forbidden, encoded)
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            dump_json(temp / "state.json", state)
            dump_json(temp / "requests.json", [{"kind": "cached", "distribute": "first",
                                                "challenge": self.challenge}])
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "zhang2025_prover_cli.py"),
                "--state", str(temp / "state.json"), "--requests", str(temp / "requests.json"),
                "--output", str(temp / "responses.json"),
            ], check=True, cwd=ROOT)
            proof = load_json(temp / "responses.json")[0]
        self.assertTrue(verify_audit(parameters, public_key, self.challenge, proof))

    def test_group_elements_and_hashes_are_valid(self):
        parameters, tags, _, _ = self.system("literal")
        for tag in tags:
            self.assertTrue(in_group(tag))
        self.assertTrue(in_group(bases_of(parameters)[0]))
        self.assertTrue(in_group(block_hash(0, self.blocks[0])))
        self.assertNotEqual(block_hash(0, self.blocks[0]), block_hash(1, self.blocks[0]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
