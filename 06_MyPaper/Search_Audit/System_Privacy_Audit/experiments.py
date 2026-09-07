"""Real local crypto/multiproof timings + explicitly synthetic probability experiments."""
import csv
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path
import cryptography
from prototype import Client, respond, wire_bytes, full_wire_bytes

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('results')
OUT.mkdir(exist_ok=True)


def write_csv(name, rows):
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def timed(func):
    start=time.perf_counter_ns(); value=func()
    return value,(time.perf_counter_ns()-start)/1e6


def miss_probability(n,d,c):
    return math.comb(n-d,c)/math.comb(n,c) if c<=n-d else 0.0


def main():
    environment=dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),
        cpu_count=os.cpu_count(),cryptography=cryptography.__version__,clock='perf_counter_ns',
        timing_repetitions=9,workload_seed=20260905,network='none; in-process',
        crypto_randomness='OS CSPRNG; keys and nonces are not seeded',
        byte_count='canonical application message model; excludes transport headers and requests')
    (OUT/'environment.json').write_text(json.dumps(environment,indent=2),encoding='utf-8')
    results=[]
    for m,n in [(8,128),(32,128),(32,1024),(64,1024)]:
        client=Client()
        documents=[(f'f{i}', ['alpha' if i%2==0 else 'beta'], os.urandom(n*256)) for i in range(m//2)]
        snap,setup_ms=timed(lambda:client.build(documents,rows=m,blocks=n,block_bytes=256))
        entries,manifest_ms=timed(lambda:client.open_manifest(snap.pin,snap.manifest))
        full=full_wire_bytes(snap)+len(snap.manifest)
        for c in [16,64,128]:
            times_p,times_v,sizes,nodes=[],[],[],[]
            for repeat in range(10):
                ch=client.challenge(snap.pin,entries,c,random.Random(20260905+repeat))
                resp,p_ms=timed(lambda:respond(snap,ch))
                accepted,v_ms=timed(lambda:client.verify(snap.pin,entries,ch,resp))
                assert accepted
                if repeat:
                    times_p.append(p_ms); times_v.append(v_ms)
                    sizes.append(wire_bytes(resp)+len(snap.manifest))
                    nodes.append(sum(len(proof) for _,proof in resp.values()))
            row=dict(rows=m,blocks=n,plaintext_block_bytes=256,samples=c,
                setup_ms=round(setup_ms,4),manifest_open_ms=round(manifest_ms,4),
                prove_median_ms=round(statistics.median(times_p),4),
                prove_min_ms=round(min(times_p),4),prove_max_ms=round(max(times_p),4),
                verify_median_ms=round(statistics.median(times_v),4),
                verify_min_ms=round(min(times_v),4),verify_max_ms=round(max(times_v),4),
                response_bytes_mean=round(statistics.mean(sizes),2),full_response_bytes=full,
                byte_ratio=round(statistics.mean(sizes)/full,6),
                multiproof_nodes_mean=round(statistics.mean(nodes),2))
            results.append(row)
        print(f'completed M={m}, n={n}',flush=True)
    write_csv('timings.csv',results)
    probability=[];rng=random.Random(20260905)
    for n,d,c in [(1024,10,16),(1024,10,64),(1024,10,128),(1024,52,64),(128,6,16)]:
        trials=20000
        detected=sum(any(i<d for i in rng.sample(range(n),c)) for _ in range(trials))
        p=detected/trials;z=1.959963984540054
        center=(p+z*z/(2*trials))/(1+z*z/trials)
        half=z*math.sqrt(p*(1-p)/trials+z*z/(4*trials*trials))/(1+z*z/trials)
        probability.append(dict(n=n,missing=d,c=c,trials=trials,theoretical_detection=1-miss_probability(n,d,c),
            empirical_detection=p,wilson95_low=center-half,wilson95_high=center+half))
    write_csv('detection.csv',probability)
    # A controlled selective-failure experiment. Both queries access the same cover.
    # Fault targets one alpha-only row before the challenge. Return only a verdict.
    # Non-target-checking verifier ignores faulty cover rows for beta queries.
    attack=[]
    for missing in [10,1024]:
        n,c,trials=1024,64,20000
        wrong_naive=wrong_cover=0
        for _ in range(trials):
            bit=rng.randrange(2)  # alpha=0, beta=1
            hit=any(i<missing for i in rng.sample(range(n),c))
            accept_naive=not(hit and bit==0)
            accept_cover=not hit
            wrong_naive+=(int(accept_naive)!=bit)
            wrong_cover+=(int(accept_cover)!=bit)
        attack.append(dict(n=n,missing=missing,c=c,trials=trials,
            naive_accuracy=1-wrong_naive/trials,cover_accuracy=1-wrong_cover/trials,
            theoretical_naive_accuracy=0.5+0.5*(1-miss_probability(n,missing,c)),
            theoretical_cover_accuracy=0.5))
    write_csv('selective_failure.csv',attack)
    # Alias-link thought experiment with actual sampled masks; not an attack on DDR-SSE.
    repeats=[]
    for t in [1,2,4,8,16]:
        trials=20000
        independent=sum(len({rng.randrange(2) for _ in range(t)})==2 for _ in range(trials))/trials
        repeats.append(dict(rounds=t,independent_both_seen=independent,
            theory=1-2**(1-t),fixed_both_seen=0.0))
    write_csv('alias_resampling.csv',repeats)
    # Required overlap lower bound for exact cover-equivalent privacy.
    cost=[dict(cover=m,true_matches=r,samples=c,required_cover_blocks=m*c,
               true_only_blocks=r*c,amplification=m/r)
          for m in [8,32,64] for r in [1,m//4,m] for c in [16,64]]
    write_csv('cover_cost.csv',cost)
    print('All measurements written to',OUT)


if __name__=='__main__':
    main()
