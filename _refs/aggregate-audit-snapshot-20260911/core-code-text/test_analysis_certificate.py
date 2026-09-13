from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.analysis_certificate import (
    CASES,
    SCHEMA,
    build_all,
    build_certificate,
    validate_certificate,
)


class AnalysisCertificateTests(unittest.TestCase):
    def setUp(self):
        self.bundle = build_all()
        self.by_case = {certificate["case"]: certificate for certificate in self.bundle["certificates"]}

    def test_every_case_builds_and_validates(self):
        self.assertEqual(set(self.by_case), set(CASES))
        for case, certificate in self.by_case.items():
            self.assertEqual(certificate["schema"], SCHEMA, case)
            self.assertEqual(validate_certificate(certificate), [], case)

    def test_counters_match_the_recorded_runs(self):
        for case, certificate in self.by_case.items():
            sufficiency = certificate["sufficiency"]
            self.assertGreater(sufficiency["total"], 0, case)
            self.assertLessEqual(sufficiency["accepted"], sufficiency["total"], case)
            if certificate["role"] == "negative-control":
                # A correct scheme must never let the cheating strategy through.
                self.assertEqual(sufficiency["accepted"], 0, case)
            else:
                self.assertEqual(sufficiency["accepted"], sufficiency["total"], case)

    def test_negative_control_with_a_nonzero_count_is_rejected(self):
        certificate = copy.deepcopy(self.by_case["yang2026"])
        certificate["sufficiency"]["accepted"] = 1
        problems = validate_certificate(certificate)
        self.assertTrue(any("negative-control" in problem for problem in problems), problems)

    def test_attack_instance_must_be_accepted_everywhere(self):
        certificate = copy.deepcopy(self.by_case["song2025"])
        certificate["sufficiency"]["accepted"] = certificate["sufficiency"]["total"] - 1
        problems = validate_certificate(certificate)
        self.assertTrue(any("drifted" in problem or "attack-instance" in problem
                            for problem in problems), problems)

    def test_invalid_role_is_rejected(self):
        certificate = copy.deepcopy(self.by_case["baseline"])
        certificate["role"] = "not-a-role"
        problems = validate_certificate(certificate)
        self.assertTrue(any("invalid role" in problem for problem in problems), problems)

    def test_drifted_counter_is_detected(self):
        certificate = copy.deepcopy(self.by_case["song2025"])
        certificate["sufficiency"]["accepted"] = certificate["sufficiency"]["accepted"] - 1
        problems = validate_certificate(certificate)
        self.assertTrue(any("drifted" in problem for problem in problems), problems)

    def test_counter_missing_from_run_is_detected(self):
        certificate = copy.deepcopy(self.by_case["baseline"])
        certificate["sufficiency"]["counter_names"]["accepted"] = "not_a_recorded_counter"
        problems = validate_certificate(certificate)
        self.assertTrue(any("not present" in problem for problem in problems), problems)

    def test_non_in_model_case_must_state_its_limits(self):
        certificate = copy.deepcopy(self.by_case["lihang2026"])
        certificate["does_not_show"] = []
        problems = validate_certificate(certificate)
        self.assertTrue(any("does not show" in problem for problem in problems), problems)

    def test_invalid_model_status_and_missing_artefact_detected(self):
        certificate = copy.deepcopy(self.by_case["otgpdp2025"])
        certificate["model_status"] = "definitely-broken"
        certificate["protocol_map"] = "evidence/does-not-exist/protocol-map.md"
        problems = validate_certificate(certificate)
        self.assertTrue(any("invalid model_status" in problem for problem in problems), problems)
        self.assertTrue(any("artefact missing" in problem for problem in problems), problems)

    def test_out_of_range_counts_detected(self):
        certificate = copy.deepcopy(self.by_case["baseline"])
        certificate["sufficiency"]["accepted"] = certificate["sufficiency"]["total"] + 1
        problems = validate_certificate(certificate)
        self.assertTrue(any("outside" in problem for problem in problems), problems)

    def test_build_certificate_rejects_unknown_case(self):
        with self.assertRaises(KeyError):
            build_certificate("no-such-case")


if __name__ == "__main__":
    unittest.main(verbosity=2)
