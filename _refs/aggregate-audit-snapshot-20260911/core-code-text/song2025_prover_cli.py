from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.common import dump_json, load_json
    from scripts.song2025_protocol import proof_from_projection, search_from_projection
else:
    from .common import dump_json, load_json
    from .song2025_protocol import proof_from_projection, search_from_projection


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated Song sector-projection prover")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--requests", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    state = load_json(args.state)
    if state.get("schema") != "song2025-projection-state-v1":
        raise ValueError("unexpected state schema")
    responses = []
    for request in load_json(args.requests):
        if request["kind"] == "audit":
            responses.append(proof_from_projection(request["file_id"], state["files"][request["file_id"]], request["challenge"]))
        elif request["kind"] == "search":
            responses.append(search_from_projection(state, request["token"], request["latest_state"], request["challenge"]))
        else:
            raise ValueError("unexpected request kind")
    dump_json(args.output, responses)


if __name__ == "__main__":
    main()
