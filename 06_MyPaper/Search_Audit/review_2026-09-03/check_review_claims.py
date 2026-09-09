"""Reproducible arithmetic and state examples for the manuscript review.

This is NOT a cryptographic implementation or a protocol benchmark.
The HLA example works algebraically in any suitable prime-order pairing group.
The toy field only makes the equality easy to inspect.
"""
from hashlib import sha256
import json
import math
from pathlib import Path


def merkle_levels(values):
    level = [sha256(b"leaf:" + str(v).encode()).digest() for v in values]
    result = []
    while len(level) > 1:
        if len(level) % 2:
            level = level + level[-1:]
        level = [sha256(b"node:" + level[i] + level[i + 1]).digest()
                 for i in range(0, len(level), 2)]
        result.append(level)
    return result


def main():
    p = 101
    original, alternate, coefficients = (10, 20), (13, 18), (2, 3)
    old_mu = sum(v * m for v, m in zip(coefficients, original)) % p
    new_mu = sum(v * m for v, m in zip(coefficients, alternate)) % p
    assert original != alternate and old_mu == new_mu == 80

    # Symbolic exponents of H(ctx_1), H(ctx_2), u in the unchanged aggregate.
    original_exponents = (*coefficients, old_mu)
    alternate_exponents = (*coefficients, new_mu)
    assert original_exponents == alternate_exponents

    # Individually authorized versions that never coexisted as current state.
    states = [(10, "S0", "R0"), (11, "S1", "R0"), (12, "S1", "R1")]
    assembled = ("S0", "R1")
    assert all((s, r) != assembled for _, s, r in states)

    # A query frozen for A is not redirected to B by a later migration.
    frozen_provider = "A"
    active_provider_after_migration = "B"
    data_after_immediate_release = {"A": False, "B": True}
    assert not data_after_immediate_release[frozen_provider]

    changed_nodes = []
    for size in (8, 64, 1024):
        old = merkle_levels(list(range(1, size + 1)))
        new = merkle_levels(list(range(0, size + 1)))
        changed = sum(1 for depth, level in enumerate(new)
                      for index, value in enumerate(level)
                      if depth >= len(old) or index >= len(old[depth])
                      or old[depth][index] != value)
        changed_nodes.append({"old_leaves": size, "changed_or_new_internal_nodes": changed})

    # Conditional on fixed unavailable blocks and uniform sampling; this is
    # sampling coverage, not a storage lower bound or a full security proof.
    sampling = [{"unavailable_fraction": f,
                 "samples_for_99pct_detection_large_n": math.ceil(math.log(0.01) / math.log(1-f))}
                for f in (0.1, 0.01, 0.001)]
    scalar_encoding = {
        "assumed_payload_bytes_per_scalar": 31,
        "assumed_serialized_scalar_bytes": 32,
        "assumed_compressed_G1_tag_bytes": 48,
        "tag_bytes_per_input_byte": 48 / 31,
        "data_plus_tags_bytes_per_input_byte_per_replica": 80 / 31,
        "three_replica_bytes_per_input_byte": 240 / 31,
        "sectors_for_4096_input_bytes": math.ceil(4096 / 31),
        "single_scalar_local_proof_bytes_excluding_framing": 48 + 32 + 32 + 64,
        "sectorized_local_proof_bytes_excluding_framing": 48 + math.ceil(4096 / 31) * 32 + 32 + 64,
    }
    result = {
        "scope": "arithmetic/state illustrations only; no pairing implementation or benchmark",
        "hla_game_counterexample": {"toy_prime": p, "original_messages": original,
            "unqueried_alternate_messages": alternate, "coefficients": coefficients,
            "original_mu": old_mu, "alternate_mu": new_mu,
            "same_aggregate_exponents": original_exponents == alternate_exponents},
        "mixed_snapshot": {"chain_states": states, "assembled_pair": assembled,
            "pair_ever_current": False},
        "migration_without_retention": {"frozen_provider": frozen_provider,
            "new_provider": active_provider_after_migration,
            "old_query_still_has_data_at_responsible_provider": False},
        "sorted_array_merkle_front_insert": changed_nodes,
        "sampling_examples": sampling,
        "encoding_estimates": scalar_encoding,
    }
    output = Path(__file__).with_name("check_results.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
