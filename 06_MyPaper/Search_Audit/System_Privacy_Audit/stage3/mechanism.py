"""Three actual samplers over the SAME authenticated ORAM backend.

rank_serial: natural traversal baseline.
rank_batch: H1 candidate, breadth-first deduplication with PUBLIC padding limits.
dense: stronger unordered-set baseline using packed slots and reverse positions.
All implement file-uniform then block-uniform sampling, with replacement.
"""
import math
import random
import secrets
import struct
from auth_oram import PathORAM

SIZE = 128
ABSENT = 2**64 - 1


def pack(*items):
    raw = struct.pack('>' + 'Q'*len(items), *items)
    return raw + bytes(SIZE-len(raw))


def unpack(raw):
    return struct.unpack('>16Q', raw)


def capacity_for(rmax, nfiles, words, bmax):
    maximum = 1 + words + words*(2*rmax-1) + words*nfiles + nfiles + nfiles*bmax
    return 1 << (maximum-1).bit_length()


class Audit:
    def __init__(self, method, rmax=128, nfiles=128, words=4, bmax=4, occupancy=None):
        if method not in ('rank_serial', 'rank_batch', 'dense'):
            raise ValueError('method')
        if rmax & (rmax-1) or nfiles < rmax:
            raise ValueError('dimensions')
        self.method, self.rmax, self.nfiles, self.words, self.bmax = method, rmax, nfiles, words, bmax
        self.height = rmax.bit_length()-1
        self.base = 1 + words
        self.stride = rmax if method == 'dense' else 2*rmax-1
        self.rev = self.base + words*self.stride
        self.files = self.rev + words*nfiles
        self.data = self.files + nfiles
        self.owner_lists = []  # Owner test/update input ONLY; never read by query().
        records = {0: pack(0)}
        for w in range(words):
            count = occupancy if occupancy is not None else rmax//2
            members = list(range(count))
            self.owner_lists.append(members)
            records[1+w] = pack(1, count)
            for fid in range(nfiles):
                records[self.rev+w*nfiles+fid] = pack(5, fid if fid < count else ABSENT)
            if method == 'dense':
                for s in range(rmax):
                    records[self.base+w*self.stride+s] = pack(2, s if s<count else ABSENT)
            else:
                nodes = {}
                for s in range(rmax):
                    nodes[rmax-1+s] = pack(2, 1 if s<count else 0, 0, s if s<count else ABSENT)
                for node in range(rmax-2, -1, -1):
                    left, right = unpack(nodes[2*node+1])[1], unpack(nodes[2*node+2])[1]
                    nodes[node] = pack(3, left+right, left)
                records.update({self.base+w*self.stride+node: value for node,value in nodes.items()})
        for fid in range(nfiles):
            length = 1 + fid % bmax
            records[self.files+fid] = pack(6, fid, 1, length)
            for j in range(bmax):
                records[self.data+fid*bmax+j] = pack(7, fid, 1, j)[:32] + secrets.token_bytes(SIZE-32)
        self.oram = PathORAM(records, capacity_for(rmax,nfiles,words,bmax), SIZE)
        self.epoch = 1

    def read(self, address):
        return unpack(self.oram.access(address))

    def slot_address(self, word, slot):
        return self.base+word*self.stride+slot+(0 if self.method=='dense' else self.rmax-1)

    def slot_value(self, fid):
        return pack(2,fid) if self.method=='dense' else pack(2,int(fid!=ABSENT),0,fid)

    def slot_fid(self, value):
        return value[1] if self.method=='dense' else value[3]

    def query(self, word, q, rng=None):
        if not 0 <= word < self.words or q < 1:
            raise ValueError('query')
        rng = rng or secrets.SystemRandom()
        count = self.read(1+word)[1]
        ranks = [rng.randrange(max(1,count)) for _ in range(q)]
        chosen = []
        if self.method == 'dense':
            # Same local deduplication privilege as H1; do NOT enumerate all results.
            unique = sorted(set(ranks))
            cache = {u:self.slot_fid(self.read(self.slot_address(word,u))) for u in unique}
            for _ in range(min(q,self.rmax)-len(unique)):
                self.read(0)
            chosen = [cache[u] for u in ranks]
        elif self.method == 'rank_serial':
            for u in ranks:
                node = 0
                for depth in range(self.height+1):
                    v = self.read(self.base+word*self.stride+node)
                    if depth == self.height:
                        chosen.append(v[3])
                    elif u < v[2]:
                        node = 2*node+1
                    else:
                        u -= v[2]
                        node = 2*node+2
        else:
            current = [(0,u) for u in ranks]
            for depth in range(self.height+1):
                unique = sorted({node for node,u in current})
                fixed_budget = min(2**depth,q)
                cache = {node:self.read(self.base+word*self.stride+node) for node in unique}
                for _ in range(fixed_budget-len(unique)):
                    self.read(0)  # true ORAM access even for repeated dummy address
                if depth == self.height:
                    chosen = [cache[node][3] for node,u in current]
                else:
                    current = [(2*node+1,u) if u<cache[node][2]
                               else (2*node+2,u-cache[node][2]) for node,u in current]
        metadata_accesses = self.oram.accesses
        answer = []
        for fid in chosen:
            valid = fid != ABSENT and count>0
            safe = fid if valid else 0
            v = self.read(self.files+safe)
            j = rng.randrange(v[3])
            raw = self.oram.access(self.data+safe*self.bmax+j)
            b = unpack(raw)
            if (v[0],v[1],b[0],b[1],b[2],b[3]) != (6,safe,7,safe,v[2],j):
                raise ValueError('version/record mismatch')
            if valid:
                answer.append((fid,j,raw))
        return answer, metadata_accesses

    def rebuild_ancestors(self, word, slot):
        if self.method=='dense':
            return
        node = self.rmax-1+slot
        while node:
            node = (node-1)//2
            a = self.base+word*self.stride
            left, right = self.read(a+2*node+1)[1], self.read(a+2*node+2)[1]
            self.oram.access(a+node, pack(3,left+right,left))

    def remove(self, word, fid):
        count = self.read(1+word)[1]
        pos = self.read(self.rev+word*self.nfiles+fid)[1]
        if pos == ABSENT or count==0:
            raise ValueError('not present')
        last = self.slot_fid(self.read(self.slot_address(word,count-1)))
        self.oram.access(self.slot_address(word,pos),self.slot_value(last))
        self.oram.access(self.slot_address(word,count-1),self.slot_value(ABSENT))
        self.oram.access(self.rev+word*self.nfiles+last,pack(5,pos))
        self.oram.access(self.rev+word*self.nfiles+fid,pack(5,ABSENT))
        self.oram.access(1+word,pack(1,count-1))
        self.rebuild_ancestors(word,pos)
        self.rebuild_ancestors(word,count-1)
        self.epoch += 1

    def insert(self, word, fid):
        count = self.read(1+word)[1]
        pos = self.read(self.rev+word*self.nfiles+fid)[1]
        if count>=self.rmax or pos!=ABSENT:
            raise ValueError('invalid insert')
        self.oram.access(self.slot_address(word,count),self.slot_value(fid))
        self.oram.access(self.rev+word*self.nfiles+fid,pack(5,count))
        self.oram.access(1+word,pack(1,count+1))
        self.rebuild_ancestors(word,count)
        self.epoch += 1

    def modify(self, fid):
        v = self.read(self.files+fid)
        for j in range(self.bmax):
            raw = pack(7,fid,v[2]+1,j)[:32] + secrets.token_bytes(SIZE-32)
            self.oram.access(self.data+fid*self.bmax+j, raw)
        self.oram.access(self.files+fid,pack(6,fid,v[2]+1,v[3]))
        self.epoch += 1


def logical_cost(method, rmax, q):
    height = rmax.bit_length()-1
    if method=='rank_serial':
        meta = 1+q*(height+1)
    elif method=='rank_batch':
        meta = 1+sum(min(2**d,q) for d in range(height+1))
    else:
        meta = 1+min(q,rmax)
    return meta, meta+2*q
