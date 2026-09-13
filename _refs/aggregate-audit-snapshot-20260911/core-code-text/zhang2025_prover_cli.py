"""Isolated proving process for the Zhang 2025 reproduction.

The process only reads the serialized cached state and the request file.  The
state holds one block hash, one sector sum and the original authentication tag
per block, the public parameters, and the audit key the paper hands to the cloud
server.  No ciphertext block, file encryption key or decryption key is present or
reachable here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import dump_json, load_json
from scripts.lihang2026_pairing import Point
from scripts.zhang2025_protocol import proof_from_cache, proof_from_single_block

STATE_SCHEMA = "zhang2025-cached-state-v1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated Zhang 2025 cached-state prover")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--requests", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    state = load_json(args.state)
    if state.get("schema") != STATE_SCHEMA:
        raise ValueError("unexpected state schema")
    parameters = state["parameters"]
    hashes = [Point.from_dict(value) for value in state["hashes"]]
    sums = [int(value) for value in state["sums"]]
    tags = [Point.from_dict(value) for value in state["tags"]]
    key = state["audit_key"]

    responses = []
    for request in load_json(args.requests):
        kind = request["kind"]
        # The proof shape is a reading of the printed notation, not secret state,
        # so a request may select it explicitly.
        effective = dict(parameters, shape=request.get("shape", parameters.get("shape")))
        if kind == "cached":
            responses.append(proof_from_cache(effective, hashes, sums, tags,
                                              request["challenge"], key,
                                              distribute=request.get("distribute", "first")))
        elif kind == "single":
            index = int(request["index"])
            responses.append(proof_from_single_block(effective, index, request["coefficient"],
                                                     hashes[index], sums[index], tags[index], key))
        else:
            raise ValueError(f"unexpected request kind: {kind}")
    dump_json(args.output, responses)


if __name__ == "__main__":
    main()
