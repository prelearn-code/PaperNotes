"""Illustrative MMR witness model; not a production library or a benchmark.

Counts a previously inserted element at most once per append operation,
excluding its initial proof assignment. The authenticated accumulator is the
entire ordered peak list, not a single hash with free access to hidden peaks.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json


@dataclass(frozen=True)
class Peak:
    start: int
    size: int
    root: bytes


def leaf(index):
    return sha256(b'L' + index.to_bytes(8, 'big')).digest()


def parent(roots):
    return sha256(b'N' + len(roots).to_bytes(4, 'big') + b''.join(roots)).digest()


class Forest:
    def __init__(self, k):
        self.k, self.peaks, self.paths = k, [], []
        self.changes = self.max_peak_count = 0

    def append(self):
        index = len(self.paths)
        self.paths.append([])
        self.peaks.append(Peak(index, 1, leaf(index)))
        changed = set()
        while len(self.peaks) >= self.k:
            children = self.peaks[-self.k:]
            if len({p.size for p in children}) != 1:
                break
            del self.peaks[-self.k:]
            roots = [p.root for p in children]
            for position, child in enumerate(children):
                siblings = tuple(roots[:position] + roots[position + 1:])
                for i in range(child.start, child.start + child.size):
                    self.paths[i].append((position, siblings))
                    if i != index:
                        changed.add(i)
            self.peaks.append(Peak(children[0].start,
                                   children[0].size * self.k, parent(roots)))
        self.changes += len(changed)
        self.max_peak_count = max(self.max_peak_count, len(self.peaks))

    def verify(self, index, path):
        if not 0 <= index < len(self.paths):
            return False
        peak = next(p for p in self.peaks if p.start <= index < p.start + p.size)
        value, size = leaf(index), 1
        for position, siblings in path:
            if len(siblings) != self.k - 1:
                return False
            if position != (index // size) % self.k:
                return False
            roots = list(siblings)
            roots.insert(position, value)
            value, size = parent(roots), size * self.k
        return size == peak.size and value == peak.root

    def bag(self):
        return sha256(b'P' + len(self.paths).to_bytes(8, 'big') + b''.join(
            p.start.to_bytes(8, 'big') + p.size.to_bytes(8, 'big') + p.root
            for p in self.peaks)).hexdigest()


def main():
    forest = Forest(2)
    for _ in range(4):
        forest.append()
    old_path, old_bag = tuple(forest.paths[0]), forest.bag()
    forest.append()
    example = {
        'four_to_five_leaf0_path_unchanged': old_path == tuple(forest.paths[0]),
        'four_to_five_old_path_verifies_under_new_peak_list': forest.verify(0, old_path),
        'four_to_five_bagged_commitment_changed': old_bag != forest.bag(),
    }
    forest.append()
    forest.append()
    old_path = tuple(forest.paths[0])
    forest.append()
    example['seven_to_eight_old_leaf0_path_fails_under_new_peak_list'] = not forest.verify(0, old_path)
    assert all(example.values())

    rows = []
    n = 4096
    for k in (2, 4, 16):
        forest = Forest(k)
        for _ in range(n):
            forest.append()
        assert all(forest.verify(i, path) for i, path in enumerate(forest.paths))
        height, power = 0, 1
        while power < n:
            power *= k
            height += 1
        assert power == n
        # Multiple merges during one append still count as one change per old
        # element. For n=k**height the exact total is n*height*(k-1)/k.
        assert forest.changes == n * height * (k - 1) // k
        rows.append({
            'n': n, 'k': k,
            'existing_witness_changes_per_append_summed': forest.changes,
            'max_path_hashes': max(len(p) * (k - 1) for p in forest.paths),
            'max_path_hash_bytes_sha256': max(len(p) * (k - 1) * 32 for p in forest.paths),
            'max_peak_hash_bytes_over_prefixes': forest.max_peak_count * 32,
            'final_peak_hash_bytes': len(forest.peaks) * 32,
        })
    result = {
        'scope': 'Structural counts only; no timings, consensus, signatures, SSE, HLA, or network. Hash-byte figures exclude identifiers, counts, and encoding overhead.',
        'small_example': example,
        'rows': rows,
    }
    target = Path(__file__).with_name('mmr_witness_model.json')
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
