"""Synchronize report numbers with the selected run; record source/result hashes."""
import csv
import hashlib
import json
import re
from pathlib import Path

base=Path(__file__).resolve().parent
rows=list(csv.DictReader((base/'results/comparison.csv').open(encoding='utf-8')))
selected={(int(r['q']),r['method']):r for r in rows if r['rmax']=='256'}
labels={'rank_serial':'逐次秩树','rank_batch':'H1 批量秩树','dense':'紧凑数组'}
table=['| q | 方法 | 元数据访问 | 全部逻辑访问 | 本地中位时间/ms | 总通信/MiB |',
       '|---:|---|---:|---:|---:|---:|']
for q in (16,64,256):
    for method,label in labels.items():
        r=selected[q,method]
        mib=(float(r['download_mean'])+float(r['upload_mean']))/2**20
        table.append(f"| {q} | {label} | {r['metadata_accesses']} | {r['total_accesses']} | {float(r['median_ms']):.2f} | {mib:.3f} |")
path=base/'机制实现与强基线比较报告.md'
text=path.read_text(encoding='utf-8')
text,n=re.subn(r'\| q \| 方法 \|.*?(?=\n\nH1 相对)', '\n'.join(table),text,flags=re.S)
assert n==1
ratios=[float(selected[q,'rank_batch']['median_ms'])/float(selected[q,'dense']['median_ms']) for q in (16,64,256)]
text,n=re.subn(r'时间分别约为紧凑数组的 .*? 倍',
              '时间分别约为紧凑数组的 '+ '、'.join(f'{x:.2f}' for x in ratios)+' 倍',text)
assert n==1
peaks=[int(r['peak_stash_payload_bytes'])/1024 for r in rows]
text,n=re.subn(r'本轮查询暂存 stash 峰值按记录负载计约 .*? KiB。',
              f'本轮查询暂存 stash 峰值按记录负载计约 {min(peaks):.1f}–{max(peaks):.1f} KiB。',text)
assert n==1
path.write_text(text,encoding='utf-8')
files=[base/x for x in ('auth_oram.py','mechanism.py','test_stage3.py','benchmark.py')]
files+=list((base/'results').glob('*.csv'))
manifest={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(base/'results/source_result_hashes.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('\n'.join(table))
