"""Research-only nonrecursive Path ORAM with SHA256 authenticated bucket storage.

Real AES-GCM; in-process transport. Linear client position map is explicit.
Not a production constant-time implementation. Fail-stop on authentication errors.
"""
import hashlib
import math
import secrets
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def digest(data):
    return hashlib.sha256(data).digest()


def leaf(i, value):
    return digest(b'L' + struct.pack('>Q', i) + value)


def branch(a, b):
    return digest(b'N' + a + b)


def needed(indices, size):
    cur, answer, level = set(indices), set(), 0
    while size > 1:
        answer.update((level, i ^ 1) for i in cur if (i ^ 1) not in cur)
        cur = {i // 2 for i in cur}
        level += 1
        size //= 2
    return answer


def reconstruct(values, proof, size):
    if set(proof) != needed(values, size):
        raise ValueError('noncanonical proof')
    cur = {i: leaf(i, v) for i, v in values.items()}
    level = 0
    while size > 1:
        cur.update({i: h for (lev, i), h in proof.items() if lev == level})
        cur = {i // 2: branch(cur[i & ~1], cur[i | 1]) for i in cur}
        size //= 2
        level += 1
    return cur[0]


class AuthStore:
    def __init__(self, buckets):
        self.buckets = list(buckets)
        self.size = 1 << (len(buckets) - 1).bit_length()
        self.levels = [[leaf(i, buckets[i] if i < len(buckets) else b'') for i in range(self.size)]]
        while len(self.levels[-1]) > 1:
            prev = self.levels[-1]
            self.levels.append([branch(prev[i], prev[i+1]) for i in range(0, len(prev), 2)])

    def get(self, indices):
        return ({i: self.buckets[i] for i in indices},
                {p: self.levels[p[0]][p[1]] for p in needed(indices, self.size)})

    def put(self, values):
        for i, value in values.items():
            self.buckets[i] = value
            self.levels[0][i] = leaf(i, value)
        cur = set(values)
        for level in range(1, len(self.levels)):
            cur = {i // 2 for i in cur}
            for i in cur:
                self.levels[level][i] = branch(self.levels[level-1][2*i], self.levels[level-1][2*i+1])


class PathORAM:
    def __init__(self, records, capacity, record_bytes=128, z=4):
        if len(records) > capacity:
            raise ValueError('capacity')
        self.capacity, self.record_bytes, self.z = capacity, record_bytes, z
        self.leaves = 1 << ((max(1, math.ceil(capacity / 2)) - 1).bit_length())
        self.height = self.leaves.bit_length() - 1
        self.key = AESGCM.generate_key(bit_length=256)
        self.aes = AESGCM(self.key)
        self.position = [secrets.randbelow(self.leaves) for _ in range(capacity)]
        self.stash = {}
        buckets = [[] for _ in range(2*self.leaves-1)]
        for rid in range(capacity):
            value = records.get(rid, bytes(record_bytes))
            if len(value) != record_bytes:
                raise ValueError('record length')
            for node in reversed(self.path(self.position[rid])):
                if len(buckets[node]) < z:
                    buckets[node].append((rid, value))
                    break
            else:
                self.stash[rid] = value
        self.store = AuthStore([self.encrypt(i, b) for i, b in enumerate(buckets)])
        self.root = self.store.levels[-1][0]
        self.failed = False
        self.reset_metrics()

    def path(self, pos):
        node, result = self.leaves - 1 + pos, []
        while True:
            result.append(node)
            if node == 0:
                return list(reversed(result))
            node = (node - 1) // 2

    def encrypt(self, node, items):
        dummy = (2**64 - 1, bytes(self.record_bytes))
        values = list(items) + [dummy] * (self.z-len(items))
        raw = b''.join(struct.pack('>Q', rid) + data for rid, data in values)
        nonce = secrets.token_bytes(12)
        return nonce + self.aes.encrypt(nonce, raw, struct.pack('>Q', node))

    def decrypt(self, node, value):
        raw = self.aes.decrypt(value[:12], value[12:], struct.pack('>Q', node))
        stride = 8 + self.record_bytes
        if len(raw) != self.z * stride:
            raise ValueError('bucket length')
        items = []
        for off in range(0, len(raw), stride):
            rid = struct.unpack('>Q', raw[off:off+8])[0]
            if rid == 2**64-1:
                continue
            if rid >= self.capacity:
                raise ValueError('bad id')
            items.append((rid, raw[off+8:off+stride]))
        return items

    def reset_metrics(self):
        self.accesses = self.download = self.upload = self.proof_bytes = 0
        self.peak_stash = len(self.stash)
        self.trace = []

    def access(self, rid, new_value=None):
        if self.failed:
            raise ValueError('fail-stop state')
        if not 0 <= rid < self.capacity:
            raise ValueError('logical address')
        if new_value is not None and len(new_value) != self.record_bytes:
            raise ValueError('write length')
        try:
            return self._access(rid, new_value)
        except Exception:
            self.failed = True
            raise

    def _access(self, rid, new_value):
        pos = self.position[rid]
        path = self.path(pos)
        values, proof = self.store.get(path)
        if set(values) != set(path) or reconstruct(values, proof, self.store.size) != self.root:
            raise ValueError('root authentication failed')
        self.trace.append(pos)
        self.accesses += 1
        # Implicit proof coordinates, implicit bucket lengths; counts defined in report.
        self.download += sum(map(len, values.values())) + 32*len(proof)
        self.proof_bytes += 32*len(proof)
        for node in path:
            for item_id, data in self.decrypt(node, values[node]):
                if item_id in self.stash:
                    raise ValueError('duplicate logical record')
                self.stash[item_id] = data
        self.peak_stash = max(self.peak_stash, len(self.stash))
        if rid not in self.stash:
            raise ValueError('missing record')
        old = self.stash[rid]
        if new_value is not None:
            self.stash[rid] = new_value
        self.position[rid] = secrets.randbelow(self.leaves)
        replacement = {}
        for depth in range(self.height, -1, -1):
            prefix = pos >> (self.height-depth)
            selected = [a for a in self.stash
                        if self.position[a] >> (self.height-depth) == prefix][:self.z]
            replacement[path[depth]] = self.encrypt(path[depth], [(a, self.stash.pop(a)) for a in selected])
        next_root = reconstruct(replacement, proof, self.store.size)
        self.store.put(replacement)
        self.root = next_root
        self.upload += sum(map(len, replacement.values())) + 8  # leaf address request
        return old

    def state_metrics(self):
        return dict(position_map_packed_bytes=4*self.capacity,
                    root_and_key_bytes=64,
                    peak_stash_payload_bytes=self.peak_stash*(8+self.record_bytes),
                    server_ciphertext_bytes=sum(map(len, self.store.buckets)),
                    server_hash_bytes=sum(len(level)*32 for level in self.store.levels),
                    oram_height=self.height, oram_capacity=self.capacity)
