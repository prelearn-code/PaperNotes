from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.common import dump_json, load_json
    from scripts.otgpdp2025_protocol import proof_from_tags
else:
    from .common import dump_json, load_json
    from .otgpdp2025_protocol import proof_from_tags


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated OTGPDP tag-only prover")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--challenges", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    state = load_json(args.state)
    if state.get("schema") != "otgpdp2025-tag-state-v1":
        raise ValueError("unexpected state schema")
    challenges = load_json(args.challenges)
    tags = [int(x, 16) for x in state["tags"]]
    responses = [proof_from_tags(state["filename"], tags, item, state["server_sign_key"])
                 for item in challenges]
    dump_json(args.output, responses)


if __name__ == "__main__":
    main()

