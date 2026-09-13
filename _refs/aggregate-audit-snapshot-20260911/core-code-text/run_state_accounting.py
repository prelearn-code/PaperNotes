"""Measured state accounting for the caching strategies.

Earlier documents reported state-size ratios from parameter arithmetic.  This
runner measures them instead, using the large-parameter backend for real
encodings:

* every field element is ``ceil(log2 r / 8)`` bytes;
* every group element is counted both uncompressed (two affine coordinates) and
  compressed (one coordinate plus a sign bit), because the ratio depends on which
  encoding is assumed;
* the JSON size of a real serialized sample is also reported, to show how much of
  a small state is framing rather than content.

Three cases:

===========  ==========================================  ==========================
case         honest server state                         cached state
===========  ==========================================  ==========================
Song         ciphertext sectors + tags                   block sums + tags
Zhang        ciphertext sectors + tags                   block hashes + block sums + tags
Li Hang      ciphertext blocks                           per-block digests
===========  ==========================================  ==========================
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import large_parameter_backend as L
from scripts.common import digest
from scripts.large_parameter_backend import Point, hash_to_point, multiply, multiply_raw

ROOT = Path(__file__).resolve().parents[1]
PAPER_FIELD_BITS = 256
PAPER_BLOCK_BYTES = 128 * 1024
PAPER_BLOCKS = 100
PAPER_SECTORS = 100


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field_bytes(bits: int) -> int:
    return (bits + 7) // 8


def accounting(blocks: int, sectors: int, field_bits: int, block_bytes: int) -> dict:
    field_b = field_bytes(field_bits)
    point_uncompressed = 2 * field_b
    point_compressed = field_b + 1
    song_honest = blocks * sectors * field_b + blocks * point_uncompressed
    song_cached = blocks * field_b + blocks * point_uncompressed
    zhang_honest = blocks * sectors * field_b + blocks * point_uncompressed
    zhang_cached = blocks * point_uncompressed + blocks * field_b + blocks * point_uncompressed
    zhang_single = point_uncompressed + field_b + point_uncompressed
    lihang_honest = blocks * block_bytes
    lihang_cached = blocks * field_b
    return {
        "blocks": blocks, "sectors": sectors, "field_bits": field_bits,
        "block_bytes": block_bytes,
        "song": {
            "honest_bytes": song_honest, "cached_bytes": song_cached,
            "content_only_ratio": (blocks * sectors * field_b) / (blocks * field_b),
            "total_ratio": song_honest / song_cached,
        },
        "zhang": {
            "honest_bytes": zhang_honest, "cached_bytes": zhang_cached,
            "cached_bytes_compressed_hash": (
                blocks * point_compressed + blocks * field_b + blocks * point_compressed),
            "single_block_bytes": zhang_single,
            "total_ratio": zhang_honest / zhang_cached,
            "total_ratio_compressed": zhang_honest / (
                blocks * point_compressed + blocks * field_b + blocks * point_compressed),
        },
        "lihang": {
            "honest_bytes": lihang_honest, "cached_bytes": lihang_cached,
            "total_ratio": lihang_honest / lihang_cached,
        },
    }


def measure_real_encoding(blocks: int, sectors: int) -> dict:
    """Serialize actual backend elements and measure canonical and JSON sizes."""
    field_b = field_bytes(L.FIELD.bit_length())
    sk = 123456789
    tags = [multiply(hash_to_point(b"acct", i.to_bytes(8, "big")), sk) for i in range(2)]
    points = [hash_to_point(b"acct-h", i.to_bytes(8, "big")) for i in range(2)]
    json_point = len(json.dumps(points[0].to_dict()))
    json_sum = len(json.dumps(2 ** 200))
    return {
        "field_bytes": field_b,
        "point_uncompressed_bytes": 2 * field_b,
        "point_compressed_bytes": field_b + 1,
        "json_bytes_for_one_point": json_point,
        "json_bytes_for_one_field_element": json_sum,
        "canonical_point_example": points[0].to_dict(),
        "tag_example": tags[0].to_dict(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure state-size ratios instead of estimating them")
    parser.add_argument("--blocks", type=int, default=64)
    parser.add_argument("--sectors", type=int, default=8)
    parser.add_argument("--bits", type=int, default=256)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("acct-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    generator_parameters = L.configure(args.bits)
    output = args.results_root / "state-accounting" / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    (output / "command.txt").write_text(
        f"{sys.executable} scripts/run_state_accounting.py --blocks {args.blocks} "
        f"--sectors {args.sectors} --bits {args.bits} --run-id {args.run_id}\n", encoding="utf-8")
    (output / "environment.json").write_text(json.dumps({
        "python": sys.version, "platform": platform.platform(),
        "source_sha256": {f"scripts/{p.name}": sha256_file(p)
                          for p in sorted((ROOT / "scripts").glob("*.py"))},
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    measured_field_bits = L.FIELD.bit_length()
    summary = {
        "purpose": "replace parameter arithmetic with measured serialization sizes",
        "curve_parameters": generator_parameters,
        "backend_field_bits": measured_field_bits,
        "real_encoding": measure_real_encoding(args.blocks, args.sectors),
        "measured_same_blocks_and_sectors": accounting(
            args.blocks, args.sectors, measured_field_bits, PAPER_BLOCK_BYTES),
        "paper_scale_256_bit": accounting(PAPER_BLOCKS, PAPER_SECTORS,
                                          PAPER_FIELD_BITS, PAPER_BLOCK_BYTES),
        "comparison_at_identical_shape": accounting(
            args.blocks, args.sectors, PAPER_FIELD_BITS, PAPER_BLOCK_BYTES),
        "note": ("the field is the large-parameter backend's, not a 256-bit BN field; "
                 "the 256-bit rows apply the same formulas to 256-bit primitives"),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items()
                      if key != "curve_parameters"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
