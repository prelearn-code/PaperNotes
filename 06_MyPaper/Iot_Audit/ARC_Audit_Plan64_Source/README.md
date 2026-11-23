# Plan64 实施入口

实际项目：`/home/zsw/codes/Paper/Exp/Iot_Audit_MY`。

Windows 的本目录用于查看新增源码；运行需要 WSL 项目的既有依赖和目录结构。正式实验使用冻结目录 `results/route_a_utility_plan64/pilot_20261022_v1/runtime`，不会修改 Plan63。

- `planner64.py`：两轮风险可行搜索、结构边际候选生成、共同成功路径成本约束、训练 SLA 和四折检查。
- `fast_risk.py`：精确 RS 成功字节直方图；统一计算热／冷预算约束。
- `run64.py`：正式入口；安装新规划器并生成三组固定测试种子。
- `engine64.py`：复用的编码、资格检查、真实恢复、规范真值和续跑执行框架。
- `test_plan64.py`：新风险计算器与旧实现的逐整数计数对照，以及搜索和约束测试。
- `crosscheck64.py`：最终选中布局在全窗口上的独立精确风险复核。
- `analyze64.py`：结果回执审计、配对 bootstrap、跨窗口／种子稳定性分析。

正式运行的命令格式：

```bash
P=/home/zsw/codes/Paper/Exp/Iot_Audit_MY
R=$P/results/route_a_utility_plan64/pilot_20261022_v1
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  "$P/.venv-plan16/bin/python" -B \
  "$R/runtime/sandbox/route_a_utility_plan64/run64.py" \
  --root "$R" --day train1_2020-07-11
```

同一命令会验证并跳过已有回执，不覆盖结果。重新实验必须先用 `freeze64.py --name 新名称` 创建新的冻结目录。不要直接执行复制保留的旧 `experiment.py` 或 `freeze63.py`；Plan64 的入口是 `run64.py` 和 `freeze64.py`。

协议中的 `guard_top`、`a_candidates`、`layer_geometries` 是保留的 Plan63 兼容字段，Plan64 入口不使用它们；实际搜索规模由 `round_sizes=[48,24]` 控制。硬读取域限制为 128 KiB；训练共同成功路径平均额外字节上限为 4 KiB。统计约束与精确低损失概率约束分开记录。
