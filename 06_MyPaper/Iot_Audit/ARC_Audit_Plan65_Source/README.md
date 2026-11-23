# Plan65 实施与复现入口

WSL 项目：`/home/zsw/codes/Paper/Exp/Iot_Audit_MY`。

本轮冻结实验：`results/route_a_utility_plan65/pilot_20261022_v1`。新窗口准备结果：`results/route_a_utility_plan65/data_preparation_20261022_v1`。旧 Plan63、Plan64 均保留。

主执行入口是 `run65.py`，冻结新实验使用 `freeze65.py --name 新名称`。从旧版复制的 `run64.py`、`experiment.py`、旧 freezer 仅作为依赖和历史兼容文件保留，不应作为本轮入口。

- `joint_moves65.py`：覆盖扩展、扩展＋迁移、扩展＋交换、单独布局交换。单缺失页代价仅用于候选排序，最终仍使用实际多故障成本和精确风险检查。
- `scenarios65.py`：三个故障模型的配对生成，以及 512 KiB 成功转失败、边界余量、共同成功额外字节和四折约束。
- `planner65.py`：两轮搜索；独立校验不通过时回退；保留仅扩展与无经验门槛对照。
- `engine65.py`：WSL 中的新执行框架，保留真实解码、规范真值核对、总字节预算和独占回执。
- `run65.py`：多窗口、多故障模型、多种子正式执行。
- `crosscheck65.py`：另一实现对最终布局全记录精确风险逐整数复核。
- `sensitivity65.py`：固定故障数的完整精确检查，以及包含全部未计算尾概率的 Bernoulli 上下界。后者不把截断尾部当作零。
- `analyze65.py`：逐回执流式审计、实际预算检查、分模型配对区间和新窗口稳定性判定。

已冻结布局的续跑命令示例：

```bash
P=/home/zsw/codes/Paper/Exp/Iot_Audit_MY
R=$P/results/route_a_utility_plan65/pilot_20261022_v1
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  "$P/.venv-plan16/bin/python" -B \
  "$R/runtime/sandbox/route_a_utility_plan65/run65.py" \
  --root "$R" --day train1_2020-07-12T12
```

重复执行会检查并跳过已完成回执，不覆盖它们；异常留下的无回执文件必须先核查，程序不会静默覆盖。正式结果中的主程序来源以 `runtime/FROZEN_RUNTIME.json` 为准，执行／分析扩展各有独立哈希清单。

新窗口使用冻结的同一规划规则，但在各自归档上建立依赖图、使用独立的训练与校验样本；这属于新窗口上的自适应分配验证，不是把旧窗口布局直接搬过去。所有测试目标排除该窗口的训练和校验目标。
