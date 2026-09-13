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
from scripts.song2025_protocol import (
    N, challenge, delete, insert, new_system, projection_state, proof_from_projection,
    proof_from_sectors, search_from_projection, search_honest, search_request, verify_audit, verify_search,
)


class SongTests(unittest.TestCase):
    def setUp(self):
        self.system = new_system(b"song-tests")
        self.f1 = insert(self.system, [[1, 2, 3], [4, 5, 6]], ["alpha", "shared"], b"state-1")
        self.f2 = insert(self.system, [[7, 8, 9], [10, 11, 12]], ["beta", "shared"], b"state-2")
        self.chal = challenge(b"audit-period-1")

    def counts(self):
        return {file_id: len(value["sectors"]) for file_id, value in self.system["files"].items()}

    def test_honest_and_projection_audit_are_identical(self):
        value = self.system["files"][self.f1]
        honest = proof_from_sectors(self.f1, value["sectors"], value["tags"], self.chal)
        projected = proof_from_projection(self.f1, projection_state(self.system)["files"][self.f1], self.chal)
        self.assertEqual(honest, projected)
        self.assertTrue(verify_audit(self.system["public"], self.f1, projected, self.chal, 2))

    def test_sector_projection_for_s_one_and_s_greater_than_one(self):
        single = new_system(b"single")
        fid = insert(single, [[5], [9]], ["one"], b"states")
        self.assertEqual(projection_state(single)["files"][fid]["block_sums"], [5, 9])
        projected = projection_state(self.system)["files"][self.f1]["block_sums"]
        self.assertEqual(projected, [6, 15])
        alternatives = [[0, 0, 6], [0, 0, 15]]
        self.assertNotEqual(alternatives, self.system["files"][self.f1]["sectors"])
        self.assertEqual([sum(x) for x in alternatives], projected)

    def test_search_both_files_and_verify_unified_proof(self):
        response = search_honest(self.system, "shared", self.chal)
        request = search_request(self.system, "shared", self.chal)
        self.assertEqual(set(response["results"]), {self.f1, self.f2})
        self.assertTrue(verify_search(self.system["public"], request, response, self.chal, self.counts()))
        projected = search_from_projection(projection_state(self.system), request["token"],
                                           request["latest_state"], self.chal)
        self.assertEqual(response, projected)

    def test_unsearched_file_audit_path(self):
        response = search_honest(self.system, "alpha", self.chal)
        request = search_request(self.system, "alpha", self.chal)
        self.assertTrue(verify_search(self.system["public"], request, response, self.chal, self.counts()))
        projected = projection_state(self.system)
        proof = proof_from_projection(self.f2, projected["files"][self.f2], self.chal)
        self.assertTrue(verify_audit(self.system["public"], self.f2, proof, self.chal, 2))

    def test_delete_preserves_search_chain_and_excludes_file(self):
        delete(self.system, self.f1)
        response = search_honest(self.system, "shared", self.chal)
        request = search_request(self.system, "shared", self.chal)
        self.assertEqual(response["results"], [self.f2])
        self.assertTrue(verify_search(self.system["public"], request, response, self.chal, self.counts()))

    def test_empty_search(self):
        response = search_honest(self.system, "absent", self.chal)
        request = search_request(self.system, "absent", self.chal)
        self.assertEqual(response["results"], [])
        self.assertTrue(verify_search(self.system["public"], request, response, self.chal, self.counts()))

    def test_tampering_and_replay_rejected(self):
        state = projection_state(self.system)
        proof = proof_from_projection(self.f1, state["files"][self.f1], self.chal)
        damaged = copy.deepcopy(proof)
        damaged["psi"] = (damaged["psi"] + 1) % N
        self.assertFalse(verify_audit(self.system["public"], self.f1, damaged, self.chal, 2))
        self.assertFalse(verify_audit(self.system["public"], self.f2, proof, self.chal, 2))
        other = challenge(b"audit-period-2")
        self.assertFalse(verify_audit(self.system["public"], self.f1, proof, other, 2))
        request = search_request(self.system, "shared", self.chal)
        response = search_from_projection(state, request["token"], request["latest_state"], self.chal)
        response["results"].pop()
        self.assertFalse(verify_search(self.system["public"], request, response, self.chal, self.counts()))
        substituted = copy.deepcopy(search_honest(self.system, "shared", self.chal))
        substituted["token"] = "00" * 32
        self.assertFalse(verify_search(self.system["public"], request, substituted, self.chal, self.counts()))

    def test_broken_index_chain_rejected(self):
        state = projection_state(self.system)
        for entry in state["db"].values():
            if entry["file_id"] == self.f2 and entry["valid"]:
                entry["pointer"] ^= 1
        with self.assertRaises(ValueError):
            request = search_request(self.system, "shared", self.chal)
            search_from_projection(state, request["token"], request["latest_state"], self.chal)

    def test_isolated_projection_process_has_no_sectors(self):
        state = projection_state(self.system)
        encoded = json.dumps(state, sort_keys=True)
        self.assertNotIn('"sectors"', encoded)
        self.assertNotIn('"mk"', encoded)
        self.assertNotIn('"states"', encoded)
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
            subprocess.run([sys.executable, str(ROOT / "scripts" / "song2025_prover_cli.py"),
                            "--state", str(temp / "state.json"), "--requests", str(temp / "requests.json"),
                            "--output", str(temp / "responses.json")], check=True, cwd=ROOT)
            audit_response, search_response = load_json(temp / "responses.json")
        self.assertTrue(verify_audit(self.system["public"], self.f1, audit_response, self.chal, 2))
        self.assertTrue(verify_search(self.system["public"], request, search_response, self.chal, self.counts()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
