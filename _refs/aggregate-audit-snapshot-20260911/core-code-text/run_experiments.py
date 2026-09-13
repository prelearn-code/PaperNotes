"""OTGPDP 2025 and Song 2025 (L1) experiment matrix.

Strictness conventions applied since 2026-09-11, matching the Li Hang runner:

* Experiment data is generated from a secret that is NOT written to the results
  directory; only its SHA-256 commitment is recorded, so a reader of the run
  directory cannot rebuild the data.
* The attacker state is serialized to disk BEFORE challenge randomness is drawn.
* Every trial uses its own challenge (fresh index set and coefficients).

The OTGPDP section additionally records the update-semantics checks: a middle
deletion is refused unless the caller supplies the post-deletion data list, a
naive pop breaks later positions, and the tag-only response still works after an
explicit renumbering.
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
from importlib.metadata import version
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import canonical, digest, dump_json, load_json, sign, verify_signature
from scripts.otgpdp2025_protocol import (
    G, P, Q, CountingBloomFilter, challenge as o_challenge, h_group, insert as o_insert,
    meta_gen, meta_verify, proof_from_data, proof_from_tags, rebuild_corrected,
    retained_state, setup as o_setup, update as o_update, verify as o_verify,
)
from scripts.song2025_protocol import (
    challenge as s_challenge, insert, new_system, projection_state, proof_from_sectors,
    search_request, verify_audit, verify_search,
)

ROOT = Path(__file__).resolve().parents[1]
BLOCKS_PER_INSTANCE = 64
LOW_ENTROPY_BLOCKS = 16
OTGPDP_PROFILES = ("literal", "literal_initialized", "corrected")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commitment(secret: bytes) -> str:
    return hashlib.sha256(secret).hexdigest()


def environment() -> dict:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "cryptography": version("cryptography"),
        "source_sha256": {
            **{f"scripts/{p.name}": sha256(p) for p in sorted((ROOT / "scripts").glob("*.py"))},
            **{f"tests/{p.name}": sha256(p) for p in sorted((ROOT / "tests").glob("*.py"))},
        },
    }


def run_process(command: list[str], log_path: Path) -> None:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log_path.write_text(
        "$ " + subprocess.list2cmdline(command) + "\n" + completed.stdout + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"isolated prover failed; see {log_path}")


def make_data(secret: bytes, instance: int, count: int) -> list[int]:
    return [int.from_bytes(digest(b"otgpdp-data", secret, instance.to_bytes(4, "big"),
                                  i.to_bytes(8, "big")), "big") % 2**32 for i in range(count)]


def update_semantics_report(filename: str, data: list[int], tags: list[int], cbf: dict,
                            public: dict, secret: dict) -> dict:
    """Check the deletion-semantics claims on one instance."""
    middle = len(data) // 2
    report = {
        "middle_delete_refused_without_data": False,
        "naive_middle_delete_rejected": False,
        "middle_delete_reindex_accepts": False,
        "tag_attack_after_reindex_accepts": False,
        "middle_insert_reindex_accepts": False,
    }
    try:
        o_update(filename, middle, data[middle], None, tags, cbf, "corrected")
    except ValueError:
        report["middle_delete_refused_without_data"] = True

    naive = tags[:]
    naive.pop(middle)
    reduced = [value for position, value in enumerate(data) if position != middle]
    bloom = CountingBloomFilter.from_dict(cbf)
    bloom.remove(tags[middle])
    chal = o_challenge(len(reduced), 9, b"update-indices", b"update-coefficients",
                       secret["client_sign_key"])
    naive_proof = proof_from_data(reduced, naive, chal, secret["server_sign_key"])
    report["naive_middle_delete_rejected"] = not o_verify(public, filename, bloom.to_dict(), chal,
                                                          naive_proof, "corrected")

    new_tags, new_cbf = o_update(filename, middle, data[middle], None, tags, cbf, "corrected",
                                 data=data)
    honest = proof_from_data(reduced, new_tags, chal, secret["server_sign_key"])
    report["middle_delete_reindex_accepts"] = o_verify(public, filename, new_cbf, chal, honest,
                                                       "corrected")
    attack = proof_from_tags(filename, new_tags, chal, secret["server_sign_key"])
    report["tag_attack_after_reindex_accepts"] = o_verify(public, filename, new_cbf, chal, attack,
                                                         "corrected")

    grown = data[:middle] + [4242] + data[middle:]
    grown_tags, grown_cbf = o_insert(filename, middle, 4242, tags, cbf, "corrected", data=data)
    grown_chal = o_challenge(len(grown), 9, b"insert-indices", b"insert-coefficients",
                             secret["client_sign_key"])
    direct_tags, direct_cbf = rebuild_corrected(filename, grown, cbf["size"], cbf["hashes"])
    report["middle_insert_reindex_accepts"] = (
        grown_tags == direct_tags and grown_cbf == direct_cbf
        and o_verify(public, filename, grown_cbf, grown_chal,
                     proof_from_data(grown, grown_tags, grown_chal, secret["server_sign_key"]),
                     "corrected"))
    return report


def run_otgpdp(output: Path, instances: int, challenge_count: int, data_secret: bytes) -> dict:
    records = []
    for instance in range(instances):
        data = make_data(data_secret, instance, BLOCKS_PER_INSTANCE)
        public, secret = o_setup(f"otgpdp-{instance}".encode())
        filename = f"instance-{instance}.bin"
        tags = meta_gen(filename, data, cbf_size=8192, mode="corrected")[0]
        cbfs = {mode: meta_gen(filename, data, cbf_size=8192, mode=mode)[1]
                for mode in OTGPDP_PROFILES}

        instance_dir = output / f"instance-{instance:02d}"
        instance_dir.mkdir(parents=True, exist_ok=True)
        state = retained_state(filename, tags, public, secret["server_sign_key"])
        encoded_state = canonical(state)
        dump_json(instance_dir / "attacker-state.json", state)
        dump_json(instance_dir / "honest-data-commitment.json", {
            "blocks": BLOCKS_PER_INSTANCE,
            "data_commitment": commitment(canonical(data)),
            "note": "commitment only; the data secret is not stored in this run directory",
        })

        # Challenge randomness is drawn only after the state above is frozen.
        challenge_secret = os.urandom(32)
        challenges = [o_challenge(len(data), 16,
                                  digest(b"oi", challenge_secret, instance.to_bytes(4, "big"),
                                         j.to_bytes(4, "big")),
                                  digest(b"oc", challenge_secret, instance.to_bytes(4, "big"),
                                         j.to_bytes(4, "big")),
                                  secret["client_sign_key"]) for j in range(challenge_count)]
        dump_json(instance_dir / "challenges.json", challenges)
        run_process([sys.executable, str(ROOT / "scripts" / "otgpdp2025_prover_cli.py"),
                     "--state", str(instance_dir / "attacker-state.json"),
                     "--challenges", str(instance_dir / "challenges.json"),
                     "--output", str(instance_dir / "responses.json")], instance_dir / "prover.log")
        responses = load_json(instance_dir / "responses.json")
        profile_metrics: dict[str, int | bool] = {}
        for mode in OTGPDP_PROFILES:
            cbf = cbfs[mode]
            profile_metrics[f"{mode}_meta_accepts"] = meta_verify(filename, data, cbf, mode)
            profile_metrics[f"{mode}_honest_accepts"] = sum(
                o_verify(public, filename, cbf, c,
                         proof_from_data(data, tags, c, secret["server_sign_key"]), mode)
                for c in challenges)
            profile_metrics[f"{mode}_attack_accepts"] = sum(
                o_verify(public, filename, cbf, c, r, mode) for c, r in zip(challenges, responses))

        # A malicious cloud holds a legitimate signing key, so a re-signed
        # tampered response must still be rejected by the algebraic/CBF checks.
        resigned = json.loads(json.dumps(responses[0]))
        resigned["body"]["P"] = hex(int(resigned["body"]["P"], 16) * G % P)
        resigned["signature"] = sign(secret["server_sign_key"], resigned["body"])
        signature_valid = verify_signature(public["server_verify_key"], resigned["body"],
                                           resigned["signature"])
        resigned_rejected = not o_verify(public, filename, cbf, challenges[0], resigned, "corrected")

        low = [int.from_bytes(digest(b"otgpdp-low", data_secret, instance.to_bytes(4, "big"),
                                     i.to_bytes(8, "big")), "big") % 32
               for i in range(LOW_ENTROPY_BLOCKS)]
        low_tags, _ = meta_gen(filename + ".low", low, cbf_size=1024)
        recovered = []
        for i, tag in enumerate(low_tags):
            target = tag * pow(h_group(filename + ".low", i), -1, P) % P
            recovered.append(next((guess for guess in range(256) if pow(G, guess, P) == target), None))

        record = {
            "instance": instance,
            "honest_accepts": profile_metrics["corrected_honest_accepts"],
            "attack_accepts": profile_metrics["corrected_attack_accepts"],
            "challenges": challenge_count,
            **profile_metrics,
            "attacker_state_logical_bytes": len(encoded_state),
            "attacker_state_disk_bytes": (instance_dir / "attacker-state.json").stat().st_size,
            "raw_block_logical_bytes": len(canonical(data)),
            "low_entropy_recovery_success": recovered == low,
            "challenge_secret_commitment": commitment(challenge_secret),
            "resigned_tamper_signature_valid": signature_valid,
            "resigned_tamper_rejected": resigned_rejected,
            **update_semantics_report(filename, data, tags, cbfs["corrected"], public, secret),
        }
        records.append(record)
    dump_json(output / "trials.json", records)
    summary = {
        "instances": instances, "challenges_per_instance": challenge_count,
        "honest_accepted": sum(x["honest_accepts"] for x in records),
        "attack_accepted": sum(x["attack_accepts"] for x in records),
        "total_challenges": instances * challenge_count,
        "literal_meta_accepted_instances": sum(bool(x["literal_meta_accepts"]) for x in records),
        "literal_honest_accepted": sum(x["literal_honest_accepts"] for x in records),
        "literal_attack_accepted": sum(x["literal_attack_accepts"] for x in records),
        "literal_initialized_meta_accepted_instances": sum(
            bool(x["literal_initialized_meta_accepts"]) for x in records),
        "literal_initialized_honest_accepted": sum(
            x["literal_initialized_honest_accepts"] for x in records),
        "literal_initialized_attack_accepted": sum(
            x["literal_initialized_attack_accepts"] for x in records),
        "corrected_meta_accepted_instances": sum(
            bool(x["corrected_meta_accepts"]) for x in records),
        "low_entropy_recovered_instances": sum(bool(x["low_entropy_recovery_success"]) for x in records),
        "resigned_tamper_rejected_instances": sum(bool(x["resigned_tamper_rejected"]) for x in records),
        "resigned_tamper_signatures_valid": sum(bool(x["resigned_tamper_signature_valid"]) for x in records),
        "middle_delete_refused_without_data_instances": sum(
            bool(x["middle_delete_refused_without_data"]) for x in records),
        "naive_middle_delete_rejected_instances": sum(
            bool(x["naive_middle_delete_rejected"]) for x in records),
        "middle_delete_reindex_accepted_instances": sum(
            bool(x["middle_delete_reindex_accepts"]) for x in records),
        "tag_attack_after_reindex_accepted_instances": sum(
            bool(x["tag_attack_after_reindex_accepts"]) for x in records),
        "middle_insert_reindex_accepted_instances": sum(
            bool(x["middle_insert_reindex_accepts"]) for x in records),
        "level": "L2-reimplementation-with-documented-signature-choice",
        "challenge_ordering": "state committed before challenges drawn",
    }
    return summary


def run_song(output: Path, instances: int, challenge_count: int, data_secret: bytes) -> dict:
    records = []
    for instance in range(instances):
        system = new_system(b"song-l1-runner" + instance.to_bytes(4, "big"))
        for file_no in range(3):
            sectors = [[int.from_bytes(digest(b"song-l1-sector", data_secret,
                                              instance.to_bytes(4, "big"), file_no.to_bytes(4, "big"),
                                              block.to_bytes(4, "big"), sector.to_bytes(4, "big")),
                                       "big") % 256 for sector in range(3)] for block in range(8)]
            insert(system, sectors, ["shared", f"file-{file_no}"], f"state-{instance}-{file_no}".encode())
        state = projection_state(system)
        file_ids = list(system["files"])
        block_counts = {fid: len(value["sectors"]) for fid, value in system["files"].items()}

        instance_dir = output / f"instance-{instance:02d}"
        instance_dir.mkdir(parents=True, exist_ok=True)
        dump_json(instance_dir / "attacker-state.json", state)
        challenge_secret = os.urandom(32)
        challenge_values = [
            s_challenge(digest(b"song-challenge", challenge_secret, instance.to_bytes(4, "big"),
                               j.to_bytes(4, "big"))) for j in range(challenge_count)]
        requests = []
        for j, chal in enumerate(challenge_values):
            requests.append({"kind": "audit", "file_id": file_ids[j % len(file_ids)], "challenge": chal})
            query = search_request(system, "shared", chal)
            requests.append({"kind": "search", "token": query["token"], "latest_state": query["latest_state"],
                             "challenge": chal})
        dump_json(instance_dir / "requests.json", requests)
        run_process([sys.executable, str(ROOT / "scripts" / "song2025_prover_cli.py"),
                     "--state", str(instance_dir / "attacker-state.json"),
                     "--requests", str(instance_dir / "requests.json"),
                     "--output", str(instance_dir / "responses.json")], instance_dir / "prover.log")
        responses = load_json(instance_dir / "responses.json")
        audit_accepts, search_accepts, honest_accepts = [], [], []
        for j, chal in enumerate(challenge_values):
            audit = responses[2 * j]
            search = responses[2 * j + 1]
            expected_fid = file_ids[j % len(file_ids)]
            query = search_request(system, "shared", chal)
            audit_accepts.append(verify_audit(system["public"], expected_fid, audit, chal,
                                              block_counts[expected_fid]))
            search_accepts.append(verify_search(system["public"], query, search, chal, block_counts))
            value = system["files"][expected_fid]
            honest_accepts.append(verify_audit(system["public"], expected_fid,
                                               proof_from_sectors(expected_fid, value["sectors"],
                                                                  value["tags"], chal),
                                               chal, block_counts[expected_fid]))
        raw_sectors = {fid: value["sectors"] for fid, value in system["files"].items()}
        encoded_state = canonical(state)
        records.append({
            "instance": instance, "challenges": challenge_count,
            "honest_audit_accepts": sum(honest_accepts),
            "projection_audit_accepts": sum(audit_accepts),
            "projection_search_accepts": sum(search_accepts),
            "attacker_state_logical_bytes": len(encoded_state),
            "attacker_state_disk_bytes": (instance_dir / "attacker-state.json").stat().st_size,
            "raw_sector_logical_bytes": len(canonical(raw_sectors)),
            "client_secret_in_attacker_state": any(
                key in encoded_state for key in (b'"mk"', b'"sk"', b'"ek"', b'"sectors"')),
            "sector_dimension": 3,
            "challenge_secret_commitment": commitment(challenge_secret),
        })
    dump_json(output / "trials.json", records)
    return {
        "instances": instances, "challenges_per_instance": challenge_count,
        "honest_audit_accepted": sum(x["honest_audit_accepts"] for x in records),
        "projection_audit_accepted": sum(x["projection_audit_accepts"] for x in records),
        "projection_search_accepted": sum(x["projection_search_accepts"] for x in records),
        "total_each_path": instances * challenge_count,
        "attacker_states_with_client_secret": sum(bool(x["client_secret_in_attacker_state"]) for x in records),
        "level": "L1-algebraic-composite-order-model",
        "challenge_ordering": "state committed before challenges drawn",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument("--challenges", type=int, default=100)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()
    if args.instances < 1 or args.challenges < 1:
        raise ValueError("instances and challenges must be positive")
    provided = os.environ.get("AGGREGATE_AUDIT_DATA_SECRET")
    data_secret = bytes.fromhex(provided) if provided else os.urandom(32)
    data_secret_source = "environment" if provided else "generated"
    params = {
        "run_id": args.run_id, "instances": args.instances, "challenges": args.challenges,
        "randomness": "per-trial challenges drawn after the attacker state is written; only commitments recorded",
        "data_secret_source": data_secret_source,
        "data_secret_commitment": commitment(data_secret),
        "challenge_ordering": "state committed before challenges drawn",
    }
    summaries = {}
    for case, function in (("otgpdp2025", run_otgpdp), ("song2025", run_song)):
        output = ROOT / "results" / case / args.run_id
        output.mkdir(parents=True, exist_ok=False)
        dump_json(output / "parameters.json", params)
        dump_json(output / "environment.json", environment())
        (output / "command.txt").write_text(
            f"{sys.executable} scripts/run_experiments.py --instances {args.instances} "
            f"--challenges {args.challenges} --run-id {args.run_id}\n", encoding="utf-8")
        summary = function(output, args.instances, args.challenges, data_secret)
        dump_json(output / "summary.json", summary)
        summaries[case] = summary
    print(json.dumps(summaries, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
