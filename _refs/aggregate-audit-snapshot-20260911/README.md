# Snapshot: aggregate-audit 复现工作区（2026-09-11）

## 这是什么

`tmp/reproductions/aggregate-audit/` 在 **2026-09-11 20:5x（R-1 执行时）** 的只读快照。

**为什么需要它**：该目录是方向 B「聚合审计信息损失」全部证据的唯一副本（约 6,000 行代码、15 个运行记录、7 份证书），但 `tmp/` 被仓库根 `.gitignore` 第 6 行整体忽略（其注释为"文献中间材料与复现工作区：本地保留，不入库"）。因此该目录**不在版本控制内**，任何误删或失败的批量重跑都会不可逆地销毁证据。

本次不把 60 MB 工作区搬进仓库（那会与 `tmp/` 的设计意图冲突），改为在此存放**归档 + 校验清单**，两者都位于受 git 跟踪的 `_refs/` 下。

## 文件

| 文件 | 内容 |
|---|---|
| `source-and-records.zip` | 714 个文件的完整归档（19.36 MB，已压缩）。含 `REPORT.md`、`TASKS.md`、`README.md`、`environment.md`、`scripts/`、`tests/`、`evidence/`、`certificates/`、`results/` 全部运行记录 |
| `SHA256SUMS.txt` | 714 行，格式 `SHA256<TAB>bytes<TAB>相对路径`，路径相对 `tmp/reproductions/aggregate-audit/` |
| `filelist.txt` | 714 个相对路径（归档条目顺序，与 zip 内条目一一对应） |
| `GIT_HEAD.txt` | 快照时的 git HEAD（`5f27768…`） |
| `core-code-text/` | **纯文本兜底副本**：46 个不可再生的小文件（31 个 `scripts/*.py`、14 个 `tests/*.py`、2 份证书 JSON），已逐个 SHA-256 比对一致。用意是万一 19 MB 的 zip 损坏或不便于阅读，核心代码与证书仍可直接查看 |

**有意排除**：`__pycache__/` 与 `*.pyc`（30 个文件，可重新生成，无证据价值）。源目录快照时共 744 个文件（61.66 MB），归档 714 个。

## 校验状态（已实测）

- 归档条目数 **714**，与清单**同集、无重复、无缺失、无多余**
- 解压回读逐文件比对 SHA-256 与字节数：**714 OK / 0 FAIL**
- `core-code-text/` 46 个文件与源文件 SHA-256 逐一比对：**46 OK / 0 FAIL**

## 如何还原

```powershell
# 在仓库根 D:\study\notes\PaperNotes 下执行
$dst = "_refs/aggregate-audit-snapshot-20260911"
Expand-Archive -LiteralPath "$dst/source-and-records.zip" -DestinationPath tmp/reproductions/aggregate-audit-restored

# 校验（应全部 OK）
foreach ($line in [IO.File]::ReadAllLines("$dst/SHA256SUMS.txt")) {
  $h, $len, $rel = $line -split "`t", 3
  $f = Join-Path "tmp/reproductions/aggregate-audit-restored" $rel
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash -ne $h) { "MISMATCH: $rel" }
}
```

还原后目录名为 `aggregate-audit-restored`；如需恢复原位，把内容移回 `tmp/reproductions/aggregate-audit/`。注意运行器要求目标运行目录**不存在**才能写入，因此还原后的 `results/` 若被复用，重跑前需先删除对应 `<run-id>` 目录。

## 快照时状态（供对照）

- git HEAD：`5f27768`（2026-09-10 "chore: 清理 GitBook 生成的重复目录并统一路径大小写"）
- 测试：116 项全过
- `scripts/analysis_certificate.py`：`{"ok": true, "problems": {}}`（7 案例）
- `scripts/independent_verifier.py`：agreement 五项全 true
- `scripts/audit_run_fingerprints.py`：12 个零漂移记录 + 3 个历史漂移记录

## 后续工作对它的依赖

R-1 之后的 P0-0（IR 语义核心）与 P0-2a（工具 MVP）会修改 `scripts/analysis_certificate.py`，并引入声明式 IR 与规则引擎。**在那些改动落地前，本快照是唯一可回滚的基线。** 改动若破坏了判定规则的可追溯性，可用本归档恢复到本文件「快照时状态」一节所记录的状态。
