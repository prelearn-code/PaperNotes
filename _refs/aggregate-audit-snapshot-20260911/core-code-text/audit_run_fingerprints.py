"""Audit recorded run fingerprints against the current code tree.

Every experiment run stores a ``source_sha256`` map of the whole
``scripts/*.py`` and ``tests/*.py`` tree at run time.  Editing any file after a
run therefore shows up as drift, and a later conversation needs to know which
drift touches a case's own modules (functional reproduction may still hold) and
which is only an unrelated later edit.

Usage::

    python -m scripts.audit_run_fingerprints            # print the table
    python -m scripts.audit_run_fingerprints --json out.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]

# Files each case actually implements its claim with; drift here matters most.
CASE_MODULES = {
    "song2025": ("scripts/run_song_l2_experiments.py", "scripts/song2025_l2_protocol.py",
                 "scripts/song2025_l2_prover_cli.py", "scripts/song2025_pairing.py"),
    "otgpdp2025": ("scripts/run_experiments.py", "scripts/otgpdp2025_protocol.py",
                   "scripts/otgpdp2025_prover_cli.py"),
    "lihang2026": ("scripts/run_lihang2026_experiments.py", "scripts/lihang2026_protocol.py",
                   "scripts/lihang2026_prover_cli.py", "scripts/lihang2026_pairing.py"),
    "zhang2025": ("scripts/run_zhang2025_experiments.py", "scripts/zhang2025_protocol.py",
                  "scripts/zhang2025_prover_cli.py"),
    "baseline": ("scripts/run_baseline_experiments.py", "scripts/authenticated_baseline.py"),
    "yang2026": ("scripts/run_yang2026_experiments.py", "scripts/yang2026_protocol.py"),
    "miao2025": ("scripts/run_miao2025_experiments.py", "scripts/miao2025_protocol.py"),
    "high-security": ("scripts/run_high_security_experiments.py",
                      "scripts/large_parameter_backend.py"),
    "state-accounting": ("scripts/run_state_accounting.py",),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalise(name: str) -> str:
    """Older runs recorded bare filenames; map them back onto the tree."""
    if "/" in name:
        return name
    for candidate in (f"scripts/{name}", f"tests/{name}"):
        if (ROOT / candidate).exists():
            return candidate
    return name


def audit() -> dict:
    cases: dict[str, dict] = {}
    for case_dir in sorted((ROOT / "results").iterdir()):
        if not case_dir.is_dir():
            continue
        for run_dir in sorted(case_dir.iterdir()):
            environment = run_dir / "environment.json"
            if not environment.exists():
                continue
            recorded = json.loads(environment.read_text(encoding="utf-8")).get("source_sha256", {})
            relevant = CASE_MODULES.get(case_dir.name, ())
            drift_relevant, drift_other = [], []
            for raw_name, recorded_hash in recorded.items():
                name = normalise(raw_name)
                path = ROOT / name
                if not path.exists():
                    (drift_relevant if name in relevant else drift_other).append(
                        {"file": name, "state": "missing"})
                    continue
                if digest(path) != recorded_hash:
                    entry = {"file": name, "state": "changed"}
                    (drift_relevant if name in relevant else drift_other).append(entry)
            cases[f"{case_dir.name}/{run_dir.name}"] = {
                "case_relevant_drift": drift_relevant,
                "unrelated_drift": [entry["file"] for entry in drift_other],
                "reproducible_functionally": not drift_relevant,
            }
    return {"runs_checked": len(cases), "runs": cases,
            "summary": {
                "runs_with_case_relevant_drift": sum(
                    1 for value in cases.values() if value["case_relevant_drift"]),
                "runs_clean": sum(1 for value in cases.values() if value["reproducible_functionally"]),
            }}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit run fingerprints against the current tree")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    report = audit()
    for name, value in sorted(report["runs"].items()):
        flag = "OK       " if value["reproducible_functionally"] else "DRIFT    "
        detail = "" if value["reproducible_functionally"] else "  " + ", ".join(
            f"{entry['file']}({entry['state']})" for entry in value["case_relevant_drift"])
        print(f"{flag} {name}{detail}")
        if value["unrelated_drift"]:
            print(f"          unrelated later edits: {len(value['unrelated_drift'])} file(s)")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
