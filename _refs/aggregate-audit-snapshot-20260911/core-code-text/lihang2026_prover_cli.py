"""Isolated proving process for the Li Hang 2026 reproduction.

The process only reads the serialized state and the request file.  For the
digest-substitution strategy the state contains per-block digests only: no
ciphertext block, no vehicle key and no decryption key is present or reachable
through this interface.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import dump_json, load_json
from scripts.lihang2026_protocol import (
    proof_degenerate,
    proof_from_digests,
)

STATE_SCHEMA = "lihang2026-cached-digest-state-v1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated Li Hang 2026 cached-digest prover")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--requests", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    state = load_json(args.state)
    if state.get("schema") != STATE_SCHEMA:
        raise ValueError("unexpected state schema")
    digest_sets = {"lattice": [int(v) for v in state["digests"]],
                   "plain": [int(v) for v in state["digests_plain"]]}
    cloud_sign_key = state["cloud_sign_key"]
    replay_pool = state.get("replay_pool", [])

    responses = []
    for request in load_json(args.requests):
        kind = request["kind"]
        hardened = bool(request.get("hardened_binding", False))
        digests = digest_sets[request.get("digest_set", "lattice")]
        if kind == "cached":
            responses.append(proof_from_digests(digests, request["challenge"], s=request["s"],
                                                cloud_sign_key=cloud_sign_key,
                                                hardened_binding=hardened))
        elif kind == "cached_single":
            index = int(request["index"])
            responses.append(proof_from_digests([digests[index]], request["challenge"], s=request["s"],
                                                cloud_sign_key=cloud_sign_key,
                                                hardened_binding=hardened,
                                                indexset=[index]))
        elif kind == "degenerate":
            responses.append(proof_degenerate(request["challenge"], cloud_sign_key,
                                              hardened_binding=hardened))
        elif kind == "replay":
            responses.append(replay_pool[int(request["slot"])])
        else:
            raise ValueError(f"unexpected request kind: {kind}")
    dump_json(args.output, responses)


if __name__ == "__main__":
    main()
