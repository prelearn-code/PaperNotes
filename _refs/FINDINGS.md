# PDP/PoR 定向检索 — 证据登记表（工作文件）

判定标准：
- N1 形式模型显式允许恶意/经济动机服务器伪造审计应答（半诚实/诚实执行 = 不满足）
- N2 响应存在可缓存低维充分状态（固定投影、逐块摘要、公开标签）
- N3 该状态比特数 < 诚实服务器需保存的状态
- N4 可用真实群运算/配对复现

排除码：E1 诚实执行假设 / E2 半诚实模型 / E3 信任根转移 / E4 纯功能组合

---

## 候选 1：Gritti–Susilo–Plantard ACISP'15 DPDP 方案（被 2015/645 攻击）
- 链接：https://eprint.iacr.org/archive/2015/645/1446094524.pdf （ePrint 2015/645，已被作者撤回，archive 版可访问）
- 目标方案出处：Gritti, C., Susilo, W., Plantard, T., 2015. Efficient dynamic provable data
  possession with public verifiability and data privacy. ACISP'15. （引自 2015/645 参考文献 [5]，
  未读到 ACISP'15 原文）
- 威胁模型：2015/645 §2.2.1 "Security against the server" 给出 data possession game，
  adversary A 拥有 TagGen/DataOp 预言机，最后 "Forge. A generates a proof of data possession ν
  on chal." 该形式模型确实允许 A 任意构造伪造 ν。**但未读到 ACISP'15 原文威胁模型段落**。
- 攻击（2015/645 §3.1 Replace Attack，读到正文 p.8–9）：
  - 诚实存储需保存全部 n 个块 m_i 与 n 个标签 T_{m_i}
  - 恶意服务器只保存一个块 m_1 与其标签 T_{m_1}
  - GenProof：c = ∏_{(i,v_i)∈chal} T_{m_1}^{v_i}      （原文 line 382-387）
  - b_j = Σ_{(i,v_i)∈chal} m_{1,j}·v_i + r_j           （原文 line 377-381）
  - ν = (R_1..R_s, B_1..B_s, c) ∈ G_1^{2s+1}
  - 原文 line 498：'Therefore, Eq. 1 holds, although the server is actually storing one block only.'
  - 原文 line 499-500：'This attack is not due to the dynamicity property of our scheme.
    Such attack could happen even on static data.'
- N1 部分满足（游戏允许伪造）；N2 满足（响应依赖常数量状态 (m_1,T_{m_1})）；
  N3 满足（O(1) vs O(n)）；N4 满足（仅配对+群指数）
- 证据层级：攻击方正文；目标方案仅二手（经 2015/645 转述）
- 待核验：ACISP'15 原文的威胁模型是否显式允许恶意服务器

## 候选 2：Wang et al. 公开审计协议（被 ePrint 2012/115 攻击）
- 链接：https://eprint.iacr.org/2012/115 （Xu Chun-xiang, He Xiao-hu, Daniel Abraha,
  "Cryptanalysis of auditing protocol proposed by Wang et al. for data storage security in Cloud Computing"）
- 目标方案：Wang et al. 的 public auditing protocol（未读到原文）
- 威胁模型原句（读到正文 p.3）：
  "The cloud server might be a malicious cloud server which might not keep data or might delete
   data owned by cloud users and might even hide some data corruptions."
  "the malicious cloud server can pass the auditing from the TPA when he loses the outsourced data."
- 方案公式（正文 p.3）：
  - TagBlock: σ_i = (H(i)·u^{m_i})^x ∈ G_1
  - GenProof: r = f_{k2}(chal); R = (u^x)^r; μ' = Σ_{i∈I} v_i m_i;
    μ = μ' + r·h(R); σ = ∏_{i∈I} σ_i^{v_i}
  - CheckProof: e(σ·R^{-h(R)}, g) = e(∏_{i∈I} H(i)^{v_i}·u^μ, v)
- 攻击 Scheme II "Data lost Auditing pass attack"（正文 p.4）：
  - 服务器预先计算并保存 T = {t(i) = σ_i/u^{m_i} = H(i)^x, 1≤i≤n}
  - μ* = r·h(R), σ* = ∏_{i∈I} t(i)^{v_i}
  - 原文："the malicious cloud server also can pass the auditing from the TPA although he does
    not possess the user's data."（line 875-877）
  - 原文："It is clear that the TPA verifies equation e(σ*·(R^{h(R)}), g) = e(∏ H(i)^{v_i}·u^{μ*}, v) equal."
- N1 满足（主动攻击者=m恶意 CSP，显式）；N2 满足（状态 = 逐索引摘要集合 T）；
  **N3 不满足**：T 有 n 个群元素，与诚实服务器保存的 n 个块 + n 个标签同阶（≈ 甚至更大），
  并未小于诚实方状态。作者本人也只声称"不需要持有用户数据"，未声称状态更小。
- 证据层级：攻击方正文（p.1-6 全文）；目标方案二手

## 候选 3：Liu, Guo et al., Security and Communication Networks 2021
- 标题：Security Analysis and Improvements on a Remote Integrity Checking Scheme for
  Regenerating-Coding-Based Distributed Storage
- 链接：https://onlinelibrary.wiley.com/doi/10.1155/2021/1805615
- 检索索引片段（**只看到片段，未读到正文**）：
  "Our attack II is based on the following observation: even if the CSP does not store any data
   blocks, the auditor does not need t[o ...]"
  （来源：Wiley XML 页面在搜索引擎中的片段）
- 状态：付费墙/Cloudflare 403，未获取正文。N1–N3 均**未核实**。
- 证据层级：仅片段（非题名、非摘要，是正文片段）

---

## 排除记录
（待补）
