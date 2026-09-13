"""Independent second reading of the verification equations.

This module deliberately does **not** import the per-case protocol modules
(``song2025_l2_protocol``, ``zhang2025_protocol``).  It shares only

* the group/pairing backends, which are not in dispute, and
* the documented implementation choices: the challenge-derivation ``pi``, the
  hash-to-group ``H2``/``H4`` derivation, and the profile constants.

Everything about *which terms the equations contain and how they are combined*
is written again here straight from the paper text, so the recorded responses can
be re-checked by a second reading:

Song Eq. (7)  psi = sum_i sum_j pi(theta||ID_F, i) * c_ij
              varphi = prod_i sigma_i^{pi(theta||ID_F, i)}
Song Eq. (10) e(varphi, g) = e(zeta * mu^psi, pk),  zeta = prod_i H2(ID_F||i)^{pi(...)}
Song Eq. (8)  zeta1 = prod_{ID in Res} prod_i H2(ID||i)^{pi(theta||ID,i)}
              zeta2 = prod_{ID in Res} H2(ID)
              zeta3 = prod_{ID in Res} varphi_alpha * varphi
              rho   = sum_{ID in Res} psi_alpha
Song Eq. (9)  e(zeta3, g) = e(zeta1 * zeta2 * H2(st_d||T) * mu^rho, pk)
Zhang Eq. (8) e(Gamma_hat * chi^{sum_j p_j}, pk) = e(Psi_hat, g1)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.common import hash_int
from scripts.lihang2026_pairing import (
    GROUP_ORDER,
    Point as PrimePoint,
    add as prime_add,
    exponentiate,
    hash_to_group,
    in_group,
    multiply_raw,
    pairing as prime_pairing,
)
from scripts.song2025_pairing import (
    MU,
    ORDER,
    Point as CompositePoint,
    add as composite_add,
    hash_to_point,
    in_subgroup,
    multiply as composite_multiply,
    pairing as composite_pairing,
)

ROOT = Path(__file__).resolve().parents[1]
ZHANG_K_L = 987654321  # documented runner constant (public in run_experiments style code)

# ---------------------------------------------------------------------------
# implementation choices shared on purpose (not the object of the check)
# ---------------------------------------------------------------------------


def song_pi(theta: bytes, file_id: str, index: int) -> int:
    return hash_int(ORDER, b"song-l2-pi", theta, file_id.encode(),
                    index.to_bytes(8, "big"), nonzero=True)


def song_h2(*parts: bytes):
    return hash_to_point(b"song-l2-h2", *parts)


def zhang_h3(material: bytes) -> int:
    return hash_int(GROUP_ORDER, b"zhang-h3", material, nonzero=True)


# ---------------------------------------------------------------------------
# Song 2025 (composite-order L2 run)
# ---------------------------------------------------------------------------


def song_audit_accept(public: dict, state: dict, file_id: str, theta: bytes,
                      proof: dict) -> bool:
    """Eq. (10), written straight from the paper text."""
    try:
        entry = state["files"][file_id]
        tags = [CompositePoint.from_dict(value) for value in entry["tags"]]
        block_count = len(entry["block_sums"])
        pk = CompositePoint.from_dict(public["pk"])
        phi = CompositePoint.from_dict(proof["phi"])
        if proof["file_id"] != file_id or not in_subgroup(phi):
            return False
        zeta = CompositePoint()
        for index in range(block_count):
            weight = song_pi(theta, file_id, index)
            zeta = composite_add(zeta, composite_multiply(
                song_h2(file_id.encode(), index.to_bytes(8, "big")), weight))
        right = composite_add(zeta, composite_multiply(MU, int(proof["psi"]) % ORDER))
        return composite_pairing(phi, _song_g(state)) == composite_pairing(right, pk)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def _song_g(state: dict) -> CompositePoint:
    return CompositePoint.from_dict(state["pp"]["generator"])


def song_search_accept(public: dict, state: dict, request: dict, theta: bytes,
                       response: dict) -> bool:
    """Eq. (8) then Eq. (9), written straight from the paper text."""
    try:
        if (response["token"] != request["token"]
                or response["latest_state"] != request["latest_state"]):
            return False
        if response["latest_state"] is None:
            return response["results"] == [] and response["proofs"] == []
        result_ids = list(response["results"])
        if len(result_ids) != len(response["proofs"]):
            return False
        if set(result_ids) != {item["file_id"] for item in response["proofs"]}:
            return False
        pk = CompositePoint.from_dict(public["pk"])
        zeta1 = CompositePoint()
        zeta2 = CompositePoint()
        zeta3 = CompositePoint.from_dict(response["keyword_phi"])
        rho = 0
        for proof in response["proofs"]:
            file_id = proof["file_id"]
            block_count = len(state["files"][file_id]["block_sums"])
            phi = CompositePoint.from_dict(proof["phi"])
            if not in_subgroup(phi):
                return False
            for index in range(block_count):
                zeta1 = composite_add(zeta1, composite_multiply(
                    song_h2(file_id.encode(), index.to_bytes(8, "big")),
                    song_pi(theta, file_id, index)))
            zeta2 = composite_add(zeta2, song_h2(file_id.encode()))
            zeta3 = composite_add(zeta3, phi)
            rho = (rho + int(proof["psi"])) % ORDER
        endpoint = song_h2(int(response["latest_state"]).to_bytes(16, "big"),
                           bytes.fromhex(response["token"]))
        right = composite_add(composite_add(composite_add(zeta1, zeta2), endpoint),
                              composite_multiply(MU, rho))
        return composite_pairing(zeta3, _song_g(state)) == composite_pairing(right, pk)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


# ---------------------------------------------------------------------------
# Zhang 2025 (prime-order L2 run)
# ---------------------------------------------------------------------------


def zhang_public_key(parameters: dict, audit_key: dict) -> PrimePoint:
    exponent = zhang_h3(ZHANG_K_L.to_bytes(32, "big")) * int(audit_key["s_t"]) % GROUP_ORDER
    return multiply_raw(exponentiate(1), exponent)


def zhang_audit_accept(parameters: dict, audit_key: dict, proof: dict) -> bool:
    """Eq. (8): the verifier sums every transmitted p into vartheta_hat."""
    try:
        if proof.get("mode") != parameters["mode"]:
            return False
        bases = [PrimePoint.from_dict(value) for value in parameters["bases"]]
        gamma = PrimePoint.from_dict(proof["Gamma"])
        psi = PrimePoint.from_dict(proof["Psi"])
        values = [int(value) % GROUP_ORDER for value in proof["p"]]
        pk = zhang_public_key(parameters, audit_key)
        left = gamma
        if parameters["mode"] == "literal":
            for value in values:
                left = prime_add(left, multiply_raw(bases[0], value))
        else:
            if len(values) != len(bases):
                return False
            for base, value in zip(bases, values):
                left = prime_add(left, multiply_raw(base, value))
        if not in_group(left) or not in_group(psi):
            return False
        return prime_pairing(left, pk) == prime_pairing(psi, exponentiate(1))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


# ---------------------------------------------------------------------------
# prover-side re-derivation: recompute the proof fields from the recorded state
# ---------------------------------------------------------------------------


def song_proof_fields(state: dict, file_id: str, theta: bytes) -> tuple[int, CompositePoint]:
    """Eq. (7) evaluated from the retained state alone."""
    entry = state["files"][file_id]
    tags = [CompositePoint.from_dict(value) for value in entry["tags"]]
    psi = 0
    phi = CompositePoint()
    for index, (block_sum, tag) in enumerate(zip(entry["block_sums"], tags)):
        weight = song_pi(theta, file_id, index)
        psi = (psi + weight * int(block_sum)) % ORDER
        phi = composite_add(phi, composite_multiply(tag, weight))
    return psi, phi


def song_chain_entries(state: dict, token: str, latest_state: int) -> list[dict]:
    """Walk the keyword chain using the documented index/pointer derivations."""
    from scripts.common import digest

    def index_key(state_value: int) -> str:
        return digest(b"song-l2-index", bytes.fromhex(token),
                      state_value.to_bytes(16, "big")).hex()

    entries, seen, current = [], set(), int(latest_state)
    while current not in seen:
        seen.add(current)
        entry = state["db"].get(index_key(current))
        if entry is None:
            raise ValueError("broken chain")
        entries.append(entry)
        previous = int(entry["pointer"]) ^ hash_int(
            ORDER, b"song-l2-h3", current.to_bytes(16, "big"))
        if previous == current:
            return entries
        current = previous
    raise ValueError("cyclic chain")


def song_search_fields(state: dict, request: dict, theta: bytes) -> dict:
    entries = song_chain_entries(state, request["token"], request["latest_state"])
    keyword_phi = CompositePoint()
    proofs = []
    for entry in entries:
        keyword_phi = composite_add(keyword_phi, CompositePoint.from_dict(entry["kt"]))
        if entry["valid"]:
            psi, phi = song_proof_fields(state, entry["file_id"], theta)
            proofs.append({"file_id": entry["file_id"], "psi": psi, "phi": phi.to_dict()})
    return {"keyword_phi": keyword_phi.to_dict(), "proofs": proofs}


def zhang_proof_fields(parameters: dict, audit_key: dict, request: dict,
                       response: dict) -> dict:
    """Eq. (7) evaluated from the cached hash/sum/tag state alone."""
    state = request["_state"]
    if request["kind"] == "single":
        pairs = [(int(request["index"]), int(request["coefficient"]))]
    else:
        challenge = request["challenge"]
        pairs = list(zip(challenge["indices"], challenge["coefficients"]))
    gamma = PrimePoint()
    psi = PrimePoint()
    for index, coefficient in pairs:
        gamma = prime_add(gamma, multiply_raw(PrimePoint.from_dict(state["hashes"][index]),
                                              coefficient))
        psi = prime_add(psi, multiply_raw(PrimePoint.from_dict(state["tags"][index]), coefficient))
    gamma = multiply_raw(gamma, int(audit_key["x_t"]))
    psi = multiply_raw(psi, int(audit_key["s_t"]) * int(audit_key["x_t"]) % GROUP_ORDER)
    total = int(audit_key["x_t"]) * sum(
        coefficient * int(state["sums"][index]) for index, coefficient in pairs) % GROUP_ORDER
    if parameters["mode"] != "literal":
        return {"Gamma": gamma.to_dict(), "Psi": psi.to_dict()}
    shape = request.get("shape", parameters.get("shape"))
    if shape == "per_block":
        values = [int(audit_key["x_t"]) * coefficient * int(state["sums"][index]) % GROUP_ORDER
                  for index, coefficient in pairs]
    else:
        values = [total]
    return {"Gamma": gamma.to_dict(), "Psi": psi.to_dict(), "p": values}


# ---------------------------------------------------------------------------
# run-directory drivers
# ---------------------------------------------------------------------------


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_song(run_dir: Path, limit: int | None = None) -> dict:
    run_dir = Path(run_dir).resolve()
    summary = load(run_dir / "summary.json")
    audit_ok = search_ok = audit_total = search_total = 0
    field_mismatches = 0
    instance_dirs = sorted(run_dir.glob("instance-*"))
    if limit is not None:
        instance_dirs = instance_dirs[:limit]
    for instance_dir in instance_dirs:
        state = load(instance_dir / "attacker-state.json")
        requests = load(instance_dir / "requests.json")
        responses = load(instance_dir / "responses.json")
        for request, response in zip(requests, responses):
            theta = bytes.fromhex(request["challenge"]["theta"])
            if request["kind"] == "audit":
                audit_total += 1
                audit_ok += int(song_audit_accept(state["public"], state,
                                                  request["file_id"], theta, response))
                psi, phi = song_proof_fields(state, request["file_id"], theta)
                field_mismatches += int(psi != int(response["psi"])
                                        or phi.to_dict() != response["phi"])
            else:
                search_total += 1
                search_ok += int(song_search_accept(state["public"], state, request,
                                                    theta, response))
                expected = song_search_fields(state, request, theta)
                if expected["keyword_phi"] != response["keyword_phi"]:
                    field_mismatches += 1
                recorded = {proof["file_id"]: proof for proof in response["proofs"]}
                for proof in expected["proofs"]:
                    got = recorded.get(proof["file_id"])
                    if (got is None or int(got["psi"]) != proof["psi"]
                            or got["phi"] != proof["phi"]):
                        field_mismatches += 1
    return {
        "case": "song2025",
        "run_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
        "independent_audit_accepted": audit_ok,
        "independent_audit_total": audit_total,
        "recorded_projection_unsearched_audit_accepted": summary[
            "projection_unsearched_audit_accepted"],
        "independent_search_accepted": search_ok,
        "independent_search_total": search_total,
        "recorded_projection_search_accepted": summary["projection_search_accepted"],
        "prover_field_mismatches": field_mismatches,
        "instances_checked": len(instance_dirs),
    }


def check_zhang(run_dir: Path, limit: int | None = None) -> dict:
    run_dir = Path(run_dir).resolve()
    summary = load(run_dir / "summary.json")
    counts = {"cached_per_block": 0, "cached_per_sector": 0, "single": 0,
              "cached_sector_bound": 0}
    totals = {"cached_per_block": 0, "cached_per_sector": 0, "single": 0,
              "cached_sector_bound": 0}
    field_mismatches = 0
    instance_dirs = sorted(run_dir.glob("instance-*"))
    if limit is not None:
        instance_dirs = instance_dirs[:limit]
    for instance_dir in instance_dirs:
        state = load(instance_dir / "attacker-state.json")
        parameters = state["parameters"]
        audit_key = state["audit_key"]
        requests = load(instance_dir / "requests.json")
        responses = load(instance_dir / "responses.json")
        for request, response in zip(requests, responses):
            request["_state"] = state
            key = "single" if request["kind"] == "single" else f"cached_{request['shape']}"
            totals[key] += 1
            counts[key] += int(zhang_audit_accept(parameters, audit_key, response))
            expected = zhang_proof_fields(parameters, audit_key, request, response)
            if expected["Gamma"] != response["Gamma"] or expected["Psi"] != response["Psi"]:
                field_mismatches += 1
            elif expected.get("p") != response["p"]:
                field_mismatches += 1
        repaired_state = load(instance_dir / "attacker-state-sector-bound.json")
        repaired_requests = load(instance_dir / "requests-sector-bound.json")
        repaired_responses = load(instance_dir / "responses-sector-bound.json")
        for request, response in zip(repaired_requests, repaired_responses):
            totals["cached_sector_bound"] += 1
            counts["cached_sector_bound"] += int(
                zhang_audit_accept(repaired_state["parameters"],
                                   repaired_state["audit_key"], response))
    return {
        "case": "zhang2025",
        "run_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
        "independent_counts": counts,
        "independent_totals": totals,
        "recorded_counts": {
            "cached_per_block": summary["cached_per_block_literal_accepted"],
            "cached_per_sector": summary["cached_per_sector_literal_accepted"],
            "single": summary["single_block_per_block_literal_accepted"],
            "cached_sector_bound": summary["cached_sector_bound_profile_accepted"],
        },
        "prover_field_mismatches": field_mismatches,
        "instances_checked": len(instance_dirs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-check recorded responses with an independent reading of the equations")
    parser.add_argument("--song-run", type=Path,
                        default=ROOT / "results" / "song2025" / "l2-strict-20260911")
    parser.add_argument("--zhang-run", type=Path,
                        default=ROOT / "results" / "zhang2025" / "l2-final-20260911")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "certificates" / "independent-recheck.json")
    args = parser.parse_args()

    report = {"method": "equations re-derived from the paper text, protocol modules not imported",
              "song": check_song(args.song_run), "zhang": check_zhang(args.zhang_run)}
    song = report["song"]
    report["agreement"] = {
        "song_audit": song["independent_audit_accepted"]
        == song["recorded_projection_unsearched_audit_accepted"],
        "song_search": song["independent_search_accepted"]
        == song["recorded_projection_search_accepted"],
        "song_prover_fields": song["prover_field_mismatches"] == 0,
        "zhang": report["zhang"]["independent_counts"] == report["zhang"]["recorded_counts"],
        "zhang_prover_fields": report["zhang"]["prover_field_mismatches"] == 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not all(report["agreement"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
