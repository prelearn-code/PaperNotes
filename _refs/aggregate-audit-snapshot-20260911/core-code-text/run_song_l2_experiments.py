"""Song 2025 real-pairing L2 experiment matrix.

Strictness conventions (2026-09-11), matching the Li Hang runner:

* Sectors are generated from a secret that is NOT written to the results
  directory; the client key seed is a second secret.  Only commitments are kept.
* The attacker state is serialized to disk BEFORE challenge randomness is drawn.
* Each period uses its own challenge, and models the paper's per-period shape:
  the unified search proof covers the files a keyword search returned, while
  every file the search did not return gets its own audit proof.
* A second phase deletes a file after retention and asks the isolated prover to
  answer the unified search for the surviving files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import canonical, digest, dump_json, load_json
from scripts.song2025_l2_protocol import (
    challenge, delete, insert, new_system, proof_from_sectors, retained_state,
    search_honest, search_request, verify_audit, verify_search,
)
from scripts.song2025_pairing import FIELD, ORDER, P_FACTOR, Q_FACTOR

ROOT = Path(__file__).resolve().parents[1]
FILES_PER_INSTANCE = 4
BLOCKS_PER_FILE = 8
SECTORS_PER_BLOCK = 3
SEARCHED_FILES = 3  # files 0..2 carry keyword "shared"; file 3 carries "gamma"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commitment(secret: bytes) -> str:
    return hashlib.sha256(secret).hexdigest()


def make_sectors(data_secret: bytes, instance: int, file_no: int) -> list[list[int]]:
    return [[int.from_bytes(digest(b"song-l2-sector", data_secret, instance.to_bytes(4, "big"),
                                   file_no.to_bytes(4, "big"), block.to_bytes(4, "big"),
                                   sector.to_bytes(4, "big")), "big") % 256
             for sector in range(SECTORS_PER_BLOCK)] for block in range(BLOCKS_PER_FILE)]


def run_process(command: list[str], log_path: Path) -> None:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log_path.write_text(
        "$ " + subprocess.list2cmdline(command) + "\n" + completed.stdout + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"isolated L2 prover failed; see {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Song 2025 real-pairing L2 matrix")
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument("--challenges", type=int, default=100)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("l2-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--results-root", type=Path, default=ROOT / "results",
                        help="root for the run directory (tests use a temporary directory)")
    args = parser.parse_args()
    if args.instances < 1 or args.challenges < 1:
        raise ValueError("instances and challenges must be positive")

    output = args.results_root / "song2025" / args.run_id
    output.mkdir(parents=True, exist_ok=False)

    provided_data = os.environ.get("AGGREGATE_AUDIT_DATA_SECRET")
    data_secret = bytes.fromhex(provided_data) if provided_data else os.urandom(32)
    provided_key = os.environ.get("SONG_L2_KEY_SECRET")
    key_secret = bytes.fromhex(provided_key) if provided_key else os.urandom(32)
    params = {
        "run_id": args.run_id, "instances": args.instances,
        "challenges_per_instance": args.challenges,
        "files_per_instance": FILES_PER_INSTANCE,
        "searched_files_per_period": SEARCHED_FILES,
        "blocks_per_file": BLOCKS_PER_FILE, "sectors_per_block": SECTORS_PER_BLOCK,
        "field": FIELD, "composite_order": ORDER, "order_factors": [P_FACTOR, Q_FACTOR],
        "backend": "supersingular y^2=x^3+x; reduced Tate pairing; embedding degree 2",
        "data_secret_source": "environment" if provided_data else "generated",
        "data_secret_commitment": commitment(data_secret),
        "key_secret_source": "environment" if provided_key else "generated",
        "key_secret_commitment": commitment(key_secret),
        "challenge_ordering": "attacker state is written to disk before challenge randomness is drawn",
        "security_note": "reduced functional parameters; not production security",
    }
    dump_json(output / "parameters.json", params)
    dump_json(output / "environment.json", {
        "python": sys.version, "platform": platform.platform(),
        "source_sha256": {
            **{f"scripts/{p.name}": sha256(p) for p in sorted((ROOT / "scripts").glob("*.py"))},
            **{f"tests/{p.name}": sha256(p) for p in sorted((ROOT / "tests").glob("*.py"))},
        },
    })
    (output / "command.txt").write_text(
        f"{sys.executable} scripts/run_song_l2_experiments.py --instances {args.instances} "
        f"--challenges {args.challenges} --run-id {args.run_id}\n", encoding="utf-8")

    records = []
    for instance in range(args.instances):
        system = new_system(key_secret + instance.to_bytes(4, "big"))
        keywords = ["shared"] * SEARCHED_FILES + ["gamma"]
        for file_no in range(FILES_PER_INSTANCE):
            insert(system, make_sectors(data_secret, instance, file_no),
                   [keywords[file_no], f"file-{file_no}"],
                   f"song-l2-state-{instance}-{file_no}".encode())
        instance_dir = output / f"instance-{instance:02d}"
        instance_dir.mkdir(parents=True, exist_ok=False)
        honest_sectors = {fid: value["sectors"] for fid, value in system["files"].items()}
        counts = {fid: len(value["sectors"]) for fid, value in system["files"].items()}
        file_ids = list(system["files"])

        # --- freeze the attacker state BEFORE drawing challenge randomness ----
        state = retained_state(system)
        encoded_state = canonical(state)
        dump_json(instance_dir / "attacker-state.json", state)
        dump_json(instance_dir / "honest-data-commitment.json", {
            "files": FILES_PER_INSTANCE, "blocks_per_file": BLOCKS_PER_FILE,
            "sectors_per_block": SECTORS_PER_BLOCK,
            "data_commitment": commitment(canonical(honest_sectors)),
            "note": "commitment only; data and key secrets are not stored in this run directory",
        })

        # --- only now draw challenge randomness -------------------------------
        challenge_secret = os.urandom(32)
        periods = [challenge(digest(b"song-l2-challenge", challenge_secret,
                                    instance.to_bytes(4, "big"), ordinal.to_bytes(4, "big")))
                   for ordinal in range(args.challenges)]
        requests, expected = [], []
        for ordinal, chal in enumerate(periods):
            query = search_request(system, "shared", chal)
            requests.append({"kind": "search", "token": query["token"],
                             "latest_state": query["latest_state"], "challenge": chal})
            expected.append(("search", ordinal))
            unsearched = file_ids[SEARCHED_FILES]  # file 3 carries only "gamma"
            requests.append({"kind": "audit", "file_id": unsearched, "challenge": chal})
            expected.append(("unsearched_audit", ordinal))
        dump_json(instance_dir / "requests.json", requests)
        run_process([
            sys.executable, str(ROOT / "scripts" / "song2025_l2_prover_cli.py"),
            "--state", str(instance_dir / "attacker-state.json"),
            "--requests", str(instance_dir / "requests.json"),
            "--output", str(instance_dir / "responses.json"),
        ], instance_dir / "prover.log")
        responses = load_json(instance_dir / "responses.json")

        search_accepts = unsearched_accepts = 0
        honest_search_accepts = honest_audit_accepts = 0
        for (kind, ordinal), response in zip(expected, responses):
            chal = periods[ordinal]
            if kind == "search":
                query = search_request(system, "shared", chal)
                search_accepts += int(verify_search(system["public"], query, response, chal, counts))
                honest_search_accepts += int(verify_search(system["public"], query,
                                                           search_honest(system, "shared", chal),
                                                           chal, counts))
            else:
                fid = file_ids[SEARCHED_FILES]
                unsearched_accepts += int(verify_audit(system["public"], fid, response, chal,
                                                       counts[fid]))
                honest_audit_accepts += int(verify_audit(
                    system["public"], fid,
                    proof_from_sectors(fid, honest_sectors[fid], system["files"][fid]["tags"], chal),
                    chal, counts[fid]))

        # --- phase 2: deletion after retention --------------------------------
        deleted = file_ids[SEARCHED_FILES - 1]
        delete(system, deleted)
        post_state = retained_state(system)
        dump_json(instance_dir / "attacker-state-post-delete.json", post_state)
        survivor_ids = list(system["files"])
        post_counts = {fid: len(value["sectors"]) for fid, value in system["files"].items()}
        post_chal = periods[0]
        post_query = search_request(system, "shared", post_chal)
        dump_json(instance_dir / "requests-post-delete.json", [
            {"kind": "search", "token": post_query["token"],
             "latest_state": post_query["latest_state"], "challenge": post_chal},
            {"kind": "audit", "file_id": survivor_ids[0], "challenge": post_chal},
        ])
        run_process([
            sys.executable, str(ROOT / "scripts" / "song2025_l2_prover_cli.py"),
            "--state", str(instance_dir / "attacker-state-post-delete.json"),
            "--requests", str(instance_dir / "requests-post-delete.json"),
            "--output", str(instance_dir / "responses-post-delete.json"),
        ], instance_dir / "prover-post-delete.log")
        post_search, post_audit = load_json(instance_dir / "responses-post-delete.json")
        post_search_accepted = verify_search(system["public"], post_query, post_search, post_chal,
                                            post_counts)
        post_audit_accepted = verify_audit(system["public"], survivor_ids[0], post_audit, post_chal,
                                           block_count=post_counts[survivor_ids[0]])
        excluded = deleted not in post_search["results"]

        forbidden = [key for key in (b'"sectors"', b'"states"', b'"mk"', b'"ek"', b'"sk"')
                     if key in encoded_state]
        records.append({
            "instance": instance, "challenges": args.challenges,
            "distinct_period_challenges": len({c["theta"] for c in periods}),
            "honest_search_accepts": honest_search_accepts,
            "honest_unsearched_audit_accepts": honest_audit_accepts,
            "projection_search_accepts": search_accepts,
            "projection_unsearched_audit_accepts": unsearched_accepts,
            "post_delete_search_accepted": post_search_accepted,
            "post_delete_audit_accepted": post_audit_accepted,
            "deleted_file_excluded_from_results": excluded,
            "forbidden_state_fields": [item.decode() for item in forbidden],
            "attacker_state_logical_bytes": len(encoded_state),
            "attacker_state_disk_bytes": (instance_dir / "attacker-state.json").stat().st_size,
            "raw_sector_logical_bytes": len(canonical(honest_sectors)),
            "challenge_secret_commitment": commitment(challenge_secret),
        })
    dump_json(output / "trials.json", records)

    def total(key: str) -> int:
        return sum(int(record[key]) for record in records)

    summary = {
        "level": "L2-real-composite-order-pairing-reimplementation-reduced-parameters",
        "instances": args.instances, "challenges_per_instance": args.challenges,
        "total_periods": args.instances * args.challenges,
        "honest_search_accepted": total("honest_search_accepts"),
        "honest_unsearched_audit_accepted": total("honest_unsearched_audit_accepts"),
        "projection_search_accepted": total("projection_search_accepts"),
        "projection_unsearched_audit_accepted": total("projection_unsearched_audit_accepts"),
        "post_delete_search_accepted_instances": total("post_delete_search_accepted"),
        "post_delete_audit_accepted_instances": total("post_delete_audit_accepted"),
        "deleted_file_excluded_instances": total("deleted_file_excluded_from_results"),
        "attacker_states_with_forbidden_fields": sum(bool(r["forbidden_state_fields"]) for r in records),
        "average_attacker_state_logical_bytes": sum(
            r["attacker_state_logical_bytes"] for r in records) / len(records),
        "average_raw_sector_logical_bytes": sum(
            r["raw_sector_logical_bytes"] for r in records) / len(records),
        "data_secret_source": params["data_secret_source"],
        "key_secret_source": params["key_secret_source"],
        "challenge_ordering": "state committed before challenges drawn",
    }
    dump_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
