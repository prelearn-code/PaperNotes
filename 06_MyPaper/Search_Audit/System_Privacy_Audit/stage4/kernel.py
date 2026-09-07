"""Executable, private-verifier reference kernel, NOT a hidden-lookup/SSE protocol.

Authenticated complete bitmaps + current block versions + PRF linear authenticators.
Synthetic owner data, in-memory transport, fixed capacity, four blocks per file.
"""
import hashlib
import hmac
import random
import secrets
import struct
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

P = 2**255 - 19
PAGE = 64
BLOCKS = 4
PLAINTEXT = 512
SECTORS = (PLAINTEXT + 16 + 30) // 31


def H(x):
    return hashlib.sha256(x).digest()


def pack(*xs):
    return b''.join(struct.pack('>Q', x) for x in xs)


def leaf(i, x):
    return H(b'L' + pack(i) + x)


def node(a, b):
    return H(b'N' + a + b)


def needed(ids, size):
    out, cur, level = set(), set(ids), 0
    while size > 1:
        out.update((level, i ^ 1) for i in cur if i ^ 1 not in cur)
        cur = {i // 2 for i in cur}
        size //= 2
        level += 1
    return out


class Tree:
    def __init__(self, values):
        self.values = list(values)
        self.size = len(values)
        assert self.size > 0 and self.size & (self.size - 1) == 0
        self.levels = [[leaf(i, v) for i, v in enumerate(values)]]
        while len(self.levels[-1]) > 1:
            prev = self.levels[-1]
            self.levels.append([node(prev[i], prev[i+1]) for i in range(0, len(prev), 2)])

    @property
    def root(self):
        return self.levels[-1][0]

    def put(self, changes):
        for i, v in changes.items():
            self.values[i] = v
            self.levels[0][i] = leaf(i, v)
        cur = set(changes)
        for level in range(1, len(self.levels)):
            cur = {i // 2 for i in cur}
            for i in cur:
                self.levels[level][i] = node(self.levels[level-1][2*i], self.levels[level-1][2*i+1])

    def open(self, ids):
        return ({i: self.values[i] for i in set(ids)},
                {p: self.levels[p[0]][p[1]] for p in needed(ids, self.size)})


def verify_open(root, size, values, proof):
    if not values or any(i < 0 or i >= size for i in values):
        return False
    if set(proof) != needed(values, size):
        return False
    cur = {i: leaf(i, v) for i, v in values.items()}
    level = 0
    while size > 1:
        cur.update({i: v for (l, i), v in proof.items() if l == level})
        cur = {i // 2: node(cur[i & ~1], cur[i | 1]) for i in cur}
        size //= 2
        level += 1
    return cur[0] == root


def split(ciphertext):
    assert len(ciphertext) == PLAINTEXT + 16
    return [int.from_bytes(ciphertext[i:i+31], 'big') for i in range(0, len(ciphertext), 31)]


@dataclass(frozen=True)
class Pin:
    epoch: int
    roots: tuple
    data_root: bytes


class Owner:
    """Owner retains authoritative update state in this prototype (linear memory)."""
    def __init__(self, n, density=0.5, seed=42):
        assert n >= 512 and n & (n-1) == 0
        self.n = n
        rng = random.Random(seed)  # workload only; never protocol randomness
        self.aes = AESGCM(AESGCM.generate_key(bit_length=256))
        self.prfkey = secrets.token_bytes(32)
        self.alpha = [secrets.randbelow(P-1)+1 for _ in range(SECTORS)]
        self.generation = [1] * n
        self.versions = [[1]*BLOCKS for _ in range(n)]
        self.active = [True]*n
        self.maps = [[rng.random() < density for _ in range(n)] for _ in range(2)]
        self.maps.append(self.active)
        self.index = [Tree([self.page(k, p) for p in range(n//512)]) for k in range(3)]
        self.meta = Tree([self.metadata(i) for i in range(n)])
        self.data, self.tags = {}, {}
        for i in range(n):
            for j in range(BLOCKS):
                self.make_block(i, j, bytes([i % 256])*PLAINTEXT)
        self.epoch = 0

    def metadata(self, i):
        return pack(self.generation[i], int(self.active[i]), *self.versions[i])

    def page(self, k, p):
        bits = sum(int(v) << j for j, v in enumerate(self.maps[k][p*512:(p+1)*512]))
        return bits.to_bytes(PAGE, 'little')

    def label(self, i, j):
        return pack(i, self.generation[i], j, self.versions[i][j])

    def f(self, label):
        return int.from_bytes(hmac.digest(self.prfkey, b'AUDIT-v1'+label, 'sha256'), 'big') % P

    def make_block(self, i, j, plaintext):
        label = self.label(i, j)
        # Unique label per encrypted block under this key; deterministic 96-bit nonce.
        nonce = H(b'nonce'+label)[:12]
        ciphertext = self.aes.encrypt(nonce, plaintext, label)
        self.data[i, j] = ciphertext
        self.tags[i, j] = (self.f(label) + sum(a*m for a, m in zip(self.alpha, split(ciphertext)))) % P

    def pin(self):
        return Pin(self.epoch, tuple(t.root for t in self.index), self.meta.root)

    def keyword(self, i, k, value):
        self.maps[k][i] = value
        p = i//512
        change = {p: self.page(k, p)}
        self.index[k].put(change)
        self.epoch += 1
        return {k: change}

    def content(self, i, j, plaintext):
        assert self.active[i] and len(plaintext) == PLAINTEXT
        self.versions[i][j] += 1
        self.make_block(i, j, plaintext)
        self.meta.put({i: self.metadata(i)})
        self.epoch += 1

    def alive(self, i, value):
        if value and not self.active[i]:
            self.generation[i] += 1
            self.versions[i] = [1]*BLOCKS
            for j in range(BLOCKS):
                self.make_block(i, j, bytes(PLAINTEXT))
        self.active[i] = value
        self.meta.put({i: self.metadata(i)})
        p = i//512
        change = {p: self.page(2, p)}
        self.index[2].put(change)
        self.epoch += 1
        return {2: change}


class Cache:
    """Caches complete authenticated query bitmaps; does not hide their positions."""
    def __init__(self, pin, pages, n):
        assert len(pages) == 3 and all(len(p) == n//512 for p in pages)
        self.trees = [Tree(p) for p in pages]
        if tuple(t.root for t in self.trees) != pin.roots:
            raise ValueError('unauthenticated bitmap')
        self.n = n
        self.pin = pin
        self.intersection = [self.intersect(p) for p in range(n//512)]

    def intersect(self, p):
        a, b, v = [int.from_bytes(t.values[p], 'little') for t in self.trees]
        return a & b & v

    def patch(self, pin, changes):
        if pin.epoch < self.pin.epoch:
            raise ValueError('rollback')
        undo = {}
        try:
            for k, cs in changes.items():
                if k not in range(3) or any(p not in range(self.n//512) or len(v) != PAGE for p, v in cs.items()):
                    raise ValueError('malformed delta')
                undo[k] = {p: self.trees[k].values[p] for p in cs}
                self.trees[k].put(cs)
            if tuple(t.root for t in self.trees) != pin.roots:
                raise ValueError('incomplete or incorrect delta')
        except Exception:
            for k, cs in undo.items():
                self.trees[k].put(cs)
            raise
        for p in {p for cs in changes.values() for p in cs}:
            self.intersection[p] = self.intersect(p)
        self.pin = pin

    def result(self):
        out = []
        for p, bits in enumerate(self.intersection):
            while bits:
                low = bits & -bits
                out.append(p*512 + low.bit_length()-1)
                bits ^= low
        return out


@dataclass
class Challenge:
    pin: Pin
    nonce: bytes
    items: list
    labels: list


def challenge(owner, cache, q):
    """Client verifies current metadata before forming private-verifier challenge.

    Owner object is used only for PRF verification later, and server metadata here;
    sampling uses authenticated cache, NOT owner.maps. Deployment must split roles.
    """
    if not isinstance(q, int) or isinstance(q, bool) or q <= 0:
        raise ValueError('positive sample count required')
    if cache.pin != owner.pin():
        raise ValueError('stale snapshot')
    result = cache.result()
    if not result:
        return None, 0
    pairs = [(secrets.choice(result), secrets.randbelow(BLOCKS)) for _ in range(q)]
    values, proof = owner.meta.open([i for i, j in pairs])
    if not verify_open(cache.pin.data_root, owner.n, values, proof):
        raise ValueError('bad metadata')
    labels, items = [], []
    for i, j in pairs:
        gen, active, *versions = struct.unpack('>6Q', values[i])
        if active != 1:
            raise ValueError('inactive sampled file')
        labels.append(pack(i, gen, j, versions[j]))
        items.append((i, j, secrets.randbelow(P-1)+1))
    wire = len(values)*(8+48)+len(proof)*(8+32)
    return Challenge(cache.pin, secrets.token_bytes(32), items, labels), wire


def respond(data, tags, c):
    mu, sigma = [0]*SECTORS, 0
    for i, j, a in c.items:
        xs = split(data[i, j])
        mu = [(x+a*m) % P for x, m in zip(mu, xs)]
        sigma = (sigma+a*tags[i, j]) % P
    return c.nonce, mu, sigma


def verify(owner, c, response, current_pin):
    nonce, mu, sigma = response
    if c.pin != current_pin or nonce != c.nonce or len(mu) != SECTORS:
        return False
    if not all(isinstance(x, int) and 0 <= x < P for x in [*mu, sigma]):
        return False
    rhs = sum(a*owner.f(label) for (_, _, a), label in zip(c.items, c.labels))
    rhs += sum(a*m for a, m in zip(owner.alpha, mu))
    return sigma == rhs % P
