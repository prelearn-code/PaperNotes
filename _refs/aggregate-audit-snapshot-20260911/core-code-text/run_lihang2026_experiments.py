"""Li Hang 2026 L2 experiment matrix.

Design notes that address earlier review points for this workspace:

* Ciphertext blocks are generated from a secret (``os.urandom`` by default) that
  is NOT written to the results directory; only its SHA-256 commitment is
  recorded.  The cached-digest state therefore cannot be inverted back into the
  experiment data by a reader of the run directory.
* The attacker state is serialized to disk BEFORE any challenge is generated.
  Challenge randomness is drawn afterwards and only its commitment is recorded,
  so challenges are unpredictable at the moment the state is frozen.
* Every trial uses its own independent challenge (fresh index set and nonce);
  the number of distinct index sets is recorded per instance.
* The isolated proving process is given only the serialized state and the
  request list.
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

from scripts.common import canonical, digest, dump_json, hash_int, load_json
from scripts.lihang2026_protocol import (
    CHUNK_BYTES,
    GROUP_ORDER,
    NONCE_BYTES,
    PAPER_BLOCK_BYTES,
    challenge,
    digest_state_bits,
    honest_state_bits,
    initialization,
    proof_from_blocks,
    proof_from_digests,
    setup,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]
STATE_SCHEMA = "lihang2026-cached-digest-state-v1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commitment(secret: bytes) -> str:
    return hashlib.sha256(secret).hexdigest()


def make_blocks(secret: bytes, instance: int, count: int, size: int) -> list[bytes]:
    if size % 32 or size % CHUNK_BYTES:
        raise ValueError("block size must be a multiple of 32 and of the chunk size")
    return [b"".join(
        digest(b"lihang-data", secret, instance.to_bytes(4, "big"),
               index.to_bytes(8, "big"), k.to_bytes(8, "big"))
        for k in range(size // 32)) for index in range(count)]


def instance_challenges(secret: bytes, instance: int, blocks: int, count: int, size: int,
                        file_id: str, auditor_sign_key: str) -> list[dict]:
    """Independent challenge per trial: fresh index set, fresh nonce, fresh timestamp."""
    result = []
    for ordinal in range(count):
        index_seed = digest(b"lihang-indices", secret, instance.to_bytes(4, "big"),
                            ordinal.to_bytes(4, "big"))
        nonce = digest(b"lihang-nonce", secret, instance.to_bytes(4, "big"),
                       ordinal.to_bytes(4, "big"))[:NONCE_BYTES]
        result.append(challenge(blocks, size, file_id, index_seed, nonce, 1000 + ordinal,
                                auditor_sign_key))
    return result


def run_process(command: list[str], log_path: Path) -> None:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log_path.write_text(
        "$ " + subprocess.list2cmdline(command) + "\n" + completed.stdout + completed.stderr,
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"isolated Li Hang prover failed; see {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Li Hang 2026 L2 matrix")
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument("--challenges", type=int, default=100)
    parser.add_argument("--blocks", type=int, default=16)
    parser.add_argument("--block-bytes", type=int, default=4096)
    parser.add_argument("--challenge-size", type=int, default=4)
    parser.add_argument("--single-digest-trials", type=int, default=10)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("l2-%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()
    if min(args.instances, args.challenges, args.blocks, args.block_bytes,
           args.challenge_size, args.single_digest_trials) < 1:
        raise ValueError("all size arguments must be positive")
    if args.challenge_size > args.blocks:
        raise ValueError("challenge size cannot exceed the block count")
    if args.single_digest_trials > args.challenges:
        raise ValueError("single-digest trials cannot exceed the challenge count")

    output = ROOT / "results" / "lihang2026" / args.run_id
    output.mkdir(parents=True, exist_ok=False)

    provided_secret = os.environ.get("LIHANG_DATA_SECRET")
    data_secret = bytes.fromhex(provided_secret) if provided_secret else os.urandom(32)
    data_secret_source = "environment" if provided_secret else "generated"
    setup_seed = b"lihang2026-runner"
    tag_seed = b"lihang2026-tag-runner"

    parameters = {
        "run_id": args.run_id,
        "instances": args.instances,
        "challenges_per_instance": args.challenges,
        "blocks_per_instance": args.blocks,
        "block_bytes": args.block_bytes,
        "challenge_size": args.challenge_size,
        "single_digest_trials": args.single_digest_trials,
        "group_order": GROUP_ORDER,
        "group_order_bits": GROUP_ORDER.bit_length(),
        "group_order_is_prime": True,
        "backend": "prime-order type-1 reduced Tate pairing, supersingular y^2=x^3+x, embedding degree 2",
        "hash_modes": ["lattice (chunk-wise additive)", "plain (non-additive SHA-256 control)"],
        "profiles": ["literal (paper equations only)", "hardened (explicit repair variant)"],
        "data_secret_source": data_secret_source,
        "data_secret_commitment": commitment(data_secret),
        "setup_seed": setup_seed.decode(),
        "tag_seed": tag_seed.decode(),
        "challenge_ordering": "attacker state is written to disk before challenge randomness is drawn",
        "security_note": "reduced functional parameters; not production security",
    }
    dump_json(output / "parameters.json", parameters)
    dump_json(output / "environment.json", {
        "python": sys.version,
        "platform": platform.platform(),
        "source_sha256": {
            **{f"scripts/{p.name}": sha256_file(p) for p in sorted((ROOT / "scripts").glob("*.py"))},
            **{f"tests/{p.name}": sha256_file(p) for p in sorted((ROOT / "tests").glob("*.py"))},
        },
    })
    (output / "command.txt").write_text(
        f"{sys.executable} scripts/run_lihang2026_experiments.py --instances {args.instances} "
        f"--challenges {args.challenges} --blocks {args.blocks} --block-bytes {args.block_bytes} "
        f"--challenge-size {args.challenge_size} --single-digest-trials {args.single_digest_trials} "
        f"--run-id {args.run_id}\n", encoding="utf-8")

    records = []
    for instance in range(args.instances):
        public, secret = setup(setup_seed + instance.to_bytes(4, "big"))
        blocks = make_blocks(data_secret, instance, args.blocks, args.block_bytes)
        lattice_init = initialization(f"instance-{instance}.bin", blocks, "lattice", tag_seed)
        plain_init = initialization(f"instance-{instance}.bin", blocks, "plain", tag_seed)

        instance_dir = output / f"instance-{instance:02d}"
        instance_dir.mkdir(parents=True, exist_ok=False)
        dump_json(instance_dir / "honest-data-commitment.json", {
            "blocks": args.blocks,
            "block_bytes": args.block_bytes,
            "ciphertext_commitment": commitment(b"".join(blocks)),
            "note": "commitment only; the data seed is not stored in this run directory",
        })

        # --- freeze the attacker state BEFORE drawing challenge randomness ----
        state = {
            "schema": STATE_SCHEMA,
            "file_id": f"instance-{instance}.bin",
            "digests": lattice_init["digests"],
            "digests_plain": plain_init["digests"],
            "cloud_sign_key": secret["cloud_sign_key"],
            "replay_pool": [],
        }
        encoded_state = canonical(state)
        dump_json(instance_dir / "attacker-state.json", state)

        # --- only now draw challenge randomness -------------------------------
        challenge_secret = os.urandom(32)
        challenges = instance_challenges(challenge_secret, instance, args.blocks,
                                         args.challenges, args.challenge_size, state["file_id"],
                                         secret["auditor_sign_key"])
        replay_index_seed = digest(b"lihang-indices", challenge_secret, instance.to_bytes(4, "big"),
                                  (0).to_bytes(4, "big"))
        replay_nonce = digest(b"lihang-replay-nonce", challenge_secret,
                              instance.to_bytes(4, "big"))[:NONCE_BYTES]
        replay_chal = challenge(args.blocks, args.challenge_size, state["file_id"],
                                replay_index_seed, replay_nonce, 2000, secret["auditor_sign_key"])

        requests, expected = [], []
        for ordinal, chal in enumerate(challenges):
            seed = instance.to_bytes(4, "big") + ordinal.to_bytes(4, "big")
            for kind, hardened, digest_set, salt in (
                    ("cached", False, "lattice", b"lihang-s"),
                    ("cached", True, "lattice", b"lihang-s2"),
                    ("degenerate", False, "lattice", b"lihang-degenerate"),
                    ("degenerate", True, "lattice", b"lihang-degenerate2"),
                    ("cached", False, "plain", b"lihang-sp")):
                request = {"kind": kind, "hardened_binding": hardened,
                           "digest_set": digest_set, "challenge": chal}
                if kind == "cached":
                    request["s"] = hash_int(GROUP_ORDER, salt, seed, nonzero=True)
                requests.append(request)
                label = "plain_cached" if digest_set == "plain" else kind
                expected.append((label, "hardened" if hardened else "literal", ordinal, digest_set))
        for ordinal in range(args.single_digest_trials):
            seed = instance.to_bytes(4, "big") + ordinal.to_bytes(4, "big")
            requests.append({"kind": "cached_single", "index": 0, "hardened_binding": False,
                             "s": hash_int(GROUP_ORDER, b"lihang-single", seed, nonzero=True),
                             "challenge": challenges[ordinal]})
            expected.append(("single_digest", "literal_trusted_indexset", ordinal, "lattice"))

        dump_json(instance_dir / "requests.json", requests)
        run_process([
            sys.executable, str(ROOT / "scripts" / "lihang2026_prover_cli.py"),
            "--state", str(instance_dir / "attacker-state.json"),
            "--requests", str(instance_dir / "requests.json"),
            "--output", str(instance_dir / "responses.json"),
        ], instance_dir / "prover.log")
        responses = load_json(instance_dir / "responses.json")
        if len(responses) != len(expected):
            raise AssertionError("response count mismatch")

        counters: dict[str, int] = {}
        for (kind, profile, ordinal, digest_set), response in zip(expected, responses):
            chal = challenges[ordinal]
            tag_set = plain_init["tag_set"] if digest_set == "plain" else lattice_init["tag_set"]
            if kind == "single_digest":
                counters["single_digest_trusted_indexset_accepted"] = counters.get(
                    "single_digest_trusted_indexset_accepted", 0) + int(
                    verify(public, tag_set, chal, response, "literal",
                           trust_proof_indexset=True))
                counters["single_digest_natural_reading_accepted"] = counters.get(
                    "single_digest_natural_reading_accepted", 0) + int(
                    verify(public, tag_set, chal, response, "literal"))
                continue
            counters[f"{kind}_{profile}_accepted"] = counters.get(f"{kind}_{profile}_accepted", 0) + int(
                verify(public, tag_set, chal, response, profile))

        # --- phase 2: replay the response retained from round 1 ---------------
        # The retained proof is exactly what a server keeps after answering the
        # first challenge; the new challenge reuses the index set but not the nonce.
        dump_json(instance_dir / "attacker-state-replay.json", dict(state, replay_pool=[responses[0]]))
        dump_json(instance_dir / "requests-replay.json", [
            {"kind": "replay", "slot": 0, "challenge": replay_chal},
            {"kind": "replay", "slot": 0, "challenge": replay_chal},
        ])
        run_process([
            sys.executable, str(ROOT / "scripts" / "lihang2026_prover_cli.py"),
            "--state", str(instance_dir / "attacker-state-replay.json"),
            "--requests", str(instance_dir / "requests-replay.json"),
            "--output", str(instance_dir / "responses-replay.json"),
        ], instance_dir / "prover-replay.log")
        replayed = load_json(instance_dir / "responses-replay.json")
        counters["replay_literal_accepted"] = int(
            verify(public, lattice_init["tag_set"], replay_chal, replayed[0], "literal"))
        counters["replay_hardened_accepted"] = int(
            verify(public, lattice_init["tag_set"], replay_chal, replayed[1], "hardened"))

        # --- honest and damaged controls over every challenge -----------------
        honest_literal = honest_hardened = damaged_rejected = 0
        for ordinal, chal in enumerate(challenges):
            s = hash_int(GROUP_ORDER, b"lihang-honest", instance.to_bytes(4, "big"),
                         ordinal.to_bytes(4, "big"), nonzero=True)
            honest = proof_from_blocks(blocks, chal, "lattice", s, secret["cloud_sign_key"])
            bound = proof_from_blocks(blocks, chal, "lattice", s, secret["cloud_sign_key"],
                                      hardened_binding=True)
            honest_literal += int(verify(public, lattice_init["tag_set"], chal, honest, "literal"))
            honest_hardened += int(verify(public, lattice_init["tag_set"], chal, bound, "hardened"))
            damaged_blocks = list(blocks)
            damaged_blocks[chal["body"]["Q"][0]] = bytes(args.block_bytes)
            damaged = proof_from_blocks(damaged_blocks, chal, "lattice", s, secret["cloud_sign_key"])
            damaged_rejected += int(not verify(public, lattice_init["tag_set"], chal, damaged, "literal"))

        first_chal = challenges[0]
        tampered = json.loads(json.dumps(responses[0]))
        tampered["body"]["B"] = responses[0]["body"]["A"]
        tampered_rejected = int(not verify(public, lattice_init["tag_set"], first_chal,
                                           tampered, "literal"))
        other_blocks = [bytes((i * 13 + 5) % 256 for i in range(args.block_bytes))
                        for _ in range(args.blocks)]
        other_init = initialization("other.bin", other_blocks, "lattice", b"other-tag")
        wrong_tagset_rejected = int(not verify(public, other_init["tag_set"], first_chal,
                                               responses[0], "literal"))
        unbound = proof_from_digests(lattice_init["digests"], first_chal, 777,
                                     secret["cloud_sign_key"])
        unbound_rejected = int(not verify(public, lattice_init["tag_set"], first_chal,
                                          unbound, "hardened"))

        forbidden = [key for key in (b'"blocks"', b'"ciphertext"', b'"plaintext"', b'"vehicle"',
                                     b'"decrypt"', b'"symmetric_key"') if key in encoded_state]
        record = {
            "instance": instance,
            "challenges": args.challenges,
            "distinct_challenge_index_sets": len({tuple(c["body"]["Q"]) for c in challenges}),
            "honest_literal_accepted": honest_literal,
            "honest_hardened_accepted": honest_hardened,
            "damaged_control_rejected": damaged_rejected,
            "forbidden_state_fields": [item.decode() for item in forbidden],
            "attacker_state_serialized_bytes": len(encoded_state),
            "attacker_state_disk_bytes": (instance_dir / "attacker-state.json").stat().st_size,
            "honest_ciphertext_bytes": args.blocks * args.block_bytes,
            "challenge_secret_commitment": commitment(challenge_secret),
            "tampered_B_rejected": tampered_rejected,
            "wrong_content_tagset_rejected": wrong_tagset_rejected,
            "unbound_proof_rejected_under_hardened": unbound_rejected,
            **counters,
        }
        records.append(record)

    dump_json(output / "trials.json", records)

    def total(key: str) -> int:
        return sum(int(record.get(key, 0)) for record in records)

    paper_scale = {
        "block_bytes": PAPER_BLOCK_BYTES,
        "blocks": [100, 500, 1000],
        "minimal_digest_state_bits_per_block": GROUP_ORDER.bit_length(),
        "compression_ratio_per_block": honest_state_bits(1, PAPER_BLOCK_BYTES) / digest_state_bits(1),
        "basis": "algebraic accounting from the recorded group order; block hashing is not re-run at this size",
    }
    summary = {
        "level": "L2-real-prime-order-type1-pairing-reimplementation-reduced-parameters",
        "instances": args.instances,
        "challenges_per_instance": args.challenges,
        "distinct_challenge_index_sets_summed_over_instances": sum(
            r["distinct_challenge_index_sets"] for r in records),
        "distinct_challenge_index_sets_per_instance_average": sum(
            r["distinct_challenge_index_sets"] for r in records) / len(records),
        "blocks_per_instance": args.blocks,
        "block_bytes": args.block_bytes,
        "challenge_size": args.challenge_size,
        "honest_literal_accepted": total("honest_literal_accepted"),
        "honest_hardened_accepted": total("honest_hardened_accepted"),
        "cached_literal_accepted": total("cached_literal_accepted"),
        "cached_hardened_accepted": total("cached_hardened_accepted"),
        "degenerate_literal_accepted": total("degenerate_literal_accepted"),
        "degenerate_hardened_accepted": total("degenerate_hardened_accepted"),
        "replay_literal_accepted": total("replay_literal_accepted"),
        "replay_hardened_accepted": total("replay_hardened_accepted"),
        "plain_cached_literal_accepted": total("plain_cached_literal_accepted"),
        "single_digest_trusted_indexset_accepted": total("single_digest_trusted_indexset_accepted"),
        "single_digest_natural_reading_accepted": total("single_digest_natural_reading_accepted"),
        "damaged_control_rejected": total("damaged_control_rejected"),
        "tampered_B_rejected": total("tampered_B_rejected"),
        "wrong_content_tagset_rejected": total("wrong_content_tagset_rejected"),
        "unbound_proof_rejected_under_hardened": total("unbound_proof_rejected_under_hardened"),
        "attacker_states_with_forbidden_fields": sum(bool(r["forbidden_state_fields"]) for r in records),
        "average_attacker_state_serialized_bytes": sum(
            r["attacker_state_serialized_bytes"] for r in records) / len(records),
        "average_honest_ciphertext_bytes": sum(r["honest_ciphertext_bytes"] for r in records) / len(records),
        "paper_scale_accounting": paper_scale,
        "data_secret_source": data_secret_source,
        "challenge_ordering": "state committed before challenges drawn",
    }
    dump_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
