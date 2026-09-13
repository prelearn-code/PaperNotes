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
from scripts.song2025_l2_protocol import (
    ORDER, challenge, delete, insert, new_system, proof_from_projection,
    proof_from_sectors, retained_state, search_from_projection, search_honest,
    search_request, verify_audit, verify_search,
)


class SongL2ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.system = new_system(b"song-l2-tests")
        self.f1 = insert(self.system, [[1, 2, 3], [4, 5, 6]], ["alpha", "shared"], b"state-1")
        self.f2 = insert(self.system, [[7, 8, 9], [10, 11, 12]], ["beta", "shared"], b"state-2")
        self.chal = challenge(b"l2-period-1")

    def counts(self):
        return {fid: len(value["sectors"]) for fid, value in self.system["files"].items()}

    def test_honest_and_projection_audit_real_pairing(self):
        value = self.system["files"][self.f1]
        honest = proof_from_sectors(self.f1, value["sectors"], value["tags"], self.chal)
        projected = proof_from_projection(self.f1, retained_state(self.system)["files"][self.f1], self.chal)
        self.assertEqual(honest, projected)
        self.assertTrue(verify_audit(self.system["public"], self.f1, honest, self.chal, 2))
        self.assertTrue(verify_audit(self.system["public"], self.f1, projected, self.chal, 2))

    def test_real_pairing_unified_search(self):
        request = search_request(self.system, "shared", self.chal)
        honest = search_honest(self.system, "shared", self.chal)
        projected = search_from_projection(retained_state(self.system), request["token"],
                                           request["latest_state"], self.chal)
        self.assertEqual(honest, projected)
        self.assertEqual(set(honest["results"]), {self.f1, self.f2})
        self.assertTrue(verify_search(self.system["public"], request, honest, self.chal, self.counts()))

    def test_s_one_control_and_s_greater_than_one_projection(self):
        one = new_system(b"song-l2-one")
        fid = insert(one, [[5], [9]], ["one"], b"one-state")
        self.assertEqual(retained_state(one)["files"][fid]["block_sums"], [5, 9])
        self.assertEqual(retained_state(self.system)["files"][self.f1]["block_sums"], [6, 15])

    def test_delete_and_unsearched_paths(self):
        delete(self.system, self.f1)
        request = search_request(self.system, "shared", self.chal)
        response = search_honest(self.system, "shared", self.chal)
        self.assertEqual(response["results"], [self.f2])
        self.assertTrue(verify_search(self.system["public"], request, response, self.chal, self.counts()))
        proof = proof_from_projection(self.f2, retained_state(self.system)["files"][self.f2], self.chal)
        self.assertTrue(verify_audit(self.system["public"], self.f2, proof, self.chal, 2))

    def test_tamper_replay_identity_and_request_binding(self):
        state = retained_state(self.system)
        proof = proof_from_projection(self.f1, state["files"][self.f1], self.chal)
        damaged = copy.deepcopy(proof)
        damaged["psi"] = (damaged["psi"] + 1) % ORDER
        self.assertFalse(verify_audit(self.system["public"], self.f1, damaged, self.chal, 2))
        self.assertFalse(verify_audit(self.system["public"], self.f2, proof, self.chal, 2))
        self.assertFalse(verify_audit(self.system["public"], self.f1, proof, challenge(b"l2-period-2"), 2))
        damaged_point = copy.deepcopy(proof)
        damaged_point["phi"]["y"] = hex(int(damaged_point["phi"]["y"], 16) + 1)
        self.assertFalse(verify_audit(self.system["public"], self.f1, damaged_point, self.chal, 2))
        request = search_request(self.system, "shared", self.chal)
        response = search_honest(self.system, "shared", self.chal)
        response["token"] = "00" * 32
        self.assertFalse(verify_search(self.system["public"], request, response, self.chal, self.counts()))

    def test_projection_search_after_delete_in_isolated_process(self):
        """Deletion happens after retention: the isolated prover must answer the
        unified search for the surviving files and audit an unsearched file."""
        delete(self.system, self.f1)
        state = retained_state(self.system)
        request = search_request(self.system, "shared", self.chal)
        requests = [
            {"kind": "search", "token": request["token"],
             "latest_state": request["latest_state"], "challenge": self.chal},
            {"kind": "audit", "file_id": self.f2, "challenge": self.chal},
        ]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            dump_json(temp / "state.json", state)
            dump_json(temp / "requests.json", requests)
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "song2025_l2_prover_cli.py"),
                "--state", str(temp / "state.json"), "--requests", str(temp / "requests.json"),
                "--output", str(temp / "responses.json"),
            ], check=True, cwd=ROOT)
            search, audit = load_json(temp / "responses.json")
        self.assertEqual(search["results"], [self.f2])
        self.assertTrue(verify_search(self.system["public"], request, search, self.chal, self.counts()))
        self.assertTrue(verify_audit(self.system["public"], self.f2, audit, self.chal, 2))

    def test_mixed_searched_and_unsearched_period(self):
        """One period: unified search proof for keyword hits plus audit proofs for
        the files the search did not return."""
        f3 = insert(self.system, [[13, 14, 15], [16, 17, 18]], ["gamma"], b"state-3")
        request = search_request(self.system, "shared", self.chal)
        searched = search_from_projection(retained_state(self.system), request["token"],
                                          request["latest_state"], self.chal)
        self.assertEqual(set(searched["results"]), {self.f1, self.f2})
        self.assertTrue(verify_search(self.system["public"], request, searched, self.chal,
                                      self.counts()))
        unsearched = proof_from_projection(f3, retained_state(self.system)["files"][f3], self.chal)
        self.assertTrue(verify_audit(self.system["public"], f3, unsearched, self.chal, 2))
        # An unsearched file must not be silently omitted: dropping its audit proof
        # leaves no acceptance evidence for it, so the period covers only two files.
        self.assertNotIn(f3, searched["results"])

    def test_broken_search_chain_is_rejected(self):
        state = retained_state(self.system)
        for entry in state["db"].values():
            if entry["valid"]:
                entry["pointer"] = (int(entry["pointer"]) + 1) % ORDER
        with self.assertRaises(ValueError):
            search_from_projection(state, search_request(self.system, "shared", self.chal)["token"],
                                   self.system["states"]["shared"], self.chal)

    def test_isolated_l2_projection_process(self):
        state = retained_state(self.system)
        encoded = json.dumps(state, sort_keys=True)
        for forbidden in ('"sectors"', '"states"', '"mk"', '"ek"', '"sk"'):
            self.assertNotIn(forbidden, encoded)
        request = search_request(self.system, "shared", self.chal)
        requests = [
            {"kind": "audit", "file_id": self.f1, "challenge": self.chal},
            {"kind": "search", "token": request["token"], "latest_state": request["latest_state"],
             "challenge": self.chal},
        ]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            dump_json(temp / "state.json", state)
            dump_json(temp / "requests.json", requests)
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "song2025_l2_prover_cli.py"),
                "--state", str(temp / "state.json"), "--requests", str(temp / "requests.json"),
                "--output", str(temp / "responses.json"),
            ], check=True, cwd=ROOT)
            audit, search = load_json(temp / "responses.json")
        self.assertTrue(verify_audit(self.system["public"], self.f1, audit, self.chal, 2))
        self.assertTrue(verify_search(self.system["public"], request, search, self.chal, self.counts()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
