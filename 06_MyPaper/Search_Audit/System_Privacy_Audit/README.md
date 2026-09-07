# 覆盖一致关键词审计：初稿与复现

**2026-09-06 新阶段：**[动态合取结果绑定内核](./stage4/核心机制与可行性评估.md)与[实际性能/攻击测试](./stage4/性能与验证报告.md)。已实现认证位图、局部版本与私有聚合审计；当前增量机制等同于采用相同缓存优化的普通组合基线，尚无独立创新优势。隐藏 lookup 与动态 SSE 没有包含在本轮性能数字内。

主文档：[论文中文初稿](./论文中文初稿.md)。研究状态与后续门槛：[审稿自检与待补工作](./审稿自检与待补工作.md)。

**最新研究方向：**[核心创新重构：TDSC/TIFS v2](./核心创新重构_TDSC_TIFS_v2.md)。旧初稿现在作为固定覆盖基线；v2 为新的内核设计，尚未实现完整密码协议。`kernel_feasibility.py` 仅复算新方向的检测合同边界，不能与旧原型性能混为一谈。

**最新检验结果：**[H1 机制实现与强基线比较](./stage3/机制实现与强基线比较报告.md)。已实现 H1 和两类同后端基线，14 项测试通过；紧凑数组基线在全部已测配置中胜过 H1。当前 H1 不再推荐作为 TDSC/TIFS 主创新。详细代码和实际结果在 `stage3/`，尚未完成完整主动隐私协议及 PoR。

此目录独立于原 `核心方案.md`、`paper_cn.md`，不修改原方案。

## 文件

| 文件 | 用途 |
|---|---|
| `prototype.py` | AES-GCM、固定清单、Merkle 多重证明、统一覆盖验证、版本状态机 |
| `test_protocol.py` | 16 项正确性和恶意响应测试 |
| `experiments.py` | 内存密码运算计时、字节计数和合成概率实验 |
| `results/timings.csv` | 12 个配置的原始摘要，包括中位数和范围 |
| `results/detection.csv` | 固定缺失集合检测率与 Wilson 区间 |
| `results/selective_failure.csv` | 两种反馈策略的合成区分实验 |
| `results/alias_resampling.csv` | 每轮重采样别名的独立诊断，不是 DDR-SSE 攻击 |
| `results/cover_cost.csv` | 请求数量的理论覆盖代价 |
| `results/environment.json` | 实验环境和方法 |
| `results/tests.txt` | 当前测试执行记录 |

## 运行

依赖 Python 3.12 与 `cryptography`；本轮实际使用 cryptography 50.0.1。无需联网、密钥文件或外部语料。以下 PowerShell 命令在仓库根目录 `F:\repositories\PaperNotes` 执行：

```powershell
& 'C:\Users\16544\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '06_MyPaper\Search_Audit\System_Privacy_Audit\test_protocol.py'
& 'C:\Users\16544\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '06_MyPaper\Search_Audit\System_Privacy_Audit\experiments.py' '06_MyPaper\Search_Audit\System_Privacy_Audit\results'
```

其他机器可将解释器路径替换为自己的 Python。第二条命令会覆盖该输出目录中的 CSV 与环境文件；保留当前论文数据时，应先新建另一个输出目录并修改最后一个参数。新一轮时间值会变化，论文表格不会自动更新。

工作负载种子只用于可重复的基准和概率实验；协议默认随机性来自 `secrets`，AES nonce 与密钥来自密码学随机源。不要把测试用固定 RNG 用于真实挑战。

## 接口约束

调用顺序为 `Client.build → open_manifest → challenge → respond → verify`。`entries` 必须来自针对可信 `Pin` 验证后的清单，`challenge` 必须由客户端创建并保留。不能把服务器自报的清单根或挑战当成可信输入。

`local_results` 只在客户端筛选关键词；它不访问网络。验证接口故意不接收关键词。生产应用不得随后只对真实结果执行可见重试，却继续宣称相同隐私。

原型仅展示单桶私有审计，不含 SSE 倒排索引、网络序列化服务、全文检索、公开第三方验证、PoR 提取、磁盘持久化或并发控制。`wire_bytes` 是约定格式的计数函数，不是网络抓包结果。
