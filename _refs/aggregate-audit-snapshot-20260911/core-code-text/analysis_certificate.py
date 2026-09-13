"""Machine-checkable analysis certificates for the aggregate-audit cases.

Contribution one asks for an analysis rule plus a *re-checkable certificate*
rather than prose.  This module builds one certificate per case from the recorded
runs and validates it:

* every acceptance number in a certificate must equal the corresponding number
  recorded in that run's ``summary.json`` (so a certificate cannot drift from the
  evidence it cites);
* every referenced artefact (analysis file, protocol map, rerun command) must
  exist;
* the model verdict must be one of the three allowed statuses, and a case that
  is not ``in-model`` must carry an explicit statement of what its result does
  *not* show.

The certificate deliberately mixes machine-checked counters with declared,
human-reviewed statements.  The validator marks which parts are machine-checked
so a reader can tell them apart.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .common import dump_json, load_json

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "aggregate-audit-analysis-certificate-v1"
MODEL_STATUSES = ("in-model", "explicit-variant", "model-mismatch")
ROLES = ("attack-instance", "negative-control", "positive-control")

CASES: dict[str, dict] = {
    "song2025": {
        "paper": "Song 2025, IEEE TC, DOI 10.1109/TC.2025.3569182",
        "role": "attack-instance",
        "run_dir": "results/song2025/l2-strict-20260911",
        "protocol_map": "evidence/song2025/protocol-map.md",
        "mechanism": "fixed projection (block sector sum)",
        "model_status": "in-model",
        "model_verdict": "Definition 5 covers a malicious storage node, so the projection strategy is an in-model failure instance at the reduced-parameter L2 level.",
        "does_not_show": [
            "that the client cannot detect the loss by downloading the file",
            "that the whole retained state is information-theoretically unable to recover the file",
            "author PBC parameter or prototype performance reproduction",
        ],
        "claim_location": "Definition 5, PDF page 4 (parsed text line 119)",
        "claim_summary": "no adversary can pass Verify.Audit except by computing the proof using the correct file",
        "sufficiency_counters": {
            "accepted": "projection_search_accepted",
            "total": "total_periods",
        },
        "extractability": {
            "verdict": "not-recovered from block sums alone; hash ID_F carries additional information",
            "basis": "evidence/song2025/extractability-argument.md",
            "unproven_parts": [
                "no preimage attempt against the ID_F constraint",
                "no upper bound on the candidate set under the hash constraint",
            ],
        },
        "storage_note": "measured at realistic field sizes, the cached state replaces n*s sector values with n block sums while both sides keep the n tags: content 8x at s=8 (100x at s=100), total 3.33x (34x at s=100). The earlier 'attacker state is larger' reading was a small-field JSON framing artifact",
    },
    "otgpdp2025": {
        "paper": "OTGPDP 2025, CMC, DOI 10.32604/cmc.2025.059949",
        "role": "attack-instance",
        "run_dir": "results/otgpdp2025/strict-20260911",
        "protocol_map": "evidence/otgpdp2025/protocol-map.md",
        "mechanism": "public tags suffice for the response",
        "model_status": "explicit-variant",
        "model_verdict": "the paper fixes the CBF threshold (greater than 1) but never the counter initial value: with the conventional initial 0 a fresh tag has count 1 and honest MetaVer always fails, while with initial 1 the literal flow is executable and admits the tag-only strategy. The failure is therefore a specification gap plus a verification gap, and the fully repaired variant is the configuration under which the strongest attack was measured",
        "does_not_show": [
            "a failure of an unambiguously specified published configuration (the initial value is unstated)",
            "that tag state saves storage (it is far larger than the raw blocks)",
            "computational non-extractability for high-entropy domains",
        ],
        "claim_location": "Verify / MetaVer, PDF pages 7-8 (venue pages 2725-2726)",
        "claim_summary": "the verification equation binds the response to the stored data",
        "sufficiency_counters": {"accepted": "attack_accepted", "total": "total_challenges"},
        "extractability": {
            "verdict": "low-entropy blocks recovered by exhaustive search; high-entropy case undecided",
            "basis": "results/otgpdp2025/strict-20260911/analysis.md",
            "unproven_parts": [
                "no argument for high-entropy cost under a discrete-log assumption",
                "update semantics only repaired for MOD/append/tail-delete and explicit renumbering",
            ],
        },
        "storage_note": "tag state is far larger than the raw blocks",
    },
    "lihang2026": {
        "paper": "Li Hang 2026, ICAIDE (no DOI in the local PDF)",
        "role": "attack-instance",
        "run_dir": "results/lihang2026/l2-final-20260911",
        "protocol_map": "evidence/lihang2026/protocol-map.md",
        "mechanism": "cached per-block digests",
        "model_status": "model-mismatch",
        "model_verdict": "the paper assumes the cloud server honestly executes challenge-response during the audit, so the cached-digest strategy is a security-model mismatch and must not be counted as an in-model attack",
        "does_not_show": [
            "an attack inside the published threat model",
            "information-theoretic non-extractability for an arbitrary lattice hash",
            "JPBC prototype or on-chain performance reproduction",
        ],
        "claim_location": "Section III.B entity definition, PDF page 2 (parsed text line 91)",
        "claim_summary": "the cloud server will honestly execute the challenge-response protocol during the audit",
        "sufficiency_counters": {"accepted": "cached_literal_accepted",
                                 "total": "distinct_challenge_index_sets_summed_over_instances"},
        "extractability": {
            "verdict": "digest state is smaller than the ciphertext; recovery requires preimages of the block hash",
            "basis": "results/lihang2026/l2-final-20260911/analysis.md",
            "unproven_parts": [
                "no preimage-resistance reduction for the concrete hash construction",
                "the q bit length is not specified by the paper, so the compression factor is parameter dependent",
            ],
        },
        "storage_note": "digest state is genuinely smaller than the ciphertext",
    },
    "zhang2025": {
        "paper": "Zhang et al. 2025, IEEE TC, DOI 10.1109/TC.2025.3540670",
        "role": "attack-instance",
        "run_dir": "results/zhang2025/l2-final-20260911",
        "protocol_map": "evidence/zhang2025/protocol-map.md",
        "mechanism": "fixed block-sum projection, plus a verification equation that does not bind the challenge",
        "model_status": "in-model",
        "model_verdict": "the threat model explicitly includes a CSP that forges audit proofs after losing the data (PDF page 4) and the paper hands that CSP the audit key, so both the cached-state strategy and the single-block strategy are in-model failure instances at the reduced-parameter L2 level",
        "does_not_show": [
            "that the client cannot detect the loss by downloading and re-hashing the file",
            "any attack on the blockchain, IBBE or deduplication components, which are not modelled",
            "author prototype, gas cost or storage-network reproduction",
        ],
        "claim_location": "threat model PDF page 4; Eq. (7), Eq. (8) and Algorithm 1 PDF page 7; security argument Eq. (9) PDF page 8",
        "claim_summary": "a CSP that lost the data cannot generate an audit proof that deceives the smart contract",
        "sufficiency_counters": {"accepted": "single_block_per_block_literal_accepted",
                                 "total": "total_challenges"},
        "extractability": {
            "verdict": "deleting the ciphertext is undetected; the minimal cheating state is one block's hash, sector sum and tag, i.e. O(1)",
            "basis": "results/zhang2025/l2-final-20260911/analysis.md",
            "unproven_parts": [
                "no argument that the stored block itself cannot be extracted from the cached hash and sum",
                "the state-size saving is established at paper scale, not by the reduced-parameter run",
            ],
        },
        "storage_note": "measured at realistic field sizes the per-block state drops from s field elements to a hash plus a sum; counting the tags both sides keep, the total is 2.0x (uncompressed hash) or 3.30x (compressed) at s=8, i.e. 20.4x / 33.3x at s=100; the content-only compressed figure is 50x. The single-block strategy is constant-size (325 B measured)",
    },
    "yang2026": {
        "paper": "Yang et al. 2026, IEEE TNSM, DOI 10.1109/TNSM.2025.3650222",
        "role": "negative-control",
        "run_dir": "results/yang2026/neg-final-20260911",
        "protocol_map": "evidence/yang2026/protocol-map.md",
        "mechanism": "single group base with secret per-sector weights; per-sector aggregates in the response",
        "model_status": "in-model",
        "model_verdict": "the paper explicitly allows a malicious CSP that falsifies proofs (adversary A3), and the analysis rule does not flag the scheme: the projection weights stay secret, so the required aggregate combination is not server-computable",
        "does_not_show": [
            "any attack on this scheme; no failure instance was found",
            "CP-ABE, deduplication, proof-of-ownership or on-chain behaviour, which are not modelled",
            "that the scheme is safe in any deployment, only that this rule does not fire",
        ],
        "claim_location": "threat model PDF page 5 (adversary A3); TagGen and Eq. (8) PDF page 7; Theorem 4 PDF page 9",
        "claim_summary": "a malicious CSP that fails to preserve the data cannot forge a proof that passes verification",
        "sufficiency_counters": {"accepted": "published_cached_projection_accepted",
                                 "total": "total_challenges"},
        "extractability": {
            "verdict": "not applicable: the cached-projection strategy is rejected, so no state reduction was achieved",
            "basis": "results/yang2026/neg-final-20260911/analysis.md",
            "unproven_parts": ["no claim about the scheme beyond the rule check"],
        },
        "storage_note": "not applicable (negative control): the cheating prover never passes, so its state is irrelevant",
    },
    "miao2025": {
        "paper": "Miao et al. 2025, IEEE TDSC, DOI 10.1109/TDSC.2025.3579124",
        "role": "negative-control",
        "run_dir": "results/miao2025/neg-final-20260911",
        "protocol_map": "results/miao2025/neg-final-20260911/analysis.md",
        "mechanism": "single group base with secret per-sector weights; per-sector aggregates in the response",
        "model_status": "in-model",
        "model_verdict": "adversary A3 attempts to create a fraudulent integrity proof, and the analysis rule does not flag the scheme: as in Yang 2026 the sector weights stay secret, so the weighted aggregate combination is not server-computable",
        "does_not_show": [
            "any attack on this scheme; no failure instance was found",
            "the searchable index structure, arbitration or on-chain behaviour, which are not modelled",
            "that the scheme is safe in any deployment, only that this rule does not fire",
        ],
        "claim_location": "adversary A3 in the security model; AuthGen and verification Eq. (1) in the scheme section",
        "claim_summary": "the cloud cannot forge a proof without holding the data",
        "sufficiency_counters": {"accepted": "published_cached_projection_accepted",
                                 "total": "total_challenges"},
        "extractability": {
            "verdict": "not applicable: the cached-projection strategy is rejected",
            "basis": "results/miao2025/neg-final-20260911/analysis.md",
            "unproven_parts": ["no claim about the scheme beyond the rule check"],
        },
        "storage_note": "not applicable (negative control)",
    },
    "baseline": {
        "paper": "positive control (this workspace), no external claim",
        "role": "positive-control",
        "run_dir": "results/baseline/baseline-final-20260911",
        "protocol_map": "results/baseline/baseline-final-20260911/analysis.md",
        "mechanism": "authenticated extractable baseline (per-sector independent generators)",
        "model_status": "in-model",
        "model_verdict": "positive control: shows the analysis rule separates an extractable construction from a collapsed one, and is not an attack on any paper",
        "does_not_show": [
            "any property of a published scheme",
            "an efficiency comparison (full-coverage challenges, no erasure coding)",
        ],
        "claim_location": "workspace test matrix, required baseline row",
        "claim_summary": "the analysis framework must distinguish a reliable construction from a candidate scheme",
        "sufficiency_counters": {"accepted": "independent_honest_accepted",
                                 "total": "independent_honest_accepted"},
        "extractability": {
            "verdict": "full per-sector extraction succeeds against the baseline; the block-sum-only prover is rejected",
            "basis": "results/baseline/baseline-final-20260911/analysis.md",
            "unproven_parts": ["no erasure-coded subset sampling, so no extractability theorem for sparse challenges"],
        },
        "storage_note": "cached state is smaller but rejected: small state alone does not imply sufficiency",
    },
}


def load_summary(run_dir: Path) -> dict:
    path = run_dir / "summary.json"
    if not path.exists():
        raise FileNotFoundError(f"missing run summary: {path}")
    return load_json(path)


def build_certificate(case: str) -> dict:
    spec = CASES[case]
    run_dir = ROOT / spec["run_dir"]
    summary = load_summary(run_dir)
    counters = spec["sufficiency_counters"]
    accepted = int(summary[counters["accepted"]])
    total = int(summary[counters["total"]])
    command_path = run_dir / "command.txt"
    return {
        "schema": SCHEMA,
        "case": case,
        "paper": spec["paper"],
        "role": spec["role"],
        "run_dir": spec["run_dir"],
        "reproduction_level": summary.get("level"),
        "mechanism": spec["mechanism"],
        "model_status": spec["model_status"],
        "model_verdict": spec["model_verdict"],
        "does_not_show": list(spec["does_not_show"]),
        "original_claim": {
            "location": spec["claim_location"],
            "summary": spec["claim_summary"],
        },
        "sufficiency": {
            "accepted": accepted,
            "total": total,
            "counter_names": dict(counters),
            "machine_checked": True,
        },
        "extractability": dict(spec["extractability"]),
        "storage_note": spec["storage_note"],
        "recorded_state_fields_checked": summary.get("attacker_states_with_forbidden_fields"),
        "protocol_map": spec["protocol_map"],
        "rerun_command": command_path.read_text(encoding="utf-8").strip() if command_path.exists() else None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def validate_certificate(certificate: dict) -> list[str]:
    """Return a list of problems; an empty list means the certificate is usable."""
    problems: list[str] = []
    if certificate.get("schema") != SCHEMA:
        problems.append(f"unexpected schema: {certificate.get('schema')!r}")
    if certificate.get("model_status") not in MODEL_STATUSES:
        problems.append(f"invalid model_status: {certificate.get('model_status')!r}")
    role = certificate.get("role")
    if role not in ROLES:
        problems.append(f"invalid role: {role!r}")
    if certificate["model_status"] != "in-model" and not certificate.get("does_not_show"):
        problems.append("a non in-model case must state what it does not show")
    sufficiency = certificate.get("sufficiency", {})
    if not isinstance(sufficiency.get("accepted"), int) or not isinstance(sufficiency.get("total"), int):
        problems.append("sufficiency counters must be integers")
    else:
        if sufficiency["total"] <= 0:
            problems.append("sufficiency total must be positive")
        if not 0 <= sufficiency["accepted"] <= sufficiency["total"]:
            problems.append("accepted count outside [0, total]")
        if role == "negative-control" and sufficiency["accepted"] != 0:
            problems.append(
                "a negative-control certificate must report zero accepted cheating responses "
                "(the rule must not fire on a correct scheme)")
        if role == "attack-instance" and sufficiency["accepted"] != sufficiency["total"]:
            problems.append("an attack-instance certificate must report the strategy accepted everywhere")
    extractability = certificate.get("extractability", {})
    if not extractability.get("verdict") or not extractability.get("basis"):
        problems.append("extractability needs a verdict and a basis")
    for key in ("protocol_map",):
        path = ROOT / str(certificate.get(key, ""))
        if not path.exists():
            problems.append(f"referenced artefact missing: {certificate.get(key)!r}")
    basis = ROOT / str(extractability.get("basis", ""))
    if not basis.exists():
        problems.append(f"extractability basis missing: {extractability.get('basis')!r}")
    if not certificate.get("rerun_command"):
        problems.append("missing rerun command")
    # The decisive check: counters must still match the run they cite.
    try:
        summary = load_summary(ROOT / certificate["run_dir"])
    except FileNotFoundError as error:
        problems.append(str(error))
        return problems
    counters = sufficiency.get("counter_names", {})
    for role in ("accepted", "total"):
        name = counters.get(role)
        if name not in summary:
            problems.append(f"counter {name!r} not present in {certificate['run_dir']}/summary.json")
        elif int(summary[name]) != sufficiency[role]:
            problems.append(
                f"{role} counter drifted: certificate={sufficiency[role]} run={summary[name]}")
    return problems


def build_all() -> dict:
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "certificates": [build_certificate(case) for case in CASES]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build analysis certificates from recorded runs")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "certificates" / "aggregate-audit-certificates.json")
    args = parser.parse_args()
    bundle = build_all()
    problems: dict[str, list[str]] = {}
    for certificate in bundle["certificates"]:
        issues = validate_certificate(certificate)
        if issues:
            problems[certificate["case"]] = issues
    bundle["validation"] = {"ok": not problems, "problems": problems}
    dump_json(args.output, bundle)
    print(json.dumps(bundle["validation"], indent=2, ensure_ascii=False))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
