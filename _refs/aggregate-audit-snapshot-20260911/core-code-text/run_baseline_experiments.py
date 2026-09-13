"""Authenticated extractable baseline experiment matrix (positive control).

Each instance runs two structures over the same real composite-order pairing
backend and the same data:

* ``independent``: per-sector generators.  The block-sum-only prover must fail,
  enough accepted responses must determine every sector, and extraction must
  return the original data.
* ``shared_base``: one base for all sectors.  The same block-sum-only prover
  answers every challenge, which is the collapse the analysis rule must flag.

The point is to show that the analysis procedure separates a genuinely
extractable construction from a collapsed one, not to attack any paper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.authenticated_baseline import (
    ORDER,
    challenge,
    extract,
    extraction_rank,
    respond_from_block_sums,
    respond_from_data,
    sector_generators,
    setup,
    tags,
    verify,
)
from scripts.common import canonical, digest, dump_json
from scripts.song2025_pairing import P_FACTOR, Q_FACTOR

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_blocks(secret: bytes, instance: int, blocks: int, sectors: int) -> list[list[int]]:
    return [[int.from_bytes(digest(b"baseline-data", secret, instance.to_bytes(4, "big"),
                                  index.to_bytes(8, "big"), sector.to_bytes(8, "big")), "big") % 256
             for sector in range(sectors)] for index in range(blocks)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the authenticated extractable baseline")
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument("--blocks", type=int, default=6)
    parser.add_argument("--sectors", type=int, default=3)
    parser.add_argument("--challenges", type=int, default=8)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("baseline-%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()
    if min(args.instances, args.blocks, args.sectors, args.challenges) < 1:
        raise ValueError("all size arguments must be positive")
    if args.challenges < args.blocks:
        raise ValueError("extraction needs at least as many challenges as blocks")

    output = ROOT / "results" / "baseline" / args.run_id
    output.mkdir(parents=True, exist_ok=False)

    provided = os.environ.get("AGGREGATE_AUDIT_DATA_SECRET")
    data_secret = bytes.fromhex(provided) if provided else os.urandom(32)
    params = {
        "run_id": args.run_id, "instances": args.instances,
        "blocks": args.blocks, "sectors": args.sectors, "challenges": args.challenges,
        "composite_order": ORDER, "order_factors": [P_FACTOR, Q_FACTOR],
        "backend": "supersingular y^2=x^3+x; reduced Tate pairing; embedding degree 2",
        "structures": ["independent per-sector generators", "shared single base"],
        "challenge_shape": "full coverage: every block carries an independent coefficient",
        "data_secret_source": "environment" if provided else "generated",
        "data_secret_commitment": hashlib.sha256(data_secret).hexdigest(),
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
        f"{sys.executable} scripts/run_baseline_experiments.py --instances {args.instances} "
        f"--blocks {args.blocks} --sectors {args.sectors} --challenges {args.challenges} "
        f"--run-id {args.run_id}\n", encoding="utf-8")

    records = []
    for instance in range(args.instances):
        public, secret = setup(b"baseline-runner" + instance.to_bytes(4, "big"))
        blocks = make_blocks(data_secret, instance, args.blocks, args.sectors)
        generators = sector_generators(args.sectors)
        name = f"baseline-{instance}.bin"
        challenge_secret = os.urandom(32)
        challenges = [challenge(name, args.blocks, digest(b"baseline-challenge", challenge_secret,
                                                          instance.to_bytes(4, "big"),
                                                          k.to_bytes(4, "big")))
                      for k in range(args.challenges)]
        block_sums = [sum(block) for block in blocks]
        record = {"instance": instance, "challenges": args.challenges,
                  "challenge_secret_commitment": hashlib.sha256(challenge_secret).hexdigest()}

        for mode in ("independent", "shared_base"):
            tag_list = tags(name, blocks, secret["sk"], generators, mode)
            honest = [respond_from_data(blocks, tag_list, c, mode) for c in challenges]
            cached = [respond_from_block_sums(block_sums, tag_list, c, mode, args.sectors)
                      for c in challenges]
            record[f"{mode}_honest_accepted"] = sum(
                verify(public, generators, c, r, mode) for c, r in zip(challenges, honest))
            record[f"{mode}_cached_prover_accepted"] = sum(
                verify(public, generators, c, r, mode) for c, r in zip(challenges, cached))
            if mode == "independent":
                record["extraction_rank"] = extraction_rank(challenges, args.blocks)
                try:
                    recovered = extract(args.blocks, args.sectors, challenges, honest)
                    record["extraction_succeeded"] = recovered == blocks
                    record["extraction_returned_original_values"] = all(
                        0 <= value < 256 for row in recovered for value in row)
                except ValueError:
                    record["extraction_succeeded"] = False
                    record["extraction_returned_original_values"] = False
                tampered = json.loads(json.dumps(honest[0]))
                tampered["mu"][0] = (tampered["mu"][0] + 1) % ORDER
                record["tampered_rejected"] = not verify(public, generators, challenges[0], tampered,
                                                        "independent")
                # A verifier that ignores the sector structure would accept an
                # independent response whose aggregates were not per-sector.
                record["independent_response_under_shared_verifier_rejected"] = not verify(
                    public, generators, challenges[0], honest[0], "shared_base")

        record["cached_state_logical_bytes"] = len(canonical(block_sums))
        record["honest_state_logical_bytes"] = len(canonical(blocks))
        records.append(record)
    dump_json(output / "trials.json", records)

    def total(key: str) -> int:
        return sum(int(record.get(key, 0)) for record in records)

    summary = {
        "level": "positive-control-authenticated-extractable-baseline",
        "instances": args.instances, "blocks": args.blocks, "sectors": args.sectors,
        "challenges_per_instance": args.challenges,
        "independent_honest_accepted": total("independent_honest_accepted"),
        "independent_cached_prover_accepted": total("independent_cached_prover_accepted"),
        "shared_base_honest_accepted": total("shared_base_honest_accepted"),
        "shared_base_cached_prover_accepted": total("shared_base_cached_prover_accepted"),
        "extraction_succeeded_instances": sum(bool(r["extraction_succeeded"]) for r in records),
        "full_rank_instances": sum(r["extraction_rank"] == args.blocks for r in records),
        "tampered_rejected_instances": total("tampered_rejected"),
        "independent_response_under_shared_verifier_rejected_instances":
            total("independent_response_under_shared_verifier_rejected"),
        "average_cached_state_logical_bytes": sum(
            r["cached_state_logical_bytes"] for r in records) / len(records),
        "average_honest_state_logical_bytes": sum(
            r["honest_state_logical_bytes"] for r in records) / len(records),
        "data_secret_source": params["data_secret_source"],
    }
    dump_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
