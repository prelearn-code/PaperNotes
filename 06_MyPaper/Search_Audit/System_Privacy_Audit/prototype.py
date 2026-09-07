"""Reference prototype: fixed-cover authenticated sampling, not a DDR-SSE implementation.

AES-GCM is from cryptography. Ciphertext authentication uses SHA-256 Merkle trees.
Production randomness uses secrets; benchmark workload randomness is separate.
"""
from __future__ import annotations
import hashlib
import json
import secrets
import struct
from dataclasses import dataclass
from typing import Dict, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def h(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()


def enc(key: bytes, msg: bytes, aad: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(key).encrypt(nonce, msg, aad)


def dec(key: bytes, value: bytes, aad: bytes) -> bytes:
    return AESGCM(key).decrypt(value[:12], value[12:], aad)


def ctx(epoch: int, bucket: int, alias: str) -> bytes:
    return b"cover-audit-v1" + struct.pack(">QQ", epoch, bucket) + bytes.fromhex(alias)


def leaf(context: bytes, i: int, value: bytes) -> bytes:
    return h(b"L" + context + struct.pack(">Q", i) + value)


def parent(left: bytes, right: bytes) -> bytes:
    return h(b"N" + left + right)


def needed_nodes(indices, n):
    current = set(indices)
    needed = set()
    level = 0
    while n > 1:
        for i in current:
            if i ^ 1 not in current:
                needed.add((level, i ^ 1))
        current = {i // 2 for i in current}
        n //= 2
        level += 1
    return needed


class Merkle:
    def __init__(self, context: bytes, values: List[bytes]):
        n = len(values)
        if n < 1 or n & (n - 1):
            raise ValueError("power-of-two row length required")
        self.levels = [[leaf(context, i, v) for i, v in enumerate(values)]]
        while len(self.levels[-1]) > 1:
            prev = self.levels[-1]
            self.levels.append([parent(prev[i], prev[i+1]) for i in range(0, len(prev), 2)])
        self.root = self.levels[-1][0]

    def proof(self, indices):
        return {p: self.levels[p[0]][p[1]] for p in sorted(needed_nodes(indices, len(self.levels[0])))}


def verify_row(context, n, indices, values, proof, root):
    if (n < 1 or n & (n-1) or not indices or indices != sorted(set(indices))
            or indices[0] < 0 or indices[-1] >= n):
        return False
    if set(values) != set(indices) or set(proof) != needed_nodes(indices, n):
        return False
    if any(not isinstance(v, bytes) or len(v) != 32 for v in proof.values()):
        return False
    current = {i: leaf(context, i, values[i]) for i in indices}
    level = 0
    while n > 1:
        for (lev, idx), digest in proof.items():
            if lev == level:
                current[idx] = digest
        next_level = {}
        for p in sorted({i // 2 for i in current}):
            if 2*p not in current or 2*p+1 not in current:
                return False
            next_level[p] = parent(current[2*p], current[2*p+1])
        current = next_level
        level += 1
        n //= 2
    return current == {0: root}


@dataclass(frozen=True)
class Pin:
    epoch: int
    bucket: int
    manifest_hash: bytes
    rows: int
    blocks: int
    block_bytes: int


@dataclass
class Row:
    alias: str
    values: List[bytes]
    tree: Merkle


@dataclass
class Snapshot:
    pin: Pin
    manifest: bytes
    rows: Dict[str, Row]


class Client:
    def __init__(self):
        self.key = AESGCM.generate_key(bit_length=256)

    def build(self, documents, rows=8, blocks=128, block_bytes=256, epoch=1, bucket=0):
        """documents = [(logical_id, keywords, bytes)] supplied by trusted Owner.
        Dummy rows are real independently encrypted random bytes and must be audited.
        """
        if len(documents) > rows:
            raise ValueError("bucket capacity exceeded")
        if blocks < 1 or blocks & (blocks - 1) or block_bytes < 1:
            raise ValueError("invalid row dimensions")
        entries, data = [], {}
        for slot in range(rows):
            alias = secrets.token_hex(16)
            context = ctx(epoch, bucket, alias)
            if slot < len(documents):
                fid, words, raw = documents[slot]
                if len(raw) > blocks * block_bytes:
                    raise ValueError("document too large")
                length = len(raw)
                padded = raw + secrets.token_bytes(blocks * block_bytes - length)
            else:
                fid, words, length = None, [], 0
                padded = secrets.token_bytes(blocks * block_bytes)
            values = [enc(self.key, padded[i*block_bytes:(i+1)*block_bytes], context+struct.pack(">Q", i))
                      for i in range(blocks)]
            tree = Merkle(context, values)
            data[alias] = Row(alias, values, tree)
            entries.append(dict(alias=alias, fid=fid, words=sorted(set(words)), length=length, root=tree.root.hex()))
        # The encrypted manifest order is independent of keyword matching.
        entries.sort(key=lambda x: x['alias'])
        payload = json.dumps(entries, ensure_ascii=False, separators=(',', ':')).encode()
        capacity = 4096 + rows * 1024
        if len(payload) + 4 > capacity:
            raise ValueError("manifest capacity exceeded")
        padded = struct.pack(">I", len(payload)) + payload
        padded += secrets.token_bytes(capacity-len(padded))
        aad = b"manifest-v1" + struct.pack(">QQ", epoch, bucket)
        manifest = enc(self.key, padded, aad)
        pin = Pin(epoch, bucket, h(manifest), rows, blocks, block_bytes)
        return Snapshot(pin, manifest, data)

    def open_manifest(self, pin, manifest):
        if len(manifest) != 4096 + pin.rows * 1024 + 28 or h(manifest) != pin.manifest_hash:
            raise ValueError("unauthenticated manifest")
        aad = b"manifest-v1" + struct.pack(">QQ", pin.epoch, pin.bucket)
        raw = dec(self.key, manifest, aad)
        size = struct.unpack(">I", raw[:4])[0]
        entries = json.loads(raw[4:4+size])
        aliases = [x['alias'] for x in entries]
        if len(entries) != pin.rows or aliases != sorted(set(aliases)):
            raise ValueError("invalid owner manifest")
        return entries

    def challenge(self, pin, entries, c, rng=None):
        if not 1 <= c <= pin.blocks:
            raise ValueError("invalid sample size")
        rng = rng or secrets.SystemRandom()
        return {e['alias']: sorted(rng.sample(range(pin.blocks), c)) for e in entries}

    def verify(self, pin, entries, challenge, response):
        try:
            return self._verify(pin, entries, challenge, response)
        except (KeyError, TypeError, ValueError, IndexError, AttributeError):
            return False

    def _verify(self, pin, entries, challenge, response):
        expected = {e['alias'] for e in entries}
        if set(challenge) != expected or set(response) != expected:
            return False
        ok = True
        for e in entries:
            alias = e['alias']
            values, proof = response[alias]
            lengths_ok = all(isinstance(v, bytes) and len(v) == pin.block_bytes+28 for v in values.values())
            valid = lengths_ok and verify_row(ctx(pin.epoch, pin.bucket, alias), pin.blocks,
                challenge[alias], values, proof, bytes.fromhex(e['root']))
            ok = bool(valid) and ok
        return ok

    @staticmethod
    def local_results(entries, keyword):
        return [e['fid'] for e in entries if e['fid'] is not None and keyword in e['words']]


def respond(snapshot, challenge):
    return {alias: ({i: snapshot.rows[alias].values[i] for i in indices},
                    snapshot.rows[alias].tree.proof(indices))
            for alias, indices in challenge.items()}


def wire_bytes(response):
    """Canonical response: count(4), alias(16), counts(8), (index(4),block),
    and (level(4),node index(4),hash(32)). Transport framing excluded.
    """
    return 4 + sum(24 + sum(4+len(v) for v in values.values()) + 40*len(proof)
                   for values, proof in response.values())


def full_wire_bytes(snapshot):
    # Whole ciphertext rows, authenticated using the same trusted manifest roots.
    return 4 + sum(20+sum(len(v) for v in row.values) for row in snapshot.rows.values())


class EpochCatalog:
    """Single-owner logical state machine. Persistence/network/concurrency are not implemented.

    Logical ticks are public policy. A bounded lease pins an old immutable snapshot;
    opening new queries always uses current. Commit is an atomic Python assignment.
    """
    def __init__(self, initial: Pin, max_lease=10):
        self.current = initial
        self.max_lease = max_lease
        self.tick = 0
        self.sessions = {}

    def commit(self, new: Pin):
        old = self.current
        if (new.epoch != old.epoch+1 or new.bucket != old.bucket or
            (new.rows,new.blocks,new.block_bytes) != (old.rows,old.blocks,old.block_bytes)):
            raise ValueError('invalid transition')
        self.current = new

    def open(self):
        sid = secrets.token_hex(16)
        self.sessions[sid] = (self.current, self.tick+self.max_lease)
        return sid

    def pinned(self, sid):
        pin, deadline = self.sessions[sid]
        if self.tick >= deadline:
            raise ValueError('expired query')
        return pin

    def advance(self, ticks=1):
        if ticks < 0:
            raise ValueError('nonmonotone clock')
        self.tick += ticks

    def close(self, sid):
        del self.sessions[sid]
