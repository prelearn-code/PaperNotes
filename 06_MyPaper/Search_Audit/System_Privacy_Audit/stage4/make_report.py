"""Generate human-readable report from actual CSVs; no synthetic timings."""
import csv
import hashlib
import json
import statistics
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / 'results'


def rows(name):
    with (OUT/name).open(encoding='utf-8') as f:
        return list(csv.DictReader(f))


summary = rows('summary.csv')
updates = rows('updates.csv')
tests = (OUT/'tests.txt').read_text(encoding='utf-8')
assert 'OK' in tests and 'FAILED' not in tests
env = json.loads((OUT/'environment.json').read_text(encoding='utf-8'))
text = '''# 核心机制实测报告

日期：2026-09-06。本报告由 make_report.py 从实际 CSV 生成。方案、安全边界和基线解释见 [核心机制与可行性评估](./核心机制与可行性评估.md)。

## 结论

完整性参考内核能够运行。缓存减少重复传输与位图认证，但没有独立于普通组合基线的新算法：缓存组合 B1 就是当前候选，不应再虚构一个被候选击败的 B1。

**本报告不含 SSE、隐藏 lookup、零知识证明、网络延迟、磁盘访问或公开验证性能。**

## 方法

采用真实 SHA-256、AES-256-GCM、HMAC-SHA256 和 p=2^255-19 上的整数域运算。每文件 4 个 512 字节明文块，密文块 528 字节，拆成 18 个域元素；使用合成数据，每个关键词独立以密度 d 出现。

N=1024、4096、16384，d=0.1、0.5，q=64、256，冷启动与缓存两种方式，共 24 个配置。每个配置预热 1 次、记录 5 次，共 120 条计时记录。重复次数少，表格用于可行性筛查，不是稳定的期刊性能结论；原始记录保留每次阶段耗时及极值。

计时采用 perf_counter_ns。总时间包括位图校验/缓存同步、结果数组重建、抽样、元数据多重证明生成和验证、随机系数生成、服务器数据响应和最终验证。challenge_ms 含服务器元数据证明生成，不能将它直接命名为纯客户端时间。进程内传递 Python 对象，无网络序列化；payload_bytes 为指定字段格式估算，不是抓包数据。

不同轮次使用独立安全随机挑战，因此独特样本数量和元数据证明大小不同。两种模式的通信差不能逐行直接解释为纯位图节省；相同挑战时位图节省恰为 3N/8 字节。未使用人为固定的密码学密钥或挑战以得到有利计时。

## N=16384 的实际中位数

| 关键词密度 | 结果数 | q | 模式 | 整轮 ms | 最小–最大 ms | 载荷 KiB |
|---|---:|---:|---|---:|---:|---:|
'''
for r in summary:
    if r['n'] == '16384':
        name = '缓存组合 B1/当前候选' if r['mode'] == 'cached_composition' else '冷启动组合 B0'
        text += f"| {r['density']} | {r['r']} | {r['q']} | {name} | {float(r['total_ms_median']):.3f} | {float(r['total_ms_min']):.3f}–{float(r['total_ms_max']):.3f} | {float(r['payload_bytes_median'])/1024:.2f} |\n"
text += '''
缓存没有呈现跨配置稳定的整轮加速，部分配置还略慢。这与缓存节省的只是较小位图开销、以及短时间测量噪声相符。不能据此声称严格的延迟提升。

640 字节只是数据聚合响应，整轮还有挑战和元数据证明。本配置 N=16384 时相同挑战下，重复位图传输可减少 6 KiB；这属于通用缓存收益。

## 更新与初始化

下表为 6 个数据配置、每种更新 10 次，共各 60 次更新的中位数。缓存更新字段仅计位图缓存同步，不包括未来查询获取新的元数据证明。变化页计数也不含可信状态分发、数据上传或元数据更新通信。

| 更新类型 | 所有者处理 ms | 位图缓存处理 ms | 更新数据标签数 |
|---|---:|---:|---:|
'''
for kind, name, ntags in [('keyword', '单关键词关系', 0), ('content', '单数据块', 1)]:
    rs = [r for r in updates if r['kind'] == kind]
    text += f"| {name} | {statistics.median(float(r['owner_ms']) for r in rs):.4f} | {statistics.median(float(r['cache_ms']) for r in rs):.4f} | {ntags} |\n"
text += '\n| N | 密度 | 初始化 ms | 密文 MiB | 标签 MiB |\n|---:|---:|---:|---:|---:|\n'
for r in rows('setup.csv'):
    text += f"| {r['n']} | {r['density']} | {float(r['setup_ms']):.2f} | {int(r['encrypted_bytes'])/2**20:.2f} | {int(r['tag_bytes'])/2**20:.2f} |\n"
text += '''
初始化时间包含合成索引、树、所有密文与标签的建立。内存列仅是逻辑密文/标签大小，不包含元数据、树节点、缓存、Python 对象或峰值 RSS。客户端仍保留完整管理状态，不能写作常数客户端空间。

## 验证记录

'''
text += '```text\n'+tests.strip()+'\n```\n'
text += '''
攻击测试覆盖密文篡改、错文件替换、缺块、旧聚合响应重用、旧数据/标签冒充新版本、元数据篡改、漏报变化页、错误变化页、回滚、空结果和零样本审计等。它们不是对所有恶意策略的形式化安全证明。

## 实验环境与复现

'''
text += '```json\n'+json.dumps(env, ensure_ascii=False, indent=2)+'\n```\n'
text += '''
在 stage4 目录运行（Python 3.12，cryptography 50.0.1）：

```powershell
python -X utf8 test_kernel.py 2> results/tests.txt
python -X utf8 benchmark.py
python -X utf8 make_report.py
```

benchmark.py 会覆盖本目录 CSV 和环境记录；make_report.py 会同步本文。所有运行均在内存中，不修改 Zotero 或原始方案。

## 论文可行性判断

功能内核可行，当前实测的基础开销可接受；完整隐私机制没有被本轮性能数据验证。与采用相同优化的普通组合基线相比，当前候选没有额外技术优势，因此尚不能据此承诺 TDSC/TIFS 级创新。应保留此实现作为强基线，只有后续新证明机制在相同隐私和检测合同下超越它，才有理由升级为主方案。
'''
(BASE/'性能与验证报告.md').write_text(text, encoding='utf-8')
paths = [BASE/'kernel.py', BASE/'test_kernel.py', BASE/'benchmark.py', BASE/'make_report.py', *sorted(OUT.glob('*.csv')), OUT/'environment.json', OUT/'tests.txt']
(OUT/'hashes.json').write_text(json.dumps({str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, indent=2), encoding='utf-8')
print('report and source/result hashes written')
