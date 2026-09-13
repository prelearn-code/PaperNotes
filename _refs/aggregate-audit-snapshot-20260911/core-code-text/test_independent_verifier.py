from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.independent_verifier import (
    ROOT as VERIFIER_ROOT,
    check_song,
    check_zhang,
    load,
    song_audit_accept,
    song_proof_fields,
    song_search_accept,
    zhang_audit_accept,
    zhang_public_key,
)
from scripts.lihang2026_pairing import exponentiate, in_group

SONG_RUN = ROOT / "results" / "song2025" / "l2-strict-20260911"
ZHANG_RUN = ROOT / "results" / "zhang2025" / "l2-final-20260911"


class IndependenceTests(unittest.TestCase):
    def test_verifier_does_not_import_the_case_protocol_modules(self):
        """The point of this file is a second reading; it must not reuse the first."""
        source = (VERIFIER_ROOT / "scripts" / "independent_verifier.py").read_text(encoding="utf-8")
        for forbidden in ("import song2025_l2_protocol", "import zhang2025_protocol",
                          "from .song2025_l2_protocol", "from .zhang2025_protocol",
                          "from scripts.song2025_l2_protocol", "from scripts.zhang2025_protocol"):
            self.assertNotIn(forbidden, source, forbidden)


class SongRecheckTests(unittest.TestCase):
    def setUp(self):
        self.instance = sorted(SONG_RUN.glob("instance-*"))[0]
        self.state = load(self.instance / "attacker-state.json")
        self.requests = load(self.instance / "requests.json")
        self.responses = load(self.instance / "responses.json")

    def pairs(self):
        for request, response in zip(self.requests, self.responses):
            yield request, response

    def test_first_instance_recheck_agrees(self):
        audit_ok = search_ok = audit_total = search_total = 0
        for request, response in self.pairs():
            theta = bytes.fromhex(request["challenge"]["theta"])
            if request["kind"] == "audit":
                audit_total += 1
                audit_ok += int(song_audit_accept(self.state["public"], self.state,
                                                  request["file_id"], theta, response))
            else:
                search_total += 1
                search_ok += int(song_search_accept(self.state["public"], self.state, request,
                                                    theta, response))
        self.assertEqual(audit_ok, audit_total)
        self.assertEqual(search_ok, search_total)

    def test_prover_fields_are_reproduced_exactly(self):
        for request, response in self.pairs():
            theta = bytes.fromhex(request["challenge"]["theta"])
            if request["kind"] != "audit":
                continue
            psi, phi = song_proof_fields(self.state, request["file_id"], theta)
            self.assertEqual(psi, int(response["psi"]))
            self.assertEqual(phi.to_dict(), response["phi"])
            return

    def test_tampered_responses_are_rejected(self):
        request = next(r for r in self.requests if r["kind"] == "audit")
        response = self.responses[self.requests.index(request)]
        theta = bytes.fromhex(request["challenge"]["theta"])
        self.assertTrue(song_audit_accept(self.state["public"], self.state, request["file_id"],
                                          theta, response))
        broken_psi = dict(response, psi=(int(response["psi"]) + 1) % (2 ** 62))
        self.assertFalse(song_audit_accept(self.state["public"], self.state, request["file_id"],
                                           theta, broken_psi))
        broken_phi = copy.deepcopy(response)
        broken_phi["phi"]["x"] = hex(int(broken_phi["phi"]["x"], 16) + 1)
        self.assertFalse(song_audit_accept(self.state["public"], self.state, request["file_id"],
                                           theta, broken_phi))
        other_file = next(fid for fid in self.state["files"] if fid != request["file_id"])
        self.assertFalse(song_audit_accept(self.state["public"], self.state, other_file,
                                           theta, response))

    def test_search_result_omission_is_rejected(self):
        request = next(r for r in self.requests if r["kind"] == "search")
        response = self.responses[self.requests.index(request)]
        theta = bytes.fromhex(request["challenge"]["theta"])
        self.assertTrue(song_search_accept(self.state["public"], self.state, request, theta,
                                           response))
        dropped = copy.deepcopy(response)
        dropped["proofs"] = dropped["proofs"][:-1]
        dropped["results"] = dropped["results"][:-1]
        self.assertFalse(song_search_accept(self.state["public"], self.state, request, theta,
                                           dropped))


class ZhangRecheckTests(unittest.TestCase):
    def setUp(self):
        self.instance = sorted(ZHANG_RUN.glob("instance-*"))[0]
        self.state = load(self.instance / "attacker-state.json")
        self.requests = load(self.instance / "requests.json")
        self.responses = load(self.instance / "responses.json")

    def test_first_instance_recheck_agrees(self):
        parameters = self.state["parameters"]
        key = self.state["audit_key"]
        accepted = 0
        for response in self.responses:
            accepted += int(zhang_audit_accept(parameters, key, response))
        self.assertEqual(accepted, len(self.responses))
        public_key = zhang_public_key(parameters, key)
        self.assertTrue(in_group(public_key))
        self.assertNotEqual(public_key, exponentiate(1))

    def test_tampered_responses_are_rejected(self):
        parameters = self.state["parameters"]
        key = self.state["audit_key"]
        good = self.responses[0]
        self.assertTrue(zhang_audit_accept(parameters, key, good))
        for field, transform in (("p", lambda proof: [(proof["p"][0] + 1) % (2 ** 31 - 1)]
                                  + proof["p"][1:]),
                                 ("Gamma", None), ("Psi", None)):
            broken = copy.deepcopy(good)
            if field == "p":
                broken["p"] = transform(broken)
            else:
                broken[field] = parameters["bases"][0]
            self.assertFalse(zhang_audit_accept(parameters, key, broken), field)


class FullRecheckTests(unittest.TestCase):
    """The full re-check is a script run; the tests verify a bounded slice and
    then check that the recorded full-run report still agrees with the runs."""

    def test_bounded_recheck_agrees_on_every_path(self):
        song = check_song(SONG_RUN, limit=1)
        self.assertEqual(song["independent_audit_total"], 100)
        self.assertEqual(song["independent_audit_accepted"], 100)
        self.assertEqual(song["independent_search_total"], 100)
        self.assertEqual(song["independent_search_accepted"], 100)
        self.assertEqual(song["prover_field_mismatches"], 0)
        zhang = check_zhang(ZHANG_RUN, limit=1)
        self.assertEqual(zhang["independent_totals"],
                         {"cached_per_block": 100, "cached_per_sector": 100,
                          "single": 100, "cached_sector_bound": 100})
        self.assertEqual(zhang["independent_counts"],
                         {"cached_per_block": 100, "cached_per_sector": 100,
                          "single": 100, "cached_sector_bound": 0})
        self.assertEqual(zhang["prover_field_mismatches"], 0)

    def test_recorded_full_recheck_report_still_agrees(self):
        report_path = ROOT / "certificates" / "independent-recheck.json"
        self.assertTrue(report_path.exists(),
                        "run python -m scripts.independent_verifier to regenerate the report")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(set(report["agreement"].values()), {True})
        song_summary = load(SONG_RUN / "summary.json")
        self.assertEqual(report["song"]["independent_audit_accepted"],
                         song_summary["projection_unsearched_audit_accepted"])
        self.assertEqual(report["song"]["independent_search_accepted"],
                         song_summary["projection_search_accepted"])
        zhang_summary = load(ZHANG_RUN / "summary.json")
        self.assertEqual(report["zhang"]["independent_counts"], report["zhang"]["recorded_counts"])
        self.assertEqual(report["zhang"]["recorded_counts"]["single"],
                         zhang_summary["single_block_per_block_literal_accepted"])

    def test_limited_recheck_counts_one_instance_only(self):
        self.assertEqual(check_song(SONG_RUN, limit=1)["instances_checked"], 1)
        self.assertEqual(check_zhang(ZHANG_RUN, limit=1)["instances_checked"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
