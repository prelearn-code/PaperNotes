"""Real cryptographic timing, not hidden lookup performance or a paper reproduction."""
import csv
import json
import platform
import statistics
import time
from pathlib import Path
import cryptography
from kernel import *

OUT = Path(__file__).parent / 'results'
OUT.mkdir(exist_ok=True)


def timed(fn):
    t = time.perf_counter_ns()
    value = fn()
    return value, (time.perf_counter_ns()-t)/1e6


def dump(name, rows):
    with (OUT/name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


raw, updates, setup = [], [], []
for n in (1024, 4096, 16384):
    for density in (0.1, 0.5):
        o, setup_ms = timed(lambda: Owner(n, density))
        cached = Cache(o.pin(), [t.values for t in o.index], n)
        setup.append(dict(n=n, density=density, setup_ms=setup_ms,
                          encrypted_bytes=n*BLOCKS*(PLAINTEXT+16), tag_bytes=n*BLOCKS*32))
        for q in (64, 256):
            for mode in ('cold_composition', 'cached_composition'):
                for rep in range(6):  # first run is warmup per configuration
                    if mode == 'cold_composition':
                        cache, search_ms = timed(lambda: Cache(o.pin(), [t.values for t in o.index], n))
                    else:
                        cache = cached
                        _, search_ms = timed(lambda: cache.patch(o.pin(), {}))
                    (ch, meta_bytes), challenge_ms = timed(lambda: challenge(o, cache, q))
                    response, server_ms = timed(lambda: respond(o.data, o.tags, ch))
                    ok, verify_ms = timed(lambda: verify(o, ch, response, o.pin()))
                    assert ok
                    if rep:
                        unique = len({i for i, j, a in ch.items})
                        # Specified payload bytes, no socket/TLS/JSON framing.
                        wire = 136+32+q*48+unique*8+meta_bytes+32+(SECTORS+1)*32
                        if mode == 'cold_composition':
                            wire += 3*n//8
                        raw.append(dict(n=n, density=density, r=len(cache.result()), q=q,
                                        mode=mode, rep=rep, search_ms=search_ms,
                                        challenge_ms=challenge_ms, server_ms=server_ms,
                                        verify_ms=verify_ms,
                                        total_ms=search_ms+challenge_ms+server_ms+verify_ms,
                                        payload_bytes=wire, aggregate_bytes=32+(SECTORS+1)*32))
        for rep in range(10):
            i, k = rep, rep%2
            delta, owner_ms = timed(lambda: o.keyword(i, k, not o.maps[k][i]))
            _, client_ms = timed(lambda: cached.patch(o.pin(), delta))
            updates.append(dict(n=n, density=density, kind='keyword', rep=rep,
                                owner_ms=owner_ms, cache_ms=client_ms, retags=0, delta_bytes=80))
            _, owner_ms = timed(lambda: o.content(i, 0, bytes([rep])*PLAINTEXT))
            _, client_ms = timed(lambda: cached.patch(o.pin(), {}))
            updates.append(dict(n=n, density=density, kind='content', rep=rep,
                                owner_ms=owner_ms, cache_ms=client_ms, retags=1, delta_bytes=0))
        print(f'completed N={n}, density={density}', flush=True)

summary = []
for key in sorted({(r['n'], r['density'], r['q'], r['mode']) for r in raw}):
    rs = [r for r in raw if (r['n'], r['density'], r['q'], r['mode']) == key]
    row = {k: rs[0][k] for k in ('n', 'density', 'r', 'q', 'mode')}
    for field in ('search_ms', 'challenge_ms', 'server_ms', 'verify_ms', 'total_ms', 'payload_bytes'):
        row[field+'_median'] = statistics.median(r[field] for r in rs)
    row['total_ms_min'] = min(r['total_ms'] for r in rs)
    row['total_ms_max'] = max(r['total_ms'] for r in rs)
    summary.append(row)
dump('raw.csv', raw)
dump('summary.csv', summary)
dump('updates.csv', updates)
dump('setup.csv', setup)
(OUT/'environment.json').write_text(json.dumps(dict(
    python=platform.python_version(), platform=platform.platform(), processor=platform.processor(),
    cryptography=cryptography.__version__, repetitions=5, warmup=1, clock='perf_counter_ns',
    protocol_randomness='secrets; keys/nonces/challenges differ per run', workload_seed=42,
    sectors=SECTORS, plaintext_block_bytes=PLAINTEXT, blocks_per_file=BLOCKS,
    measurement='in-process; no network, disk or hidden lookup; payload accounting only',
    baseline='cached_composition IS the candidate with the same natural optimization'
), ensure_ascii=False, indent=2), encoding='utf-8')
