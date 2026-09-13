"""Yang 2026 negative-control matrix.

Purpose: show that the analysis rule does **not** flag a real published scheme
whose response is computed from per-sector aggregates, because the projection
weights stay secret.  The matrix also contains an explicitly marked control
variant in which those weights are revealed, to show the rule keys on
server-computability rather than on the mere existence of a projection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import dump_json
from scripts.yang2026_protocol import (
    cached_state,
    challenge,
    keygen,
    proof_from_cached,
    proof_from_data,
    setup,
    taggen,
    verify_audit,
    verify_upload,
    with_revealed_weights,
)

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = 8
SECTORS = 3
K_L = 13579


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Yang 2026 negative-control matrix")
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument("--challenges", type=int, default=100)
    parser.add_argument("--challenge-size", type=int, default=4)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("neg-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    if min(args.instances, args.challenges, args.challenge_size) < 1:
        raise ValueError("all size arguments must be positive")

    output = args.results_root / "yang2026" / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    provided = os.environ.get("AGGREGATE_AUDIT_DATA_SECRET")
    data_secret = bytes.fromhex(provided) if provided else os.urandom(32)
    dump_json(output / "parameters.json", {
        "run_id": args.run_id, "instances": args.instances,
        "challenges_per_instance": args.challenges, "challenge_size": args.challenge_size,
        "blocks_per_instance": BLOCKS, "sectors_per_block": SECTORS,
        "paper": "Yang et al. 2026, IEEE TNSM, DOI 10.1109/TNSM.2025.3650222",
        "purpose": "negative control: a real published scheme the analysis rule must not flag",
        "profiles": ["published", "weights_public (explicit control variant, not the paper)"],
        "data_secret_source": "environment" if provided else "generated",
        "data_secret_commitment": hashlib.sha256(data_secret).hexdigest(),
        "security_note": "reduced functional parameters; this case is a rule check, not a security result",
    })
    dump_json(output / "environment.json", {
        "python": sys.version, "platform": platform.platform(),
        "source_sha256": {
            **{f"scripts/{p.name}": sha256_file(p) for p in sorted((ROOT / "scripts").glob("*.py"))},
            **{f"tests/{p.name}": sha256_file(p) for p in sorted((ROOT / "tests").glob("*.py"))},
        },
    })
    (output / "command.txt").write_text(
        f"{sys.executable} scripts/run_yang2026_experiments.py --instances {args.instances} "
        f"--challenges {args.challenges} --challenge-size {args.challenge_size} "
        f"--run-id {args.run_id}\n", encoding="utf-8")

    records = []
    for instance in range(args.instances):
        rng = random.Random(97531 + instance)
        blocks = [[rng.randrange(1, 2 ** 16) for _ in range(SECTORS)] for _ in range(BLOCKS)]
        parameters = setup(b"yang-runner" + instance.to_bytes(4, "big"))
        owner = keygen(parameters, f"do-{instance}", b"yang-owner" + instance.to_bytes(4, "big"))
        record = {"instance": instance}
        for profile in ("published", "weights_public"):
            state = taggen(parameters, owner, K_L, blocks, b"yang-a" + instance.to_bytes(4, "big"),
                           profile=profile)
            record[f"{profile}_upload_accepted"] = int(
                verify_upload(parameters, owner, state, blocks, b"upload"))
            accepts = honest = cached = tampered = damaged_rejected = 0
            cache = cached_state(blocks, "published")
            if profile == "weights_public":
                cache = with_revealed_weights(state, blocks)
            for ordinal in range(args.challenges):
                chal = challenge(BLOCKS, args.challenge_size,
                                 instance.to_bytes(4, "big") + ordinal.to_bytes(4, "big"))
                honest_proof = proof_from_data(state, blocks, chal)
                honest += int(verify_audit(parameters, owner, state, chal, honest_proof))
                cached += int(verify_audit(parameters, owner, state, chal,
                                           proof_from_cached(state, cache, chal)))
                broken = dict(honest_proof)
                broken["u"] = [(honest_proof["u"][0] + 1) % (2 ** 31 - 1)] + honest_proof["u"][1:]
                tampered += int(not verify_audit(parameters, owner, state, chal, broken))
                damaged = list(blocks)
                damaged[chal["indices"][0]] = [0] * SECTORS
                damaged_rejected += int(not verify_audit(
                    parameters, owner, state, chal, proof_from_data(state, damaged, chal)))
                accepts += 1
            record[f"{profile}_honest_accepted"] = honest
            record[f"{profile}_cached_projection_accepted"] = cached
            record[f"{profile}_tampered_rejected"] = tampered
            record[f"{profile}_damaged_rejected"] = damaged_rejected
            record[f"{profile}_total"] = accepts
        records.append(record)

    dump_json(output / "trials.json", records)

    def total(key: str) -> int:
        return sum(int(record.get(key, 0)) for record in records)

    summary = {
        "case": "yang2026",
        "level": "key-audit-path reimplementation, reduced parameters (negative control)",
        "paper": "Yang et al. 2026, IEEE TNSM, DOI 10.1109/TNSM.2025.3650222",
        "instances": args.instances, "challenges_per_instance": args.challenges,
        "total_challenges": args.instances * args.challenges,
        "published_upload_accepted_instances": total("published_upload_accepted"),
        "published_honest_accepted": total("published_honest_accepted"),
        "published_cached_projection_accepted": total("published_cached_projection_accepted"),
        "published_tampered_rejected": total("published_tampered_rejected"),
        "published_damaged_rejected": total("published_damaged_rejected"),
        "weights_public_honest_accepted": total("weights_public_honest_accepted"),
        "weights_public_cached_projection_accepted": total("weights_public_cached_projection_accepted"),
        "verdict": ("the analysis rule does not flag this scheme: with the published "
                    "(secret-weight) configuration the cached-projection prover is rejected "
                    "on every challenge, while the explicit control variant with revealed "
                    "weights is accepted, so the rule keys on server-computability"),
        "data_secret_source": "environment" if provided else "generated",
    }
    dump_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
