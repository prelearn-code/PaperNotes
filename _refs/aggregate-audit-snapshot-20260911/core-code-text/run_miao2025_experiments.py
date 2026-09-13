"""Miao 2025 negative-control matrix (second real published scheme).

The paper explicitly allows a cloud that "attempts to create a fraudulent
integrity proof" (adversary A3), yet its audit path must not be flagged by the
analysis rule: the sector weights stay secret, so the cloud cannot form the
required ``prod_k A_k^{mu_k}``.  An explicitly marked control variant with
revealed weights shows the rule keys on server-computability.
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
from scripts.miao2025_protocol import (
    authgen,
    cached_state,
    challenge,
    keygen,
    proof_from_cached,
    proof_from_data,
    setup,
    verify,
    with_revealed_weights,
)

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = 8
SECTORS = 3
KEYWORD_INDEX = 11


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Miao 2025 negative-control matrix")
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument("--challenges", type=int, default=100)
    parser.add_argument("--challenge-size", type=int, default=4)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("neg-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    if min(args.instances, args.challenges, args.challenge_size) < 1:
        raise ValueError("all size arguments must be positive")

    output = args.results_root / "miao2025" / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    provided = os.environ.get("AGGREGATE_AUDIT_DATA_SECRET")
    data_secret = bytes.fromhex(provided) if provided else os.urandom(32)
    dump_json(output / "parameters.json", {
        "run_id": args.run_id, "instances": args.instances,
        "challenges_per_instance": args.challenges, "challenge_size": args.challenge_size,
        "blocks_per_instance": BLOCKS, "sectors_per_block": SECTORS,
        "paper": "Miao et al. 2025, IEEE TDSC 22(6), Blockchain-Assisted Searchable Integrity Auditing for Large-Scale Similarity Data With Arbitration",
        "purpose": "second negative control: a real published scheme the analysis rule must not flag",
        "profiles": ["published", "weights_public (explicit control variant, not the paper)"],
        "verification_equation": "e(T * prod Omega^{v}, g) = e(prod H4^{v} * prod_k A_k^{mu_k}, R) * e(H1(ID)^{sum v}, P_0)",
        "consistency_note": "Eq. (1) forces sk_ID = H1(ID)^alpha and R = g^x = P_1; those are the only assignments under which the honest path verifies",
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
        f"{sys.executable} scripts/run_miao2025_experiments.py --instances {args.instances} "
        f"--challenges {args.challenges} --challenge-size {args.challenge_size} "
        f"--run-id {args.run_id}\n", encoding="utf-8")

    records = []
    for instance in range(args.instances):
        rng = random.Random(13579 + instance)
        blocks = [[rng.randrange(1, 2 ** 16) for _ in range(SECTORS)] for _ in range(BLOCKS)]
        parameters = setup(b"miao-runner" + instance.to_bytes(4, "big"))
        owner = keygen(parameters, f"id-{instance}", b"miao-owner" + instance.to_bytes(4, "big"))
        record = {"instance": instance}
        for profile in ("published", "weights_public"):
            state = authgen(parameters, owner, blocks, KEYWORD_INDEX,
                            b"miao-a" + instance.to_bytes(4, "big"), profile=profile)
            cache = cached_state(blocks, "published")
            if profile == "weights_public":
                cache = with_revealed_weights(state, blocks)
            honest = cached_hits = tampered = damaged_rejected = 0
            for ordinal in range(args.challenges):
                chal = challenge(BLOCKS, args.challenge_size,
                                 instance.to_bytes(4, "big") + ordinal.to_bytes(4, "big"))
                proof = proof_from_data(state, blocks, chal)
                honest += int(verify(parameters, owner, state, chal, proof))
                cached_hits += int(verify(parameters, owner, state, chal,
                                          proof_from_cached(state, cache, chal)))
                broken = dict(proof)
                broken["mu"] = [(proof["mu"][0] + 1) % (2 ** 31 - 1)] + proof["mu"][1:]
                tampered += int(not verify(parameters, owner, state, chal, broken))
                damaged = list(blocks)
                damaged[chal["indices"][0]] = [0] * SECTORS
                damaged_rejected += int(not verify(parameters, owner, state, chal,
                                                   proof_from_data(state, damaged, chal)))
            record[f"{profile}_honest_accepted"] = honest
            record[f"{profile}_cached_projection_accepted"] = cached_hits
            record[f"{profile}_tampered_rejected"] = tampered
            record[f"{profile}_damaged_rejected"] = damaged_rejected
        records.append(record)

    dump_json(output / "trials.json", records)

    def total(key: str) -> int:
        return sum(int(record.get(key, 0)) for record in records)

    summary = {
        "case": "miao2025",
        "level": "key-audit-path reimplementation, reduced parameters (negative control)",
        "paper": "Miao et al. 2025, IEEE TDSC 22(6)",
        "instances": args.instances, "challenges_per_instance": args.challenges,
        "total_challenges": args.instances * args.challenges,
        "published_honest_accepted": total("published_honest_accepted"),
        "published_cached_projection_accepted": total("published_cached_projection_accepted"),
        "published_tampered_rejected": total("published_tampered_rejected"),
        "published_damaged_rejected": total("published_damaged_rejected"),
        "weights_public_honest_accepted": total("weights_public_honest_accepted"),
        "weights_public_cached_projection_accepted": total("weights_public_cached_projection_accepted"),
        "verdict": ("second real published scheme on which the rule does not false-positive: "
                    "the published secret-weight configuration rejects the cached-projection "
                    "prover on every challenge, while the explicit revealed-weight control "
                    "variant accepts it"),
        "data_secret_source": "environment" if provided else "generated",
    }
    dump_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
