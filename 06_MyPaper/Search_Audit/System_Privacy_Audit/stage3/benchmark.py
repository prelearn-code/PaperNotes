"""Same-backend comparison. Wall clock is local combined client/server time.

No network, no disk, no recursive position map, no third-party vPIR timings.
"""
import csv
import json
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path
import cryptography
from mechanism import Audit, logical_cost


def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    rows,updates,raw_runs=[] ,[],[]
    for rmax in (64,256):
        for method in ('rank_serial','rank_batch','dense'):
            start=time.perf_counter()
            a=Audit(method,rmax,rmax,4,4,rmax//2)
            setup_ms=1000*(time.perf_counter()-start)
            for q in (16,64,256):
                a.query(0,q,random.Random(101))  # warmup
                times=[];download=[];upload=[];peaks=[];proof=[]
                for repeat in range(5):
                    a.oram.reset_metrics()
                    start=time.perf_counter()
                    result,meta=a.query(repeat%4,q,random.Random(20260905+repeat))
                    elapsed=1000*(time.perf_counter()-start)
                    assert len(result)==q
                    assert (meta,a.oram.accesses)==logical_cost(method,rmax,q)
                    times.append(elapsed);download.append(a.oram.download);upload.append(a.oram.upload)
                    peaks.append(a.oram.peak_stash);proof.append(a.oram.proof_bytes)
                    raw_runs.append(dict(rmax=rmax,method=method,q=q,repeat=repeat,
                                         elapsed_ms=elapsed,download_bytes=a.oram.download,
                                         upload_bytes=a.oram.upload,peak_stash=a.oram.peak_stash))
                state=a.oram.state_metrics()
                state['peak_stash_payload_bytes']=max(peaks)*136
                rows.append(dict(rmax=rmax,method=method,q=q,matching_files=rmax//2,
                    setup_ms=setup_ms,median_ms=statistics.median(times),min_ms=min(times),max_ms=max(times),
                    metadata_accesses=meta,total_accesses=a.oram.accesses,
                    download_mean=statistics.mean(download),upload_mean=statistics.mean(upload),
                    proof_download_mean=statistics.mean(proof),**state))
                print(json.dumps(rows[-1]),flush=True)
            for action in ('remove','insert','modify'):
                a.oram.reset_metrics()
                start=time.perf_counter()
                if action=='remove': a.remove(0,1)
                elif action=='insert': a.insert(0,1)
                else: a.modify(1)
                updates.append(dict(rmax=rmax,method=method,action=action,
                    elapsed_ms=1000*(time.perf_counter()-start),accesses=a.oram.accesses,
                    download_bytes=a.oram.download,upload_bytes=a.oram.upload))
    write_csv(out/'comparison.csv',rows)
    write_csv(out/'raw_runs.csv',raw_runs)
    write_csv(out/'updates.csv',updates)
    (out/'environment.json').write_text(json.dumps(dict(
        python=sys.version,platform=platform.platform(),processor=platform.processor(),
        cpu_count=os.cpu_count(),cryptography=cryptography.__version__,repeats=5,
        record_bytes=128,bucket_slots=4,position_map='nonrecursive; linear client storage',
        transport='in-process; encrypted payload and Merkle hash counts; no network timing',
        randomness='OS CSPRNG for ORAM/encryption; seeded workload only',
        initialization='trusted bulk placement, not online oblivious rebuild',
        update_measurement='one operation per action/configuration; descriptive only'
    ),indent=2),encoding='utf-8')


if __name__=='__main__': main()
