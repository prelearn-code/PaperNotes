"""Deterministic sampling-contract checks; NOT a cryptographic implementation or benchmark.

Run from repository root; output contains theoretical probabilities only.
"""
import json
import math
from pathlib import Path


def required_samples(p, epsilon):
    if not 0 < p <= 1 or not 0 < epsilon < 1:
        raise ValueError('invalid probability')
    return 1 if p == 1 else math.ceil(math.log(epsilon) / math.log1p(-p))


def result(label, p, q):
    log_miss = q * math.log1p(-p) if p < 1 else float('-inf')
    return dict(scenario=label, hit_probability_per_sample=p, samples=q,
                detection_probability=-math.expm1(log_miss),
                log10_miss_probability=log_miss / math.log(10),
                interpretation='analytic with-replacement fixed-loss model; not measured')


def main():
    rows = [
        result('one complete file lost out of 1000; uniform file sampling', 1 / 1000, 459),
        result('999 one-block files lost; one million-block file retained; uniform block sampling',
               999 / 1000999, 459),
        result('same losses; uniform file then block sampling', 999 / 1000, 459),
        result('5 percent files each lose 10 percent blocks; lower bound', 0.05 * 0.1,
               required_samples(0.05 * 0.1, 0.01)),
    ]
    target = Path('06_MyPaper/Search_Audit/System_Privacy_Audit/results/kernel_feasibility.json')
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
