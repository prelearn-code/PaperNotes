"""Zhang et al. 2025 (IEEE TC) L2 experiment matrix.

Strictness conventions match the other runners: data comes from a secret that is
not written to the run directory (only its commitment), the attacker state is
written before challenge randomness is drawn, and every trial uses its own
challenge.

The printed proof list in Eq. (7) is ``{p_{a_i}}_{1<=i<=l2}`` while the
verification sums ``p`` over the sector index; the paper's notation is
self-inconsistent, so both readings are measured:

* ``per_block``  - one value per challenged block (follows the printed list);
* ``per_sector`` - one value per sector (follows the printed sum).

Measured paths: honest upload check (Eq. 2), honest audit proof, the cached-state
prover under both readings, the single-block prover, cross-challenge reuse, and
the explicitly repaired ``sector_bound`` profile.
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
from scripts.lihang2026_pairing import GROUP_ORDER, Point
from scripts.zhang2025_protocol import (
    audit_key,
    authentication_tags,
    cached_state,
    challenge,
    file_public_key,
    minimal_state_bits,
    owner_key,
    proof_from_data,
    proof_from_single_block,
    setup,
    verify_audit,
    verify_upload,
)

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = 16
SECTORS = 4
K_L = 987654321
SHAPES = ("per_block", "per_sector")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commitment(secret: bytes) -> str:
    return hashlib.sha256(secret).hexdigest()


def make_blocks(secret: bytes, instance: int) -> list[list[int]]:
    return [[int.from_bytes(digest(b"zhang-data", secret, instance.to_bytes(4, "big"),
                                   index.to_bytes(8, "big"), sector.to_bytes(8, "big")), "big")
             % (2 ** 16) for sector in range(SECTORS)] for index in range(BLOCKS)]


def run_process(command: list[str], log_path: Path) -> None:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log_path.write_text("$ " + subprocess.list2cmdline(command) + "\n"
                        + completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"isolated Zhang prover failed; see {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Zhang 2025 L2 matrix")
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument("--challenges", type=int, default=100)
    parser.add_argument("--challenge-size", type=int, default=6)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("l2-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--results-root", type=Path, default=ROOT / "results",
                        help="root for the run directory (tests use a temporary directory)")
    args = parser.parse_args()
    if min(args.instances, args.challenges, args.challenge_size) < 1:
        raise ValueError("all size arguments must be positive")
    if args.challenge_size > BLOCKS:
        raise ValueError("challenge size cannot exceed the block count")

    output = args.results_root / "zhang2025" / args.run_id
    output.mkdir(parents=True, exist_ok=False)

    provided = os.environ.get("AGGREGATE_AUDIT_DATA_SECRET")
    data_secret = bytes.fromhex(provided) if provided else os.urandom(32)
    literal = {shape: setup(b"zhang2025-runner", sectors=SECTORS, mode="literal", shape=shape)
               for shape in SHAPES}
    repaired = setup(b"zhang2025-runner", sectors=SECTORS, mode="sector_bound",
                     shape="per_sector")
    params = {
        "run_id": args.run_id, "instances": args.instances,
        "challenges_per_instance": args.challenges, "challenge_size": args.challenge_size,
        "blocks_per_instance": BLOCKS, "sectors_per_block": SECTORS,
        "group_order_bits": GROUP_ORDER.bit_length(),
        "backend": "prime-order type-1 reduced Tate pairing (reduced functional parameters)",
        "profiles": ["literal", "sector_bound"],
        "proof_shapes": list(SHAPES),
        "notation_note": "Eq. (7) prints one p per challenged block while the verification sums p over the sector index; both readings are measured",
        "paper": "Zhang et al. 2025, IEEE TC, DOI 10.1109/TC.2025.3540670",
        "data_secret_source": "environment" if provided else "generated",
        "data_secret_commitment": commitment(data_secret),
        "challenge_ordering": "attacker state is written to disk before challenge randomness is drawn",
        "security_note": "reduced functional parameters; not production security",
    }
    dump_json(output / "parameters.json", params)
    dump_json(output / "environment.json", {
        "python": sys.version, "platform": platform.platform(),
        "source_sha256": {
            **{f"scripts/{p.name}": sha256_file(p) for p in sorted((ROOT / "scripts").glob("*.py"))},
            **{f"tests/{p.name}": sha256_file(p) for p in sorted((ROOT / "tests").glob("*.py"))},
        },
    })
    (output / "command.txt").write_text(
        f"{sys.executable} scripts/run_zhang2025_experiments.py --instances {args.instances} "
        f"--challenges {args.challenges} --challenge-size {args.challenge_size} "
        f"--run-id {args.run_id}\n", encoding="utf-8")

    records = []
    for instance in range(args.instances):
        blocks = make_blocks(data_secret, instance)
        key = audit_key(b"zhang-audit-key" + instance.to_bytes(4, "big"))
        owner = owner_key(b"zhang-owner-key" + instance.to_bytes(4, "big"))
        public_keys = {shape: file_public_key(K_L, key["s_t"]) for shape in SHAPES}
        repaired_key = file_public_key(K_L, key["s_t"])
        upload_key = file_public_key(K_L, owner["s_a"])
        tags = {shape: authentication_tags(literal[shape], blocks, K_L) for shape in SHAPES}
        repaired_tags = authentication_tags(repaired, blocks, K_L)

        instance_dir = output / f"instance-{instance:02d}"
        instance_dir.mkdir(parents=True, exist_ok=False)
        state = cached_state(literal["per_block"], blocks, tags["per_block"], key)
        repaired_state = cached_state(repaired, blocks, repaired_tags, key)
        dump_json(instance_dir / "attacker-state.json", state)
        dump_json(instance_dir / "attacker-state-sector-bound.json", repaired_state)
        dump_json(instance_dir / "honest-data-commitment.json", {
            "blocks": BLOCKS, "sectors": SECTORS,
            "ciphertext_commitment": commitment(canonical(blocks)),
            "note": "commitment only; the data secret is not stored in this run directory",
        })

        # --- only now draw challenge randomness ---------------------------------
        challenge_secret = os.urandom(32)
        challenges = [challenge(BLOCKS, args.challenge_size,
                                digest(b"zhang-challenge", challenge_secret,
                                       instance.to_bytes(4, "big"), ordinal.to_bytes(4, "big")))
                      for ordinal in range(args.challenges)]

        requests, expected = [], []
        for ordinal, chal in enumerate(challenges):
            coefficient = chal["coefficients"][ordinal % len(chal["coefficients"])]
            for shape in SHAPES:
                requests.append({"kind": "cached", "shape": shape, "distribute": "first",
                                 "challenge": chal})
                expected.append(("cached", shape, ordinal))
            requests.append({"kind": "single", "index": ordinal % BLOCKS,
                             "coefficient": coefficient, "challenge": chal})
            expected.append(("single", "per_block", ordinal))
        dump_json(instance_dir / "requests.json", requests)
        run_process([sys.executable, str(ROOT / "scripts" / "zhang2025_prover_cli.py"),
                     "--state", str(instance_dir / "attacker-state.json"),
                     "--requests", str(instance_dir / "requests.json"),
                     "--output", str(instance_dir / "responses.json")], instance_dir / "prover.log")
        responses = load_json(instance_dir / "responses.json")

        counters: dict[str, int] = {}
        for (kind, shape, ordinal), response in zip(expected, responses):
            chal = challenges[ordinal]
            label = f"single_block_{shape}" if kind == "single" else f"cached_{shape}"
            counters[f"{label}_literal_accepted"] = counters.get(
                f"{label}_literal_accepted", 0) + int(
                verify_audit(literal[shape], public_keys[shape], chal, response))
            # Same response checked against the explicitly repaired profile.
            counters[f"{label}_sector_bound_accepted"] = counters.get(
                f"{label}_sector_bound_accepted", 0) + int(
                verify_audit(repaired, repaired_key, chal, response | {"mode": "sector_bound"}))

        # --- the repaired profile with its own isolated prover ------------------
        dump_json(instance_dir / "requests-sector-bound.json",
                  [{"kind": "cached", "shape": "per_sector", "challenge": chal}
                   for chal in challenges])
        run_process([sys.executable, str(ROOT / "scripts" / "zhang2025_prover_cli.py"),
                     "--state", str(instance_dir / "attacker-state-sector-bound.json"),
                     "--requests", str(instance_dir / "requests-sector-bound.json"),
                     "--output", str(instance_dir / "responses-sector-bound.json")],
                    instance_dir / "prover-sector-bound.log")
        repaired_responses = load_json(instance_dir / "responses-sector-bound.json")
        counters["cached_sector_bound_profile_accepted"] = sum(
            int(verify_audit(repaired, repaired_key, chal, response))
            for chal, response in zip(challenges, repaired_responses))

        # --- controls -----------------------------------------------------------
        honest_upload = honest_audit = damaged_rejected = zeroed_rejected = 0
        cross_challenge_accepted = collapsed_split_accepted = 0
        for ordinal, chal in enumerate(challenges):
            honest_upload += int(verify_upload(literal["per_block"], blocks,
                                               tags["per_block"], upload_key, owner["s_a"],
                                               b"upload"))
            proof = proof_from_data(literal["per_block"], blocks, tags["per_block"], chal, key)
            honest_audit += int(verify_audit(literal["per_block"], public_keys["per_block"],
                                             chal, proof))
            damaged = list(blocks)
            damaged[chal["indices"][0]] = [0] * SECTORS
            damaged_rejected += int(not verify_audit(
                literal["per_block"], public_keys["per_block"], chal,
                proof_from_data(literal["per_block"], damaged, tags["per_block"], chal, key)))
            zeroed_rejected += int(not verify_audit(literal["per_block"],
                                                    public_keys["per_block"], chal,
                                                    dict(proof, p=[0] * len(proof["p"]))))
            collapsed_split_accepted += int(verify_audit(
                literal["per_block"], public_keys["per_block"], chal,
                dict(proof, p=[sum(proof["p"]) % GROUP_ORDER])))
            other = challenges[(ordinal + 1) % len(challenges)]
            cross_challenge_accepted += int(verify_audit(literal["per_block"],
                                                         public_keys["per_block"], other, proof))

        single_proof = proof_from_single_block(
            literal["per_block"], 0, challenges[0]["coefficients"][0],
            Point.from_dict(state["hashes"][0]), state["sums"][0], tags["per_block"][0], key)
        record = {
            "instance": instance,
            "challenges": args.challenges,
            "distinct_challenge_index_sets": len({tuple(chal["indices"]) for chal in challenges}),
            "honest_upload_accepted": honest_upload,
            "honest_audit_accepted": honest_audit,
            "damaged_control_rejected": damaged_rejected,
            "zeroed_aggregates_rejected": zeroed_rejected,
            "collapsed_split_accepted": collapsed_split_accepted,
            "cross_challenge_accepted": cross_challenge_accepted,
            "attacker_state_serialized_bytes": len(canonical(state)),
            "single_block_state_bytes": len(canonical(
                {"hash": state["hashes"][0], "sum": state["sums"][0],
                 "tag": state["tags"][0], "audit_key": state["audit_key"],
                 "parameters": state["parameters"]})),
            "honest_ciphertext_logical_bytes": len(canonical(blocks)),
            "challenge_secret_commitment": commitment(challenge_secret),
            **counters,
        }
        records.append(record)

    dump_json(output / "trials.json", records)

    def total(key: str) -> int:
        return sum(int(record.get(key, 0)) for record in records)

    summary = {
        "level": "L2-real-prime-order-type1-pairing-reimplementation-reduced-parameters",
        "paper": "Zhang et al. 2025, IEEE TC, DOI 10.1109/TC.2025.3540670",
        "instances": args.instances, "challenges_per_instance": args.challenges,
        "challenge_size": args.challenge_size, "blocks_per_instance": BLOCKS,
        "sectors_per_block": SECTORS,
        "total_challenges": args.instances * args.challenges,
        "distinct_challenge_index_sets": sum(r["distinct_challenge_index_sets"] for r in records),
        "honest_upload_accepted": total("honest_upload_accepted"),
        "honest_audit_accepted": total("honest_audit_accepted"),
        "cached_per_block_literal_accepted": total("cached_per_block_literal_accepted"),
        "cached_per_sector_literal_accepted": total("cached_per_sector_literal_accepted"),
        "single_block_per_block_literal_accepted": total("single_block_per_block_literal_accepted"),
        "cached_per_block_sector_bound_accepted": total("cached_per_block_sector_bound_accepted"),
        "cached_per_sector_sector_bound_accepted": total("cached_per_sector_sector_bound_accepted"),
        "single_block_per_block_sector_bound_accepted": total(
            "single_block_per_block_sector_bound_accepted"),
        "cached_sector_bound_profile_accepted": total("cached_sector_bound_profile_accepted"),
        "collapsed_split_accepted": total("collapsed_split_accepted"),
        "damaged_control_rejected": total("damaged_control_rejected"),
        "zeroed_aggregates_rejected": total("zeroed_aggregates_rejected"),
        "cross_challenge_accepted": total("cross_challenge_accepted"),
        "average_attacker_state_serialized_bytes": sum(
            r["attacker_state_serialized_bytes"] for r in records) / len(records),
        "average_single_block_state_bytes": sum(
            r["single_block_state_bytes"] for r in records) / len(records),
        "average_honest_ciphertext_logical_bytes": sum(
            r["honest_ciphertext_logical_bytes"] for r in records) / len(records),
        "paper_scale_accounting": {
            "field_and_group_bits": 256,
            "sectors": 100,
            "compression_ratio_cached_full_state": minimal_state_bits(
                1, 100, 256, 256)["compression_ratio"],
            "single_block_state_is_constant": True,
        },
        "data_secret_source": params["data_secret_source"],
        "challenge_ordering": params["challenge_ordering"],
    }
    dump_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
