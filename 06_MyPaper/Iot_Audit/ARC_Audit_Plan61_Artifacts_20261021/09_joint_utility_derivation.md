# Plan61 后续理论候选：读取上限内认证记录恢复的二维生成函数

日期：2026-10-21。本文是独立推导与小实例理论自检，**不是本轮正式结果，也不是已经完成的新算法或创新证明**。仅新增本文；02/03 文档、冻结 runtime、候选与实验规则均不修改。写作时未读取 Plan61 正式结果。

## 提纲与核对结论

先固定成本与故障语义，证明成功执行的读片数不依赖两个获取阶段的次序，再推导生成函数及预算内成功概率，最后解释其与现有代码预算的差别、失效边界和下一轮实现接口。

结论：在完整记录依赖集合固定、互不相交满条带、等长4096 B片、请求冷缓存、纯擦除、有效认证元数据已常驻、原页优先的 eager 整片恢复等假设下，题述二维式成立。它把“能恢复”改为“能在给定有效载荷读取额度内完整恢复”，可直接表达宽码的读取代价。该式目前是候选建模工具；还没有完成真实读取上限执行器、广码基线验证、跨数据确认或新颖性排查。

## 1. 模型、符号与必须成立的假设

| 符号 | 含义 |
|---|---|
| n | 实际原始密文对象数 |
| P_s | 条带s的实际原页集合；不同条带互不相交 |
| k_s, r_s | 条带s的实际原页数和校验片数，|P_s|=k_s；可为异构MDS，r=1可为XOR |
| P | 所有受保护原页的并集，|P|=sum_s k_s |
| N | 物理故障总体 n+sum_s r_s，不含虚拟零槽位或常驻可信元数据 |
| D_i | 请求i在该固定快照下完整且精确的原页依赖集合 |
| a_is | |D_i intersect P_s| |
| u_i | |D_i minus P|，必须直接存活的未保护依赖页数 |
| F_i | n-|P|-u_i，未保护且该请求不需要的自由原页数 |
| m | 从N个物理对象中等概率、不放回选择的固定擦除数 |
| ell | 每个实际原页和校验片的长度，本节固定4096 B |
| C_i | 成功执行下载的有效载荷片数；原始/校验片同单位，缓存命中和重建产物不再收费 |
| L, b | 读取上限L字节，b=floor(L/ell)片。保护侧车的存储预算是另一变量 |

“完整且认证”是在以下有效设置条件下讨论的：所有者诚实构建、正确密钥、元数据/可信pin已验证、对象内容与签名承诺一致、解码器/码实现正确。故障只有缺失，缺失读取返回零载荷；未发生哈希伪造、签名攻击、AEAD损坏、超时或瞬时状态变化。模型不重新证明密码学安全，也不把这些条件的失败概率算进m。

读取器还必须满足：

1. 请求开始时原片、校验片缓存为空；同一恢复器/缓存持续覆盖所有阶段，读取过的有效片与已确认擦除均缓存，不逐页或逐阶段重建实例。
2. 上层只显式要求D_i中的页；初始结构/引用页集合I_i是D_i的子集。其余获取仅由这些页触发条带修复。
3. 先尝试目标原页。需要修复时，eager检查该条带所有原页；再按固定顺序获取足够的校验片，使有效片总数达到k_s即停止。
4. 成功重建后验证所有实际原页对原承诺的匹配，再将整个条带的原页内容发布到缓存。后续需要其中任何页都不再触发存储下载。
5. 本定理统计串行、无预取、无重复传输的实际对象载荷。它不统计RPC/失败探测消息、初始化签名读取、CPU、内存、读取尝试次数或端到端时延。
6. 下面首先研究无额度截断时的完整执行，再按总载荷筛选是否在额度内。它不是对当前代码已经实现硬上限的声明。

已知D_i是**离线所有者/分析模型已知**，不要求线上检索器预先知道D_i。第3节证明为什么线上二阶段发现仍可用这个固定集合做离线评分。

## 2. 给定故障集合时，成功成本的确定式

考虑某条带(k,r,a)，a为本请求必需的原页数。

### 情况A：a个必需原页全存活

请求直接取得这a个原页。该条带其余k+r-a个对象可以任意擦除；即使整条带已不可整体解码，也不影响当前请求。没有该条带的必需页丢失，就不会因本请求触发其修复。成功成本恰为a片。

### 情况B：至少一个必需原页缺失，且条带总擦除数不超过r

第一个缺失必需页触发修复。设原页中有e个擦除。eager获得所有k-e个存活原页，再取得e个存活校验片，共k片。若此前阶段已读取了部分存活必需原页，它们包含在这k片中，由缓存避免重复计费。

重建并验证成功后，所有条带原页均可从缓存提供；随后其它必需页不再下载。因此该条带整个请求的成功成本恰为k片，不是“此前已读的片再加k”。

### 情况C：至少一个必需原页缺失，且条带总擦除数超过r

该条带不可恢复，请求失败。它可能已消耗读取成本，但没有成功项进入本节的生成函数。

由此，在成功执行上，

\[
C_i(M)=u_i+\sum_s
\begin{cases}
a_{is},&D_i\cap P_s\text{中的原页全存活},\\
k_s,&\text{否则且该条带可恢复}.
\end{cases}
\]

未保护依赖页全部存活是成功的必要条件，每页读取一次，贡献u_i。不同条带不共享片，故各条带成本相加。对于a=0的条带，永远属于情况A，成本为0。

这说明成本取决于该故障集合与依赖/条带关系，不取决于上层先处理哪个必需页。**这只是成功执行的载荷性质；失败执行的提前停止成本通常与次序有关。**

## 3. 二阶段认证发现不会破坏成功成本定理

本次只读核对的现有实现：

- sandbox/route_a_secure/secure_recovery.py:33–42 导出initial_pages；这些是结构与引用页。
- 同文件:76–86 的exact_pages明确从initial_pages union local_pages起步，再根据已认证解密的BaseID加入字典页，所以I_i subset D_i。
- 同文件:125–127 先acquire(initial_pages)，再计算exact_pages并acquire(needed)。plaintext cache在同一次recover内保留。
- sandbox/route_a_utility_plan61/mixed_rs.py:247–275 对原片/校验片缓存并计实际读取；:285–293 为eager“原页全部检查、校验片只取足k”的路径；重建后验证和缓存整个条带。
- secure_recovery.py:129–147 的最终解析使用认证明文缓存；缺页或不匹配会失败，不再绕过fetch读取隐含文件。

证明分两种情况即可：

1. 若某条带的全部必需页存活，初始与最终阶段合起来只需取得其中a个不同原页，不发生修复。
2. 若某个必需页缺失且最终成功，无论这个缺失出现在引用发现阶段还是最终字典/局部数据阶段，第一次修复都把之前已取得的该条带原页计入缓存，并将本条带总有效下载补足到k。其后的必需页全部命中已重建缓存。

因此，即使最终字典页只有解密BaseID后才能知道，成功总载荷仍由最终固定D_i描述。这里没有把D_i预先交给线上客户端，也没有利用故障mask选择读取策略。

下列改动会打破这段对接：每阶段使用新的MixedFetch；主动预取D_i之外的条带；提前失败后换一条更宽松的查询路径；只缓存目标重建页而丢弃其余原页；实际解析器需要D_i未包含的页。若采用Conservative策略，第一阶段可能获取D_i之外的公共闭包页，必须改用它真正要求的集合，不能沿用Exact的D_i计算成本。

## 4. 单条带二维生成函数

z的指数计该条带擦除数，w的指数计成功载荷片数。令

\[
A_{k,r,a}(z)=(1+z)^{k+r-a},
\]

其系数统计必需原页全存活时，其他对象的任意擦除模式；情况A贡献w^a A。

总擦除数为j且至少一个必需原页丢失的模式数为

\[
\binom{k+r}{j}-\binom{k+r-a}{j}.
\]

只有1<=j<=r时这些模式可恢复，成功成本为k。情况B与A互斥，因此

\[
\boxed{
G_{k,r,a}(z,w)
=w^a(1+z)^{k+r-a}
+w^k\sum_{j=1}^{r}
\left[\binom{k+r}{j}-\binom{k+r-a}{j}\right]z^j
}.
\]

当a=0时，第二项为0，G=(1+z)^(k+r)，没有读取成本。当a=k时，两类成功事件虽然拥有相同w指数，系数应相加，不能覆盖。失败事件无项。

这不假设各条带在固定m下独立；先通过多项式乘法计数所有物理组合，再取总z^m系数，已经保留了固定总擦除数带来的耦合。

## 5. 完整记录的额度内成功率

全部条带都纳入乘积时，记录生成函数为

\[
Q_i(z,w)=w^{u_i}(1+z)^{F_i}\prod_sG_{k_s,r_s,a_{is}}(z,w),
\qquad F_i=n-\sum_s k_s-u_i.
\]

u_i个未保护依赖必须存活，只贡献w^u而不贡献自由擦除项；F_i个其余未保护原页不影响请求。a=0条带的全部物理对象已在对应G中计入，不能再次加到F里。若实现把a=0条带从乘积移除，才需把其k+r个对象另加到自由因子。

定义

\[
[z^m w^{\le b}]Q_i
=\sum_{c=0}^{b}[z^m w^c]Q_i.
\]

对均匀固定m故障集合，

\[
\boxed{
V_{i,m,L}
=\Pr(S_i\land\ell C_i\le L)
=\frac{[z^m w^{\le\lfloor L/\ell\rfloor}]Q_i(z,w)}
{\binom Nm}
}.
\]

所有系数和分母均可用整数精确表示；最后展示时再转浮点。若目标请求按事先固定的权重rho_i分布，效用为sum_i rho_i V_i；均匀记录就是取平均。不同方案自己的N与m=ceil(alpha*N)必须分别计算；不能把跨N的相同m冒充相同alpha。

多记录请求应使用其实际合并依赖D(T)，每个请求只计一次共享缓存。平均单记录V不等于批量请求的联合成功率或成本。

可立即检验的性质：

- b增大时V单调不减；b足够大时退化为原一维availability模型。
- 因C_i>=|D_i|，若b<|D_i|，连无故障读取也不满足额度。
- 同一条带内a=k时，完整读取本条带本来就需要k片；成功修复不会增加等长有效载荷片数。
- 令w=1可恢复原G(z)；在w=1处对Q求导可得E[C_i 1{S_i}]的分子。除以Pr(S_i)后才是成功条件下平均成本；这不是全部请求的平均成本。
- 本函数只刻画给定布局的效用，不提供最优规划算法、近似比或复杂度下界。

## 6. 一个能说明研究价值的单故障推论

设d=|D_i|、所有r_s>=1且m=1。故障未命中D_i时共有N-d种模式，成本为d；故障命中条带s中的必需原页时有a_is种模式，修复使总成本变为d-a_is+k_s；命中未保护依赖则失败。因此

\[
\boxed{
V_{i,1,b}
=\frac{
(N-d)\,\mathbf1\{d\le b\}
+\sum_s a_{is}\,\mathbf1\{d-a_{is}+k_s\le b\}
}{N}.
}
\]

b趋于无穷时，退化为1-u_i/N，即固定保护集合下的单故障可用性与分组无关。但有限读取额度会让条带宽度k_s和依赖集中程度a_is在单故障时就影响目标。

这给依赖分组提供了比“可能有用的Jaccard”更直接的机制解释：同样能够恢复的两种布局，可能只有一种能以有限数据读取量完成记录。它也解释宽码为何不能只凭高可用性占据所有方案的优势。该推论是本文针对指定模型的推导，尚未完成相关工作穷尽检索，不能称“首次”。

## 7. 与真实max-bytes执行器的差别

### 7.1 当前budget不是这个物理读取额度

secure_recovery.py:108–111 用尚未进入明文cache的请求原页长度累计planned；:115–118 的response_bytes累计外层fetch返回的目标原页字节。它们都不直接等于辅助原页与parity的物理读取总量。

例如模型中D只有一个原页，原页丢失后需k=4个辅助有效片：外层逻辑请求仍是一页，而底层可读取四片。将旧budget参数设为L，不能声称已经限制真实恢复载荷。反过来，从重建cache交付目标原页也不该再次计作网络/存储下载。

未来执行器须在原片和校验片的共同物理读取边界计费；只包裹CloudStore原页fetch会漏掉parity读取。应保留单独的logical response、original bytes、parity bytes和total physical payload字段。

### 7.2 系数事件可以对应硬上限，但需要单独的实现与等价性验证

Q先描述无上限执行中的成功成本，再判断是否<=L。要实现严格上限，在线计费器应只利用已发生的请求、缓存、公开侧车及已认证引用，决定是否还能发起下一次物理读取；不能先查离线D或故障mask。

在等长、单线程、无预取、纯擦除等假设下，如果额度器不会误拒绝任何总成功载荷<=L的执行，则硬上限下的成功事件与Q的事件相同：成功路径的载荷前缀不超过其总量；总量>L的路径必须在完成前被拒绝。这个“不会误拒绝”是需要证明和测试的实现性质，不应直接假定。

计费语义不同会改变事件。例如按每次尝试预收4096 B、连返回None的缺失尝试也不退还额度，会比本模型更保守；k=2,r=1的目标原页缺失，实际成功载荷为2片，但目标原页失败探测加两次有效下载共3次尝试。若只允许2次尝试，它就失败。RPC消息/超时应使用另外的成本模型。

将无上限运行结果事后按bytes筛选，可以估计V；但不能把其耗时、失败成本或已实际超过上限的传输，报告成已经执行了硬上限的服务。当前没有完成此执行器验证。

## 8. 明确不适用的边界与反例

| 情况 | 为什么简单G(z,w)不再是实际字节分布 | 后续处理 |
|---|---|---|
| 最后一原页较短 | 同样k个有效片可能包含短原页，字节数不等于4096*k；a与j不足以确定字节 | 对实际长度类别扩展权重/状态，或明确统一收费单位模型；不能偷偷把片数当真实字节 |
| 坏块返回完整损坏载荷 | 无效块占流量但不计有效片；如k=2,r=1目标损坏，下载坏目标后再读2有效片，总3片而非2 | 扩展损坏读取与探测顺序状态；目前仅纯擦除 |
| 全部请求平均成本 | 失败请求已消耗的流量被Q有意排除，提前停止点随次序变化 | 单独测/建模失败分布，不用成功条件均值替代 |
| 元数据、pin或签名不常驻 | 请求前有额外读取与验证；失效也可能使整个请求失败 | 对确定开销可移位额度；对随机/失败开销另建状态并计入总体 |
| Warm cache或跨请求复用 | 部分片在开始前免费可用，且缓存与故障可能相关 | 以已知缓存状态为条件评分，或给出预先固定的缓存分布 |
| 跨阶段丢弃cache | 初始原页可能在修复时再次下载，成功成本超过k | 共享同一恢复器、预算和缓存，并做集成测试 |
| 不发布全部重建原页 | 之后的同条带必需页可能再次下载/解码 | 按真实cache策略建模 |
| 并发预取、重试、超时、对象状态变化 | 已在途/重复字节或晚到响应改变成本和成功事件 | 定义并验证真实调度模型 |
| 虚拟零槽位 | 已知零槽位无需物理读取，不能按k个真实片收费，也不能纳入故障总体 | 对缩短码/已知槽单独推导 |
| 重叠条带、LRC、跨文件迭代恢复 | 片和恢复路径不再按条带独立分解 | 使用其真实编码图和恢复策略；不得直接套本乘积 |
| 读模式改变 | lazy也可能在本理想模型的成功路径读k片，但失败/短页/坏块成本可不同 | 当前命题只绑定已核对eager路径；扩展需独立证明和测试 |
| 错key、篡改元数据或不诚实构建 | 足够片不保证AEAD/解析成功 | 作为安全失败测试；不能用故障概率定理替代安全证明 |
| 实际需要页超出D_i | 初始引用、私有framing或解码器读集合不完整 | 必须以真实认证解码器的完整集合定义D |

短页的一个反例：k=2,r=1，必需目标缺失，另一存活原页仅1024 B，校验片4096 B。eager实际下载5120 B，G按片数给2*4096=8192 B。可以把它当统一对象收费模型或保守计量，但不能称精确物理字节。

失败次序的一个反例：两个未保护必需页中页0缺失、页1存活。先取页0即失败，载荷0；先取页1再取页0则消耗1片后失败。故“路径无关”严格限定在成功执行，不延伸到全部请求。

### 8.1 对接本轮真实frame长度时的更精确表达

本轮对象是密文frame：原始载荷包含nonce与AEAD tag，原页长度应取已签名descriptor中的实际frame字节数；parity由补齐后的密文编码得到。4096 B等长假设只是上文理想例，不代表本轮每个原页都恰好4096 B。物理original_bytes与parity_bytes还会计入已经读取、随后验证失败的坏块字节。

令原页p的真实长度为ell_p，校验片长为ell（当前通常为4096）。在其余假设不变、仍为纯擦除且采用eager时，给定本条带擦除集合M_s，成功字节成本可精确写为

\[
c_s(M_s)=
\begin{cases}
\displaystyle\sum_{p\in D_i\cap P_s}\ell_p,
&\text{必需原页全存活},\\[2mm]
\displaystyle\sum_{p\in P_s\setminus M_s}\ell_p
+|P_s\cap M_s|\ell,
&\text{至少一个必需原页丢失且条带可恢复}.
\end{cases}
\]

第二行的理由是eager仍读取全部存活原页，加上与原页擦除数相等的有效parity。虚拟补零在内存中完成，不应补记为原页的物理下载。因此，**短页本身不破坏eager成功字节数对阶段次序的不变性；它破坏的是只按(k,r,a)使用w^a/w^k的等长简化。**

若v的指数直接计字节，可定义

\[
G^{\rm bytes}_{s,i}(z,v)
=\sum_{M_s\in{\cal S}_{s,i}}
z^{|M_s|}v^{c_s(M_s)},
\]

其中集合S只含该条带对请求成功的擦除模式。以未保护必需原页的实际长度总和作v的前置指数，再乘自由对象因子和各条带G_bytes，提取[z^m v^{<=L}]即可得到真实frame载荷额度下的精确模型概率。此处上限L直接是字节，无需floor(L/ell)。

这给出了定义层面的修正，**尚未实现高效求值器**。直接枚举宽条带的2^(k+r)种局部模式通常不可行，下一轮需按长度类别/必需性等设计可验证DP，或先限定并公开支持的长度结构。等长理论自检不能冒充这套真实frame模型已通过测试。

即便采用这个实际长度版本，签名/manifest的冷读取、损坏载荷、失败请求、跨请求缓存、重叠码、重试和超时仍不在成功纯擦除模型中。对应硬cap执行器必须逐例核对模型CDF与真实完成事件，不能仅用均值或总成功次数相同代替。

## 9. 下一轮可实现的接口与验证顺序

以下是候选下一阶段工作，不属于本轮已实现结果：

1. **离线规划器。** 所有者从合法解密得到FullGraph，传入固定请求分布、公开页长度、候选条带、存储预算及预先固定的L集合。不得传入正式fault cases或未来目标抽样。计划和数据依赖侧车可能泄露的信息需写入Leak定义。
2. **JointEvaluator。** 以稀疏整数二维多项式或等价DP计算V；m、读取次数均可按所需上限安全截断。对a=0因子做自由对象合并；记录重复依赖可用整数权重合并。输出分子/分母、单位、模型假设和计算成本。
3. **有限状态优化。** 以V或明确的Pareto目标筛选覆盖、码强度和分组；强基线须包含宽uniform配置及公平的元数据格式。不能将18码库最优或精确评分等同全局最优。
4. **线上认证检索器。** 只接收target、可信snapshot、合法key和公开sidecar，按原二阶段获取。initial_pages认证/解密后才得到BaseID和最终needed；不接收离线D。缓存和physical byte limiter跨两个阶段共享。
5. **物理计量器。** 同时覆盖original和parity；缓存/重建的交付不重复收费；明确短页、失败探测和损坏载荷的处理。先决定是真实载荷、统一片收费还是含协议开销的wire bytes，再匹配模型。
6. **验证顺序。** 先小图穷举；再真密文、签名/hash/AEAD的模拟小归档逐mask比较；然后用真实页长/全部失败分支检查模型误差和硬上限；最后才做冻结后的新数据确认。
7. **指标。** 首先展示预先固定的完整读取额度曲线V(alpha,L)，以及无额度的U(alpha)、实际成功率、超额拒绝、全部尝试成本及共同成功配对成本。不能在看到结果后挑选有利上限；若后来选单个L，须有独立应用依据并重新冻结验证。
8. **安全测试。** 对预算拒绝无部分记录输出、错key/清单/快照、坏块、错误BaseID、修复后hash不匹配等保持显式失败；函数的概率正确不代表实现已安全。

目前最有实质的候选方向是“认证记录闭包的可用性—读取成本联合建模与规划”。是否足以成为核心贡献，仍取决于超越强基线的效果、理论/实现闭环和与已有工作的具体差别。

## 10. 纯理论自检：完成了什么，没完成什么

使用下附可复现Python，直接枚举全部故障集合，并独立模拟eager阈值恢复、缓存、阶段拆分和访问顺序。对成功执行统计完整(m,载荷片数)直方图，与二维多项式全部系数相等；对全部读取上限继续核对累计系数。

本次输出：

| 项目 | 数量 |
|---|---:|
| 小配置 | 6 |
| 依赖集合案例 | 28 |
| 枚举故障集合（按依赖案例计） | 13504 |
| 阶段/访问顺序执行 | 171752 |
| 累计预算系数核对 | 1581 |
| 结果 | PASS |

覆盖无侧车、无依赖数学边界、未保护依赖、整条带依赖、多个条带、异构r及r=1/2/3。最大物理总体N=11。有些k=2用于最小数学例子，不是改变本轮冻结码库。

这只是有限实例的理论自检，支持排除公式/计数错误；一般命题仍由第2–5节论证支撑。模拟器用MDS阈值，不执行真实GF编码、签名、哈希、AEAD或在线额度器，也未加载任何归档、源记录和正式实验结果。因此不是性能提升证据、密码学验收或可投稿结论。

## 11. 原始文献与新颖性边界

- **Huang等，Erasure Coding in Windows Azure Storage，USENIX ATC 2012，15–26。** 已阅读官方全文的恢复成本与LRC机制；说明低冗余之外还需限制读取片数、I/O与延迟。本文的读取约束动机不能当新颖概念。[官方论文页](https://www.usenix.org/conference/atc12/technical-sessions/presentation/huang)、[全文](https://www.usenix.org/system/files/conference/atc12/atc12-final181_0.pdf)。
- **Gopalan、Huang、Simitci、Yekhanin，On the Locality of Codeword Symbols，arXiv:1106.3625，2011。** 已核对全文定理5及相关定义；编码冗余、距离和locality之间已有严格界限。本推导使用整片MDS恢复，不能宣称对所有编码/子分片修复都最优。[原始全文入口](https://arxiv.org/abs/1106.3625)。
- **Dimakis、Godfrey、Wu、Wainwright、Ramchandran，Network Coding for Distributed Storage Systems，arXiv:0803.0632。** 本次核对作者提交的摘要与书目；其storage–repair-bandwidth权衡和函数式下载说明整片RS只是一个限制类。没有在本次重做其完整安全/编码证明。[作者预印本](https://arxiv.org/abs/0803.0632)。
- MOAT的多对象可用性、PFP的文件语义保护、TREAT的压缩编码查询，以及近期degraded-read工作，已在 [03_related_work_gap.md](../ARC_Audit_Plan61_Related_Work_Gap_20261021.md) 列原始来源与阅读深度。二维生成函数是否已有同类表达、同类记录目标或同类规划，仍须专项查重；本次不作“首次”保证。

## 12. 代码定位版本与写作检查

本次只读源文件SHA256：

| 文件 | SHA256 |
|---|---|
| sandbox/route_a_secure/secure_recovery.py | 4dba4a676fd83f4f23a1f8094bc9afcfc4687acf1de2d78727818b5e93df322b |
| sandbox/route_a_utility_plan61/mixed_rs.py | 470b76000183172903fe1623cda25f08d3c4df125053b944f92fca62ca364d70 |

这些哈希标识本推导检查的接口版本；本文件没有读取或验证正式运行receipt。02/03仍分别为e684d5458a7125cfb1a930f8f917675979384531d20a202a2526772c0faf8c69与737bb983778773c17f692e291c87d44b89953ae7f23918de276149bb7420bbd6。

按research-paper-writing方法/审稿检查：贡献是候选，精确式的假设和成本单位明确；理论自检不能代替实现/实验；短页、失败、上限执行与安全前提未混为一谈；下一轮须用强基线与新确认决定是否保留。主稿暂不改写成“已实现的新联合最优化方法”。

## 附录：本次内存执行的完整理论自检代码

运行该代码只使用Python标准库和内存，不需要实验目录。最后一行打印JSON。以下代码SHA256：854c5bca98874e0cbbdcb931fdd309493acc8f5099bedb1231eb1d12f4a9f8af。

~~~python
from collections import Counter
from itertools import combinations, permutations
from math import comb
import json, hashlib

def multiply(a,b):
    out=Counter()
    for (za,wa),ca in a.items():
        for (zb,wb),cb in b.items():
            out[za+zb,wa+wb]+=ca*cb
    return +out

def poly(n,stripes,D):
    protected={p for P,r in stripes for p in P}
    u=len(set(D)-protected)
    out=Counter({(j,u):comb(n-len(protected)-u,j)
                 for j in range(n-len(protected)-u+1)})
    for P,r in stripes:
        k=len(P); a=len(set(P)&set(D)); component=Counter()
        for j in range(k+r-a+1):
            component[j,a]+=comb(k+r-a,j)
        for j in range(1,r+1):
            component[j,k]+=comb(k+r,j)-comb(k+r-a,j)
        out=multiply(out,component)
    return out

def simulate(n,stripes,D,missing,first,second):
    mapping={p:s for s,(P,r) in enumerate(stripes) for p in P}
    offsets=[]; N=n
    for P,r in stripes: offsets.append(N); N+=r
    cache={}; pcache={}; payload=0
    def original(p):
        nonlocal payload
        if p not in cache:
            cache[p]=p not in missing
            payload+=int(cache[p])
        return cache[p]
    def parity(s,j):
        nonlocal payload
        p=offsets[s]+j
        if p not in pcache:
            pcache[p]=p not in missing
            payload+=int(pcache[p])
        return pcache[p]
    def fetch(p):
        if original(p): return True
        if p not in mapping: return False
        s=mapping[p]; P,r=stripes[s]; k=len(P)
        valid=sum(original(member) for member in P)
        if valid<k-r: return False
        for j in range(r):
            if valid>=k: break
            valid+=int(parity(s,j))
        if valid<k: return False
        for member in P: cache[member]=True
        return True
    plaintext=set()
    for phase in (first,second):
        for p in phase:
            if p in plaintext: continue
            if not fetch(p): return False,payload
            plaintext.add(p)
    assert plaintext==set(D)
    return True,payload

specs=[
    (3,[],[(),(0,),(0,1),(0,1,2)]),
    (4,[((0,1),1)],[(),(0,),(0,1),(0,2),(2,3)]),
    (6,[((0,1),1),((2,3),2)],[(),(0,2),(0,2,4),(0,1,2,3),(4,5)]),
    (6,[((0,1,2,3),2)],[(),(0,),(0,1,2),(0,4),(4,5)]),
    (8,[((0,1,2,3),1),((4,5,6,7),2)],[(),(0,4),(0,1,4),(0,1,4,5)]),
    (5,[((0,1,2,3),3)],[(),(0,),(0,1),(0,1,2,3),(0,4)])
]
total_masks=total_paths=cap_checks=0
summary=[]
for n,stripes,Ds in specs:
    N=n+sum(r for P,r in stripes)
    for D in Ds:
        D=tuple(D); computed=poly(n,stripes,D); observed=Counter()
        plans=set()
        for order in permutations(D):
            plans.add(((),order))
        for cutmask in range(1<<len(D)):
            first=tuple(D[j] for j in range(len(D)) if cutmask>>j&1)
            second=tuple(D[j] for j in range(len(D)) if not cutmask>>j&1)
            plans.add((first,second))
        for m in range(N+1):
            for lost in combinations(range(N),m):
                total_masks+=1
                M=set(lost)
                answers=[]
                for first,second in plans:
                    ok,cost=simulate(n,stripes,D,M,first,second)
                    total_paths+=1
                    answers.append((ok,cost))
                assert len({ok for ok,cost in answers})==1
                if answers[0][0]:
                    assert len(set(answers))==1
                    observed[m,answers[0][1]]+=1
        assert observed==computed
        for m in range(N+1):
            for B in range(n+1):
                left=sum(c for (j,cost),c in computed.items() if j==m and cost<=B)
                right=sum(c for (j,cost),c in observed.items() if j==m and cost<=B)
                assert left==right
                cap_checks+=1
        summary.append(dict(n=n,N=N,stripes=[dict(k=len(P),r=r) for P,r in stripes],
                            D=list(D),success_patterns=sum(observed.values()),
                            histogram_terms=len(observed),phase_order_plans=len(plans)))
print(json.dumps(dict(status='PASS',scope='pure theoretical equal-length erasure threshold simulation; no archive, source records or formal results read',
     configurations=len(specs),dependency_cases=len(summary),fault_masks=total_masks,
     execution_paths=total_paths,budget_coefficient_checks=cap_checks,
     cases=summary),sort_keys=True))
~~~
