# Plan61：原始文献、候选机制的创新边界与补证据要求

检索与阅读日期：2026-10-21。本文只用作者、机构、出版社或会议官方来源；明确区分全文核对与仅官方摘要核对。不以搜索未命中等同“首次”。本文配合 [ARC_Audit_Plan61_Full_Paper_Pipeline_20261021.md](ARC_Audit_Plan61_Full_Paper_Pipeline_20261021.md)，不修改主稿或既有参考文献库。

## 写作提纲与结论

相关工作宜按问题而非算法名罗列：多对象操作可用性 → 共享/去重数据的保护 → 压缩编码数据的选择性查询 → 自适应编码与修复调度 → 本文的认证边界。

**可以继续研发的主线是：以完整记录依赖为效用单位，把部分覆盖、每条带冗余强度和实际认证侧车成本放进同一规划问题，并将规划结果接入保持认证语义的选择性恢复。** 这仍是候选系统贡献，不是已确立的原创算法。改变 RS 参数、使用 Jaccard、缓存共享页或先取 parity，单独都不足以支撑新颖性。

## 1. 最接近工作的实际机制

### 1.1 MOAT：多对象操作的可用性早已是独立问题

Haifeng Yu, Phillip B. Gibbons, Suman Nath. **Availability of Multi-Object Operations.** NSDI 2006.

已核对官方全文：研究一次操作需要多个对象时，单对象的高可用性不能直接转为操作可用性。副本/片段放在哪些机器、对象失效如何相关，会改变整个操作成功率；分组与随机放置的优劣还取决于操作允许缺失的程度。其 GroupDHT 和布局分析处理对象—机器映射，并非本文的密文页编码分组。

因此，“记录需要所有依赖”“共访问对象应一起考虑”“布局相关性影响可用性”不是新问题。ARC 的潜在区别是预算下对压缩依赖闭包作部分保护，并把所选方案接入有认证语义的恢复；需要验证这个区别带来实际技术问题与解法。

原始来源：[USENIX 论文页](https://www.usenix.org/conference/nsdi-06/presentation/availability-multi-object-operations)、[全文 HTML](https://www.usenix.org/legacy/event/nsdi06/tech/yu/yu_html/)、[论文 PDF](https://www.usenix.org/events/nsdi06/tech/yu/yu.pdf)。

### 1.2 PFP：文件语义、共享块与跨文件恢复已有直接先例

Suzhen Wu, Huagao Luan, Bo Mao, Hong Jiang, Gen Niu, Hui Rao, Fang Yu, Jindong Zhou. **Improving Reliability of Deduplication-based Storage Systems with Per-File Parity.** SRDS 2018, pp. 171–180. DOI: 10.1109/SRDS.2018.00028.

本次机制核对使用作者托管的会议全文：在去重前为每个文件生成 XOR parity；共享数据块仍全局去重，parity 保留文件语义。全局指纹/引用关系和保护表使文件内恢复不足时能够借其他引用文件进行迭代恢复。文件完整性与共享块保护之间的关系因此不是本文首次提出。

期刊版准确书目为：Suzhen Wu, Bo Mao, Hong Jiang, Huagao Luan, Jindong Zhou. **PFP: Improving the Reliability of Deduplication-Based Storage Systems with Per-File Parity.** IEEE TPDS 30(9):2117–2129, 2019. DOI: 10.1109/TPDS.2019.2898942。已由作者实验室书目核对，但本次未获取期刊版全文；不将会议版阅读说成逐项核验了期刊版所有增补。

原始来源：[作者托管会议 PDF](https://ranger.uta.edu/~jiang/publication/Conferences/2018/2018-SRDS-Improving%20Reliability%20of%20Deduplication-based%20Storage%20Systems%20with%20Per-File%20Parity.pdf)、[作者实验室出版记录](https://astl.xmu.edu.cn/Publications.htm)。

### 1.3 TREAT：压缩、编码和选择性查询已被联合设计

Francesco Taurone, Marcell Fehér, Márton Sipos, Daniel E. Lucani. **TREAT—Two wRongs makE A righT: Efficient Distributed Storage and Queries of IoT Datasets with Erasure Coding and Compression.** DEBS 2024, pp. 147–158. DOI: 10.1145/3629104.3666039.

已核对机构提供的发表版全文：系统使用 GreedyGD 的 base/deviation 与 BaseID，实现选择性数据访问；把数据置于 RLNC 多云片段中，并通过适合编码后访问的布局减少无用下载。查询谓词可逐步筛选记录并提取所需内容。因此“压缩后仍能选择性访问”“编码与压缩协同”“只读取相关 base”均不能作为 ARC 的独占新颖点。

本文可能强调的不同约束是：完整 AEAD 密文页、可信版本/几何、公开充分闭包与持钥精确闭包的能力差异，以及输出完整规范记录前的认证恢复。TREAT 方法讨论中采用 RLNC 的隐私性质并指出更强认证加密的取舍；不能把它描述为实现了与 ARC 相同的公开聚合审计协议。

原始来源：[Aarhus 官方论文页](https://pure.au.dk/portal/en/publications/treat-two-wrongs-make-a-right-efficient-distributed-storage-and-q/)、[发表版 PDF](https://pure.au.dk/portal/files/427453904/3629104.3666039.pdf)。

### 1.4 HACFS：异构/自适应码率本身已有成熟先例

Mingyuan Xia, Mohit Saxena, Mario Blaum, David A. Pease. **A Tale of Two Erasure Codes in HDFS.** FAST 2015, pp. 213–226.

已核对全文。HACFS 用低恢复成本的 fast code 和节省空间的 compact code 服务不同热度数据，并支持码间转换。其核心是工作负载驱动的编码选择，在 HDFS 中平衡空间和恢复成本。ARC 的静态不可变批次、部分保护和依赖闭包目标不同，但“混用两个/多个编码”不能直接算新颖。

原始来源：[USENIX 论文页](https://www.usenix.org/conference/fast15/technical-sessions/presentation/xia)、[全文 PDF](https://www.usenix.org/system/files/conference/fast15/fast15-paper-xia.pdf)。

### 1.5 PACEMAKER：按失效率调整冗余还要处理转换成本

Saurabh Kadekodi, Francisco Maturana, Suhas Jayaram Subramanya, Juncheng Yang, K. V. Rashmi, Gregory R. Ganger. **PACEMAKER: Avoiding HeART attacks in storage clusters with disk-adaptive redundancy.** OSDI 2020, pp. 369–385.

本次核对官方摘要和书目信息，未逐节审读其全部算法。系统按磁盘失效特征调整冗余，并通过布局与提前、限速转换避免编码迁移造成资源峰值。Plan61 静态已知故障模型下的离线选择不包含在线失效率估计、迁移和资源协调，不能称为已完成“自适应生产集群保护”。

原始来源：[USENIX 论文页](https://www.usenix.org/conference/osdi20/presentation/kadekodi)、[官方 PDF](https://www.usenix.org/system/files/osdi20-kadekodi_0.pdf)。

### 1.6 RepairBoost：修复 DAG 和调度的优化已有直接工作

Shiyao Lin, Guowen Gong, Zhirong Shen, Patrick P. C. Lee, Jiwu Shu. **Boosting Full-Node Repair in Erasure-Coded Storage.** USENIX ATC 2021, pp. 641–655.

已核对全文相关机制。RepairBoost 用 repair DAG 表示辅助节点到目的节点的修复关系，结合发送/接收负载均衡与传输调度提升整节点恢复。它针对网络与多条带修复调度；Plan61 的本地按需请求、认证片选择和记录依赖复用是不同层次。不能把通用“按依赖图调度修复”写成新概念，也不能用当前本地 elapsed 结果宣称网络调度优越。

原始来源：[USENIX 论文页](https://www.usenix.org/conference/atc21/presentation/lin)、[全文 PDF](https://www.usenix.org/system/files/atc21-lin.pdf)。

### 1.7 DRBoost：最近的 degraded-read 工作也覆盖避免过度重建

Xiao Niu, Guangyan Zhang, Zhiyue Li, Sijie Cai. **DRBoost: Boosting Degraded Read Performance in MSR-Coded Storage Clusters.** FAST 2026, pp. 613–629.

已核对官方摘要/书目；本次网页工具未成功打开其较大的 PDF，不能声称完成全文技术比较。官方摘要说明 partial-chunk reconstruction、两种数据复用、便于重建的编码布局和无碎片存储。对 Plan61 的明确提醒是：避免重建未请求内容、利用复用和布局改善 degraded read，均已有近期工作。完整投稿前应补读全文，检查任何“首个按需修复/读取最小化”措辞。

原始来源：[USENIX 论文页](https://www.usenix.org/conference/fast26/presentation/niu)、[官方 PDF](https://www.usenix.org/system/files/fast26-niu.pdf)。

### 1.8 Total Recall 与 Shacham–Waters：术语和安全承诺需要分开

Ranjita Bhagwan, Kiran Tati, Yu-Chung Cheng, Stefan Savage, Geoffrey M. Voelker. **Total Recall: System Support for Automated Availability Management.** NSDI 2004。核对官方全文：其 lazy repair 指推迟后台冗余维护，以可用性风险决定何时修复；与本轮请求内推迟辅助片读取不是同一种策略。论文宜写 request-time verified survivor acquisition 等明确操作，不借名称暗示新颖性。[官方论文页](https://www.usenix.org/conference/nsdi-04/total-recall-system-support-automated-availability-management)、[全文 HTML](https://www.usenix.org/legacy/publications/library/proceedings/nsdi04/tech/full_papers/bhagwan/bhagwan_html/index.html)。

Hovav Shacham, Brent Waters. **Compact Proofs of Retrievability.** Journal of Cryptology 26(3):442–483, 2013。核对作者论文页及其对安全证明的说明；本文未在此次工作中重新审计其完整密码学证明。原工作有 PoR 安全与提取语义；ARC 当前 compact 接口的 selected-set consistency 假设不自动继承该结论。[作者论文页及全文入口](https://hovav.net/ucsd/papers/sw13.html)。

## 2. 哪些只能称 adaptation，哪些可能形成贡献

| Plan61 机制/表述 | 最接近的已有点 | 本轮准确名字与区别 | 不可直接宣称 |
|---|---|---|---|
| 固定 FrequencyD 集合后按共依赖分组 | MOAT 的操作可用性；PFP 的文件语义 | dependency-coaccess grouping heuristic，受不相交条带和真实预算约束 | 原 MOAT/PFP 复现；首次考虑多对象可用性 |
| XOR 高覆盖 | PFP 使用文件内 XOR parity | 同预算的固定码率 XOR 基线；没有跨文件 overlapping parity 和迭代恢复 | PFP 对照已完成；“本方法胜过PFP” |
| 每条带选 k/r 并决定覆盖 | HACFS、PACEMAKER 的码率/冗余选择 | 静态记录效用驱动的 partial-coverage mixed-code allocation 候选 | 混合码本身是新编码；动态故障自适应已实现 |
| public K 与 authorized D | TREAT 的压缩后选择性访问；已有认证数据结构 | 公开能力与解密能力分离，认证几何/引用共同确定接受语义 | 选择性访问或 BaseID 本身新颖 |
| lazy parity-first | 已有按需恢复、数据复用与 degraded read；旧 ARC 已缓存 | 保持成功事件的认证辅助片顺序策略 | 首次懒恢复/首次认证重建/最少网络读取 |
| 精确多项式评分 | 概率组合与编码容错的标准工具 | 给定不相交异构布局的可核验精确记录成功率 | 精确全局优化；新的纠删码理论 |
| A+B | 上述机制组合 | 若有独立机制、可解释交互和强基线增量，可成系统贡献 | 拼接现成模块即满足核心创新 |

PFP 的保护关系允许文件间重叠，成本、恢复机会和状态管理都改变。本轮完整不相交条带是合理的受控模型，但应明确它排除了 PFP 的一个关键机制。18 个固定码型能够排除“只因换了码率”的解释，不能替代对最接近外部方案的机制讨论或后续公平实现。

## 3. 候选 A：完整记录效用驱动的混合保护配置

### 3.1 真正需要解决的问题

每条记录的依赖集合为 D_i，保护方案 L 由互不相交条带 (P_s,k_s,r_s) 构成，其中 |P_s|=k_s，未被选中的原始页没有冗余。页面共用使“多保护一个高频页”的收益取决于其他依赖和它们的编码处境。每增加 parity 又改变故障总体 N，实际元数据成本也依赖方案。

令 N(L)=n+sum_s r_s，m(alpha,L)=ceil(alpha*N(L))。固定 m 从 N 个物理对象中均匀选择丢失对象。以整条记录成功为事件，而非独立页面成功率相乘：

\[
U_\alpha(L)=\frac{1}{R}\sum_{i=1}^{R}\Pr[D_i\subseteq {\cal R}(L,M)].
\]

真实预算约束应包含完整已签名侧车：

\[
4096\sum_s r_s + B_{\rm manifest}(L)+B_{\rm signature}+B_{\rm pin}
\le \lfloor\beta B_{\rm cipher}\rfloor.
\]

核心候选是如何在这个非线性的记录目标下选择覆盖和码强度，并维持低风险可用性限制；不是把 RS(10,8) 换成 RS(18,16)。代码目前采用有限18种几何 k∈{4,8,12,16,24,32}, r∈{1,2,3}，其中 r=1 为 XOR；这个搜索域是工程设定，不是编码创新。

### 3.2 精确评分的推导义务

对一条带内 a 个必需原页，成功条件为“它们全部存活”或“条带总丢失数不超过 r”。把两事件的交集扣除，可得生成函数：

\[
G_{k,r,a}(z)=(1+z)^{k+r-a}
+\sum_{j=1}^{r}\left[\binom{k+r}{j}-\binom{k+r-a}{j}\right]z^j.
\]

令 u_i 为该记录必需却未保护的原页数；每个这样的页必须存活，不能贡献自由丢失项。其余未保护原页可自由丢失，因此

\[
\Pr[\text{record }i\text{ succeeds}\mid m]
=\frac{[z^m](1+z)^{n-\sum_s k_s-u_i}
\prod_s G_{k_s,r_s,|D_i\cap P_s|}(z)}
{\binom{N(L)}m}.
\]

a=0 的条带自然成为全部 k+r 片都不影响该请求的自由项。该推导依赖不相交条带、MDS/XOR 阈值、均匀固定 m、有效认证片视作可信输入。它不包含相关设备故障、网络不可达、损坏的可信根、重叠编码或动态修复过程。

Plan61 MixedEvaluator 用整数 favourable counts 和记录重复次数累加，最后才转浮点；理论描述应保留 exact numerator/denominator 证据。此处是给定方案的精确求值，不说明候选搜索达到最优。若声称近似比、单调性、次模性或最优性，需要另行证明，不能从“每次提议精确评分”推出。

### 3.3 与先前工作的具体区别和强对照

与 MOAT 的机器放置不同，本候选主要改变密文页的预算覆盖与码强度。与 PFP 的文件内外重叠 parity 不同，当前采用不相交整页条带以获得明确预算和精确概率。与 HACFS/PACEMAKER 不同，不以热度或磁盘失效率驱动在线转换；这是静态归档的记录依赖规划。与 TREAT 的查询布局不同，所有读取和重建最终服从已承诺密文/AEAD/完整记录语义。

最低实验要求：

1. 所有允许的固定码型在同预算下各用自己的 native cap；开发选择强基线，再固定新确认对照。旧FD10只作为历史锚点。
2. 相同图信息、相同图构建成本口径、相同搜索/候选预算；将“混合码”与“覆盖更多页”分开解释。至少比较按频率/效益密度的简单混合启发式。
3. 低风险连续 alpha 区间通过候选与基线的联合离散断点检验；不能只取三点。不同 N 对应不同 m，需准确交叉比较有理概率。
4. 小实例穷举或完整可行解枚举展示搜索离最优还有多远；大实例报告候选数量、运行时、缓存/内存和无改进率。
5. 开发窗口上的择优不作为确认性结论。新窗口只在算法、阈值和比较集合封存后打开。

若 A 最后只选出一个固定码型且不优于强固定码，就应报告“码率/覆盖是主要因素”，不能保留混合优化为核心创新。

## 4. 候选 B：有认证约束的依赖分组与辅助片读取

### 4.1 值得验证的机制

请求要完成的是记录的认证依赖闭包。将常共用的页聚在适当条带，可能减少一个请求跨越的修复条带数；读取器可利用已验证缓存和已确认失败信息，按固定策略取得足够可信片。二者都需要在引用发现阶段与数据获取阶段共用同一验证接口。

当前代码的 lazy 分支先使用已验证的缓存原页，再尝试 parity，最后补原页；达到 k 个有效片后解码，并在所有重建原页的承诺检查通过后发布。它仍重建完整条带，并非 DRBoost 式 partial-chunk reconstruction。它没有跨节点并发网络调度，也没有 PFP 式跨文件迭代修复。

### 4.2 必须承认的下界和可能失败的原因

冷缓存下要从 MDS 条带恢复一个缺失的完整原页，当前整片解码器需要 k 个独立有效片。旧 eager 常已达到 k 个有效片，因此 parity-first 不保证字节减少。它可能改变失败探测次数、已有缓存利用、先前失败后重试成本；在不可恢复的条带中，先取 parity 也可能额外花费。所有这些都应保留原始记录。

“repairs”只能统计已确认缺失的原页。lazy 未探测便重建某原页，不代表该原页在故障掩码中缺失；没有额外探测时不能用隐藏真值增加修复计数。模型的已知故障事件只用于独立验证，不能反向进入读取决策。

### 4.3 最小消融

| 对照 | 保持相同 | 主要隔离因素 |
|---|---|---|
| 原布局 eager vs 原布局 lazy | 覆盖、k/r、物理 mask、缓存生命周期、targets | 辅助片顺序本身 |
| 分组布局 eager vs 原布局 eager | 覆盖、k/r、预算、targets/故障耦合 | 分组本身 |
| 分组 lazy vs 分组 eager | 分组布局及其他条件 | 分组之后是否仍有 lazy 增量 |
| A+B vs A 与 B | 同预算和协议 | 组合的额外效用及交互 |

同时报告成功率、所有请求的原始/校验读取字节与尝试数、失败原因、共同成功配对成本、解码CPU和缓存命中。相同布局下 eager/lazy 成功事件原则上应一致；若不同，先检查是否存在实现错误、资源预算或停止规则改变，不能直接当算法收益。

Jaccard/共访问启发式必须明确命名为 adaptation。若只能证明既有启发式的少量节省，应定位辅助工程设计；若要提升为核心，需要更明确的问题、策略与可证明/可验证的独立机制。

## 5. 旧 C1/C2 与新候选怎样形成完整论文

可以保留的系统骨架是：可寻址共享表示 → 认证几何与密文对象 → 公开充分覆盖/持钥精确发现 → 记录依赖规划 → 认证恢复。其价值在约束共同成立，不能靠把各组件的名字串起来认定新颖。

建议候选贡献表述，均须等证据成立后才进入主稿：

- **基础接口贡献：** 定义并实现共享压缩记录在公开和持钥两种能力下的认证依赖接口，给出返回完整记录的条件和可审计成本。现有论文已有这一方向，需明确其组合性质与假设。
- **核心算法候选：** 在实际侧车预算和低风险约束下联合选择不相交条带的覆盖/强度，以完整记录成功率为目标；报告超越强固定码型的可重复增量。
- **辅助流程候选：** 让布局与经过认证的辅助片读取配合，保持相同输出接受条件并减少可测的请求成本；通过拆分消融说明增量来源。

若 A 不成立而 B 成立，应重写主线围绕验证过的恢复过程；若 B 不成立，保留基线读取器。不能先决定要三项创新，再为每个分支挑正面的窗口。

当前 C2 的密码学原语、BLS聚合与AEAD组合不宜单独声称原创密码学方案。若要宣称新PoR，必须补适用的新安全游戏和证明；若系统目标不需要，则明确保持现有条件式安全结论，不扩大任务。

## 6. 投稿前仍缺的关键证据

| 缺口 | 为什么本轮开发筛选不能替代 | 后续最小完成条件 |
|---|---|---|
| 新颖性比较 | 本次检索不是穷尽，DRBoost仅摘要核对，PFP期刊版未逐节核对 | 补读最近相关全文，写逐机制差异，不使用“首次” |
| 外部强基线 | 18码型回答参数解释，未实现PFP重叠保护或TREAT网络查询 | 公平受控 adaptation 或明确适用范围，避免胜过原方法的措辞 |
| 独立泛化 | 六个窗口已用于多轮设计 | 预注册新确认材料、冻结选择，补独立数据来源 |
| 完整系统安全/成本 | 当前恢复筛选不生成公开tags | 最终配置 tag-ready 端到端链路、攻击验证、统一账本 |
| 运行机制解释 | 平均成功率可能只因覆盖增加 | 覆盖、码强度、分组、读取各自消融及相同信息控制 |
| 故障模型外推 | 精确评分只覆盖指定物理对象模型 | 相关/突发故障与元数据故障；明确何处模型失配 |
| 真实服务效率 | 本地读文件不是跨云网络 | 网络/部署实验或适当仿真，分解准备、认证、解码和传输成本 |
| 公开泄露 | 依赖驱动布局本身可能泄漏相关性 | 威胁模型显式包含侧车/访问轨迹，保密性游戏与实现一致 |

## 7. 主张检查清单

- “精确”只修饰指定概率模型下的求值，除非另有搜索最优证明。
- “低风险不退化”说明比较基线、完整 alpha 区间/离散状态、精确概率与容差；不等于每个故障实例保证。
- “可用性提升”给出绝对成功率、百分点差、配对区间和适用窗口，不只给相对百分比。
- “减少恢复读取”区分字节、失败探测、I/O次数、CPU和网络时间；成功样本集合不同要显式处理。
- “端到端安全”列出可信根、构建/密钥前提、认证路径和公开泄露，不用诚实吞吐结果代替安全证据。
- “新颖”限定到经比较验证的机制或系统问题；不把成熟技术的改名算贡献。

按 research-paper-writing 的五项审查：目前主线清楚、实现基础可复用；算法贡献和实验强度仍待开发筛选与新确认；完整性需安全/预算/统计接口补齐；设计合理性依赖保留失败分支及公平强基线。上述建议不保证中科院二区/三区或 CCF B 录用。
