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

from scripts.common import dump_json, load_json, sign, verify_signature
from scripts.otgpdp2025_protocol import (
    G, P, Q, CountingBloomFilter, challenge, data_process, h_group, insert, meta_gen,
    meta_verify, profile, proof_from_data, proof_from_tags, rebuild_corrected,
    retained_state, setup, update, verify,
)


class OTGPDPTests(unittest.TestCase):
    def setUp(self):
        self.public, self.secret = setup(b"otgpdp-tests")
        self.filename = "orders.bin"
        self.data = data_process(range(11, 43), b"mask-seed")
        self.tags, self.cbf = meta_gen(self.filename, self.data, cbf_size=8192)
        self.chal = challenge(len(self.data), 9, b"indices-1", b"coefficients-1",
                              self.secret["client_sign_key"])

    def honest(self):
        return proof_from_data(self.data, self.tags, self.chal, self.secret["server_sign_key"])

    def test_real_prime_order_subgroup(self):
        self.assertEqual(pow(G, Q, P), 1)
        self.assertNotEqual(G, 1)
        self.assertEqual(pow(h_group(self.filename, 0), Q, P), 1)

    def test_corrected_honest_end_to_end(self):
        self.assertTrue(meta_verify(self.filename, self.data, self.cbf, "corrected"))
        self.assertTrue(verify(self.public, self.filename, self.cbf, self.chal, self.honest(), "corrected"))

    def test_literal_greater_than_one_breaks_fresh_cbf(self):
        self.assertFalse(meta_verify(self.filename, self.data, self.cbf, "literal"))
        self.assertFalse(verify(self.public, self.filename, self.cbf, self.chal, self.honest(), "literal"))

    def test_cbf_initial_value_decides_whether_the_literal_flow_runs(self):
        """The paper fixes the threshold (">1") but never the counter initial value.

        With the usual initial 0 a fresh tag has count 1 and honest MetaVer fails.
        With initial 1, ">1" means "inserted at least once" and the literal flow is
        executable -- and then the tag-only strategy passes in that very profile.
        """
        for mode, executable in (("literal", False), ("literal_initialized", True)):
            tags, cbf = meta_gen(self.filename, self.data, cbf_size=8192, mode=mode)
            self.assertEqual(meta_verify(self.filename, self.data, cbf, mode), executable, mode)
            self.assertEqual(verify(self.public, self.filename, cbf, self.chal,
                                    self.honest(), mode), executable, mode)
            attack = proof_from_tags(self.filename, tags, self.chal, self.secret["server_sign_key"])
            self.assertEqual(verify(self.public, self.filename, cbf, self.chal, attack, mode),
                             executable, mode)
        self.assertEqual(profile("literal").cbf_initial, 0)
        self.assertEqual(profile("literal_initialized").cbf_initial, 1)
        self.assertEqual(profile("literal_initialized").cbf_minimum, 2)

    def test_tag_only_attack_matches_honest_response(self):
        attack = proof_from_tags(self.filename, self.tags, self.chal, self.secret["server_sign_key"])
        self.assertEqual(self.honest()["body"]["P"], attack["body"]["P"])
        self.assertTrue(verify(self.public, self.filename, self.cbf, self.chal, attack, "corrected"))

    def test_negative_binding_and_replay_controls(self):
        response = self.honest()
        for field in ("P", "challenge_digest"):
            damaged = copy.deepcopy(response)
            damaged["body"][field] = "0x2" if field == "P" else "00"
            self.assertFalse(verify(self.public, self.filename, self.cbf, self.chal, damaged, "corrected"))
        damaged = copy.deepcopy(response)
        damaged["body"]["tags"][0] = hex(int(damaged["body"]["tags"][0], 16) * G % P)
        self.assertFalse(verify(self.public, self.filename, self.cbf, self.chal, damaged, "corrected"))
        damaged = copy.deepcopy(response)
        damaged["signature"] = damaged["signature"][:-2] + "AA"
        self.assertFalse(verify(self.public, self.filename, self.cbf, self.chal, damaged, "corrected"))
        other = challenge(len(self.data), 9, b"indices-2", b"coefficients-2", self.secret["client_sign_key"])
        self.assertFalse(verify(self.public, self.filename, self.cbf, other, response, "corrected"))
        self.assertFalse(verify(self.public, "other.bin", self.cbf, self.chal, response, "corrected"))

    def test_literal_verifier_omits_signature_check(self):
        cbf = CountingBloomFilter.from_dict(self.cbf)
        for tag in self.tags:
            cbf.add(tag)
        response = self.honest()
        response["signature"] = "not-a-signature"
        self.assertTrue(verify(self.public, self.filename, cbf.to_dict(), self.chal, response, "literal"))
        self.assertFalse(verify(self.public, self.filename, cbf.to_dict(), self.chal, response, "corrected"))

    def test_corrected_modify_and_delete_update_cbf(self):
        tags, cbf = update(self.filename, 3, self.data[3], 999, self.tags, self.cbf, "corrected")
        changed = self.data[:]
        changed[3] = 999
        self.assertTrue(meta_verify(self.filename, changed, cbf, "corrected"))
        self.assertNotEqual(tags[3], self.tags[3])
        tags, cbf = update(self.filename, len(tags) - 1, changed[-1], None, tags, cbf, "corrected")
        self.assertEqual(len(tags), len(self.tags) - 1)

    def test_literal_update_does_not_track_tags(self):
        _, cbf = update(self.filename, 2, self.data[2], 1234, self.tags, self.cbf, "literal")
        changed = self.data[:]
        changed[2] = 1234
        self.assertFalse(meta_verify(self.filename, changed, cbf, "corrected"))

    def test_isolated_tag_only_process_has_no_data(self):
        state = retained_state(self.filename, self.tags, self.public, self.secret["server_sign_key"])
        encoded = json.dumps(state, sort_keys=True)
        self.assertNotIn('"data"', encoded)
        self.assertNotIn('"blocks"', encoded)
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            dump_json(temp / "state.json", state)
            dump_json(temp / "challenges.json", [self.chal])
            subprocess.run([sys.executable, str(ROOT / "scripts" / "otgpdp2025_prover_cli.py"),
                            "--state", str(temp / "state.json"), "--challenges", str(temp / "challenges.json"),
                            "--output", str(temp / "responses.json")], check=True, cwd=ROOT)
            response = load_json(temp / "responses.json")[0]
        self.assertTrue(verify(self.public, self.filename, self.cbf, self.chal, response, "corrected"))

    def challenge_covering(self, index: int) -> dict:
        """Deterministically find a challenge whose index set contains ``index``."""
        for attempt in range(200):
            candidate = challenge(len(self.data), 9, f"cover-{attempt}".encode(),
                                  b"coefficients-1", self.secret["client_sign_key"])
            if index in candidate["body"]["indices"]:
                return candidate
        raise AssertionError("no covering challenge found")

    def test_middle_delete_without_data_is_refused(self):
        """The paper never specifies index renumbering; we refuse to invent it."""
        with self.assertRaises(ValueError):
            update(self.filename, 3, self.data[3], None, self.tags, self.cbf, "corrected")

    def test_naive_middle_delete_breaks_later_audits(self):
        """Popping a middle tag renumbers positions and silently breaks later blocks."""
        naive = self.tags[:]
        naive.pop(3)
        reduced = [value for position, value in enumerate(self.data) if position != 3]
        self.assertEqual(naive[5], self.tags[6])  # retained tag now sits at the wrong position
        bloom = CountingBloomFilter.from_dict(self.cbf)
        bloom.remove(self.tags[3])
        covering = self.challenge_covering(5)
        broken = proof_from_data(reduced, naive, covering, self.secret["server_sign_key"])
        self.assertFalse(verify(self.public, self.filename, bloom.to_dict(), covering, broken, "corrected"))

    def test_middle_delete_with_reindex_passes_and_tag_attack_survives(self):
        reduced = [value for position, value in enumerate(self.data) if position != 3]
        tags, cbf = update(self.filename, 3, self.data[3], None, self.tags, self.cbf, "corrected",
                           data=self.data)
        self.assertEqual(len(tags), len(self.tags) - 1)
        self.assertTrue(meta_verify(self.filename, reduced, cbf, "corrected"))
        covering = self.challenge_covering(5)
        self.assertTrue(verify(self.public, self.filename, cbf, covering,
                               proof_from_data(reduced, tags, covering, self.secret["server_sign_key"]),
                               "corrected"))
        # Fixing the update semantics does not remove the tag-only strategy.
        attack = proof_from_tags(self.filename, tags, covering, self.secret["server_sign_key"])
        self.assertEqual(attack["body"]["P"],
                         proof_from_data(reduced, tags, covering, self.secret["server_sign_key"])["body"]["P"])
        self.assertTrue(verify(self.public, self.filename, cbf, covering, attack, "corrected"))

    def test_middle_insert_needs_reindex_and_rebuild_matches(self):
        with self.assertRaises(ValueError):
            insert(self.filename, 2, 4242, self.tags, self.cbf, "literal", data=self.data)
        grown = self.data[:2] + [4242 % Q] + self.data[2:]
        tags, cbf = insert(self.filename, 2, 4242, self.tags, self.cbf, "corrected", data=self.data)
        self.assertEqual(len(tags), len(self.tags) + 1)
        self.assertTrue(meta_verify(self.filename, grown, cbf, "corrected"))
        direct_tags, direct_cbf = rebuild_corrected(self.filename, grown,
                                                    self.cbf["size"], self.cbf["hashes"])
        self.assertEqual(tags, direct_tags)
        self.assertEqual(cbf, direct_cbf)

    def test_tampered_but_resigned_response_is_still_rejected(self):
        """A malicious cloud holds a legitimate signing key, so rejection must come
        from the algebraic and CBF checks, not only from the signature check."""
        response = self.honest()
        cases = {}
        changed_p = copy.deepcopy(response)
        changed_p["body"]["P"] = hex(int(changed_p["body"]["P"], 16) * G % P)
        cases["P"] = changed_p
        changed_tag = copy.deepcopy(response)
        changed_tag["body"]["tags"][0] = hex(int(changed_tag["body"]["tags"][0], 16) * G % P)
        cases["tags"] = changed_tag
        changed_digest = copy.deepcopy(response)
        changed_digest["body"]["challenge_digest"] = "00"
        cases["challenge_digest"] = changed_digest
        for name, damaged in cases.items():
            damaged["signature"] = sign(self.secret["server_sign_key"], damaged["body"])
            self.assertTrue(verify_signature(self.public["server_verify_key"], damaged["body"],
                                             damaged["signature"]),
                            f"{name}: test payload must carry a valid server signature")
            self.assertFalse(verify(self.public, self.filename, self.cbf, self.chal, damaged,
                                    "corrected"), f"{name}: re-signed tampering must still be rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
