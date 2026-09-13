from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_SECRET = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
KEY_SECRET = "ffeeddccbbaa99887766554433221100ffeeddccbbaa99887766554433221100"


def run(command: list[str], env_extra: dict[str, str]) -> None:
    environment = dict(os.environ)
    environment.update(env_extra)
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                               env=environment)
    if completed.returncode:
        raise AssertionError(f"runner failed: {completed.stdout}\n{completed.stderr}")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ReproducibilityTests(unittest.TestCase):
    """The runs must be reproducible when the secret is supplied, and the secret
    must stay out of the run directory when it is not."""

    def test_supplied_secret_reproduces_the_data_and_is_only_committed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = {"AGGREGATE_AUDIT_DATA_SECRET": DATA_SECRET}
            for run_id in ("a", "b"):
                run([sys.executable, str(ROOT / "scripts" / "run_zhang2025_experiments.py"),
                     "--instances", "1", "--challenges", "2", "--run-id", run_id,
                     "--results-root", str(root)], env)
            first = root / "zhang2025" / "a"
            second = root / "zhang2025" / "b"
            parameters = load(first / "parameters.json")
            self.assertEqual(parameters["data_secret_source"], "environment")
            self.assertEqual(parameters["data_secret_commitment"],
                             hashlib.sha256(bytes.fromhex(DATA_SECRET)).hexdigest())
            commitment_a = load(first / "instance-00" / "honest-data-commitment.json")[
                "ciphertext_commitment"]
            commitment_b = load(second / "instance-00" / "honest-data-commitment.json")[
                "ciphertext_commitment"]
            self.assertEqual(commitment_a, commitment_b)
            # The secret itself must not appear anywhere in the run directory.
            for path in first.rglob("*.json"):
                self.assertNotIn(DATA_SECRET, path.read_text(encoding="utf-8"), path.name)

    def test_song_l2_honours_both_secret_environment_variables(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run([sys.executable, str(ROOT / "scripts" / "run_song_l2_experiments.py"),
                 "--instances", "1", "--challenges", "2", "--run-id", "s",
                 "--results-root", str(root)],
                {"AGGREGATE_AUDIT_DATA_SECRET": DATA_SECRET, "SONG_L2_KEY_SECRET": KEY_SECRET})
            parameters = load(root / "song2025" / "s" / "parameters.json")
            self.assertEqual(parameters["data_secret_source"], "environment")
            self.assertEqual(parameters["key_secret_source"], "environment")
            self.assertEqual(parameters["data_secret_commitment"],
                             hashlib.sha256(bytes.fromhex(DATA_SECRET)).hexdigest())
            self.assertEqual(parameters["key_secret_commitment"],
                             hashlib.sha256(bytes.fromhex(KEY_SECRET)).hexdigest())

    def test_without_a_supplied_secret_the_source_is_generated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run([sys.executable, str(ROOT / "scripts" / "run_zhang2025_experiments.py"),
                 "--instances", "1", "--challenges", "2", "--run-id", "g",
                 "--results-root", str(root)],
                {"AGGREGATE_AUDIT_DATA_SECRET": ""})
            environment = dict(os.environ)
            environment.pop("AGGREGATE_AUDIT_DATA_SECRET", None)
            parameters = load(root / "zhang2025" / "g" / "parameters.json")
            self.assertEqual(parameters["data_secret_source"], "generated")


if __name__ == "__main__":
    unittest.main(verbosity=2)
