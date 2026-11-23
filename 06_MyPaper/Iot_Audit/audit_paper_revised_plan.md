# ARC-Audit 论文逐段、分段内模块与逐句修改计划 (Paper-Polish Revision Plan)

**目标论文**：_ARC-Audit: Dependency-Aware Auditing and Authenticated Record Recovery for Industrial IoT Data_

**润色准则**：严格遵循 `paper-polish` 核心规范——**绝对忠实于作者原意（Stay faithful to the author's meaning）**、**零内容编造（Never fabricate content）**、**默认保守克制润色（Conservative by default）**、**证据强度校准（Calibration）**，并对任何可能触及科学/技术边界的改动显式标注 **【语义确认标记 / Meaning-Check Flag】**。

## 〇、修订依据、逐句执行方式与总体诊断

**本次修订范围**：修订修改计划，不改写 Overleaf 源码，不修改用户提供的 `SKILL.md`。依据为该 skill 与原计划中列出的原句、段落和技术说明。本次没有重新读取完整论文、参考文献原文、补充材料或实验日志，因此不把原计划中的数值、页码、算法行号及文献评价标记为已独立核实。

### 逐句执行规则

1. 对每个原句作出“保留 / 轻改 / 句法调整 / 待语义核实”的判断。逐句检查不等于每句必须改写；短句、被动语态和无生命主语均不能单独构成修改理由。
2. 只修复真实存在的语法、指代、搭配和衔接问题。不为了显得学术而增加抽象词，不为了增加连接词而引入原文没有的因果或转折。
3. 保留结论强度、成立条件、量词、实验范围和指标口径。`may`、`under the tested conditions`、`conditional`、`sufficient` 等限定不得在合并或删重时丢失。
4. 本文既有的技术细节可在必要时重述，但应区分“语言调整”和“从其他段落补入信息”。新增命名、机制、参数、比较或证明前提不能归入纯语言润色。
5. 合并相邻句仅用于明确同一论点，不得删去独立论据。原计划未逐句列出原文的段落，建议稿须在应用时逐句与当前源码对齐；不得把建议稿句数当作原文句数。
6. 标题中的原有句数仅作定位线索，尚未重新清点。以下引用段中新增的“建议句 S1、S2……”是该段建议稿的局部句号，不声称与原文编号一一对应；引用段可去掉编号后连成正文。含多个句子的行内建议必须逐句核对后应用。
7. 公式和公式占位符保持其原有位置；本计划不是可编译 LaTeX。`[Eq. (n)]` 必须保留为定位标记，不能用润色文字替代原公式。算法、图示和统计解释中待核实事项见第九、十节。
8. 对于所有涉及到第一人称的叙述，都修改为类似于 This paper这种叙述，不要使用we our这种。后续有部分未进行修改，可以进行相关的修改。

### 总体判断

原稿已经具备明确的技术术语、实验范围限定和代价说明。润色应保留这些优点，重点处理以下具体问题：

|检查方面|可以修改的情况|应避免的处理|
|---|---|---|
|句间衔接|指代不清、角色切换突兀或确有逻辑关系未表达|统一给短句添加 `However`、`Consequently` 或强行合成长句|
|词语搭配|多层修饰难解、重复用词妨碍理解|把正常的无生命主语或技术术语本身判为语病|
|段落组织|说明性短语可帮助区分直觉、定义和对照|以润色名义重排论证、删去独立解释|
|数值表达|说明 `train1/train2` 的对应顺序，减少同一句中的并列数据|更改数值、统计单位、时间口径或置信区间含义|
|语言强度|让措辞与原文证据和假设一致|新增 `fundamentally`、`seamlessly`、`slashing` 或未经检验的协同效应|

**状态说明**：“保留”及无语义变化的措辞调整可进入语言润色；“待核实”项保留原文，不能混入干净稿。第九节记录已撤回的风险建议与仍需核实的事项，不要求为这些事项暂停其他段落的润色。

## 一、 Title, Abstract & Index Terms 逐句修改计划

### 1. Title（标题）

- **原句**：`ARC-Audit: Dependency-Aware Auditing and Authenticated Record Recovery for Industrial IoT Data`
- **诊断**：标题清晰、克制、易检索，准确涵盖了系统名（ARC-Audit）、两个核心机制（Dependency-Aware Auditing、Authenticated Record Recovery）和应用场景（Industrial IoT Data）。
- **建议**：**无需修改（Keep as is）**。

### 2. Abstract（摘要，共 1 段，12 句）

#### 【段落内部结构拆解】

- **Part 1：背景与核心矛盾（S1–S2）** —— 指出工业物联网（IIoT）共享压缩带来局部编码与共享字典的双重依赖，进而引出审计与恢复中的密文对象选择问题。
- **Part 2：方法总览与核心机制（S3–S7）** —— 提出 ARC-Audit 框架，分别阐述面向公共验证者的充分依赖覆盖、面向授权检索者的精确依赖发现，以及预算受限的密文纠删修复。
- **Part 3：理论分析范围（S8）** —— 概述安全性与可恢复性分析的四个维度。
- **Part 4：实验结果与核心结论（S9–S12）** —— 报告 HAI 数据集上的存储/通信收益、计算开销折中，以及纠删条件下的恢复表现。

#### 【逐句修改方案】

|句号|功能|原句|修改理由|建议句|状态|
|---|---|---|---|---|---|
|S1|背景|Shared compression reduces storage for industrial Internet of Things (IIoT) data but makes record reconstruction depend on both local encodings and shared dictionaries.|原句语法正确；将 storage 明确为存储需求，保留 reduces 和依赖关系。|Shared compression reduces storage requirements for industrial Internet of Things (IIoT) data but makes record reconstruction depend on both local encodings and shared dictionaries.|轻改|
|S2|核心问题|Therefore, auditing and recovery of records require an authenticated selection of the ciphertext objects needed for decoding.|调整并列结构，保留原有因果关系。|Therefore, record auditing and recovery require an authenticated selection of the ciphertext objects needed for decoding.|轻改|
|S3|框架|This paper presents ARC-Audit, a framework that connects public integrity auditing with authenticated record recovery through authenticated recovery closure.|将 closure 作为集合概念使用时补冠词；缩写与正文对齐，不改连接关系。|This paper presents ARC-Audit, a framework that connects public integrity auditing with authenticated record recovery through an authenticated recovery closure (ARC).|术语对齐|
|S4|双角色|The design combines publicly verifiable dependency coverage with exact dependency discovery by an authorized retriever.|角色与机制已明确，无需为增加变化而重写。|The design combines publicly verifiable dependency coverage with exact dependency discovery by an authorized retriever.|保留|
|S5|公共路径|An authenticated layout maps the shared representation to encrypted pages, allowing a public verifier to combine sufficient object sets before aggregate authentication.|原句清楚，combine 表示集合合并；不扩写新的闭包机制。|An authenticated layout maps the shared representation to encrypted pages, allowing a public verifier to combine sufficient object sets before aggregate authentication.|保留|
|S6|恢复路径|The retriever authenticates and decrypts references to identify actual dependencies, then reconstructs complete records from verified ciphertext.|before 明确先后关系；ciphertext 可作不可数名词，无需强制复数。|The retriever authenticates and decrypts references to identify actual dependencies before reconstructing complete records from verified ciphertext.|轻改|
|S7|保护层|Budgeted ciphertext protection supports repair along this retrieval path.|句子虽短，但功能清楚；不在语言润色中额外加入 RS 名称和参数。|Budgeted ciphertext protection supports repair along this retrieval path.|保留|
|S8|分析范围|We analyze representation correctness, dependency coverage, aggregate response authentication, and returned-record authenticity.|原句准确；不额外加入 formally 来改变读者对证明强度的预期。|We analyze representation correctness, dependency coverage, aggregate response authentication, and returned-record authenticity.|保留|
|S9|实验结果|Experiments on two workloads derived from the HAI dataset show that the shared representation reduces cloud storage requirements, while aggregate auditing reduces application-layer audit traffic.|原句已注明数据范围；不添加 substantially。|Experiments on two workloads derived from the HAI dataset show that the shared representation reduces cloud storage requirements, while aggregate auditing reduces application-layer audit traffic.|保留|
|S10|代价|These benefits come with higher construction costs and greater local computation overhead, respectively, compared with the respective baselines.|去掉 respective 的重复，保留 construction costs、local computation 及一一对应关系。|Compared with the corresponding baselines, the storage savings come with higher construction costs, while the communication savings come with greater local computation overhead.|句法调整|
|S11|恢复结果|Exact dependency selection reduces retrieval overhead and improves record recovery success rates under the tested erasure conditions.|保留 overhead 的范围及 tested 条件，不将其缩窄为 latency。|Exact dependency selection reduces retrieval overhead and improves record recovery success rates under the tested erasure conditions.|保留|
|S12|总结|The recovery results further show that recovery success depends jointly on protection allocation and request-specific dependencies.|删除相邻的 recovery 重复；保留 show 和 success，不新增协同或普遍性结论。|These results further show that recovery success depends jointly on protection allocation and request-specific dependencies.|轻改|

#### 【摘要建议成稿】

> **建议句 S1**　Shared compression reduces storage requirements for industrial Internet of Things (IIoT) data but makes record reconstruction depend on both local encodings and shared dictionaries.
> 
> **建议句 S2**　Therefore, record auditing and recovery require an authenticated selection of the ciphertext objects needed for decoding.
> 
> **建议句 S3**　This paper presents ARC-Audit, a framework that connects public integrity auditing with authenticated record recovery through an authenticated recovery closure (ARC).
> 
> **建议句 S4**　The design combines publicly verifiable dependency coverage with exact dependency discovery by an authorized retriever.
> 
> **建议句 S5**　An authenticated layout maps the shared representation to encrypted pages, allowing a public verifier to combine sufficient object sets before aggregate authentication.
> 
> **建议句 S6**　The retriever authenticates and decrypts references to identify actual dependencies before reconstructing complete records from verified ciphertext.
> 
> **建议句 S7**　Budgeted ciphertext protection supports repair along this retrieval path.
> 
> **建议句 S8**　We analyze representation correctness, dependency coverage, aggregate response authentication, and returned-record authenticity.
> 
> **建议句 S9**　Experiments on two workloads derived from the HAI dataset show that the shared representation reduces cloud storage requirements, while aggregate auditing reduces application-layer audit traffic.
> 
> **建议句 S10**　Compared with the corresponding baselines, the storage savings come with higher construction costs, while the communication savings come with greater local computation overhead.
> 
> **建议句 S11**　Exact dependency selection reduces retrieval overhead and improves record recovery success rates under the tested erasure conditions.
> 
> **建议句 S12**　These results further show that recovery success depends jointly on protection allocation and request-specific dependencies.

### 3. Index Terms（关键词）

原计划未逐项转录关键词。执行时核对当前源码中的关键词与正文术语，默认保留；不凭本计划新增关键词。

## 二、 Section I: INTRODUCTION 逐段逐句修改计划

### 第 1 段（共 4 句）：研究背景——IIoT 外包存储中的共享压缩与访问粒度变化

#### 【段落内部结构拆解】

- **Part 1：领域大背景（S1）** —— 外包 IIoT 数据需要完整性验证与可靠记录重建。
- **Part 2：共享压缩技术现状（S2）** —— 广义去重（GD）与相似性去重利用跨字段与跨记录冗余。
- **Part 3：引发的核心变化（S3–S4）** —— 共享改变了访问基本单元，单条记录重建依赖多个本地与共享对象，且都必须纳入认证检索路径。

#### 【逐句修改方案】

- **S1**
    - **原句**：`Outsourced industrial Internet of Things (IIoT) data require integrity verification and reliable reconstruction of requested records.`
    - **诊断**：原句清楚，可保留。不要把 integrity verification 自动缩窄为 public integrity verification。
    - **建议**：`Outsourced industrial Internet of Things (IIoT) data require integrity verification and reliable reconstruction of requested records.`
- **S2**
    - **原句**：`Shared compression exploits repeated structure across sensor fields and records: generalized deduplication (GD) stores shared bases with record-specific references and deviations [1], while secure similarity-based deduplication supports outsourced IIoT management [2].`
    - **诊断**：原句已清楚说明共享压缩利用何种冗余，无需补写动机或推断两项被引工作的技术继承关系。
    - **建议**：`Shared compression exploits repeated structure across sensor fields and records: generalized deduplication (GD) stores shared bases with record-specific references and deviations [1], while secure similarity-based deduplication supports outsourced IIoT management [2].`
- **S3 & S4**
    - **原句**：`This sharing changes the unit of access. Reconstructing one record can require several local and shared objects, all of which must be covered by its authenticated retrieval path.`
    - **诊断**：S3 概括、S4 展开，可分别保留，也可用冒号连接。此处选择保留两句以便逐句核对，不添加程度词。
    - **建议**：`This sharing changes the unit of access. Reconstructing one record can require several local and shared objects, all of which must be covered by its authenticated retrieval path.`

#### 【第 1 段润色成稿】

> **建议句 S1**　Outsourced industrial Internet of Things (IIoT) data require integrity verification and reliable reconstruction of requested records.
> 
> **建议句 S2**　Shared compression exploits repeated structure across sensor fields and records: generalized deduplication (GD) stores shared bases with record-specific references and deviations [1], while secure similarity-based deduplication supports outsourced IIoT management [2].
> 
> **建议句 S3**　This sharing changes the unit of access.
> 
> **建议句 S4**　Reconstructing one record can require several local and shared objects, all of which must be covered by its authenticated retrieval path.

### 第 2 段（共 4 句）：核心洞见——公开可验证充分覆盖 vs. 授权精确解码依赖

#### 【段落内部结构拆解】

- **Part 1：核心矛盾声明（S1）** —— 共享依赖导致“公开充分覆盖”与“实际解码需求”不一致。
- **Part 2：机理阐述与具体实例（S2–S3）** —— 在本文的公共闭包构造中，公开覆盖包含完整的相关字典；未使用的字典页丢失会阻碍公开字典覆盖，但并不妨碍单条记录解码。
- **Part 3：设计动机导出（S4）** —— 由此引出同时支持“公开充分覆盖验证”与“授权精确依赖发现”的依赖模型。

#### 【逐句修改方案】

- **S1**
    - **原句**：`Shared dependencies make sufficient coverage differ from actual decoding requirements.`
    - **诊断**：原表达语法正确；可将 sufficient coverage 的角色明确为 public coverage，保持差异本身的含义。
    - **建议**：`With shared dependencies, public sufficient coverage can differ from actual decoding requirements.`
- **S2**
    - **原句**：`When references are encrypted, publicly verifiable coverage may include shared dictionary objects that a record does not actually require.`
    - **诊断**：保留 When 与 may；不把条件描述改成对所有加密存储方案的必然性断言。
    - **建议**：`When references are encrypted, publicly verifiable coverage may include shared dictionary objects that a record does not actually require.`
- **S3**
    - **原句**：`For example, a record may reference only part of a dictionary, so the unavailability of an unused dictionary page can prevent complete dictionary coverage without preventing record reconstruction.`
    - **诊断**：可避免 prevent 重复，同时保留 only part、may 与 can，不将例子缩窄为 single entry。
    - **建议**：`For example, a record may reference only part of a dictionary, so an unavailable dictionary page that it does not use can prevent complete dictionary coverage without blocking record reconstruction.`
- **S4**
    - **原句**：`This distinction motivates a dependency model that supports both public verification of sufficient coverage and authorized discovery of exact decoding dependencies.`
    - **诊断**：原句定义清楚，保留；不新增 dual-view 的机制名称。
    - **建议**：`This distinction motivates a dependency model that supports both public verification of sufficient coverage and authorized discovery of exact decoding dependencies.`

#### 【第 2 段润色成稿】

> **建议句 S1**　With shared dependencies, public sufficient coverage can differ from actual decoding requirements.
> 
> **建议句 S2**　When references are encrypted, publicly verifiable coverage may include shared dictionary objects that a record does not actually require.
> 
> **建议句 S3**　For example, a record may reference only part of a dictionary, so an unavailable dictionary page that it does not use can prevent complete dictionary coverage without blocking record reconstruction.
> 
> **建议句 S4**　This distinction motivates a dependency model that supports both public verification of sufficient coverage and authorized discovery of exact decoding dependencies.

### 第 3 段（共 4 句）：研究空白（Research Gap）——现有工作的割裂与本文切入点

#### 【段落内部结构拆解】

- **Part 1：现有四类机制综述（S1–S2）** —— 压缩优化、公共存储证明、选择性访问、共享块保护各自只解决局部问题。
- **Part 2：未解决的桥梁问题（S3–S4）** —— 面向记录的审计必须把“对象级认证”连接到“完整解码路径覆盖”，因此对象选择取决于表示布局、认证引用以及各角色可见的信息。

#### 【逐句修改方案】

- **S1 & S2**
    - **原句**：`Existing compression, verification, and protection mechanisms address complementary parts of this problem. Compression optimization selects an economical representation [3]; public storage proofs authenticate declared challenge objects [4]; selective access systems optimize retrieval [5]; and shared-storage protection considers the impact of losing common chunks [6].`
    - **诊断**：并列文献定位已清楚；保留 complementary，不补写 in isolation 或 blast radius。
    - **建议**：`Existing compression, verification, and protection mechanisms address complementary parts of this problem. Compression optimization selects an economical representation [3]; public storage proofs authenticate declared challenge objects [4]; selective access systems optimize retrieval [5]; and shared-storage protection considers the impact of losing common chunks [6].`
- **S3 & S4**
    - **原句**：`Record-oriented auditing must connect authentication of selected objects to coverage of a target record’s complete decoding path. The selection therefore depends on the representation layout, authenticated references, and the information available to each role.`
    - **诊断**：原文是在说明本文所需的连接关系，不必额外加入 recovery 或断言现有层次彼此割裂。
    - **建议**：`Record-oriented auditing must connect authentication of selected objects to coverage of a target record's complete decoding path. Object selection therefore depends on the representation layout, authenticated references, and the information available to each role.`

#### 【第 3 段润色成稿】

> **建议句 S1**　Existing compression, verification, and protection mechanisms address complementary parts of this problem.
> 
> **建议句 S2**　Compression optimization selects an economical representation [3]; public storage proofs authenticate declared challenge objects [4]; selective access systems optimize retrieval [5]; and shared-storage protection considers the impact of losing common chunks [6].
> 
> **建议句 S3**　Record-oriented auditing must connect authentication of selected objects to coverage of a target record's complete decoding path.
> 
> **建议句 S4**　Object selection therefore depends on the representation layout, authenticated references, and the information available to each role.

### 第 4 段（共 5 句）：ARC-Audit 核心方法设计

#### 【段落内部结构拆解】

- **Part 1：核心概念定义（S1）** —— 提出 ARC（认证恢复闭包）。
- **Part 2：三角色协同工作流（S2–S4）** —— 数据拥有者发布认证寻址几何并加密内容；公共验证者利用几何构造充分覆盖并绑定聚合挑战；授权检索者先认证解密引用再按需拉取剩余对象。
- **Part 3：设计小结（S5）** —— 总结两种选择如何将同一记录请求映射到不同权限下的对象集。

#### 【逐句修改方案】

- **S1**
    - **原句**：`ARC-Audit expresses this connection through an authenticated recovery closure (ARC), a set of ciphertext objects sufficient to reconstruct the target records.`
    - **建议**：`ARC-Audit expresses this connection through an authenticated recovery closure (ARC), a set of ciphertext objects sufficient to reconstruct the target records.`
- **S2**
    - **原句**：`The owner publishes authenticated addressing geometry while encrypting the complete decoding content.`
    - **建议**：`The owner publishes authenticated addressing geometry while encrypting the complete decoding content.`
- **S3**
    - **原句**：`A public verifier uses this geometry to cover the relevant dictionaries, combine shared objects, and bind the result to a fresh aggregate challenge.`
    - **建议**：`A public verifier uses this geometry to cover the relevant dictionaries, combine shared objects, and bind the result to a fresh aggregate challenge.`
- **S4**
    - **原句**：`An authorized retriever authenticates and decrypts references to identify the actual dependencies before fetching the remaining objects.`
    - **建议**：`An authorized retriever authenticates and decrypts references to identify the actual dependencies before fetching the remaining objects.`
- **S5**
    - **原句**：`These two selections connect the same record request to different object sets according to the available information.`
    - **建议**：`These two selections map the same record request to different object sets according to the information available to each role.`

#### 【第 4 段润色成稿】

> **建议句 S1**　ARC-Audit expresses this connection through an authenticated recovery closure (ARC), a set of ciphertext objects sufficient to reconstruct the target records.
> 
> **建议句 S2**　The owner publishes authenticated addressing geometry while encrypting the complete decoding content.
> 
> **建议句 S3**　A public verifier uses this geometry to cover the relevant dictionaries, combine shared objects, and bind the result to a fresh aggregate challenge.
> 
> **建议句 S4**　An authorized retriever authenticates and decrypts references to identify the actual dependencies before fetching the remaining objects.
> 
> **建议句 S5**　These two selections map the same record request to different object sets according to the information available to each role.

### 第 5 段（共 3 句）：容错保护层的协同 integration

#### 【段落内部结构拆解】

- **Part 1：纠删修复介入位置（S1）** —— 预算受限的密文保护沿认证检索路径提供修复。
- **Part 2：安全不变量保持（S2）** —— 原始对象与 RS 修复对象在解码前通过完全相同的校验。
- **Part 3：全系统闭环（S3）** —— 共享布局统一了存储表示、审计覆盖与恢复验收。

#### 【逐句修改方案】

- **S1–S3**
    - **原句**：`Budgeted ciphertext protection supplies repairs through this authenticated retrieval path. Original objects and those reconstructed by Reed–Solomon (RS) coding pass the same checks before complete record decoding. The shared layout thus connects storage representation, audit coverage, and recovery acceptance.`
    - **诊断**：保留三句的层次。校验细节已在方法部分说明，此处不新增 single cryptographic boundary 等概括。
    - **建议**：`Budgeted ciphertext protection supplies repairs through this authenticated retrieval path. Original objects and those reconstructed by Reed–Solomon (RS) coding pass the same checks before complete record decoding. The shared layout thus connects storage representation, audit coverage, and recovery acceptance.`

### 第 6 段（贡献列表 Contributions 1–3）与第 7 段（实验总结段）

#### 【段落内部结构拆解】

- **Part 1：贡献列表导语与三项核心贡献（Contribution 1, 2, 3）** —— 分别对应共享加密表示、依赖感知公共审计、带预算保护的精确认证恢复。
- **Part 2：实验评估综述（第 7 段，S1–S4）** —— 概述在两个 HAI 工作负载上的评估维度与三项实验发现。

#### 【逐句修改方案】

- **Contribution 1**
    - **原句**：`1) A dependency-addressable encrypted shared representation. We combine field grouping verified by full-input serialized cost with an authenticated mapping from logical bit spans to ciphertext pages. This mapping connects logical record dependencies to authenticated ciphertext objects while keeping private decoding content encrypted.`
    - **诊断**：`field grouping verified by full-input serialized cost` 中 `verified` 容易与密码学验证（cryptographic verification）混淆（正文用的是 `cost-confirmed`）。建议统一为 `confirmed by full-input serialized byte cost`。
    - **建议**：`1) A dependency-addressable encrypted shared representation. We combine field grouping confirmed by full-input serialized cost with an authenticated mapping from logical bit spans to ciphertext pages. This mapping connects logical record dependencies to authenticated ciphertext objects while keeping private decoding content encrypted.`
- **Contribution 2**
    - **原句**：`2) Dependency-aware public auditing. We define sufficient ciphertext closures from the authenticated layout and combine overlapping objects before aggregate authentication. Public geometry supplies sufficient coverage without decrypting references, and challenge binding connects the target records to the selected objects.`
    - **建议**：`2) Dependency-aware public auditing. We define sufficient ciphertext closures from the authenticated layout and merge overlapping object sets before aggregate authentication. Public geometry supplies sufficient coverage without decrypting references, and challenge binding connects the target records to the selected objects.`
- **Contribution 3**
    - **原句**：`3) Exact authenticated recovery with budgeted protection. We use authenticated references to discover actual dependencies and accept only complete decoded records. A ciphertext RS layer supplies verified repairs within a serialized storage cap.`
    - **建议**：`3) Exact authenticated recovery with budgeted protection. We use authenticated references to discover actual dependencies and accept only complete decoded records. A ciphertext RS layer supplies verified repairs within a serialized storage cap.`
- **第 7 段（S1–S4）**
    - **原句**：`Two HAI workloads evaluate these designs through storage and secure construction, public audit communication and computation, and recovery under erasures. Grouping reduces stored cloud bytes while increasing construction work. Public closure planning saves reference-transfer traffic while covering a wider object set. Exact recovery reduces acquisition and decoding work and improves success in tested cases where unused dictionary objects are unavailable.`
    - **诊断**：无生命主语并非语法错误，但此处 This paper更直接。后三句分别报告独立结果，保留其范围和计算开销口径。
    - **建议**：`This paper evaluates these designs on two HAI workloads in terms of storage and secure construction, public audit communication and computation, and recovery under erasures. Grouping reduces stored cloud bytes while increasing construction work. Public closure planning saves reference-transfer traffic while covering a wider object set. Exact recovery reduces acquisition and decoding work and improves success in tested cases where unused dictionary objects are unavailable.`

## 三、 Section II: RELATED WORK 逐段逐句修改计划

### Subsection II-A: Shared Compression and Selective Access（共 2 段）

#### 第 1 段（共 5 句）：广义去重（GD）与面向分析的压缩表示

- **【段落内部结构拆解】**
    - **Part 1：核心概念引入（S1–S2）** —— 共享压缩如何划分局部编码与公共字典；GD 的基本原理 [1]。
    - **Part 2：近期演进（S3）** —— GreedyGD [3] 与 EntroGD [7] 结合压缩与直接分析。
    - **Part 3：与本文的差异化定位（S4–S5）** —— 上述工作聚焦于压缩率与分析效率，而 ARC-Audit 通过认证跨度与字典几何将其连接到完整性验证。
- **【逐句修改方案】**
    - **S1–S2**：`Shared compression determines how record content is divided between local encodings and common dictionaries. GD reconstructs chunks from shared bases and individual deviations [1].`
        
        → **建议（逐句保留或轻改）**：`Shared compression determines how record content is divided between local encodings and common dictionaries. GD reconstructs chunks from shared bases and individual deviations [1].`
        
    - **S3**：`GreedyGD selects base bits for compression and direct analytics [3], and EntroGD combines analytical summaries with entropy-guided compression [7].`
        
        → **建议**：`GreedyGD selects base bits for compression and direct analytics [3], while EntroGD combines analytical summaries with entropy-guided compression [7].`
        
    - **S4–S5**：`These works optimize the shared representation and its use for analytics. ARC-Audit connects that representation to verification through authenticated record spans and dictionary geometry, enabling ciphertext selection before reading references.`
        
        → **建议**：`These works optimize the shared representation and its use for analytics. ARC-Audit connects that representation to verification through authenticated record spans and dictionary geometry, enabling ciphertext selection before reading references.`
        

#### 第 2 段（共 4 句）：安全去重与分布式物联网选择性检索

- **【段落内部结构拆解】**
    - **Part 1：安全相似性去重（S1–S2）** —— FuzzyDedup [8] 与 IIoT 安全相似性去重 [2]。
    - **Part 2：分布式 IoT 编码与选择性获取（S3）** —— TREAT [5]。
    - **Part 3：本文区别（S4）** —— 分离公开寻址几何与私有解码内容，认证完整记录的依赖关系。
- **【逐句修改方案】**
    - **S1–S2**：`Security and selective access introduce further requirements on this representation. Secure similarity deduplication addresses ownership and confidentiality, including fuzzy message-locked encryption and ownership proofs [8] and IIoT storage management [2].`
        
        → **建议**：`Security and selective access introduce further requirements on this representation. Secure similarity deduplication addresses ownership and confidentiality, including fuzzy message-locked encryption and ownership proofs [8] and IIoT storage management [2].`
        
    - **S3–S4**：`TREAT combines GD, coding, rearrangement, and selective fetching for distributed IoT queries [5]. Our construction separates public addressing geometry from private decoding content and authenticates the dependencies of a complete canonical record.`
        
        → **建议**：`TREAT combines GD, coding, rearrangement, and selective fetching for distributed IoT queries [5]. This paper's(你看一下怎么使用第三人称进行修改，尽量使用This paper进行) construction separates public addressing geometry from private decoding content and authenticates the dependencies of a complete canonical record.`
        

### Subsection II-B: Public Auditing and Retrievability（共 5 段）

#### 第 1 段（共 5 句）：经典 PDP / PoR 框架演进

- **【段落内部结构拆解】**
    - **Part 1：框架定义（S1）** —— 公共存储验证针对被挑战对象提供保证。
    - **Part 2：经典代表工作（S2–S4）** —— PDP [9]、PoR [4], [10], [11]、HAIL [12]、Dynamic PDP [13]。
    - **Part 3：共性局限小结（S5）** —— 这些接口只证明给定认证对象本身的性质（未处理共享压缩记录的依赖映射）。
- **【逐句修改方案】**
    - **S1–S4**：保留引用脉络与原有技术描述，不补入未经核实的机制解释：
        
        `Public storage verification defines guarantees over the objects selected for a challenge. PDP checks outsourced possession [9]; PoR connects challenge responses to recovery through extraction [4], [10]. Bowers et al. develop the PoR framework [11], and HAIL combines integrity checking with distributed redundancy [12]. Dynamic PDP authenticates updates with an authenticated dictionary [13].`
        
    - **S5**：`These interfaces establish properties of their specified authentication objects.`
        
        → **建议（保留原范围）**：`These interfaces establish properties of their specified authentication objects.`
        

#### 第 2 段（共 3 句）：压缩 PDP 与本文的本质区别

- **【段落内部结构拆解】**
    - **Part 1：近期工作介绍（S1）** —— Yang et al. [14] 的 compressed PDP。
    - **Part 2：概念辨析（S2–S3）** —— 区分“对审计认证子本身的压缩”与“对共享压缩数据记录的依赖选择”。
- **【逐句修改方案】**
    - **S1–S3**：`More recently, Yang et al. reduce additional authenticator storage through compressed PDP and use a proof-exchange mechanism with linear communication for decentralized multi-cloud self-auditing [14]. Here, compressed PDP concerns the audit representation and its overhead. ARC-Audit instead studies the dependency selection that connects authentication objects to shared-compressed record reconstruction.`
        
        → **建议**：`More recently, Yang et al. reduce additional authenticator storage through compressed PDP and use a proof-exchange mechanism with linear communication for decentralized multi-cloud self-auditing [14]. Here, compressed PDP concerns the audit representation and its overhead. ARC-Audit instead studies the dependency selection that connects authentication objects to shared-compressed record reconstruction.`
        

#### 第 3 段（共 3 句）：去重存储中的公共审计与隐私保护

- **【段落内部结构拆解】**
    - **Part 1：去重审计结合（S1–S2）** —— [15]–[18] 减少密钥与认证子冗余。
    - **Part 2：加密去重隐私保护（S3–S4）** —— [19], [20] 保护所有权与标签隐私。
- **【逐句修改方案】**
    - **S1–S4**：`Shared-data auditing also reduces redundancy in authentication and supports selective verification. Auditing and deduplication have been combined through storage proofs [15], shared authenticators [16], client-side off-chain deduplication [17], and reduced key and authenticator redundancy [18]. Privacy-preserving designs protect file ownership in encrypted-data deduplication and auditing [19], and protect file-tag and audit-proof privacy while using identity-based broadcast encryption for key management [20]. These designs address privacy and authentication in shared encrypted storage.`
        
        → **建议**：`Shared-data auditing also reduces redundancy in authentication and supports selective verification. Prior schemes combine auditing and deduplication through storage proofs [15], shared authenticators [16], client-side off-chain deduplication [17], and reduced key and authenticator redundancy [18]. Privacy-preserving designs protect file ownership in encrypted-data deduplication and auditing [19], and protect file-tag and audit-proof privacy while using identity-based broadcast encryption for key management [20]. These designs address privacy and authentication in shared encrypted storage.`
        

#### 第 4 段（共 4 句）：细粒度去重检索与可搜索/动态审计

- **【段落内部结构拆解】**
    - **Part 1：细粒度去重检索（S1–S2）** —— Liu et al. [21] 使用重构矩阵与布隆过滤器。
    - **Part 2：可搜索与多副本动态审计（S3）** —— [22]–[24]。
    - **Part 3：本文定位（S4）** —— 显式建立与记录解码的关联。
- **【逐句修改方案】**
    - **S1–S4**：`Fine-grained deduplication also connects auditing with data retrieval. Liu et al. deduplicate ciphertexts and authentication tags within and across users, and use a reconstruction matrix and a Bloom filter to retrieve distributed deduplicated blocks [21]. Searchable auditing with arbitration [22], dynamic mixed auditing [23], and updatable multi-copy authentication [24] address related selective and shared verification settings. ARC-Audit makes the connection to record decoding explicit: authenticated geometry determines public coverage, and authenticated private references determine exact recovery inputs.`
        
        → **建议**：`Fine-grained deduplication also connects auditing with data retrieval. Liu et al. deduplicate ciphertexts and authentication tags within and across users and use a reconstruction matrix and a Bloom filter to retrieve distributed deduplicated blocks [21]. Searchable auditing with arbitration [22], dynamic mixed auditing [23], and updatable multi-copy authentication [24] address related selective and shared verification settings. ARC-Audit makes the connection to record decoding explicit: authenticated geometry determines public coverage, and authenticated private references determine exact recovery inputs.`
        

#### 第 5 段（共 5 句）：认证数据结构（ADS）视角下的双路径对照

- **【段落内部结构拆解】**
    - **Part 1：理论溯源（S1–S2）** —— Goodrich et al. [25] 的认证数据结构思想及其在本文布局/引用映射中的应用。
    - **Part 2：双路径对比（S3–S5）** —— 公开闭包规划 vs. 授权引用发现，决定访问权限与通信代价。
- **【逐句修改方案】**
    - **S1–S5**：`Authenticated data structures bind directory answers to source-authenticated information [25]. We apply this principle to the layout and the reference-to-basis relation. Public closure planning obtains sufficient coverage from the signed geometry. Authorized reference discovery first authenticates and decrypts the referenced positions, then selects a tighter set. This distinction determines both access permissions and communication costs.`
        
        → **建议**：`Authenticated data structures bind directory answers to source-authenticated information [25]. This paper apply this principle to the layout and the reference-to-basis relation. Public closure planning obtains sufficient coverage from the signed geometry. Authorized reference discovery first authenticates and decrypts the referenced positions, then selects a tighter set. This distinction determines both access permissions and communication costs.`
        

### Subsection II-C: Reliability of Shared Storage（共 1 段，6 句）

#### 【段落内部结构拆解】

- **Part 1：共享存储可靠性核心问题（S1–S3）** —— 共享块丢失具有放大效应；基于丢失影响的复制 [6] 与去重纠删码分析 [26]。
- **Part 2：系统级融合方案（S4–S5）** —— CDStore [27]、PFP [28]、RepEC+ [29]。
- **Part 3：本文设计边界与实验控制变量（S6–S7）** —— 采用标准密文级 RS 编码 [30]，固定编码参数与 10% 存储预算上限，考察保护分配策略与精确/保守依赖选择的联合效应。

#### 【逐句修改方案】

- **原段（S1–S7）**：`Shared-storage protection must account for the records that depend on each protected object. Shared-chunk loss affects several logical objects. Loss-impact-based replication [6] and analysis of deduplicated, erasure-coded storage [26] establish the importance of this dependency structure. At the system level, CDStore combines convergent dispersal with two-stage deduplication to coordinate reliability, security, and storage efficiency across multiple clouds [27]. Per-File Parity combines pre-deduplication parity with intra-/inter-file recovery [28]; RepEC+ combines replication, coding, selection, and cooperative restore [29]. ARC-Audit uses standard RS coding [30] on complete ciphertext objects. Its evaluation holds the code and storage cap fixed while varying page allocation and the dependency set required by authenticated recovery.`
    
- **诊断**：S1 提出保护要求，S2 解释原因，可用 because 衔接；其余句保留原有文献定位和实验控制范围。
    
- **润色成稿**：
    
    > **建议句 S1**　Shared-storage protection must account for the records that depend on each protected object, because shared-chunk loss affects several logical objects.
    > 
    > **建议句 S2**　Loss-impact-based replication [6] and analysis of deduplicated, erasure-coded storage [26] establish the importance of this dependency structure.
    > 
    > **建议句 S3**　At the system level, CDStore combines convergent dispersal with two-stage deduplication to coordinate reliability, security, and storage efficiency across multiple clouds [27].
    > 
    > **建议句 S4**　Per-File Parity combines pre-deduplication parity with intra- and inter-file recovery [28]; RepEC+ combines replication, coding, selection, and cooperative restore [29].
    > 
    > **建议句 S5**　ARC-Audit uses standard RS coding [30] on complete ciphertext objects.
    > 
    > **建议句 S6**　Its evaluation holds the code and storage cap fixed while varying page allocation and the dependency set required by authenticated recovery.
    

## 四、 Section III: SYSTEM MODEL AND PROBLEM FORMULATION 逐段逐句修改计划

### Subsection III-A: Roles and Trusted State（共 3 段）

#### 第 1 段（共 6 句）：批次（Batch）定义、数据拥有者（Owner）与云服务商（CSP）职责

- **【段落内部结构拆解】**
    
    - **Part 1：核心数据单元定义（S1）** —— 定义 batch 为独立配置、编码和认证的数据单元。
    - **Part 2：Owner 与 CSP 职责划分（S2–S4）** —— Owner 编码、密封密文页、生成审计标签、签名清单并保留私有状态；CSP 存储密文、标签、公共参数、签名布局与可选纠删 sidecar。
    - **Part 3：对象标识与快照（Snapshot）概念（S5–S6）** —— 对象标识由 `(batch_id, page_index)` 组成；快照为签名清单所承诺的不可变编码状态。
- **【逐句修改方案】**
    
    - **S1**：`A batch is a data unit configured, encoded, and authenticated independently.` → `In ARC-Audit, a batch is the fundamental data unit that is configured, encoded, and authenticated independently.`
    - **S2–S3**：`The owner encodes each data batch and seals it into immutable ciphertext objects, generates audit tags, and signs its manifest. The owner retains batch-scoped base and private encoding state.` → `For each batch, the data owner encodes the input records, seals them into immutable ciphertext objects, generates public audit tags, and signs a batch manifest while retaining the batch-scoped base catalog and private encoding state locally.`
    - **S4**：`The cloud service provider (CSP) stores ciphertext objects, audit tags, public parameters, the signed layout, and any deployed protection sidecar.` → `The cloud service provider (CSP) stores the resulting ciphertext objects, audit tags, public parameters, signed layout, and any deployed protection sidecar.`
    - **S5–S6**：`Object identity includes a batch identifier and a page index. A snapshot is the immutable encoded state committed by that batch’s signed manifest.` → `Each ciphertext object is uniquely identified by a batch identifier paired with a local page index, and a snapshot denotes the immutable encoded state committed by that batch's signed manifest.`
- **【第 1 段润色成稿】**
    
    > **建议句 S1**　In ARC-Audit, a batch is the fundamental data unit that is configured, encoded, and authenticated independently.
    > 
    > **建议句 S2**　For each batch, the data owner encodes the input records, seals them into immutable ciphertext objects, generates public audit tags, and signs a batch manifest while retaining the batch-scoped base catalog and private encoding state locally.
    > 
    > **建议句 S3**　The cloud service provider (CSP) stores the resulting ciphertext objects, audit tags, public parameters, signed layout, and any deployed protection sidecar.
    > 
    > **建议句 S4**　Each ciphertext object is uniquely identified by a batch identifier paired with a local page index, and a snapshot denotes the immutable encoded state committed by that batch's signed manifest.
    

#### 第 2 段（共 3 句）：公共验证者（Public Verifier）与授权检索者（Authorized Retriever）

- **【段落内部结构拆解】**
    - **Part 1：Public Verifier 的信任锚与能力（S1–S2）** —— 持有验证公钥与目标清单摘要（trusted pins），在发起挑战前先认证布局和审计参数。
    - **Part 2：Authorized Retriever 的扩展能力（S3）** —— 额外持有批次解密密钥，通过认证后的云端响应恢复完整记录。
- **【逐句修改方案】**
    - **S1–S2**：`The public verifier holds the owner verification key and intended manifest digest as trusted pins. It authenticates the public layout and audit parameters before constructing challenges.` → `The public verifier holds the owner's verification public key and the target manifest digest as trusted cryptographic pins, using them to authenticate the public layout and audit parameters prior to constructing audit challenges.`
    - **S3**：`The authorized retriever additionally holds the batch decryption capability and recovers records through authenticated cloud replies.` → `In contrast, the authorized retriever additionally possesses the batch decryption key and reconstructs target records from authenticated cloud replies.`

#### 第 3 段（共 4 句）：签名清单绑定内容、客户端状态扩展性与跨批次请求处理

- **【段落内部结构拆解】**
    - **Part 1：清单绑定范围与状态代价（S1–S2）** —— 清单绑定批次、布局、密文对象标识/长度/摘要、协议与审计参数；客户端保留完整认证清单，其状态随对象数线性增长。
    - **Part 2：密钥隔离与跨批次请求切分（S3–S4）** —— 加密、清单签名、审计标签使用独立密钥材料；跨批次请求按不可变批次独立切分处理。
- **【逐句修改方案】**
    - **S1–S2**：`A signed manifest binds the batch, public layout, cipher-object identities, lengths and digests, protocol, and audit parameters. Clients retain the complete authenticated manifest; its state grows with object count.` → `Specifically, each signed manifest cryptographically binds the batch identifier, public layout, ciphertext object descriptors (identities, valid lengths, and digests), protocol identifier, and audit parameters. Because clients retain the complete authenticated manifest, client-side metadata scales linearly with the number of ciphertext objects.`
        
        _(术语说明：建议将 `cipher-object` 统一为 `ciphertext object`。尚未核对当前源码，不能断言这是跨行提取残留。)_
        
    - **S3–S4**：`Encryption, manifest signing, and audit tagging use separate secret material. Requests spanning batches are partitioned by immutable batch, each with its corresponding pins and cryptographic context.` → `Furthermore, symmetric encryption, manifest signing, and audit tag generation use strictly separate secret material, and requests spanning multiple batches are partitioned by immutable batch under their respective pins and cryptographic contexts.`
        

### Subsection III-B: Threat Model and Security Goals（共 3 段）

#### 第 1 段（共 4 句）：敌手能力（CSP）与诚实方假设

- **【段落内部结构拆解】**
    - **Part 1：不受信任的 CSP 攻击面（S1）** —— 丢弃对象、篡改密文、替换元数据/标签、重放旧快照或历史响应。
    - **Part 2：诚实参与方与密码学基石（S2–S4）** —— Owner 诚实构建，Verifier/Retriever 按协议持真实 pins 与密钥执行；签名不可伪造性与抗碰撞哈希保护认证状态。
- **【逐句修改方案】**
    - **S1–S2**：`The CSP may omit objects, modify ciphertext, substitute metadata or tags, and replay snapshots or responses. The owner constructs encoded data honestly; verifiers and retrievers execute the declared algorithms using authentic pins and provisioned keys.` → `This paper considers an untrusted CSP that may omit stored objects, tamper with ciphertexts, substitute metadata or audit tags, or replay stale snapshots and audit responses. Conversely,asuming the data owner constructs encoded batches that honestly and verifiers and retrievers execute the specified protocols using authentic pins and provisioned keys.`
    - **S3–S4**：`The intended digest identifies the requested immutable version. Signature unforgeability and collision-resistant hash binding protect this authenticated state.` → `The pinned manifest digest uniquely identifies the requested immutable snapshot, while digital signature unforgeability and collision-resistant hashing protect this authenticated state against tampering and replay.`

#### 第 2 段（共 3 句）：公开视图（Public View）泄露边界与机密性定义

- **【段落内部结构拆解】**
    - **Part 1：公开暴露的几何与访问信息（S1）** —— 记录数、密文长度、分组与比特几何、字典基数、被请求的目标与对象。
    - **Part 2：加密保护的私有内容（S2）** —— 私有解码值、常量、时间戳/标签内容、共享基（bases）与偏差（deviations）。
    - **Part 3：形式化机密性口径（S3）** —— 在给定相同公开视图条件下的内容机密性（基于第 V 节 AEAD 与密钥派生假设）。
- **【逐句修改方案】**
    - **S1–S3**：`The public view exposes record counts, ciphertext lengths, group and bit geometry, dictionary cardinalities, and requested targets and objects. Private decoding values, constants, time and label contents, bases, and deviations are encrypted inside the logical container. Content confidentiality is defined for inputs with the same declared public view, under the authenticated encryption with associated data (AEAD) and key-derivation assumptions in Section V.`
        
    - **润色成稿**：
        
        > **建议句 S1**　In our privacy model, the public view intentionally exposes record counts, ciphertext page lengths, group and bit geometry, dictionary cardinalities, and the transcript of requested targets and objects.
        > 
        > **建议句 S2**　All private decoding values—including field constants, timestamps, label contents, dictionary bases, and per-record deviations—remain encrypted inside the logical container.
        > 
        > **建议句 S3**　Accordingly, content confidentiality is defined over inputs sharing an identical declared public view under the key-derivation and authenticated encryption with associated data (AEAD) assumptions detailed in Section V.
        

#### 第 3 段（共 3 句）：五大安全目标与可用性刻画

- **【段落内部结构拆解】**
    - **Part 1：列出五项核心安全性质（S1–S2）** —— 精确表示、公开视图条件下的内容机密性、认证依赖绑定、选定集响应认证、返回记录真实性。
    - **Part 2：恢复可用性边界（S3）** —— 由请求期间可用的已认证原始页与纠删修复分片共同决定。
- **【逐句修改方案】**
    - **S1–S3**：`The security goals are exact representation, content confidentiality conditioned on this public view, authenticated dependency binding, selected-set response authentication, and authenticity of returned records. Section V states the premises and analysis for these goals. Recovery availability is characterized by the authenticated originals and repair shards available during the request.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Overall, ARC-Audit targets five core security properties: (i) exact representation, (ii) content confidentiality conditioned on the public view, (iii) authenticated dependency binding, (iv) selected-set response authentication, and (v) authenticity of returned records, with premises and analysis stated in Section V.
        > 
        > **建议句 S2**　In addition, recovery availability is characterized by the set of authenticated original pages and valid repair shards accessible during a retrieval request.
        

### Subsection III-C: Records and Ciphertext Objects（共 2 段）

#### 第 1 段（共 9 句，含公式 (1)）：逻辑记录到密文页的切分与 AEAD 封装

- **【段落内部结构拆解】**
    - **Part 1：精确恢复的语义标准（S1–S3）** —— 规范记录（canonical record）包含缩放后的过程值、索引/时间戳和标签；精确恢复要求解码值在声明 schema 下完全相等。
    - **Part 2：容器切片与 AEAD 封装公式（S4–S7，含 Eq. 1）** —— 逻辑容器 F 切分为 \le 4068 B 的明文片 F_p，加上 12B nonce 与 16B tag 构成 \le 4096 B 的密文页 C_p。
    - **Part 3：尾页处理与术语约定（S8–S9）** —— 尾页保留实际长度；定义“page”与集合 \mathcal{P}。
- **【逐句修改方案】**
    - **S1–S3**：`The representation connects logical records to the ciphertext pages that carry their decoding inputs. A canonical record contains scaled process values, index and time, and labels. Exact recovery means equality of these values under the declared schema.` → `The representation maps logical records to the ciphertext pages that carry their decoding inputs. A canonical record contains scaled process values, an index and time, and labels. Exact recovery requires equality of these values under the declared schema.`
    - **S4–S9**：`For batch b, let F be the logical encoded container. Split F into plaintext slices Fp of at most P0 = 4068 B. The stored object is [Eq. (1)], where Np is a 12-byte nonce, Ap is associated data, and the AEAD output includes a 16-byte tag. Thus the valid length ℓ(p) = |Fp| + 28 ≤ 4096 B. The object descriptor and associated data bind identity and length; short final slices retain their actual lengths. Hereafter a page denotes this complete ciphertext object; P is the set of its batch-qualified object identities.` → `For a given batch $b$, let $F$ denote the serialized logical container, which is partitioned into contiguous plaintext slices $F_p$ of at most $P_0 = 4068\text{ B}$. Each stored ciphertext object is sealed as [Eq. (1)], where $N_p$ is a 12-byte nonce, $A_p$ denotes the associated data, and the AEAD ciphertext includes a 16-byte authentication tag, yielding a valid object length of $\ell(p) = |F_p| + 28 \le 4096\text{ B}$. Both the public object descriptor and $A_p$ bind the object's identity and exact byte length so that a short trailing slice retains its true length without physical padding. Hereafter, we refer to each complete ciphertext object $C_p$ as a *page*, and denote the universe of batch-qualified page identities by $\mathcal{P}$.`

#### 第 2 段（共 3 句，含公式 (2)）：逻辑比特区间到物理密文页的映射 \Phi\_{\mathcal{L}}

- **【段落内部结构拆解】**
    - **Part 1：映射公式定义（S1，含 Eq. 2）** —— 逻辑比特区间 [a, a+w) 映射到页下标集合 \Phi\_{\mathcal{L}}(a,w)。
    - **Part 2：边界与跨页性质说明（S2–S3）** —— 空区间映射为空集；跨切片边界时自动包含两侧页；批次号 b 消除不同批次间相同页号的歧义。
- **【逐句修改方案】**
    - **S1–S3**：`For a logical bit interval [a, a + w), the public mapping is [Eq. (2)], with ΦL(a, 0) = ∅. It covers both objects whenever a bit span crosses a slice boundary. Batch identity disambiguates equal local page indices in different batches.` → `For any logical bit interval $[a, a + w)$ of width $w > 0$, the public bit-span mapping is given by [Eq. (2)], with $\Phi_{\mathcal{L}}(a, 0) = \varnothing$. By construction, $\Phi_{\mathcal{L}}(a, w)$ captures all spanned pages whenever a bit interval straddles a slice boundary, and the batch prefix $b$ disambiguates identical local page indices across distinct batches.`

### Subsection III-D: Record Dependencies and Acceptance（共 3 段）

#### 第 1 段（共 5 句，含公式 (3)）：单记录精确依赖集 \mathcal{D}_{\mathcal{L}}(i) 与公共恢复闭包 K_{\mathcal{L}}(i)

- **【段落内部结构拆解】**
    - **Part 1：单记录双集合定义（S1–S3，含 Eq. 3）** —— 固定诚实编码表示与确定性解码器，定义 \mathcal{D}_{\mathcal{L}}(i)（实际解码依赖页）与 K_{\mathcal{L}}(i)（包含完整相关字典的公共闭包），满足 \mathcal{D}_{\mathcal{L}}(i) \subseteq K_{\mathcal{L}}(i) \subseteq \mathcal{P}。
    - **Part 2：两者关系机理阐述（S4–S5）** —— 共享同一解码器与页映射；精确依赖由实际引用值决定，公共闭包则基于认证几何覆盖所有合法引用可能。
- **【逐句修改方案】**
    - **S1–S5**：`Fix an honest representation and its deterministic decoder. The exact dependency set DL(i) contains ciphertext objects covering the structure, reference, local data, labels, and actual dictionary rows used to decode record i. The public recovery closure KL(i) instead includes the complete relevant group dictionaries: [Eq. (3)]. Both sets refer to the same fixed decoder and page mapping. Exact dependencies are selected by the actual references in that representation; the public closure covers all such reference choices using authenticated layout geometry.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Fix an honestly constructed representation and its deterministic decoder.
        > 
        > **建议句 S2**　For a target record i, the exact dependency set \mathcal{D}\_{\mathcal{L}}(i) contains the ciphertext pages covering the structure, references, local data, labels, and actual dictionary rows used for decoding.
        > 
        > **建议句 S3**　The public recovery closure K\_{\mathcal{L}}(i) instead includes the complete relevant group dictionaries: [Eq. (3)].
        > 
        > **建议句 S4**　Both sets refer to the same fixed decoder and page mapping.
        > 
        > **建议句 S5**　Exact dependencies are selected by the actual references in that representation; the public closure covers all such reference choices using authenticated layout geometry.
        

#### 第 2 段（共 8 句，含公式 (4)）：多目标并集 U(T), D(T) 与全有或全无恢复验收准则

- **【段落内部结构拆解】**
    - **Part 1：从单记录扩展到多目标请求集合** T**（S1–S4）** —— 公共审计验证 U(T) = \bigcup\_{i \in T} K\_{\mathcal{L}}(i)，授权恢复两阶段获取 D(T) = \bigcup\_{i \in T} \mathcal{D}\_{\mathcal{L}}(i)。
    - **Part 2：形式化恢复正确性准则（S5–S8，含 Eq. 4）** —— 定义已验证页面集合 \mathcal{A} 与单记录恢复指示函数 \text{Rec}\_i(\mathcal{A})；客户端仅接受全部认证通过且完整解码的结果；保守基线（Conservative）要求获取完整的 U(T)。
- **【逐句修改方案】**
    - **S1–S4**：`For targets T, public auditing authenticates U(T) = ⋃_{i∈T} KL(i). Authorized recovery obtains references through authenticated decryption and constructs D(T) = ⋃_{i∈T} DL(i). Thus K(i) and D(i) describe single-record coverage, while U(T) and D(T) combine the corresponding objects for a request. The public verifier uses U(T); the authorized retriever acquires D(T) in two stages.` → `For targets $T$, public auditing authenticates $U(T) = \bigcup_{i \in T} K_{\mathcal{L}}(i)$. Authorized recovery obtains references through authenticated decryption and constructs $D(T) = \bigcup_{i \in T} \mathcal{D}_{\mathcal{L}}(i)$. The single-record sets describe coverage for each record, while their unions combine objects for a request. The public verifier uses $U(T)$; the authorized retriever acquires $D(T)$ in two stages.`
    - **S5–S8**：`Let A be objects whose committed ciphertext and authenticated plaintext have been obtained, including successful repairs. Record recovery is [Eq. (4)]. Equation (4) defines recovery correctness. The client accepts only authenticated inputs and complete decoding, returning all requested records or failure. The Conservative control requires U(T) before decoding.` → `Let $\mathcal{A}$ denote the set of pages whose committed ciphertexts and authenticated plaintexts have been successfully obtained (either directly or via verified erasure repair). Recovery of record $i$ is defined by the indicator [Eq. (4)], which formalizes strict recovery correctness: the retriever enforces all-or-nothing acceptance over authenticated inputs and complete decoding, returning either all requested canonical records $\{r_i\}_{i \in T}$ or $\perp$. The experimental *Conservative* control requires the full public closure $U(T)$ before decoding.`

#### 第 3 段（共 3 句）：审计验收与恢复验收的统一语义与差异化页面需求

- **【逐句修改方案】**
    - **原段（S1–S3）**：`Audit acceptance requires valid metadata, the verifier’s expected context, and a valid response for every involved batch. Recovery acceptance requires authenticated inputs and successful complete decoding. These operations share dependency semantics while making different demands on available pages.`
        
    - **润色成稿**：
        
        > **建议句 S1**　`In summary, public audit acceptance requires valid signed metadata, consistency with the verifier's challenge context, and a valid aggregate proof for every involved batch, whereas recovery acceptance requires authenticated page plaintexts and complete canonical decoding.`
        > 
        > **建议句 S2**　`Both operations share the same underlying layout semantics while placing different availability demands on stored pages.`
        

## 五、 **Section IV: ARC-AUDIT DESIGN 逐段逐句修改计划**

### Subsection IV-A: Overview（共 2 段）

#### 第 1 段（共 4 句）与第 2 段（共 2 句）：架构总览与路线图

- **【段落内部结构拆解】**
    - **第 1 段（S1–S4）** —— 结合图 1 概述四大环节：构建期（分组编码、页加密、布局认证）、公共依赖规划与聚合审计、授权两阶段精确恢复。
    - **第 2 段（S1–S2）** —— 概述保护层如何通过同一验证接口提供修复，并引出后续各小节。
- **【逐句修改方案】**
    - **第 1 段润色成稿**：
        
        > **建议句 S1**　`ARC-Audit unifies ciphertext selection, audit response authentication, and record reconstruction through an authenticated dependency layout (Fig. 1).`
        > 
        > **建议句 S2**　`During batch construction, the data owner groups and encodes sensor fields, seals the serialized container into addressable ciphertext pages, and signs their layout geometry.`
        > 
        > **建议句 S3**　`During public auditing, dependency planning derives and merges the page closures needed for sufficient coverage, after which aggregate auditing verifies the CSP's linear response to a fresh challenge.`
        > 
        > **建议句 S4**　`During authorized recovery, the retriever discovers exact dictionary dependencies from authenticated references and reconstructs canonical records after verifying and decoding all required inputs.`
        
    - **第 2 段润色成稿**：
        
        > **建议句 S1**　`Complementing these operations, a budgeted Reed–Solomon protection layer supplies verified repairs for missing pages through the same authenticated access interface.`
        > 
        > **建议句 S2**　`The remainder of this section details each design component and its resource accounting.`
        

### Subsection IV-B: Cost-Confirmed Shared Representation（共 5 段 + Proposition 1）

#### 第 1 段（共 3 句）：SDA-GGD 设计目标与命名

- **【逐句修改方案】**
    - **原段**：`Field grouping must reduce encoded size while preserving the locations needed for dependency planning. We denote the field-grouped GD construction by SDA-GGD: sampled gains order candidate merges, and full-input serialized cost determines acceptance. The resulting layout exposes record spans and dictionary ranges so that the verifier can select pages before reading references.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Field grouping must reduce encoded size while preserving the locations needed for dependency planning.
        > 
        > **建议句 S2**　We denote the field-grouped GD construction by SDA-GGD: sampled gains rank candidate merges, and full-input serialized cost determines acceptance.
        > 
        > **建议句 S3**　The resulting layout exposes record spans and dictionary ranges so that the verifier can select pages before reading references.
        

#### 第 2 段（共 5 句）与第 3 段（共 4 句，含公式 (5)）：Encoding and serialized cost

- **【段落内部结构拆解】**
    - **第 2 段（S1–S5）** —— 字段定标、常量提取、非常量字段分组 G（总位宽 L_g、基位宽 k、观测基数量 M_g、偏差位宽 L_g - k、定长基索引 b_g = \lceil \log_2 M_g \rceil）。
    - **第 3 段（S1–S4，含 Eq. 5）** —— 给出 n 条记录下分组 G 的序列化字节开销公式 C(G)、组头开销 C\_{\text{hdr}}(G,k)、RAW 退化开销以及全局容器总开销 C_0 + \sum_G C(G)。
- **【逐句修改方案】**
    - **第 2 段润色成稿**：
        
        > **建议句 S1**　_Encoding and serialized cost._ Under the declared schema, each sensor field is assigned an exact decimal scale and fixed integer bit width.
        > 
        > **建议句 S2**　Constant fields are recorded once in the global header, while nonconstant fields are partitioned into disjoint field groups.
        > 
        > **建议句 S3**　For a group G of total bit width L_g, the encoder selects k base-bit positions; let M_g denote the number of distinct base bit-patterns observed across the batch, while the remaining L_g - k bit positions form each record's local deviation.
        > 
        > **建议句 S4**　Each record stores a fixed-width base identifier (`BaseID`) of b_g = \lceil \log_2 M_g \rceil bits alongside its (L_g - k)-bit deviation, and a group dictionary stores the M_g unique bases.
        
    - **第 3 段润色成稿**：
        
        > **建议句 S1**　Across n records, the byte-aligned serialized cost of a GD group G is [Eq. (5)], where C\_{\text{hdr}}(G, k) = 11 + 2|G| + 2k bytes encodes the group mode, constituent field identifiers, and chosen base-bit positions.
        > 
        > **建议句 S2**　Conversely, encoding G in uncompressed `RAW` mode incurs C\_{\text{hdr}}(G, 0) + \lceil n L_g / 8 \rceil bytes.
        > 
        > **建议句 S3**　Each logical stream—dictionary bases, base identifiers, and deviations—is byte-rounded independently because the streams are serialized into separate contiguous regions.
        > 
        > **建议句 S4**　Summing across all groups yields a total logical container size of C_0 + \sum_G C(G), where C_0 accounts for the fixed schema, constant fields, timestamp and label streams, and global container header.
        

#### 第 4 段（共 6 句）：Within-group configuration

- **【逐句修改方案】**
    - **原段**：`Within-group configuration. The configurator stably sorts local bit positions by increasing empirical binary entropy and tests prefixes of length k = 0, 1, . . . , Lg. It stops when Mg = n. Among feasible candidates it selects the smallest byte-rounded cost, with the earlier prefix winning ties. It selects RAW whenever RAW costs no more than that GD candidate. Merged groups concatenate their field sequences; entropy ties preserve this local bit order. The tested configuration selects among these candidates by serialized cost.`
        
    - **诊断**：可通过明确 configurator 和 RAW 的指代改善流畅度。保留候选范围、停止条件和 tie-breaking，不把局部候选选择表述为全局最优；不因重复而直接删除最后一句。
        
    - **润色成稿**：
        
        > **建议句 S1**　_Within-group configuration._ The configurator stably sorts local bit positions by increasing empirical binary entropy and tests prefixes of length k = 0, 1, \dots, L_g.
        > 
        > **建议句 S2**　It stops when M_g = n.
        > 
        > **建议句 S3**　Among feasible candidates, it selects the smallest byte-rounded cost, with the earlier prefix winning ties.
        > 
        > **建议句 S4**　The configurator selects `RAW` whenever `RAW` costs no more than that GD candidate.
        > 
        > **建议句 S5**　Merged groups concatenate their field sequences, and entropy ties preserve this local bit order.
        > 
        > **建议句 S6**　The tested configuration therefore selects among these candidates by serialized cost.
        

#### 第 5 段（共 12 句，含公式 (6)）与第 6 段（共 2 句）+ Proposition 1：Sample ranking and full-data confirmation

- **【段落内部结构拆解】**
    - **Part 1：初始化与样本增益入队（S1–S5）** —— 每个非常量字段初始化为单元素组；在固定样本集 X_I 上估算合并增益 \widehat{\Delta}，仅正增益入优先队列，并在全量确认前刷新过期版本。
    - **Part 2：全量数据确认准则（S6–S8，含 Eq. 6）** —— 合并前在全量数据 X 上重配置并计算 \Delta\_{\text{full}}，必须同时满足全量总字节正收益（\Delta\_{\text{full}} > 0）与净荷正收益（\Delta_P > 0）。
    - **Part 3：算法 1 符号与辅助函数说明（S9–S14，跨第 5、6 段）** —— 解释 `Config`, C(G;c), C\_{\text{pay}}(G;c), `SampleGain`, 拒绝集 J, 重入队计数器 d_e \le d\_{\max}=8, `TopGain`。
- **【逐句修改方案】**
    - **第 5–6 段逐句建议（保持原段落边界）**：
        
        **作者备注 MC-07**：下列文字只保留现有算法步骤，不解释未变化的候选为何会产生不同增益。重算或重入队的原因仍需核对实现；不能将“早先合并影响候选”写成对非过期候选的解释。
        
        > **建议句 S1**　_Sample ranking and full-data confirmation._ Algorithm 1 initializes \mathcal{G} with one singleton group per nonconstant field and ranks candidate merges using a fixed row sample X_I.
        > 
        > **建议句 S2**　`SampleGain` evaluates \widehat{\Delta} = C_m(G_a) + C_m(G_b) - C_m(G_a \mathbin{|} G_b), where C_m configures and measures a group on X_I and | denotes ordered field concatenation.
        > 
        > **建议句 S3**　Only pairs with positive sampled gain enter the queue.
        > 
        > **建议句 S4**　Stale entries are discarded on extraction, and the sample gain is recomputed for surviving candidates.
        > 
        > **建议句 S5**　The algorithm permits bounded requeueing when the refreshed gain is below `TopGain(Q)`, with d_e counting requeues and d\_{\max}=8.
        > 
        > **建议句 S6**　`TopGain` returns the current head gain, or -\infty for an empty queue.
        > 
        > **建议句 S7**　Before accepting a merge, the encoder configures G_c=G_a\mathbin{|}G_b on the full input via `Config(X, G_c)`, including `RAW` fallback, and computes the full-input gain: [Eq. (6)].
        > 
        > **建议句 S8**　Acceptance requires both \Delta\_{\text{full}}=C(G_a)+C(G_b)-C(G_c;c)>0 and \Delta_P=C\_{\text{pay}}(G_a)+C\_{\text{pay}}(G_b)-C\_{\text{pay}}(G_c;c)>0.
        > 
        > **建议句 S9**　Here, C(G;c) is serialized cost and C\_{\text{pay}}(G;c) is header-excluded payload cost; an omitted configuration denotes the current accepted one.
        > 
        > **建议句 S10**　Rejected versioned pairs are recorded in J to avoid repeated testing.
        > 
        > **建议句 S11**　Supplementary Section S-II gives the version-tracking and tie-breaking rules.
        
    - **Proposition 1 及其证明与后置说明段**：
        
        - **Proposition 1 原文**：`Every accepted merge strictly decreases both the checked logical serialized cost and its payload cost. Starting from g0 active groups, at most g0 − 1 merges are accepted.` → **保持不变（已非常精炼）**。
        - **Proof 原文**：`Algorithm 1 accepts only positive full-input serialized and payload gains. Unchanged groups retain their contributions and the fixed container component is unchanged. Each accepted merge replaces two groups with one. Rejected versioned pairs are recorded, obsolete entries are discarded, and bounded requeue counts ensure termination between merges. Q.E.D.` → **建议微调衔接**：`A merge is accepted only when both $\Delta_{\text{full}} > 0$ and $\Delta_P > 0$. Because unmerged groups and the global container overhead $C_0$ remain invariant during a step, every accepted merge strictly reduces both the total logical container size and total payload bytes while reducing the number of active groups by one (bounding total accepted merges by $g_0 - 1$). Finally, recording rejected versioned pairs in $J$, discarding stale queue entries, and bounding lazy requeues by $d_{\max}$ guarantee finite termination between successive merges. Q.E.D.`
        - **后置说明段（2 句）**：`The measured secure cost in Eq. (13) additionally includes encryption framing, tags and the public manifest. RQ1 evaluates that final cost separately from the grouping objective.` → `Note that the total secure cloud footprint in Eq. (13) additionally includes AEAD framing, public audit tags, and the signed manifest; Section VI-B (RQ1) evaluates this end-to-end sealed footprint alongside the logical grouping gain.`

### Subsection IV-C: Page Encryption and Authenticated Layout（共 3 段）

#### 第 1 段（共 4 句）：公开几何布局 vs. 加密容器切片的信息分离

- **【逐句修改方案】**
    - **原段**：`Page encryption separates the information needed to locate dependencies from the values needed to decode them. The public layout contains stream positions, widths, modes, base-bit positions, dictionary cardinalities, and record counts. The complete logical container holds the private decoding header and values together with encoded records. The geometry supports Eq. (2); numeric constants and private field values remain in encrypted slices.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Page encryption explicitly decouples the structural metadata needed to locate dependencies from the sensitive values needed to decode them.
        > 
        > **建议句 S2**　Specifically, the public layout \mathcal{L} exposes stream bit offsets, field widths, group modes (`GD` or `RAW`), base-bit positions, dictionary cardinalities, and batch record counts.
        > 
        > **建议句 S3**　While this public geometry suffices to evaluate the page mapping \Phi\_{\mathcal{L}} in Eq. (2), the private decoding header, field constants, dictionary bases, and encoded record streams reside exclusively within the encrypted slices of the logical container F.
        

#### 第 2 段（共 6 句）：批次密钥派生、确定性 Nonce 与关联数据（AD）绑定

- **【逐句修改方案】**
    - **原段**：`For each construction the owner samples a fresh 256-bit batch identifier b and a random encryption master secret. HKDF-SHA256 derives kb with salt b and context ARC/ENC/v1 [31]. The nonce is the 96-bit encoding of the local page index. Consequently, page nonces are distinct under the batch key. AES-256-GCM seals each slice using Eq. (1) [32]. Associated data is the canonical encoding of protocol, owner domain, batch, object identity, codec, and plaintext length. These fields are retained in the public descriptor.`
        
    - **润色成稿**：
        
        > **建议句 S1**　For each construction, the owner samples a fresh 256-bit batch identifier b and a random encryption master secret.
        > 
        > **建议句 S2**　HKDF-SHA256 derives k_b using salt b and context `ARC/ENC/v1` [31].
        > 
        > **建议句 S3**　The nonce is the 96-bit encoding of the local page index, so page nonces are distinct under the batch key.
        > 
        > **建议句 S4**　AES-256-GCM seals each slice using Eq. (1) [32].
        > 
        > **建议句 S5**　Associated data is the canonical encoding of the protocol, owner domain, batch, object identity, codec, and plaintext length.
        > 
        > **建议句 S6**　These fields are retained in the public descriptor.
        

#### 第 3 段（共 6 句）：描述符构建、标签绑定与无循环依赖的清单签名顺序

- **【逐句修改方案】**
    - **原段**：`The descriptor additionally records the complete ciphertext length and hash. Audit tag identity binds this descriptor and the public-parameter fingerprint. After creating ciphertext objects and tags, the owner signs a canonical manifest containing their descriptors, public layout, parameters, and tag-file digest with Ed25519. The manifest digest and signing public key form the provisioned pins. This order binds tags to immutable objects and the manifest to completed tags without a circular digest dependency. Algorithm 2 summarizes this construction.`
        
    - **润色成稿**：
        
        > **建议句 S1**　The descriptor also records the complete ciphertext length and hash.
        > 
        > **建议句 S2**　Audit tag identity binds this descriptor and the public-parameter fingerprint.
        > 
        > **建议句 S3**　After creating the ciphertext objects and tags, the owner signs a canonical manifest containing their descriptors, public layout, parameters, and tag-file digest using Ed25519.
        > 
        > **建议句 S4**　The manifest digest and signing public key form the provisioned pins.
        > 
        > **建议句 S5**　This order binds tags to immutable objects and the manifest to completed tags without a circular digest dependency.
        > 
        > **建议句 S6**　Algorithm 2 summarizes the construction.
        

### Subsection IV-D: Authenticated Recovery Closure（共 4 段）

#### 第 1 段（共 6 句，含公式 (7)）与第 2 段（共 4 句）：单记录公共恢复闭包 K(i) 的形式化构成

- **【段落内部结构拆解】**
    - **第 1 段（S1–S4，含 Eq. 7）** —— 定义私有结构元数据页 S、组 g 内记录 i 的引用跨度页 R_g(i)、偏差/RAW 内容页 V_g(i)、标签页 L(i) 及字典页集合 \mathcal{P}\_g^{\text{dict}}，给出 K(i) 的并集公式 (7)。
    - **第 2 段（S1–S4）** —— 补充说明 `RAW` 组无引用与字典项、S 的具体内容、L(i) 的覆盖范围，以及物理页混装多逻辑流时的包含原则。
- **【逐句修改方案】**
    - **第 1–2 段逐句建议（保留段落边界）**：
        
        > **建议句 S1**　Given a target record set T and the authenticated layout \mathcal{L}, public closure planning computes the sufficient page union U(T) directly from public geometry by including the full dictionary range of every GD group.
        > 
        > **建议句 S2**　Formally, under the bit-span map \Phi\_{\mathcal{L}}, let S denote the pages covering private structural metadata (the internal schema and decoder framing), L(i) the pages covering record i's label bits, and—for each field group g—let R_g(i) denote the pages covering record i's `BaseID` reference span, V_g(i) its deviation or `RAW` value span, and \mathcal{P}\_g^{\text{dict}} all pages intersecting group g's dictionary.
        > 
        > **建议句 S3**　The single-record public recovery closure is defined as [Eq. (7)], where R_g(i) = \mathcal{P}\_g^{\text{dict}} = \varnothing whenever group g is encoded in `RAW` mode.
        > 
        > **建议句 S4**　Because \Phi\_{\mathcal{L}} maps any logical bit interval to all intersecting pages, every component term in Eq. (7) captures all required ciphertext pages even when a boundary page multiplexes bits from adjacent logical streams.
        

#### 第 3 段（共 4 句）：公开构造 K(i) vs. 授权构造 \mathcal{D}(i) 的两阶段操作对比

- **【逐句修改方案】**
    - **原段**：`The verifier constructs K(i) using public geometry. Including each complete group dictionary covers the row selected by any valid BaseID. The authorized alternative authenticates and decrypts S and the reference pages, reads each BaseID at its committed position, checks its range, and maps the referenced dictionary row. Together with S, references, local content, and labels, these rows form D(i).`
        
    - **润色成稿**：
        
        > **建议句 S1**　Whereas a public verifier constructs K(i) solely from \mathcal{L}—relying on \mathcal{P}\_g^{\text{dict}} to cover whichever dictionary row a valid `BaseID` might address—an authorized retriever resolves exact dependencies in two stages.
        > 
        > **建议句 S2**　First, the retriever fetches, authenticates, and decrypts S and the reference pages \bigcup_g R_g(i), extracts each `BaseID` at its committed bit offset, verifies that \text{BaseID} < M_g, and maps only the single referenced dictionary row via \Phi\_{\mathcal{L}}.
        > 
        > **建议句 S3**　Combining those exact dictionary-row pages with S, \bigcup_g R_g(i), \bigcup_g V_g(i), and L(i) yields the exact dependency set \mathcal{D}(i).
        

#### 第 4 段（共 5 句，含公式 (8)）：多目标合并去重收益 B_U vs. B_N 与缓存效应区分

- **【逐句修改方案】**
    - **原段**：`Public requests merge overlaps as U(T) = ⋃_{i∈T} K(i). For ciphertext lengths ℓ(p), the logical bytes read by an object union and separate uncached closures are [Eq. (8)]. A request cache can also reduce separate traversal to the unique object set. We distinguish this read-reuse effect from proof aggregation in the controls. For multiple data batches, targets and unions are computed separately using batch-qualified identities, then combined at the request level.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Across a target set T, public auditing merges overlapping per-record closures into the deduplicated union U(T) = \bigcup\_{i \in T} K(i).
        > 
        > **建议句 S2**　Given page lengths \ell(p), the total ciphertext bytes read under union planning (B_U) versus naive uncached per-record traversal (B_N) are [Eq. (8)].
        > 
        > **建议句 S3**　While maintaining a request-local page cache during separate per-record traversal can similarly eliminate duplicate page reads, proof aggregation further compresses the verification responses across U(T); Section VI-C isolates these two mechanisms experimentally.
        > 
        > **建议句 S4**　When T spans multiple batches, closure unions are computed independently per batch using batch-qualified page identities and combined at the request level.
        

### Subsection IV-E: Fresh Public Aggregate Audit（共 8 段）

#### 第 1 段（共 2 句）与第 2 段（共 3 句）：扇区化（Sectorization）与 BLS12-381 标量域映射

- **【逐句修改方案】**
    - **第 1–2 段润色成稿**：
        
        > **建议句 S1**　Fresh public aggregate auditing authenticates a linear combination of the pages in U(T) while cryptographically binding the target set T, snapshot digest, and selected page set to a fresh verifier challenge.
        > 
        > **建议句 S2**　To support homomorphic aggregation over the BLS12-381 scalar field \mathbb{F}\_q, each complete ciphertext page C_p (of valid length \ell(p) \le 4096\text{ B}) is partitioned into s = 133 little-endian sectors of 31\text{ B} each, with virtual zero padding beyond \ell(p).
        > 
        > **建议句 S3**　Because each 31-byte sector integer satisfies m\_{p,j} < 2^{248} < q, this sectorization injectively covers the entire sealed page—including its nonce N_p, encrypted payload, and AEAD tag—while the signed length \ell(p) governs deterministic tail truncation during retrieval.
        

#### 第 3 段（共 3 句，含公式 (9)）：Shacham–Waters 线性公有可验证标签构造

- **【逐句修改方案】**
    - **原段**：`The owner selects secret x, publishes Y = xg2, and computes tags in G1, with pairing e : G1 × G2 → GT : [Eq. (9)]. Wp binds the complete ciphertext descriptor and parameter fingerprint. The bases uj and descriptor hash H use domain-separated hash-to-curve operations [33]. The construction follows the linear public authentication structure of Shacham–Waters [4].`
        
    - **润色成稿**：
        
        > **建议句 S1**　Following the Shacham–Waters linear public authenticator structure [4] over a bilinear pairing e : \mathbb{G}\_1 \times \mathbb{G}\_2 \to \mathbb{G}\_T, the owner samples a secret key x \in \mathbb{F}\_q^\*, publishes Y = x g_2 \in \mathbb{G}\_2, and computes each page's audit tag \tau_p \in \mathbb{G}\_1 as [Eq. (9)].
        > 
        > **建议句 S2**　Here, W_p canonically binds the complete page descriptor d_p and the public-parameter fingerprint, while both the sector bases {u_j}\_{j=1}^s \subset \mathbb{G}\_1 and the descriptor hash H(W_p) \in \mathbb{G}\_1 are derived via domain-separated hash-to-curve operations [33].
        

#### 第 4 段（共 5 句，含公式 (10)）与第 5 段（共 3 句，含公式 (11)）：挑战生成、聚合响应与配对验证方程

- **【逐句修改方案】**
    - **第 4–5 段润色成稿**：
        
        > **建议句 S1**　For each involved batch (Algorithm 3), the verifier samples a fresh 256-bit nonce and constructs a canonical challenge context binding the pinned snapshot digest, public parameters, batch target subset T_b, sorted closure U_b, request policy, and session identifier.
        > 
        > **建议句 S2**　Nonzero challenge coefficients \nu_p \in \mathbb{F}\_q^\* are derived deterministically by hashing this canonical context alongside each page index p \in U_b and a retry counter (via scalar reduction mod q with zero rejection; see Supplementary Section S-III-B).
        > 
        > **建议句 S3**　Upon receiving the challenge, the CSP reads each unique page C_p (p \in U_b) and returns the aggregate tag \sigma \in \mathbb{G}_1 and sector linear combinations {\mu_j}_{j=1}^s \subset \mathbb{F}\_q: [Eq. (10)].
        > 
        > **建议句 S4**　After validating message framing, context binding, point subgroup membership, scalar ranges, and vector dimensions against its retained local context, the verifier checks the pairing equation: [Eq. (11)].
        > 
        > **建议句 S5**　Public parameter validation excludes identity or invalid curve points, and any parsing or pairing failure causes Algorithm 3 to return `REJECT`.
        

#### 第 6、7、8 段（共 7 句）：固定每批次证明尺寸与对照基线说明

- **【逐句修改方案】**
    - **原第 6–8 段**：
        
        `The aggregate occupies 4310 B per batch for this fixed sectorization. Consequently a request involving bT batches has 4310bT proof bytes, in addition to declarations and challenges.`
        
        `Section VI compares this public interface with authorized reference discovery and public download using their actual application framing.`
        
        `For a fixed challenge, the individual-proof control returns (νpτp,(νpmp,j )j ) for each p and verifies the corresponding single-page equation. Aggregate and individual responses therefore use the same selected pages and fresh coefficients. Supplementary Section S-III-C details the serialization.`
        
    - **逐句建议稿（保留独立论点）**：
        
        > **建议句 S1**　Under our fixed s = 133 sectorization, the serialized aggregate proof \pi = (\sigma, \mu) occupies a constant 4310\text{ B} per batch (4310 b_T\text{ B} across b_T involved batches, excluding request declarations and challenges).
        > 
        > **建议句 S2**　In Section VI-C, we evaluate this `Public-Aggregate` interface against both authorized reference discovery (`Owner-MinRef`) and direct closure download (`Public-Download`), as well as an unaggregated `Individual-Proof` control that returns (\nu_p \tau_p, (\nu_p m\_{p,j})\_{j=1}^s) per page p \in U_b under the exact same challenge coefficients (see Supplementary Section S-III-C for wire serialization details).
        

### Subsection IV-F: Authenticated Exact Record Recovery（共 4 段）

#### 第 1 段（共 6 句）：两阶段精确恢复工作流（Stage 1 引用发现 + Stage 2 依赖拉取）

- **【逐句修改方案】**
    - **原段**：`Exact recovery uses two authenticated stages: discover the references that identify dependencies, then obtain those dependencies for complete decoding. The retriever validates the manifest, version pins, and any sidecar binding. It acquires the structural and reference ciphertext needed to resolve the targets, checks each object’s identity, length and committed digest, and applies AEAD authenticated decryption. Only then can it parse the private structure and BaseIDs to construct exact dependencies. Remaining dictionary rows, deviations, RAW content and target labels are fetched through the same verified path.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Authorized exact recovery (Algorithm 4) proceeds in two authenticated stages: reference discovery followed by exact dependency acquisition.
        > 
        > **建议句 S2**　First, the retriever authenticates the batch manifest, version pins, and optional protection sidecar.
        > 
        > **建议句 S3**　In Stage 1, it fetches the structural metadata pages S and reference pages \bigcup\_{i \in T, g} R_g(i) via `VerifiedOpen`, which verifies each page's descriptor (identity, length \ell(p), and ciphertext digest) before executing AES-256-GCM authenticated decryption.
        > 
        > **建议句 S4**　Only after authenticating these plaintexts does the retriever parse the private schema and `BaseID` values, verify that every `BaseID` falls within [0, M_g), and derive the exact dependency union D(T).
        > 
        > **建议句 S5**　In Stage 2, all remaining pages in D(T)—covering the referenced dictionary rows, local deviations, `RAW` fields, and target labels—are fetched and authenticated through the exact same `VerifiedOpen` path.
        

#### 第 2 段（共 5 句）、第 3 段（共 2 句）与第 4 段（共 2 句）：请求级缓存、全有或全无解码验收与 Conservative 对照

- **【逐句修改方案】**
    - **第 2–4 段逐句建议（保留原段落边界）**：
        
        > **建议句 S1**　A request-local cache stores verified ciphertext and authenticated plaintext so that pages obtained during reference discovery can be reused during dependency acquisition.
        > 
        > **建议句 S2**　Before decoding, the retriever checks private framing against the authenticated public layout and requires authenticated inputs for complete decoding.
        > 
        > **建议句 S3**　`VerifiedOpen` returns verified plaintext or \perp and caches only verified ciphertext and authenticated plaintext.
        > 
        > **建议句 S4**　Any failed check causes the request to return failure rather than a partial record.
        > 
        > **建议句 S5**　Multi-batch requests use the corresponding authenticated state for each batch.
        > 
        > **建议句 S6**　The `Conservative` control requires U(T) before decoding and retains the same authentication and complete-decoding checks.
        

### Subsection IV-G: Budgeted Ciphertext Protection（共 4 段）

#### 第 1 段（共 2 句）与第 2 段（共 6 句）：密文级 RS(10, 8) 编码与签名 Sidecar 结构

- **【逐句修改方案】**
    - **第 1–2 段润色成稿**：
        
        > **建议句 S1**　Because a single shared page (such as a dictionary page) may sit on the decoding path of many records, how redundancy is allocated across pages directly impacts record recoverability.
        > 
        > **建议句 S2**　ARC-Audit provides budgeted ciphertext protection via a systematic \text{RS}(10, 8) erasure code over \text{GF}(256) that groups eight ciphertext pages into a stripe and generates two 4096-byte parity shards.
        > 
        > **建议句 S3**　Original ciphertext pages remain unmodified in place: short pages (\ell(p) < 4096\text{ B}) are virtually zero-padded to 4096\text{ B} during parity computation, and trailing incomplete stripes are padded with declared virtual zero slots.
        > 
        > **建议句 S4**　Because parity is computed over complete sealed pages (covering N_p, the AEAD ciphertext, and the 16-byte tag), repairs occur entirely in the ciphertext domain, and a detached Ed25519-signed sidecar manifest binds the parent snapshot digest, RS code dimensions, stripe membership table, and parity shard digests.
        

#### 第 3 段（共 8 句，含公式 (12)）：三种保护优先级策略与统一 10% 存储预算上限

- **【逐句修改方案】**
    - **原段**：`Dictionary orders dictionary-containing pages before other objects. Uniform uses a seeded permutation. FrequencyD ranks objects by dependency frequency in a reference set of records. The three orders admit a common stripe count chosen so that every resulting sidecar fits the same per-batch cap: [Eq. (12)]. The budget determines how many ciphertext stripes receive protection; RS(10, 8) specifies the redundancy within each admitted stripe. The charged sidecar contains parity, serialized manifest, signature, signing public key and digest pin. The evaluation uses β = 0.10 and a NoEC zero-redundancy reference. Common stripe count and cap hold while actual serialized sidecar lengths may differ.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Under a fractional storage budget \beta, we evaluate three protection orders.
        > 
        > **建议句 S2**　`Dictionary` places dictionary-containing pages before other objects, `Uniform` uses a seeded permutation, and `FrequencyD` ranks objects by dependency frequency in a reference set of records.
        > 
        > **建议句 S3**　The orders use a common stripe count chosen so that every serialized sidecar fits the same per-batch cap: [Eq. (12)].
        > 
        > **建议句 S4**　The budget determines how many ciphertext stripes receive protection, while RS(10, 8) determines redundancy within each admitted stripe.
        > 
        > **建议句 S5**　The sidecar charge includes parity, the serialized manifest, signature, signing public key, and digest pin.
        > 
        > **建议句 S6**　The evaluation uses \beta = 0.10 and an unprotected `NoEC` reference.
        > 
        > **建议句 S7**　The common stripe count and cap are fixed, although actual serialized sidecar sizes may differ.
        

#### 第 4 段（共 6 句）：受保护检索与修复后双重验证流程

- **【逐句修改方案】**
    - **原段**：`Protected retrieval first checks the original. If it is unavailable, the retriever collects distinct authentic surviving original/parity slots from its stripe. Eight valid slots permit RS reconstruction. Every reconstructed real object is truncated to its signed length and checked against its original ciphertext digest before entering the cache. AEAD authentication then precedes record decoding. The same helper handles repairs needed by either the reference-discovery stage or the final exact dependency set.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Protected retrieval first checks the original object.
        > 
        > **建议句 S2**　If it is unavailable, the retriever collects distinct authentic surviving original and parity slots from its stripe.
        > 
        > **建议句 S3**　Eight valid slots permit RS reconstruction.
        > 
        > **建议句 S4**　Each reconstructed real object is truncated to its signed length and checked against its original ciphertext digest before entering the cache.
        > 
        > **建议句 S5**　AEAD authentication then precedes record decoding.
        > 
        > **建议句 S6**　The same helper handles repairs needed during reference discovery and acquisition of the final exact dependency set.
        

### Subsection IV-H: Computation and Storage Accounting（共 4 段，含公式 (13)）

#### 第 1–2 段（复杂度渐近分析）与第 3–4 段（存储字节公式 (13) 与通信/计时口径）

- **【逐句修改方案】**
    - **第 1–2 段润色成稿**：
        
        **作者备注 MC-06**：保持当前源码中标量乘法、点加法和多标量乘法的具体区分。下列计数仅来自原计划转录，不替代原文的精确资源计数。
        
        > **建议句 S1**　Let N be the number of ciphertext pages in a batch and u=|U(T)|.
        > 
        > **建议句 S2**　Enumerating U(T) requires O(\sum\_{i\in T}|K(i)|) expected hash-set insertions and O(u) working state beyond the authenticated manifest.
        > 
        > **建议句 S3**　SDA-GGD construction cost includes sample evaluations, full-input configurations, and queue updates across at most g_0-1 accepted merges.
        > 
        > **建议句 S4**　Batch sealing computes Ns sector multiplications.
        > 
        > **建议句 S5**　Aggregate proof generation uses us scalar-field multiplications and u scalar-point multiplications in \mathbb{G}\_1.
        > 
        > **建议句 S6**　Verification uses the stated u+s group-operation terms and two pairings.
        > 
        > **建议句 S7**　These costs sum across involved batches, with a 4310-B proof per batch and an O(N) manifest.
        
    - **第 3–4 段润色成稿**：
        
        > **建议句 S1**　Without a protection sidecar, secure cloud storage is defined by [Eq. (13)].
        > 
        > **建议句 S2**　Audit tags contribute B\_{\text{tags}}=48N bytes, and nonce and AEAD-tag framing contribute 28N bytes within B\_{\text{cipher}}.
        > 
        > **建议句 S3**　B\_{\text{manifest}} includes the signed public manifest and public parameters.
        > 
        > **建议句 S4**　Owner-retained base catalogs and private keys are accounted for separately as owner disk state.
        > 
        > **建议句 S5**　A deployed RS sidecar adds B\_{\text{side},b} to cloud storage and its corresponding pins to client state.
        > 
        > **建议句 S6**　Application-layer traffic counts declarations, challenges, Stage-1 reference transfers when applicable, and server responses.
        > 
        > **建议句 S7**　Manifest initialization is timed separately from per-request execution.
        > 
        > **建议句 S8**　Server object reads are tracked separately from application reply bytes.
        

## 六、 Section V: SECURITY AND RECOVERABILITY ANALYSIS 逐段逐句修改计划

### Section V 导言段（共 2 段，7 句）

- **【段落内部结构拆解】**
    - **第 1 段（S1–S4）** —— 概述第 V 节的论证路线图：从精确表示、闭包充分性、认证对象绑定，到公开视图机密性、聚合审计响应认证、返回记录真实性，最后到纠删恢复充分条件（并指出分组开销单调性已在 Proposition 1 证明）。
    - **第 2 段（S1–S3）** —— 统一声明功能性前提与密码学假设，并引出 Table II。
- **【逐句修改方案】**
    - **第 1–2 段润色成稿**：
        
        > **建议句 S1**　We analyze representation correctness, closure sufficiency, dependency binding, content confidentiality under the public view, aggregate response authentication, and returned-record authenticity.
        > 
        > **建议句 S2**　We then state a sufficient condition for authenticated recovery under erasures; Proposition 1 addresses grouping-cost reduction.
        > 
        > **建议句 S3**　The analysis assumes honest batch construction, exact schema arithmetic, valid configurations, authentic pins, and correctly provisioned keys.
        > 
        > **建议句 S4**　Table II summarizes the signature, hashing, key-derivation, nonce-respecting AEAD, and selected-set response-authentication premises used for these properties.
        

### Subsection V-A: Representation Correctness（共 1 段 + Proposition 2 & Proof）

- **【逐句修改方案】**
    - **第 1 段（S1–S6）原句**：`Exact reconstruction follows from the complementary positions of base and deviation bits. For a configured field group, let Ig contain the chosen base-bit positions and Jg their complement. A record’s group bit string satisfies xi,g[Ig] = Bg,IDi,g and xi,g[Jg] = di,g. The stored identifier chooses the exact dictionary row. Reinserting its bits and the deviation at complementary positions reconstructs xi,g. Inverting the declared widths and exact decimal scales reconstructs field values; RAW, constants, time and labels follow their declared representations.`
        
    - **第 1 段润色成稿**：
        
        > **建议句 S1**　Lossless record reconstruction follows directly from the complementary partitioning of base and deviation bit positions.
        > 
        > **建议句 S2**　For any configured GD group g, let I_g denote the selected base-bit positions and J_g their complement within the L_g-bit group width.
        > 
        > **建议句 S3**　Because record i's group bit string x\_{i,g} satisfies x\_{i,g}[I_g] = B\_{g, \text{ID}_{i,g}} and x_{i,g}[J_g] = d\_{i,g}, indexing the group dictionary with \text{ID}_{i,g} retrieves the exact base bits B_{g, \text{ID}_{i,g}}, and interleaving them with the local deviation d_{i,g} at complementary positions I_g and J_g losslessly recovers x\_{i,g}.
        > 
        > **建议句 S4**　Inverting the declared bit widths and exact decimal scales then restores the canonical process values, while `RAW` groups, constant fields, timestamps, and anomaly labels are decoded directly from their declared representations.
        
    - **Proposition 2 & Proof**：
        
        - **Proposition 2 原文**：`For an honestly configured batch, authenticated decryption and decoding of its undamaged required ciphertext objects return the complete canonical records.` → **保持不变**。
        - **Proof 润色**：`By AEAD correctness under the bound nonce $N_p$ and associated data $A_p$, decrypting each undamaged required page $C_p$ recovers its exact plaintext slice $F_p$, and concatenating these slices at their committed offsets reassembles all decoder input streams. Complementary bit interleaving then reconstructs every nonconstant GD group, while` RAW `and metadata decoding restore all remaining fields, yielding every component of the canonical record $r_i$. Q.E.D.`

### Subsection V-B: Closure Sufficiency and Shared-Object Reuse（共 1 段 + Proposition 3 & Proof + 后置段）

- **【逐句修改方案】**
    - **前置段 + Proposition 3 & Proof**：
        
        - **前置段润色**：`To verify integrity without decrypting references, the public closure $K(i)$ must cover every page that could be selected by a valid reference in $\mathcal{D}(i)$, as formalized below.`
        - **Proposition 3 原文**：`For every valid target, D(i) ⊆ K(i); therefore D(T) ⊆ U(T) for any valid target set T.` → **保持不变**。
        - **Proof 润色**：`Both $\mathcal{D}(i)$ and $K(i)$ include the identical page sets for structural metadata ($S$), reference spans ($\bigcup_g R_g(i)$), local values ($\bigcup_g V_g(i)$), and labels ($L(i)$). For each GD group $g$, exact recovery selects a single valid dictionary row ($0 \le \text{BaseID} < M_g$), whose bit span is a sub-interval of the full group dictionary span; because $\Phi_{\mathcal{L}}$ in Eq. (2) is monotonic with respect to interval inclusion, every page intersecting that row belongs to $\mathcal{P}_g^{\text{dict}} \subseteq K(i)$ (while` RAW `groups contribute no dictionary pages). Taking unions over all groups and across $i \in T$ preserves inclusion, yielding $D(T) \subseteq U(T)$. Q.E.D.`
    - **后置段（含公式 (14)）原句**：`Let ap = |{i ∈ T : p ∈ K(i)}|. Then [Eq. (14)]. This identity attributes saved uncached reads to overlap. It also explains why separate traversal with a complete request cache can match union reads. Aggregation reduces response multiplicity for the chosen set, a distinct mechanism evaluated with the same challenge and pages.`
        
    - **后置段润色**：
        
        > **建议句 S1**　Let a_p = |{i \in T : p \in K(i)}| count how many target closures in T contain page p; the byte savings of union planning over uncached separate traversal then satisfy [Eq. (14)].
        > 
        > **建议句 S2**　This identity directly attributes uncached read savings to cross-target page overlap (a_p > 1) and explains why separate per-record traversal equipped with a request-local page cache reads the exact same unique page set U(T).
        > 
        > **建议句 S3**　Proof aggregation, by contrast, compresses the verification responses returned over U(T)—an orthogonal mechanism that we isolate in Section VI-C under identical page sets and challenge coefficients.
        

### Subsection V-C: Authenticated Dependency Binding（共 2 段）

- **【逐句修改方案】**
    - **第 1 段润色成稿**：
        
        > **建议句 S1**　Authenticated dependency binding ensures that an adversary cannot redirect either public closure planning or exact reference discovery to unintended pages.
        > 
        > **建议句 S2**　Because the manifest signature and pinned digest authenticate the layout \mathcal{L} and all page descriptors {d_p}, public selection deterministically follows the owner's committed bit-span map \Phi\_{\mathcal{L}}.
        > 
        > **建议句 S3**　Exact selection goes one step further: it authenticates the reference pages against their committed descriptors, decrypts them under k_b and A_p, verifies that each parsed `BaseID` satisfies 0 \le \text{BaseID} < M_g before computing its dictionary bit offset, and cross-checks private framing headers against the authenticated public layout \mathcal{L}.
        
    - **第 2 段润色成稿**：
        
        > **建议句 S1**　Formally, let `BadBind` denote the event that a client accepts a manifest or page descriptor inconsistent with the pinned snapshot digest, and let `BadHash` denote the event that a client accepts ciphertext or parity bytes that differ from their committed digest.
        > 
        > **建议句 S2**　Under authentic client pins, digital signature unforgeability and hash collision resistance render \Pr[\text{BadBind}] and \Pr[\text{BadHash}] negligible.
        > 
        > **建议句 S3**　Conditioned on \neg\text{BadBind} \land \neg\text{BadHash}, an adversary cannot substitute a different reference, ciphertext page, snapshot version, or erasure stripe without detection, because every page—whether fetched directly or reconstructed via RS repair—is verified against its committed original digest \text{Hash}(C_p) prior to AEAD decryption.
        

### Subsection V-D: Content Confidentiality under the Public View（共 1 段 + Proposition 4 & Proof + 后置段）

- **【逐句修改方案】**
    - **第 1 段润色成稿**：
        
        > **建议句 S1**　Content confidentiality is defined for inputs with the same declared public view.
        > 
        > **建议句 S2**　This view includes record counts, ciphertext lengths, group and bit geometry, dictionary cardinalities, and requested targets and objects.
        > 
        > **建议句 S3**　Private decoding values remain encrypted.
        > 
        > **建议句 S4**　Batch keys are derived independently of data content and use secret material separate from signing and audit keys; page nonces are distinct under each batch key.
        > 
        > **建议句 S5**　The equal-view condition and the key-derivation and nonce-respecting AEAD assumptions remain part of the confidentiality statement.
        
    - **Proposition 4 & Proof 润色**：
        
        - **Proposition 4 原文**：`Under secure batch-key derivation and nonce-respecting AEAD confidentiality, the publicly stored data and public audit views of two equal-leakage inputs are computationally indistinguishable.` → **保持不变**。
        - **Proof 润色**：`We proceed via a standard hybrid argument. First, under the pseudorandom key-derivation assumption for HKDF-SHA256, we replace each derived batch key $k_b$ with an independently sampled uniform key, incurring negligible distinguishing advantage. Next, for each batch, because $\text{Leak}(X_0) = \text{Leak}(X_1)$ guarantees identical slice lengths $|F_p|$, identical public associated data $A_p$, and distinct page nonces $N_p$, multi-message nonce-respecting AEAD confidentiality implies that the resulting ciphertext pages $\{C_p\}$ are computationally indistinguishable. Finally, all remaining public components—page descriptors $\{d_p\}$, RS parity shards, signed manifests, audit tags $\{\tau_p\}$, and aggregate audit responses $\pi = (\sigma, \mu)$—are deterministic or randomized functions of the ciphertext pages $\{C_p\}$, the shared leakage $\text{Leak}(X)$, and independent signing/audit keys; hence, these components preserve computational indistinguishability under the stated public-view and key-independence premises. Q.E.D.`
    - **后置段润色**：`By conditioning on $\text{Leak}(X)$, this definition explicitly captures layout geometry and page-access disclosures while isolating decryption capabilities exclusively to authorized retrievers.`
        

### Subsection V-E: Audit Correctness and Selected-Set Authentication（共 2 段 + Proposition 5 & Proof + 后置段）

- **【逐句修改方案】**
    - **第 1 段（含公式 (15)）润色成稿**：
        
        > **建议句 S1**　We first verify completeness of the aggregate pairing check in Eq. (11) before stating the response-authentication assumption that links it to closure selection.
        > 
        > **建议句 S2**　Because s = 133 sectors of 31\text{ B} span 4123\text{ B} > 4096\text{ B} and each sector integer satisfies m\_{p,j} < 2^{248} < q, the mapping from a page C_p of fixed valid length \ell(p) to its sector vector \mathbf{m}\_p \in \mathbb{F}\_q^s is injective.
        > 
        > **建议句 S3**　For an honest CSP response, substituting Eqs. (9) and (10) into \sigma yields [Eq. (15)], and bilinear pairing linearity immediately gives Eq. (11).
        
    - **第 2 段（含公式 (16)）+ Proposition 5 & Proof + 后置段润色成稿**：
        
        > _Selected-set response-authentication assumption._ For our instantiated BLS12-381 parameters, context-bound coefficient derivation, and validated adaptive request interface (detailed in Supplementary Section S-III-B), we assume that any polynomial-time adversary has negligible probability of causing the verifier to accept an aggregate sector-response vector \mu that deviates from the true linear combination of the committed ciphertexts over the challenged closure U, corresponding to the bad event [Eq. (16)].
        > 
        > **Proposition 5 (Conditional closure response authentication).** _Under authenticated metadata and the selected-set response-authentication assumption, an accepted audit authenticates the declared linear response for the verifier-derived ciphertext closure._
        > 
        > **建议句 S1**　_Proof._ For each involved batch, the verifier deterministically derives U_b from the authenticated layout \mathcal{L}\_b and retains its locally bound challenge context.
        > 
        > **建议句 S2**　Conditioned on \neg\text{BadBind} \land \neg\text{BadHash}, accepting a response whose sector vector \mu does not equal \sum\_{p \in U_b} \nu_p \mathbf{m}\_p \pmod q over the committed pages in U_b directly triggers \text{BadAudit}; applying a union bound across the b_T involved batches completes the proof.
        > 
        > **建议句 S3**　_Q.E.D._
        > 
        > While Proposition 5 binds public audit acceptance to the committed closures U_b, the authorized retrieval path below authenticates the returned page bytes directly via cryptographic digests and AEAD opening.
        

### Subsection V-F: Authenticity of Returned Records（共 1 段 + Proposition 6 & Proof + 后置段）

- **【逐句修改方案】**
    - **前置段 + Proposition 6 & Proof 润色**：
        
        > **建议句 S1**　Returned-record authenticity bounds the probability that the retriever returns a record differing from its canonical value under the stated functional and cryptographic premises, including when pages are reconstructed via erasure coding.
        > 
        > **建议句 S2**　Let `Wrong` denote the event that Algorithm 4 returns a non-\perp result containing any \widehat{r}\_i \ne r_i, where probabilities are taken over key generation, protocol randomness, and adversary actions under authentic pins and provisioned keys.
        > 
        > **Proposition 6 (Returned-record authenticity).** _Under the functional premises,_ \text{Wrong} _implies_ \text{BadBind} _or_ \text{BadHash}_, and hence_ [Eq. (17)].
        > 
        > **建议句 S1**　_Proof._ Conditioned on \neg\text{BadBind} \land \neg\text{BadHash}, every page C_p admitted into the retriever's cache \mathcal{C}—whether fetched directly from its original slot or reconstructed from eight stripe shards and verified against \text{Hash}(C_p)—is bit-identical to the owner's committed ciphertext.
        > 
        > **建议句 S2**　Decryption under the authentic key k_b and bound associated data A_p therefore recovers the exact original plaintext slice F_p, Stage-1 reference parsing recovers the exact `BaseID` values, and Stage-2 fetching acquires all pages in D(T).
        > 
        > **建议句 S3**　By Proposition 2, passing the framing and complete-decoding checks then deterministically yields \widehat{r}\_i = r_i for all i \in T; consequently, \text{Wrong} can occur only if `BadBind` or `BadHash` occurs.
        > 
        > **建议句 S4**　_Q.E.D._
        
    - **后置段润色**：
        
        > **建议句 S1**　Verifying \text{Hash}(C_p) after RS reconstruction preserves the same committed-ciphertext invariant used for direct retrieval.
        > 
        > **建议句 S2**　Under the stated premises, digest binding supports the bound on \Pr[\text{Wrong}] in Eq. (17).
        > 
        > **建议句 S3**　AEAD opening is still required before decoding, and a failed check aborts the request before partial records are released.
        

### Subsection V-G: Recovery Conditions and Protection Budget（共 1 段 + Proposition 7 & Proof + 后置 2 段）

- **【逐句修改方案】**
    - **前置段 + Proposition 7 & Proof 润色**：
        
        > **建议句 S1**　Finally, we characterize when exact recovery succeeds in the presence of storage erasures or corruptions.
        > 
        > **建议句 S2**　Let \mathcal{A}_0 \subseteq \mathcal{P} denote the set of intact, authentic original pages available from the CSP, \mathcal{P}_{\text{prot}} \subseteq \mathcal{P} the subset of pages admitted into protected RS stripes, S(p) the ten stripe slots associated with p \in \mathcal{P}\_{\text{prot}}, and \mathcal{V} the set of all authentic available stripe slots (including declared virtual zero slots).
        > 
        > **Proposition 7 (Sufficient exact recovery condition).** _With authentic metadata and correct decryption capability, Exact recovery succeeds if_ [Eq. (18)].
        > 
        > **建议句 S1**　_Proof._ Under Eq. (18), every page p \in D(T) can either be fetched directly as an intact original (p \in \mathcal{A}\_0) or reconstructed via \text{RS}(10, 8) from at least eight surviving authentic slots (|S(p) \cap \mathcal{V}| \ge 8) and verified against \text{Hash}(C_p).
        > 
        > **建议句 S2**　Because the Stage-1 structural and reference pages satisfy S \cup \bigcup\_{i \in T, g} R_g(i) \subseteq D(T), Eq. (18) guarantees that Stage 1 succeeds in discovering D(T) and that Stage 2 subsequently recovers and authenticates all remaining pages in D(T), after which Proposition 2 guarantees exact canonical decoding.
        > 
        > **建议句 S3**　_Q.E.D._
        
    - **后置 2 段润色**：
        
        > **建议句 S1**　The `Conservative` control requires the availability condition over U(T), whereas `Exact` recovery requires it over D(T).
        > 
        > **建议句 S2**　Since D(T) \subseteq U(T), `Exact` can succeed when the actual dependencies are obtainable but an unused object in U(T) \setminus D(T) is not.
        > 
        > **建议句 S3**　Sidecar admission enforces Eq. (12) over the complete serialized sidecar state.
        > 
        > **建议句 S4**　Section VI-D compares the protection orders using the common stripe count, per-batch cap, and erasure code; it does not require identical realized sidecar lengths.
        

## 七、 Section VI: EXPERIMENTAL EVALUATION 逐段逐句修改计划

### Section VI 导言段（共 1 段，5 句）

- **【逐句修改方案】**
    - **原段**：`The evaluation follows the three design contributions. RQ1 measures the storage and construction costs of the shared representation. RQ2 measures the communication and computation of public dependency planning and aggregate auditing. RQ3 examines how protection allocation and dependency selection affect authenticated record recovery. Table III records the workload size and experimental unit of each comparison.`
        
    - **润色成稿**：
        
        > **建议句 S1**　Our experimental evaluation addresses three research questions corresponding to the design contributions: **RQ1** evaluates the cloud storage footprint, owner state, and construction time of the cost-confirmed shared representation; **RQ2** quantifies the communication and local computation trade-offs of public closure planning and aggregate auditing; and **RQ3** investigates how protection allocation and exact dependency selection jointly govern authenticated record recovery under erasures.
        > 
        > **建议句 S2**　Table III summarizes the dataset segments, configurations, and observation counts for each experiment (denoted C1–C3 and Clean).
        

### Subsection VI-A: Experimental Setup（共 3 小节，11 段）

#### 1) Data and Implementation（共 3 段）

- **【逐句修改方案】**
    - **第 1 段（数据源与外部评分器）润色**：
        
        > **建议句 S1**　_1) Data and Implementation:_ We evaluate ARC-Audit using the `train1` and `train2` segments of the HAI 21.03 industrial control dataset [34], which contain 216{,}001 and 226{,}801 records, respectively.
        > 
        > **建议句 S2**　Each record comprises 84 columns: a timestamp, 79 physical process measurements, and four anomaly/attack indicators (three process-specific indicators encoded independently and one combined indicator derived from them).
        > 
        > **建议句 S3**　All floating-point process measurements undergo exact decimal canonicalization during ingestion, and after every recovery trial an external harness independently verifies \widehat{r}\_i = r_i against the raw canonical source outside the client's service timer.
        
    - **第 2 段（工作负载切分与斜杠记号约定）润色**：
        
        > **建议句 S1**　Experiment C1 uses a 6-hour window (21{,}600 records) starting at 00:00 on July 11, 2020 (`train1`) and August 1, 2020 (`train2`), whereas C2 and C3 operate over the complete segments partitioned into three immutable batches for `train1` and four for `train2` (batch boundaries and source hashes are listed in Supplementary Section S-IV).
        > 
        > **建议句 S2**　Throughout Section VI, paired numeric values reported as x/y denote measurements on `train1`/`train2`, respectively.
        
    - **第 3 段（软件栈与计时隔离）润色**：
        
        **作者备注 MC-11**：软件栈句按原计划转录。计时边界句暂保留当前论文原文，核对后再润色；不得据原计划把 manifest 创建和签名排除在完整构建时间外。
        
        > **建议句 S1**　Our prototype is implemented in Python 3.10.12 using `NumPy` 2.2.6, `cryptography` 50.0.1 for AES-256-GCM and Ed25519, and `py-ecc` 8.0.0 for BLS12-381 operations, alongside a systematic RS(10, 8) codec over GF(256).
        > 
        > **建议句 S2**　To reduce measurement noise on a shared host, C1 and full-segment processes were pinned to CPU cores `{2}` and `{4}`, respectively.
        

#### 2) Controls and Metrics（共 6 段）

- **【逐句修改方案】**
    - **第 1–2 段（C1 基线与样本设置）润色**：
        
        > **建议句 S1**　_2) Controls and Metrics:_ In C1 (RQ1), we compare `SDA-GGD` against three representation baselines under identical AES-256-GCM sealing, BLS12-381 tagging, and manifest accounting: `Per-field-GD` (which applies GD to each nonconstant column independently without cross-field grouping), `RAW` (uncompressed canonical encoding), and `Block-CZ-256` (which groups nonconstant columns into 256-record row blocks and compresses each block as an independent Zstandard frame at level 3).
        > 
        > **建议句 S2**　The sample size for merge ranking is set to \min(50{,}000, n) rows—covering the full 21{,}600-row C1 window—and we report the median and min–max range across two independent builds per window.
        
    - **第 3–4 段（C2 接口与指标口径）润色**：
        
        > **建议句 S1**　In C2 (RQ2), we decouple dependency discovery from proof aggregation across target set sizes r \in {1, 16, 256} (with three target sets per segment and size): `Public-Aggregate` computes the public closure U(T) from \mathcal{L} and returns a 4310-B aggregate proof per batch; `Public-Download` computes the same U(T) without a decryption key but downloads the full ciphertext pages for local SHA-256 verification; and `Owner-MinRef-Aggregate` (abbreviated `Owner-MinRef`) uses the batch decryption key to fetch and decrypt Stage-1 reference pages, narrows the dictionary closure to actual dependencies, and audits that reduced set via an aggregate proof.
        > 
        > **建议句 S2**　Comparing `Public-Aggregate` against `Public-Download` isolates the proof-format trade-off under public access, whereas comparing `Public-Aggregate` against `Owner-MinRef` isolates public geometry planning versus authorized two-stage reference discovery (reporting medians and min–max ranges of application traffic and local CPU time across matched target sets).
        
    - **第 5–6 段（C3 矩阵与 FrequencyD 训练/测试集隔离）润色**：
        
        > **建议句 S1**　In C3 (RQ3), we cross the two dependency-selection policies (`Exact` and `Conservative`) with four protection-allocation controls (`Dictionary`, `Uniform`, `FrequencyD`, and unprotected `NoEC`), holding the \text{RS}(10, 8) code, common stripe count, and 10% per-batch sidecar cap (\beta = 0.10) fixed across all protected orders.
        > 
        > **建议句 S2**　To keep recovery targets separate from the reference records used for placement, `FrequencyD` profiles dependency frequencies strictly over the first \min(4096, \max(1, \lfloor n/5 \rfloor)) records of each batch (1440 reference records for the 7200-record trailing batch and 4096 for each of the other six batches), and all C3 recovery targets are drawn exclusively from outside these reference ranges.
        

#### 3) Faults and Statistics（共 2 段）

- **【逐句修改方案】**
    - **第 1–2 段润色成稿**：
        
        > **建议句 S1**　_3) Faults and Statistics:_ For each segment in C3, we generate five seeded protection layouts and evaluate nominal erasure fractions \alpha \in {0.001, 0.01, 0.05} across 50 single-record recovery cases per layout and loss rate (250 trials per point).
        > 
        > **建议句 S2**　In each trial, a uniform fixed-count erasure mask of \lceil \alpha N\_{\text{fault}} \rceil slots is drawn without replacement from the segment-wide pool of original ciphertext pages and deployed parity shards (N\_{\text{fault}} = 5000 and 4765 for `train1` and `train2`, corresponding to 5/50/250 and 5/48/239 erased slots), with all eight policy controls evaluated over identical targets and erasure masks in rotated execution order.
        > 
        > **建议句 S3**　We report empirical recovery rates alongside pointwise 95% Wilson confidence intervals across the 250 trials, and report median recovery latencies over successful trials (complemented by 30 fault-free `Clean` trials per segment and control—480 total outcomes—and complete failure/initialization ledgers in the Supplementary Material).
        

### Subsection VI-B: RQ1: Storage and Secure Construction（共 3 段）

#### 第 1 段（云存储收益）、第 2 段（编码与打标时间折中）、第 3 段（Owner 私有状态开销）

- **【段落内部结构拆解与逐句修改方案】**
    - **第 1 段润色成稿**：
        
        > **建议句 S1**　As shown in Fig. 2 and Table IV, `SDA-GGD` achieves the smallest secure cloud footprint on both C1 windows, requiring 1{,}903{,}138 and 1{,}770{,}118\text{ B} (1.815 and 1.688\text{ MiB}) compared with 2{,}198{,}812 and 1{,}938{,}839\text{ B} (2.097 and 1.849\text{ MiB}) for `Per-field-GD`—representing storage reductions of 13.45% and 8.70%.
        > 
        > **建议句 S2**　By comparison, `Block-CZ-256` consumes 2{,}278{,}001 and 2{,}227{,}359\text{ B} (2.172 and 2.124\text{ MiB}), while uncompressed `RAW` requires roughly 15.17\text{ MB} (14.463\text{ MiB}) per window; all 16 builds pass end-to-end canonical decoding verification (Supplementary Table S-II).
        
    - **第 2 段润色成稿**：
        
        > **建议句 S1**　This cloud storage reduction trades higher group-configuration time against lower cryptographic tag-generation time.
        > 
        > **建议句 S2**　Specifically, end-to-end secure construction takes median times of 274.356/235.621\text{ s} for `SDA-GGD` versus 231.521/206.163\text{ s} for `Per-field-GD` (a descriptive median increase of 18.50%/14.29%).
        > 
        > **建议句 S3**　While iterative group merging and full-input confirmation raise the codec stage time from 1.00/0.83\text{ s} (`Per-field-GD`) to 73.66/47.63\text{ s} (`SDA-GGD`), emitting fewer ciphertext pages reduces subsequent BLS12-381 tag generation from 230.25/205.05\text{ s} to 200.42/187.72\text{ s}, partially offsetting the encoding overhead.
        
    - **第 3 段润色成稿**：
        
        > **建议句 S1**　Table IV further distinguishes cloud storage from owner-retained private state: `SDA-GGD` retains 303{,}595/184{,}687\text{ B} of base dictionaries within 335{,}884/215{,}702\text{ B} (328.012/210.646\text{ KiB}) of total owner disk state, compared with 208{,}267/174{,}552\text{ B} of bases within 245{,}064/209{,}287\text{ B} (239.320/204.382\text{ KiB}) for `Per-field-GD`.
        > 
        > **建议句 S2**　Thus, cross-field grouping lowers outsourced cloud storage while retaining a modestly larger local base catalog at the owner.
        

### Subsection VI-C: RQ2: Public Audit Communication and Computation（共 6 段）

#### 第 1 段（相同公开权限下的响应格式对比）

- **【逐句修改方案】**
    - **润色成稿**：
        
        > **建议句 S1**　_Responses under the same public access capability._ Although `Public-Aggregate` and `Public-Download` audit the exact same public closure U(T), they exhibit opposite communication–computation profiles (Fig. 3).
        > 
        > **建议句 S2**　At r = 256 target records, `Public-Aggregate` transfers only 35{,}405/38{,}524\text{ B} of application traffic while requiring 32.532/30.908\text{ s} of local computation, whereas `Public-Download` transfers 17{,}041{,}940/15{,}754{,}868\text{ B} of ciphertext pages but requires 0.0400/0.0354\text{ s} of local computation.
        > 
        > **建议句 S3**　Aggregate auditing thus compresses application-layer audit traffic by more than two orders of magnitude in exchange for higher local verification CPU time (these measurements describe application traffic and local computation, rather than a measured network deployment).
        

#### 第 2–3 段（不同访问权限下的依赖发现对比：r=256 vs. r=1, 16）

- **【逐句修改方案】**
    - **第 2–3 段润色成稿**：
        
        > **建议句 S1**　_Dependency discovery under different access capabilities._ The comparison between `Public-Aggregate` and `Owner-MinRef` examines public geometry planning versus authorized reference discovery.
        > 
        > **建议句 S2**　At r = 256, `Owner-MinRef` incurs 11{,}163{,}473/11{,}010{,}612\text{ B} of application traffic (dominated by Stage-1 reference page downloads) and 31.532/30.148\text{ s} of local computation; relative to `Owner-MinRef`, `Public-Aggregate` lowers application-layer audit traffic by 99.68%/99.65% while increasing local CPU time by 3.17%/2.52% (ratios of observed medians).
        > 
        > **建议句 S3**　For a single target record (r = 1), `Owner-MinRef` narrows the audited dictionary pages enough to reduce local verification time from 3.106/3.169\text{ s} (`Public-Aggregate`) to 1.164/1.126\text{ s}, but its Stage-1 reference transfer still consumes 169{,}601/173{,}696\text{ B} compared with just 6237/6254\text{ B} for `Public-Aggregate` (with intermediate r = 16 breakdowns reported in Supplementary Table S-IV).
        

#### 第 4 段（流量构成与上下文一次性初始化）

- **【逐句修改方案】**
    - **润色成稿**：
        
        > **建议句 S1**　_Traffic composition._ Decomposing the r = 256 traffic shows that `Owner-MinRef` spends 11{,}128{,}596/10{,}972{,}500\text{ B} on Stage-1 reference transfers—a phase completely absent in the two public interfaces—while both aggregate interfaces return identical 4310\text{ B}-per-batch proofs (12{,}930/17{,}240\text{ B} across the 3/4 involved batches; Supplementary Table S-V).
        > 
        > **建议句 S2**　One-time batch context initialization for r = 1 requires a median of 8.101/7.805\text{ s} and is reported separately from per-request execution.
        > 
        > **建议句 S3**　All 54 honest audit requests pass verification.
        

#### 第 5–6 段（机制消融对照：页面去重复用 vs. 证明聚合）

- **【逐句修改方案】**
    - **第 5–6 段润色成稿**：
        
        > **建议句 S1**　_Mechanism controls._ Finally, two representative 16-target controls isolate page-read deduplication from cryptographic proof aggregation.
        > 
        > **建议句 S2**　On `train1`, union closure planning (U(T)) and cached separate traversal both read 805 unique pages (3{,}297{,}280\text{ B}) compared with 5643 page reads (23{,}113{,}728\text{ B}) for uncached separate traversal (and 125 vs. 892 page reads on `train2`), confirming that request-level deduplication eliminates redundant storage reads regardless of traversal order.
        > 
        > **建议句 S3**　Holding those 805 and 125 selected pages and challenge coefficients fixed, proof aggregation compresses the returned proof from 3{,}475{,}990\text{ B} and 539{,}750\text{ B} (`Individual-Proof`) to a single 4310\text{ B} batch proof while reducing verification time from 472.659\text{ s} to 3.477\text{ s} (`train1`) and from 73.646\text{ s} to 1.074\text{ s} (`train2`), and both controls reject the tested synthetic last-byte ciphertext mutations.
        

### Subsection VI-D: RQ3: Authenticated Recovery and Protection Allocation（共 5 段）

#### 第 1 段（Protection placement）、第 2 段（Frequency-based allocation）、第 3 段（Dependency policy）、第 4 段（Recovery time）、第 5 段（本节总结）

- **【逐句修改方案】**
    - **第 1 段（Protection placement）润色**：
        
        > **建议句 S1**　_Protection placement._ Holding `Exact` dependency selection fixed isolates the impact of protection allocation under the common 10% sidecar cap (Fig. 4).
        > 
        > **建议句 S2**　At a 1% nominal loss rate, prioritizing dictionary pages (`Dictionary`) successfully recovers 185/250 records on both segments (74.0%), exceeding the observed rate for `Uniform` (153/250 and 164/250, or 61.2%/65.6%) by 12.8/8.4 percentage points and unprotected `NoEC` (114/250 and 117/250, or 45.6%/46.8%) by 28.4/27.2 percentage points (with `Dictionary` also leading `Uniform` at 0.1% loss: 95.2%/97.6% vs. 94.0%/95.6%).
        
    - **第 2 段（Frequency-based allocation）润色**：
        
        **作者备注 MC-12**：频率来自指定参考集，不能自动解释成全批次或未来请求的最优排序。
        
        > **建议句 S1**　_Frequency-based allocation._ Under heavier erasures (5% nominal loss), empirical frequency ranking (`FrequencyD` with `Exact` recovery) recovers 43/250 and 65/250 records (17.2%/26.0%), exceeding the observed rate for `Dictionary` (14.8%/21.6%) while matching or closely tracking `Dictionary` at 0.1% loss (Supplementary Table S-VIII).
        > 
        > **建议句 S2**　Whereas `Dictionary` prioritizes pages purely by structural role, `FrequencyD` ranks pages using dependency frequencies measured in its designated reference records.
        
    - **第 3 段（Dependency policy）润色**：
        
        **作者备注 MC-12**：相同恢复率不能证明全部字典条带可恢复；将配对差异归因于具体字典页须查逐请求日志。
        
        > **建议句 S1**　_Dependency policy._ Holding the `Dictionary` sidecar fixed isolates the benefit of `Exact` two-stage recovery over `Conservative` closure recovery.
        > 
        > **建议句 S2**　While both policies achieve identical recovery rates at 0.1% and 1% loss , at 5% loss `Exact` recovers 37/250 and 54/250 records (14.8%/21.6%) compared with 27/250 and 45/250 (10.8%/18.0%) for `Conservative`—gaining 10 and 9 paired recovery successes with zero regressions.
        > 
        > **建议句 S3**　These paired outcomes are consistent with the availability distinction between D(T) and U(T).
        
    - **第 4 段（Recovery time）润色**：
        
        > _Recovery time._ In the reported latency comparisons, `Exact` selection reduces request latency: on fault-free (`Clean`) runs, `Exact/Dictionary` completes in a median of 3.693/3.507\text{ ms} versus 8.991/7.205\text{ ms} for `Conservative/Dictionary`, and at 5% loss successful `Exact/Dictionary` requests require 4.298/4.074\text{ ms} versus 11.933/7.079\text{ ms} for `Conservative/Dictionary` (interpreted alongside their respective success rates in Supplementary Table S-IX).
        
    - **第 5 段（RQ3 总结）润色**：
        
        > **建议句 S1**　Taken together, these controlled comparisons demonstrate two complementary mechanisms under an identical erasure code and storage budget: protection allocation changes which pages receive redundancy, while exact reference discovery limits required decoding inputs to actual dependencies.
        > 
        > **建议句 S2**　The observed policy rankings remain specific to the tested workloads and fault settings.
        

## 八、 Section VII: CONCLUSION 逐句修改计划

### 全文结论段（共 1 段，6 句）

#### 【段落内部结构拆解】

- **Part 1：核心架构回顾（S1–S3）** —— ARC-Audit 通过从 IIoT 记录到密文页的认证映射连接公共审计与认证恢复；公开几何提供充分覆盖，认证私有引用发现精确依赖；原始页与修复页遵循完全一致的验证与解码验收规则。
- **Part 2：实验发现与全篇收束（S4–S6）** —— 总结存储/通信节省与构建/本地计算代价的折中，强调保护分配与精确依赖选择的协同效应。

#### 【逐句修改方案】

- **原段（S1–S6）**：`ARC-Audit connects public auditing and authenticated record recovery through an authenticated mapping from industrial IoT records to ciphertext objects. Public geometry supplies sufficient coverage, while verified private references identify the actual recovery dependencies. Original and repaired objects follow the same authentication and complete-decoding rules. The evaluation shows storage and communication savings with corresponding construction and local computation costs. It also shows that protection allocation and dependency selection jointly determine recovery. Exact selection permits complete record recovery when the authenticated inputs required by the decoder remain obtainable, even if unused shared objects are unavailable.`
    
- **润色成稿**：
    
    > **建议句 S1**　ARC-Audit connects public auditing and authenticated record recovery through an authenticated mapping from industrial IoT records to ciphertext objects.
    > 
    > **建议句 S2**　Public geometry supplies sufficient coverage, while verified private references identify actual recovery dependencies.
    > 
    > **建议句 S3**　Original and repaired objects follow the same authentication and complete-decoding rules.
    > 
    > **建议句 S4**　The evaluation on two HAI workloads shows storage and communication savings with corresponding construction and local computation costs.
    > 
    > **建议句 S5**　It also shows that protection allocation and dependency selection jointly affect recovery in the tested settings.
    > 
    > **建议句 S6**　Exact selection permits complete record recovery when the authenticated inputs required by the decoder remain obtainable, even if unused shared objects are unavailable.
    

## 九、语义风险与来源核实清单

本计划不再使用“99%为纯语言修改”的比例判断。以下区分已在计划中纠正的建议与仍需核对的内容；核对项不是已发现的论文错误，也不阻碍其他句子的润色。

|编号|位置|原计划风险|修订后的处理与状态|
|---|---|---|---|
|MC-01|Abstract S1、S8–S12|overhead、latency、verification、formally、substantially 改变范围或强度|已纠正：保留存储需求、retrieval overhead、local computation、analyze 和 tested 条件；不增加程度词。|
|MC-02|Introduction 第2段|may 改为 must；part 改为 single entry；新增 dual-view 命名|已纠正：恢复可能性和原例子的范围，不新增机制名称。|
|MC-03|Contribution 1、III-C|固定页长、bit-for-bit equality、全局最小化目标|已纠正：保留实际尾页长度、schema 下值相等，以及候选代价选择；不宣称全局最优。|
|MC-04|Related Work|排他性否定、技术继承、knowledge extraction、广播加密作用的扩写|已撤回额外判断，恢复原有文献定位。若要新增“未建模……”等比较，先读被引文献并单独提议。|
|MC-05|III-D、IV-F|先解密再认证；将 Conservative 写成改变依赖集定义|已纠正：保留 authenticated decryption；Conservative 只是对获取与验收集合的实验控制，不改 D(T) 的定义。|
|MC-06|IV-B、IV-H|将逻辑分组收益与完整安全云存储成本混同；压缩掉详细资源计数|已纠正目标区分。原公式、精确计数和辅助函数定义均须保留；建议摘要式文字不能替代这些内容。|
|MC-07|Algorithm 1、IV-B|为解释 requeue 而假设入队是上界或近似估计|待核实：检查入队键、SampleGain 是否确定、版本定义和实际重入队条件。没有实现证据时保留原步骤，不新增惰性估计机制。|
|MC-08|IV-G、Algorithm 4|新增“原始对象无效时自动修复”的分支；先写缓存再失败被断言为漏洞|待核实：按实现决定 fallback。可用临时变量改善伪代码的不变量，但不把立即失败的局部赋值定性为实际缓存漏洞。|
|MC-09|V-D|无条件不泄露、完美模拟、未明确支持的自适应接口|已收回绝对措辞。保留等泄露、独立密钥及 nonce-respecting AEAD 前提；完整公开视图及自适应交互范围须对照原命题核实。|
|MC-10|V-E、V-F|省略 selected-set 假设或写 never 返回错误记录|已纠正：保持 Proposition 5 的条件性和 Proposition 6 的概率界，不升级为无条件 PoR、持有或可提取性结论。|
|MC-11|VI-A、VI-C|错把 manifest 创建排除在完整构建计时外；把本地 CPU 数值仅归于配对；推断实际网络时延|待核实具体计时边界；已移除不受支持的阶段归因和网络部署结论。初始化与请求时间分开报告。|
|MC-12|VI-D|相同成功率推出全部字典条带可修复；参考集频率被写成全批次频率|已撤回原因推断，保留观测值。具体故障原因需逐请求日志支持。|
|MC-13|VI、Conclusion|描述性差值被写为显著优势或协同效应；故障结论扩大到所有分布|已纠正：保留测试条件、成功请求条件、配对结果与零退化观测，不新增统计显著性或交互效应结论。|
|MC-14|全文引用与实验数据|原计划转录数值、版本、批次、时刻、表号可能与当前论文不同|本次不独立验证；应用时以当前源码及原始结果为准。不要把转录值当成新生成的实验依据。|
|MC-15|图与符号表|h_snap 的定义对象、序列化和签名是否计入摘要尚未回源|只做与现有 manifest digest 定义一致的对齐；不另设哈希域或更改协议字节。|

**本轮可采用的语言修正**：补冠词、去掉 respective 的重复、将代价确认的 verified 改为 confirmed、清理指代，以及在不改语义的前提下改善并列结构。

**不混入正文的内容**：本节 MC 编号、作者核实备注、关于实现是否正确的判断和新增实验解释。它们属于计划记录，不属于润色后的论文文字。

## 十、图示、伪代码与符号一致性的独立修订建议

本节与语言润色分开执行。原计划中的四份“可直接替换 LaTeX”已撤回：它们包含未核实的实现细节、辅助过程和算法行号，不能据此整块替换现有算法。本节给出最小修改项，不新增系统功能。

### 1. Fig. 1

|元素|建议|边界|
|---|---|---|
|两阶段恢复|用简短标签指出先获取结构与引用页，再获取未缓存的剩余依赖|不必为此重绘整图。若标集合，应考虑缓存，以当前 Algorithm 4 为准。|
|h_snap 与 chal|在题注或符号表定义图中使用但正文未解释的符号|先核对当前全文是否已有定义；h_snap 必须等于现有协议使用的 manifest digest。|
|客户端 pins 和解密能力|如图需自包含，可在现有角色说明中简短注明|已在正文说明时可保留原图，不新增密钥分发协议或复杂连线。|
|optional sidecar|将 manifest、sidecar、parity 的用词与正文保持一致|它们不是可以无条件互换的同义词。|

**题注的最小处理**：保留现有题注中的公开规划、授权引用发现、原始与修复密文的共同校验及 AEAD 参数说明。仅在需要时补一句“两阶段获取”或符号定义，避免将整个检索算法塞入题注。

### 2. Algorithm 1：分组算法

- 语言项：统一 `if`、`continue`、`end if` 的排版；明确配置变量指向当前组还是合并候选。采用与现有算法宏包兼容的语法，无需声称存在唯一的“IEEE 标准伪代码结构”。
- MC-07：确定性 SampleGain 在固定样本和固定组版本下原则上应给出相同值。重算可能是冗余校验，也可能涉及其他缓存状态；必须以实现为据，不能仅凭伪代码判定为逻辑漏洞。
- 不把 `positive sampled-gain pairs` 改为 `positive initial gain estimates`，除非代码确实使用另一种入队估计。
- 保留分组目标与最终安全云存储成本的区别，不以润色名义把合并判据换成密文、标签和 manifest 的总成本。

### 3. Algorithm 2：封装算法

- `authenticated header A_p` 若确指 AEAD associated data，可统一为 `associated data A_p`。
- 若正文公钥 Y 已属于 pp，可在现有密钥生成行澄清符号，不新增另一套密钥。
- 标签、manifest、签名和 pins 的生成顺序保持不变；tag-file digest 不应改写为未经定义的抽象集合哈希。
- 如补 Eq. 引用，使用已有 `\eqref{...}` 标签；不写死未经核实的编号。

### 4. Algorithm 3：公共审计

- 在系数行补全 p \in U_b，可提高索引清晰度。
- 若当前行仅写读取 C_p，可注明同时使用对应标签 τ_p；这只是展开现有聚合公式，不改变证明格式。
- 保留每批次分割、参数验证、挑战上下文绑定和失败退出规则。响应身份元、子群检查、标量范围等检查不能在润色时随意增加或删除。

### 5. Algorithm 4：精确恢复

- 引用解析顺序保持“认证输入、认证解密、解析并检查范围、映射依赖”。
- 如希望使“仅缓存成功结果”的不变量在伪代码中更直观，可把单行赋值改为临时变量形式。以下仅为局部表达示意，不是整个算法的替换稿：

```
F_p <- VerifiedOpen(p)
if F_p = failure: return failure
cache[p] <- F_p
```

- `VerifiedOpen` 的输入输出、实际缓存对象及 RS fallback 以原实现为准。若 C_p 包含 nonce 前缀，解密调用不能把整个带前缀对象直接当作 AEAD 的密文载荷；保留现有拆分方式。
- RS 修复后的截断、原密文摘要检查和 AEAD opening 可在正文说明；没有必要追加冗长辅助函数。虚拟零槽的计数方式也须与原算法一致。

### 6. Table I 与图题注

- 若布局固定后省略下标 L，在首次简写处说明即可；不必在符号表同一行堆叠两套长符号。
- 牛津逗号可统一，但属于风格选择，不是语法错误。
- 保留 median、min–max、Wilson interval、descriptive ratios、successful trials 等统计限定。具体表号与算法行号在应用后重新核对。

## 十一、将计划应用到论文时的逐句核对记录

每段均采用下列简短记录，不为没有问题的句子编造修改理由：

|原文位置|原句|判断|建议句|理由与语义风险|
|---|---|---|---|---|
|Section / paragraph / Sx|从当前源码逐字读取|保留、轻改、句法调整或待核实|保留时可写“同原句”|说明真正改善之处；有风险时关联 MC 编号|

应用要求：

1. 先读取当前段落，以当前源码为准解决本计划转录与原文的差异。
2. 每句都核对；原计划只提供建议稿而没有完整原句的段落，不得伪造原句或宣称已完成逐句对照。
3. 不删除论据、统计限定、公式、辅助函数定义或计数明细来缩短文字。较大结构调整单列建议。
4. 方法保持操作顺序和复现条件；结果段按实际报告对象选择时态，不为统一时态而改写命题、公式或文献事实。
5. 用现有标签保留引用与交叉引用；公式、实验数值和源码结构不因语言替换而改变。
6. 修改后比较差异，并编译检查断行、公式、算法、题注与交叉引用。干净稿中删除作者备注，但保留它们在计划里的待核实状态。