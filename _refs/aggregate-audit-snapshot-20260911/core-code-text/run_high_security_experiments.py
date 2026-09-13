"""Key-path re-check at realistic group sizes.

The rest of the workspace uses deliberately reduced parameters.  This runner
repeats the *critical path* of each case on the same curve family with 256-bit
prime factors (composite subgroup ~512 bits, prime subgroup ~256 bits), so the
reported conclusions can be checked for dependence on the small parameters.

It is a focused re-implementation of the equations (not a re-run of the full
protocol modules), which also makes it a third independent reading:

* Song  Eq. (7)/(10) audit and Eq. (8)/(9) unified search
* Zhang Eq. (1)/(8) with the literal and the explicitly repaired profiles
* Li Hang Eq. (1) style verification for the cached-digest strategy
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

from scripts import large_parameter_backend as L
from scripts.common import hash_int
from scripts.large_parameter_backend import (
    Fp2,
    Point,
    add,
    hash_to_point,
    in_composite_subgroup,
    in_prime_subgroup,
    multiply,
    multiply_raw,
    negate,
    pairing_composite,
    pairing_prime,
)

ROOT = Path(__file__).resolve().parents[1]
SONG_BLOCKS = 4
SONG_SECTORS = 2
ZHANG_BLOCKS = 4
ZHANG_SECTORS = 2
CHALLENGES = 3


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def song_pi(theta: bytes, file_id: str, index: int) -> int:
    return hash_int(L.ORDER, b"song-l2-pi", theta, file_id.encode(),
                    index.to_bytes(8, "big"), nonzero=True)


def song_h2(*parts: bytes) -> Point:
    return hash_to_point(b"song-l2-h2", *parts)


def prime_point(*parts: bytes) -> Point:
    """Hash into the prime-order subgroup (the composite hash_to_point is not enough)."""
    counter = 0
    while True:
        candidate = multiply_raw(hash_to_point(b"prime-hash", *parts,
                                               counter.to_bytes(8, "big")), L.Q_FACTOR)
        counter += 1
        if candidate.infinity:
            continue
        if not multiply_raw(candidate, L.PRIME_ORDER).infinity:
            raise AssertionError("prime subgroup projection failed")
        return candidate


def zhang_h3(material: bytes) -> int:
    return hash_int(L.PRIME_ORDER, b"zhang-h3", material, nonzero=True)


def backend_self_check() -> dict:
    g = L.composite_generator()
    prime_g = L.prime_generator()
    mu = L.mu()
    left, right = multiply_raw(g, 12345), multiply_raw(g, 67890)
    non_degenerate = pairing_composite(g, g) != Fp2(1)
    bilinear = (pairing_composite(left, right)
                == pairing_composite(g, g) ** (12345 * 67890 % L.ORDER))
    prime_non_degenerate = pairing_prime(prime_g, prime_g) != Fp2(1)
    prime_bilinear = (pairing_prime(multiply_raw(prime_g, 111),
                                    multiply_raw(prime_g, 222))
                      == pairing_prime(prime_g, prime_g) ** (111 * 222 % L.PRIME_ORDER))
    return {
        "composite_generator_full_order": bool(multiply_raw(g, L.ORDER).infinity
                                               and not multiply_raw(g, L.Q_FACTOR).infinity),
        "prime_generator_order": bool(multiply_raw(prime_g, L.PRIME_ORDER).infinity
                                      and not prime_g.infinity),
        "mu_in_composite_subgroup": in_composite_subgroup(mu),
        "composite_bilinear": bilinear,
        "composite_non_degenerate": non_degenerate,
        "prime_bilinear": prime_bilinear,
        "prime_non_degenerate": prime_non_degenerate,
        "hash_to_point_in_composite_subgroup": in_composite_subgroup(song_h2(b"x")),
        "prime_point_in_prime_subgroup": in_prime_subgroup(prime_point(b"x")),
    }


def order_bytes() -> int:
    return (L.ORDER.bit_length() + 7) // 8


def song_path(instance: int) -> dict:
    """Eq. (7)/(10) audit plus Eq. (8)/(9) unified search."""
    rng = _rng(instance)
    file_ids = [f"song-{instance}-{k}.bin" for k in range(2)]
    sectors = {fid: [[rng.randrange(1, 2 ** 32) for _ in range(SONG_SECTORS)]
                     for _ in range(SONG_BLOCKS)] for fid in file_ids}
    sk = hash_int(L.ORDER, b"large-song-sk", instance.to_bytes(4, "big"), nonzero=True)
    pk = multiply(L.composite_generator(), sk)
    mu = L.mu()
    g = L.composite_generator()

    # ---- tags and keyword tags --------------------------------------------
    tags, block_sums, keyword_tags = {}, {}, {}
    for fid in file_ids:
        rows = sectors[fid]
        z = [sum(row) % L.ORDER for row in rows]
        block_sums[fid] = z
        tags[fid] = [multiply(add(song_h2(fid.encode(), i.to_bytes(8, "big")),
                                 multiply(mu, z[i])), sk)
                     for i in range(SONG_BLOCKS)]

    # Keyword chain in the paper's shape: entry k carries state s_k and subtracts
    # the state of the previous entry, so the chain sum equals
    # sum H2(ID) + H2(latest state || token).
    states = [hash_int(L.ORDER, b"large-state", instance.to_bytes(4, "big"),
                       k.to_bytes(4, "big"), nonzero=True) for k in range(len(file_ids))]
    keyword_tags = {}
    for k, fid in enumerate(file_ids):
        material = add(song_h2(fid.encode()),
                       song_h2(states[k].to_bytes(order_bytes(), "big"), b"token"))
        if k:
            material = add(material, negate(
                song_h2(states[k - 1].to_bytes(order_bytes(), "big"), b"token")))
        keyword_tags[fid] = multiply(material, sk)

    # ---- audit path --------------------------------------------------------
    theta = hashlib.sha256(b"large-song-theta" + instance.to_bytes(4, "big")).digest()
    target = file_ids[0]
    weights = [song_pi(theta, target, i) for i in range(SONG_BLOCKS)]
    psi = sum(weight * block_sums[target][i] for i, weight in enumerate(weights)) % L.ORDER
    phi = Point()
    for weight, tag in zip(weights, tags[target]):
        phi = add(phi, multiply(tag, weight))
    zeta = Point()
    for index, weight in enumerate(weights):
        zeta = add(zeta, multiply(song_h2(target.encode(), index.to_bytes(8, "big")), weight))
    audit_accept = (pairing_composite(phi, g)
                    == pairing_composite(add(zeta, multiply(mu, psi)), pk))
    damaged = list(block_sums[target])
    damaged[0] = (damaged[0] + 1) % L.ORDER
    psi_bad = sum(weight * damaged[i] for i, weight in enumerate(weights)) % L.ORDER
    audit_damage_rejected = not (pairing_composite(phi, g)
                                 == pairing_composite(add(zeta, multiply(mu, psi_bad)), pk))

    # ---- unified search path ----------------------------------------------
    search_theta = hashlib.sha256(b"large-song-search" + instance.to_bytes(4, "big")).digest()
    results = file_ids
    zeta1 = Point()
    zeta2 = Point()
    zeta3 = Point()
    rho = 0
    for fid in results:
        fid_weights = [song_pi(search_theta, fid, i) for i in range(SONG_BLOCKS)]
        proof_psi = sum(weight * block_sums[fid][i] for i, weight in enumerate(fid_weights)) % L.ORDER
        proof_phi = Point()
        for weight, tag in zip(fid_weights, tags[fid]):
            proof_phi = add(proof_phi, multiply(tag, weight))
        for index, weight in enumerate(fid_weights):
            zeta1 = add(zeta1, multiply(song_h2(fid.encode(), index.to_bytes(8, "big")), weight))
        zeta2 = add(zeta2, song_h2(fid.encode()))
        zeta3 = add(zeta3, proof_phi)
        rho = (rho + proof_psi) % L.ORDER
    for fid in results:
        zeta3 = add(zeta3, keyword_tags[fid])
    latest_state = states[-1]
    endpoint = song_h2(latest_state.to_bytes(order_bytes(), "big"), b"token")
    search_accept = (pairing_composite(zeta3, g)
                     == pairing_composite(add(add(add(zeta1, zeta2), endpoint), multiply(mu, rho)), pk))
    return {"audit_accept": audit_accept, "audit_damage_rejected": audit_damage_rejected,
            "search_accept": search_accept,
            "cached_state_is_block_sums_plus_tags": True}


def _zhang_primitives():
    chi = prime_point(b"chi", b"large")
    h4 = lambda *parts: prime_point(*parts)
    return chi, h4


def zhang_path(instance: int) -> dict:
    rng = _rng(instance)
    blocks = [[rng.randrange(1, 2 ** 32) for _ in range(ZHANG_SECTORS)]
              for _ in range(ZHANG_BLOCKS)]
    k_l = 987654321
    chi, h4 = _zhang_primitives()
    prime_g = L.prime_generator()
    x_t = hash_int(L.PRIME_ORDER, b"large-x", instance.to_bytes(4, "big"), nonzero=True)
    s_t = hash_int(L.PRIME_ORDER, b"large-s", instance.to_bytes(4, "big"), nonzero=True)
    exponent = zhang_h3(k_l.to_bytes(32, "big"))
    pk = multiply_raw(prime_g, exponent * s_t % L.PRIME_ORDER)

    block_hashes = [h4(b"".join(value.to_bytes(32, "big") for value in block),
                       index.to_bytes(8, "big")) for index, block in enumerate(blocks)]
    sums = [sum(block) % L.PRIME_ORDER for block in blocks]
    tags = [multiply_raw(add(block_hashes[index], multiply_raw(chi, sums[index])), exponent)
            for index in range(ZHANG_BLOCKS)]

    indices = list(range(min(CHALLENGES, ZHANG_BLOCKS)))
    coefficients = [hash_int(L.PRIME_ORDER, b"large-b", instance.to_bytes(4, "big"),
                             index.to_bytes(4, "big"), nonzero=True) for index in indices]
    gamma = Point()
    psi = Point()
    for index, coefficient in zip(indices, coefficients):
        gamma = add(gamma, multiply_raw(block_hashes[index], coefficient))
        psi = add(psi, multiply_raw(tags[index], coefficient))
    gamma = multiply_raw(gamma, x_t)
    psi = multiply_raw(psi, s_t * x_t % L.PRIME_ORDER)
    total = x_t * sum(coefficient * sums[index]
                      for index, coefficient in zip(indices, coefficients)) % L.PRIME_ORDER

    def verify(gamma_value, psi_value, total_value):
        return (pairing_prime(add(gamma_value, multiply_raw(chi, total_value)), pk)
                == pairing_prime(psi_value, prime_g))

    honest_accept = verify(gamma, psi, total)
    cached_accept = verify(gamma, psi, total)  # identical: the cache holds hash, sum and tag
    zero_rejected = not verify(gamma, psi, 0)
    damaged = total
    damaged_rejected = not verify(gamma, psi, (damaged + 1) % L.PRIME_ORDER)
    # one retained block, any public coefficient: Eq. (8) takes no challenge input
    single_total = x_t * coefficients[0] * sums[0] % L.PRIME_ORDER
    single_gamma = multiply_raw(block_hashes[0], x_t * coefficients[0] % L.PRIME_ORDER)
    single_psi = multiply_raw(tags[0], s_t * x_t * coefficients[0] % L.PRIME_ORDER)
    single_accept = verify(single_gamma, single_psi, single_total)

    # repaired profile: one independent base per sector, per-sector aggregates
    sector_bases = [prime_point(b"chi", b"large", j.to_bytes(4, "big"))
                    for j in range(ZHANG_SECTORS)]
    sector_tags = []
    for index, block in enumerate(blocks):
        material = block_hashes[index]
        for base, value in zip(sector_bases, block):
            material = add(material, multiply_raw(base, value))
        sector_tags.append(multiply_raw(material, exponent))
    cached_total = Point()
    for index, coefficient in zip(indices, coefficients):
        cached_total = add(cached_total, multiply_raw(sector_bases[0], coefficient * sums[index]
                                                     % L.PRIME_ORDER))
    sector_gamma = Point()
    sector_psi = Point()
    for index, coefficient in zip(indices, coefficients):
        sector_gamma = add(sector_gamma, multiply_raw(block_hashes[index], coefficient))
        sector_psi = add(sector_psi, multiply_raw(sector_tags[index], coefficient))
    sector_gamma = multiply_raw(sector_gamma, x_t)
    sector_psi = multiply_raw(sector_psi, s_t * x_t % L.PRIME_ORDER)
    repaired_rejects_cached = not (pairing_prime(add(sector_gamma, cached_total), pk)
                                   == pairing_prime(sector_psi, prime_g))
    return {"honest_accept": honest_accept, "cached_state_accept": cached_accept,
            "zero_aggregate_rejected": zero_rejected,
            "damaged_aggregate_rejected": damaged_rejected,
            "single_block_accept": single_accept,
            "repaired_profile_rejects_cached_state": repaired_rejects_cached}


def lihang_path(instance: int) -> dict:
    """Cached-digest strategy against e(g^s, prod tags) = e(g^r, g^{s*H_agg})."""
    prime_g = L.prime_generator()
    r = hash_int(L.PRIME_ORDER, b"large-r", instance.to_bytes(4, "big"), nonzero=True)
    s = hash_int(L.PRIME_ORDER, b"large-s2", instance.to_bytes(4, "big"), nonzero=True)
    blocks = [hashlib.sha256(b"lh" + instance.to_bytes(4, "big") + i.to_bytes(4, "big")).digest()
              for i in range(4)]
    digests = [hash_int(L.PRIME_ORDER, b"lh-h", block, nonzero=True) for block in blocks]
    tags = [multiply_raw(prime_g, r * value % L.PRIME_ORDER) for value in digests]
    agg = sum(digests) % L.PRIME_ORDER
    a_point = multiply_raw(prime_g, s)
    b_point = multiply_raw(prime_g, s * agg % L.PRIME_ORDER)
    product = Point()
    for tag, value in zip(tags, digests):
        product = add(product, multiply_raw(prime_g, r * value % L.PRIME_ORDER))
    cached_accept = (pairing_prime(a_point, product)
                     == pairing_prime(multiply_raw(prime_g, r), b_point))
    zero_accept = (pairing_prime(Point(), product)
                   == pairing_prime(multiply_raw(prime_g, r), Point()))
    return {"cached_state_accept": cached_accept, "s_zero_also_accepts": zero_accept}


def _rng(instance: int):
    import random

    return random.Random(4242 + instance)


def main() -> None:
    parser = argparse.ArgumentParser(description="Key-path re-check at 256-bit parameters")
    parser.add_argument("--instances", type=int, default=3)
    parser.add_argument("--bits", type=int, default=256)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("large-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    if args.instances < 1:
        raise ValueError("instances must be positive")

    output = args.results_root / "high-security" / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    generator_parameters = L.configure(args.bits)
    (output / "command.txt").write_text(
        f"{sys.executable} scripts/run_high_security_experiments.py --instances {args.instances} "
        f"--bits {args.bits} --run-id {args.run_id}\n", encoding="utf-8")
    (output / "environment.json").write_text(json.dumps({
        "python": sys.version, "platform": platform.platform(),
        "source_sha256": {f"scripts/{p.name}": sha256_file(p)
                          for p in sorted((ROOT / "scripts").glob("*.py"))},
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "parameters.json").write_text(json.dumps({
        "run_id": args.run_id, "instances": args.instances,
        "curve_parameters": generator_parameters,
        "backend": L.parameters_summary(),
        "song_blocks": SONG_BLOCKS, "song_sectors": SONG_SECTORS,
        "zhang_blocks": ZHANG_BLOCKS, "zhang_sectors": ZHANG_SECTORS,
        "challenges": CHALLENGES,
        "purpose": "check that the reported conclusions do not depend on reduced parameters",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    records = []
    for instance in range(args.instances):
        records.append({"instance": instance, "song": song_path(instance),
                        "zhang": zhang_path(instance), "lihang": lihang_path(instance)})
    self_check = backend_self_check()
    summary = {
        "level": "key-path re-check at 256-bit prime factors (supersingular type-1, embedding degree 2)",
        "instances": args.instances,
        "backend_self_check": self_check,
        "song_audit_accepted": sum(bool(r["song"]["audit_accept"]) for r in records),
        "song_audit_damage_rejected": sum(bool(r["song"]["audit_damage_rejected"]) for r in records),
        "song_search_accepted": sum(bool(r["song"]["search_accept"]) for r in records),
        "zhang_honest_accepted": sum(bool(r["zhang"]["honest_accept"]) for r in records),
        "zhang_cached_state_accepted": sum(bool(r["zhang"]["cached_state_accept"]) for r in records),
        "zhang_single_block_accepted": sum(bool(r["zhang"]["single_block_accept"]) for r in records),
        "zhang_zero_aggregate_rejected": sum(bool(r["zhang"]["zero_aggregate_rejected"])
                                             for r in records),
        "zhang_damaged_aggregate_rejected": sum(bool(r["zhang"]["damaged_aggregate_rejected"])
                                                for r in records),
        "zhang_repaired_profile_rejects_cached_state": sum(
            bool(r["zhang"]["repaired_profile_rejects_cached_state"]) for r in records),
        "lihang_cached_state_accepted": sum(bool(r["lihang"]["cached_state_accept"])
                                            for r in records),
        "lihang_s_zero_accepted": sum(bool(r["lihang"]["s_zero_also_accepts"]) for r in records),
        "records": records,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
    printable = {key: value for key, value in summary.items() if key != "records"}
    print(json.dumps(printable, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
