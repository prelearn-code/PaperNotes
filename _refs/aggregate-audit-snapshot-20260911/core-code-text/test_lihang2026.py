from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import lihang2026_pairing as pairing_backend
from scripts.common import dump_json, load_json
from scripts.lihang2026_protocol import (
    CHUNK_BYTES,
    GROUP_ORDER,
    HASH_MODES,
    NONCE_BYTES,
    PROFILES,
    challenge,
    digest_state_bits,
    honest_state_bits,
    initialization,
    lattice_hash,
    plain_hash,
    proof_degenerate,
    proof_from_blocks,
    proof_from_digests,
    setup,
    state_summary,
    verify,
)
from scripts.song2025_pairing import Fp2, multiply_raw

BLOCK = bytes(range(256)) * 4  # 1024 bytes, on the 16-byte chunk grid
CLOUD_KEY = "cloud-key-for-tests"


class PairingBackendTests(unittest.TestCase):
    def test_prime_order_group_and_pairing(self):
        self.assertEqual(GROUP_ORDER, 2_147_483_647)
        self.assertTrue(pairing_backend.parameters()["group_order_is_prime"])
        self.assertFalse(pairing_backend.pairing(pairing_backend.GENERATOR,
                                                 pairing_backend.GENERATOR) == Fp2(1))
        self.assertTrue(pairing_backend.in_group(pairing_backend.GENERATOR))

    def test_bilinearity_and_membership(self):
        generator = pairing_backend.GENERATOR
        left, right = multiply_raw(generator, 12345), multiply_raw(generator, 67890)
        self.assertEqual(pairing_backend.pairing(left, right),
                         pairing_backend.pairing(generator, generator) ** (12345 * 67890 % GROUP_ORDER))
        self.assertTrue(pairing_backend.in_group(multiply_raw(generator, GROUP_ORDER - 1)))
        self.assertFalse(pairing_backend.in_group(multiply_raw(generator, GROUP_ORDER)))

    def test_serialization_round_trip_and_rejection(self):
        generator = pairing_backend.GENERATOR
        self.assertEqual(pairing_backend.Point.from_dict(generator.to_dict()), generator)
        with self.assertRaises(ValueError):
            pairing_backend.Point.from_dict({"x": hex(1), "y": hex(1)})


class HashTests(unittest.TestCase):
    def test_lattice_hash_is_additive_on_chunk_grid(self):
        left = BLOCK[:512]
        right = BLOCK[512:]
        self.assertEqual(lattice_hash(BLOCK), (lattice_hash(left) + lattice_hash(right)) % GROUP_ORDER)

    def test_plain_hash_is_not_additive(self):
        left = BLOCK[:512]
        right = BLOCK[512:]
        self.assertNotEqual(plain_hash(BLOCK), (plain_hash(left) + plain_hash(right)) % GROUP_ORDER)

    def test_chunk_grid_is_enforced(self):
        with self.assertRaises(ValueError):
            lattice_hash(BLOCK[: CHUNK_BYTES - 1])


class LiHangProtocolTests(unittest.TestCase):
    def setUp(self):
        self.public, self.secret = setup(b"lihang2026-tests")
        self.blocks = [BLOCK, bytes(reversed(BLOCK)), bytes((i * 7) % 256 for i in range(1024))]
        self.file_id = "file-a"
        self.init = initialization(self.file_id, self.blocks, seed=b"tag-seed")
        self.tag_set = self.init["tag_set"]
        self.nonce = bytes(range(NONCE_BYTES))
        self.chal = challenge(len(self.blocks), 2, self.file_id, b"indices", self.nonce, 1000,
                              self.secret["auditor_sign_key"])

    def test_honest_end_to_end_both_profiles(self):
        for profile in PROFILES:
            proof = proof_from_blocks(self.blocks, self.chal, "lattice", 12345,
                                      self.secret["cloud_sign_key"],
                                      hardened_binding=(profile == "hardened"))
            self.assertTrue(verify(self.public, self.tag_set, self.chal, proof, profile))

    def test_cached_digests_reproduce_honest_proof(self):
        honest = proof_from_blocks(self.blocks, self.chal, "lattice", 999, self.secret["cloud_sign_key"])
        cached = proof_from_digests(self.init["digests"], self.chal, 999, self.secret["cloud_sign_key"])
        self.assertEqual(honest["body"], cached["body"])
        self.assertTrue(verify(self.public, self.tag_set, self.chal, cached, "literal"))

    def test_cached_digests_survive_hardened_profile(self):
        proof = proof_from_digests(self.init["digests"], self.chal, 4242,
                                   self.secret["cloud_sign_key"], hardened_binding=True)
        self.assertTrue(verify(self.public, self.tag_set, self.chal, proof, "hardened"))

    def test_hardened_profile_rejects_degenerate_s_zero(self):
        degenerate = proof_degenerate(self.chal, self.secret["cloud_sign_key"])
        self.assertTrue(verify(self.public, self.tag_set, self.chal, degenerate, "literal"))
        hardened = proof_degenerate(self.chal, self.secret["cloud_sign_key"], hardened_binding=True)
        self.assertFalse(verify(self.public, self.tag_set, self.chal, hardened, "hardened"))
        self.assertTrue(PROFILES["hardened"]["require_nonzero_s"])

    def test_nonce_is_not_bound_in_literal_profile(self):
        proof = proof_from_blocks(self.blocks, self.chal, "lattice", 77, self.secret["cloud_sign_key"])
        replay_chal = challenge(len(self.blocks), 2, self.file_id, b"indices",
                                bytes(range(1, NONCE_BYTES + 1)), 2000,
                                self.secret["auditor_sign_key"])
        self.assertEqual(replay_chal["body"]["Q"], self.chal["body"]["Q"])
        self.assertNotEqual(replay_chal["body"]["nonce"], self.chal["body"]["nonce"])
        self.assertTrue(verify(self.public, self.tag_set, replay_chal, proof, "literal"))
        self.assertFalse(verify(self.public, self.tag_set, replay_chal, proof, "hardened"))

    def test_single_digest_suffices_only_under_trusted_indexset_reading(self):
        proof = proof_from_digests([self.init["digests"][0]], self.chal, 31337,
                                   self.secret["cloud_sign_key"], indexset=[0])
        self.assertTrue(verify(self.public, self.tag_set, self.chal, proof, "literal",
                               trust_proof_indexset=True))
        self.assertFalse(verify(self.public, self.tag_set, self.chal, proof, "literal"))
        hardened = proof_from_digests([self.init["digests"][0]], self.chal, 31337,
                                      self.secret["cloud_sign_key"], indexset=[0],
                                      hardened_binding=True)
        self.assertFalse(verify(self.public, self.tag_set, self.chal, hardened, "hardened"))

    def test_damaged_data_is_detected_when_server_recomputes_from_data(self):
        damaged = list(self.blocks)
        damaged[self.chal["body"]["Q"][0]] = bytes(len(self.blocks[0]))
        proof = proof_from_blocks(damaged, self.chal, "lattice", 5, self.secret["cloud_sign_key"])
        self.assertFalse(verify(self.public, self.tag_set, self.chal, proof, "literal"))

    def test_negative_controls(self):
        proof = proof_from_digests(self.init["digests"], self.chal, 8, self.secret["cloud_sign_key"])
        tampered = copy.deepcopy(proof)
        tampered["body"]["B"] = pairing_backend.GENERATOR.to_dict()
        self.assertFalse(verify(self.public, self.tag_set, self.chal, tampered, "literal"))

        other_blocks = [bytes((i * 11 + 3) % 256 for i in range(1024)) for _ in range(len(self.blocks))]
        other = initialization("file-b", other_blocks, seed=b"other-seed")
        self.assertFalse(verify(self.public, other["tag_set"], self.chal, proof, "literal"))

        wrong_chal = challenge(len(self.blocks), 2, self.file_id, b"other-indices", self.nonce, 1000,
                               self.secret["auditor_sign_key"])
        if wrong_chal["body"]["Q"] != self.chal["body"]["Q"]:
            self.assertFalse(verify(self.public, self.tag_set, wrong_chal, proof, "literal"))

        broken_signature = copy.deepcopy(proof)
        broken_signature["signature"] = "AA==" * 8
        self.assertFalse(verify(self.public, self.tag_set, self.chal, broken_signature, "hardened"))

    def test_tags_bind_content_not_file_identity(self):
        """The tag set and the verified equation never use fileID.

        Two files with identical content therefore accept each other's proofs,
        and the fileID carried by the challenge is decorative.  This is recorded
        as a binding observation, not as a data-loss attack.
        """
        twin = initialization("file-twin", self.blocks, seed=b"twin-seed")
        proof = proof_from_digests(twin["digests"], self.chal, 5150, self.secret["cloud_sign_key"])
        self.assertNotEqual(twin["tag_set"]["basic"], self.tag_set["basic"])
        self.assertTrue(verify(self.public, twin["tag_set"], self.chal, proof, "literal"))
        renamed = challenge(len(self.blocks), 2, "file-twin", b"indices", self.nonce, 1000,
                            self.secret["auditor_sign_key"])
        self.assertTrue(verify(self.public, twin["tag_set"], renamed, proof, "literal"))
        self.assertNotEqual(renamed["body"]["file_id"], self.file_id)

    def test_plain_hash_variant_supports_the_same_cached_strategy(self):
        plain_init = initialization(self.file_id, self.blocks, hash_mode="plain", seed=b"tag-seed")
        proof = proof_from_digests(plain_init["digests"], self.chal, 606, self.secret["cloud_sign_key"])
        self.assertTrue(verify(self.public, plain_init["tag_set"], self.chal, proof, "literal"))
        self.assertIs(HASH_MODES["plain"], plain_hash)
        self.assertIs(HASH_MODES["lattice"], lattice_hash)

    def test_state_accounting(self):
        summary = state_summary(1000, 128 * 1024, 4000)
        self.assertEqual(summary["minimal_digest_state_bits"], 1000 * GROUP_ORDER.bit_length())
        self.assertEqual(summary["honest_server_state_bits"], honest_state_bits(1000, 128 * 1024))
        self.assertGreater(summary["logical_compression_ratio"], 30000)
        self.assertEqual(digest_state_bits(4), 4 * GROUP_ORDER.bit_length())


class LiHangIsolationTests(unittest.TestCase):
    def test_isolated_process_uses_only_digests(self):
        public, secret = setup(b"lihang2026-isolation")
        blocks = [BLOCK, bytes(reversed(BLOCK))]
        init = initialization("file-iso", blocks, seed=b"iso-seed")
        state = {
            "schema": "lihang2026-cached-digest-state-v1",
            "file_id": "file-iso",
            "digests": init["digests"],
            "digests_plain": initialization("file-iso", blocks, hash_mode="plain",
                                            seed=b"iso-seed")["digests"],
            "cloud_sign_key": secret["cloud_sign_key"],
            "replay_pool": [],
        }
        encoded = json.dumps(state, sort_keys=True)
        for forbidden in ("blocks", "ciphertext", "plaintext", "vehicle", "decrypt"):
            self.assertNotIn(forbidden, encoded)

        nonce = os.urandom(NONCE_BYTES)
        chal = challenge(2, 2, "file-iso", b"iso-indices", nonce, 500, secret["auditor_sign_key"])
        requests = [{"kind": "cached", "hardened_binding": False, "s": 24680, "challenge": chal}]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            dump_json(temp / "state.json", state)
            dump_json(temp / "requests.json", requests)
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "lihang2026_prover_cli.py"),
                "--state", str(temp / "state.json"), "--requests", str(temp / "requests.json"),
                "--output", str(temp / "responses.json"),
            ], check=True, cwd=ROOT)
            proof = load_json(temp / "responses.json")[0]
        self.assertTrue(verify(public, init["tag_set"], chal, proof, "literal"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
