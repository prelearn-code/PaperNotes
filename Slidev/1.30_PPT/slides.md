---
# ================= 全局配置 =================
theme: seriph
title: Efficient Blockchain-Based Data Integrity Auditing  for Multi-Copy in Decentralized Storage
info: |
  ## Slidev Presentation
  Presentation slides for developers.
transition: slide-left
mdc: true

layout: cover
hideInToc: true
background: https://cover.sli.dev
class: text-center
---

# Efficient Blockchain-Based Data Integrity Auditing  for Multi-Copy in Decentralized Storage

<div class="opacity-50 text-sm mt-2">
  IEEE Transactions on Dependable and Secure Computing(2023)
</div>

汇报人：张松伟
日期：1.30

---
hideInToc: true
layout: center
class: text-center
---

# 目录

<Toc minDepth="1" maxDepth="1" />

---
layout: default
---

# 方案背景

<div class="leading-relaxed opacity-90 mb-8">
  在去中心化网络存储时代，<b>信息安全性</b>是核心挑战。
  <br>
  目前的审计方案（PDP/POR）虽然解决了部分问题，但在<b>多副本存储</b>场景下存在漏洞：
  <span class="text-red-700 bg-red-100 px-1 rounded font-bold">云服务商可能内部勾结，只存一份数据却收取多份费用。</span>
</div>

<div class="mt-4 mb-6 font-bold text-xl border-b border-gray-500 pb-2">
  🚫 现存方案的三大核心缺陷
</div>

<div class="grid grid-cols-3 gap-6">

  <div class="bg-white text-gray-800 p-5 rounded-xl shadow-md border border-gray-200">
    <div class="text-4xl mb-3">🤝</div>
    <div class="font-bold text-lg mb-2 text-black">第三方不可信</div>
    <p class="text-sm opacity-80 leading-normal">
      引入第三方审计员(TPA)带来了新的信任风险，审计员可能并不中立。
    </p>
  </div>

  <div class="bg-white text-gray-800 p-5 rounded-xl shadow-md border border-gray-200">
    <div class="text-4xl mb-3">🛑</div>
    <div class="font-bold text-lg mb-2 text-black">服务单点故障</div>
    <p class="text-sm opacity-80 leading-normal">
      审计完全依赖第三方，一旦其发生故障，审计服务将完全停滞。
    </p>
  </div>

  <div class="bg-white text-gray-800 p-5 rounded-xl shadow-md border border-gray-200">
    <div class="text-4xl mb-3">🛡️</div>
    <div class="font-bold text-lg mb-2 text-black">信任假设不可靠</div>
    <p class="text-sm opacity-80 leading-normal">
      预设“云管理者与服务商是诚实的”这一前提在现实中往往不成立。
    </p>
  </div>
</div>


---
layout: default
---

# 基础技术介绍

<div class="opacity-90 mb-6">
本方案基于以下两个核心密码学原语：
</div>

<div class="grid grid-cols-2 gap-10">

<div class="bg-white text-gray-800 p-6 rounded-xl border-l-4 border-blue-600 shadow-xl">
<div class="text-4xl mb-4">🧩</div>
<h3 class="text-2xl font-bold text-blue-800 mb-4">PCS-PLONK</h3>
<div class="text-sm font-bold text-gray-700 mb-1">核心逻辑：</div>
<p class="text-sm opacity-90 mb-4 leading-relaxed text-gray-600">
将程序的正确执行转化为<b>多项式约束问题</b>(Arithmetization)。
</p>
<div class="text-sm font-bold text-gray-700 mb-1">关键作用：</div>
<p class="text-sm opacity-90 leading-relaxed text-gray-600">
利用多项式承诺，验证者只需付出<b>极小的计算代价</b>，即可验证复杂逻辑是否成立。
</p>
</div>

<div class="bg-white text-gray-800 p-6 rounded-xl border-l-4 border-purple-600 shadow-xl">
<div class="text-4xl mb-4">📦</div>
<h3 class="text-2xl font-bold text-purple-800 mb-4">PCS-MPAP</h3>
<div class="text-sm font-bold text-gray-700 mb-1">面临挑战：</div>
<p class="text-sm opacity-90 mb-4 leading-relaxed text-gray-600">
涉及<b>多个多项式</b>在<b>多个点</b>上的验证，逐一证明效率极低。
</p>
<div class="text-sm font-bold text-gray-700 mb-1">解决方案：</div>
<p class="text-sm opacity-90 leading-relaxed text-gray-600">
<b>批量聚合证明 (Batching)</b>。一次性打包所有约束关系，大幅降低通信和验证开销。
</p>
</div>

</div>


---
layout: default
hideInToc: false
---

# PCS 方案全流程演示

<div class="grid grid-cols-[1fr_1.6fr] gap-6 items-start h-[480px]">

<div class="flex flex-col gap-3 relative h-full justify-center">
<div class="absolute left-6 top-8 bottom-8 w-0.5 bg-gray-200 -z-10"></div>

<div class="bg-white p-3 rounded-lg border-l-4 border-gray-500 shadow-sm flex justify-between items-center z-10">
<div><span class="font-bold text-gray-800 text-sm">1. Setup (初始化)</span><div class="text-[10px] text-gray-500">生成公开参数 SRS</div></div>
<div class="text-xl">⚙️</div>
</div>

<div class="bg-white p-3 rounded-lg border-l-4 border-blue-500 shadow-sm flex justify-between items-center z-10">
<div><span class="font-bold text-blue-800 text-sm">2. Commit (承诺)</span><div class="text-[10px] text-gray-500">P 计算多项式指纹</div></div>
<div class="text-xl">🔒</div>
</div>

<div class="bg-white p-3 rounded-lg border-l-4 border-yellow-500 shadow-sm flex justify-between items-center z-10">
<div><span class="font-bold text-yellow-800 text-sm">3. Open (打开)</span><div class="text-[10px] text-gray-500">V 发起挑战，P 生成证据</div></div>
<div class="text-xl">🧾</div>
</div>

<div class="bg-white p-3 rounded-lg border-l-4 border-green-500 shadow-sm flex justify-between items-center z-10">
<div><span class="font-bold text-green-800 text-sm">4. Verify (验证)</span><div class="text-[10px] text-gray-500">V 执行双线性配对检查</div></div>
<div class="text-xl">✅</div>
</div>
</div>

<div class="bg-[#1e1e1e] text-gray-300 rounded-xl shadow-2xl h-full border border-gray-700 flex flex-col font-mono text-xs overflow-hidden">

<div class="bg-[#2d2d2d] px-3 py-2 border-b border-black font-bold text-gray-400 flex justify-between">
<span>Math Walkthrough: &alpha; = 5</span>
<span class="text-[10px] opacity-60">Mocking KZG Protocol</span>
</div>

<div class="p-4 space-y-4 overflow-y-auto custom-scrollbar">

<div class="border-l-2 border-gray-600 pl-3">
<div class="text-white font-bold mb-1">1. Setup (上帝视角)</div>
<div>秘密参数: <b class="text-red-400">&alpha; = 5</b> (生成后立即销毁)</div>
<div class="mt-1 text-gray-400">公开参数 SRS (映射到群上):</div>
<div class="bg-gray-800 p-2 rounded mt-1">
SRS<sub>0</sub> = g<sup>1</sup>, SRS<sub>1</sub> = g<sup>5</sup>, SRS<sub>2</sub> = g<sup>25</sup>
</div>
</div>

<div class="border-l-2 border-blue-500 pl-3">
<div class="text-blue-400 font-bold mb-1">2. Commit (Prover 计算)</div>
<div>多项式: <i>f<sub>1</sub></i> = X+2, &nbsp; <i>f<sub>2</sub></i> = 3X</div>
<div class="mt-1 text-gray-400">利用 SRS 计算承诺 (盲算):</div>
<div class="bg-gray-800 p-2 rounded mt-1 space-y-1">
<div>C<sub>1</sub> = (g<sup>1</sup>)<sup>2</sup> · (g<sup>5</sup>)<sup>1</sup> = g<sup>2+5</sup> = <b class="text-blue-300">g<sup>7</sup></b></div>
<div>C<sub>2</sub> = (g<sup>1</sup>)<sup>0</sup> · (g<sup>5</sup>)<sup>3</sup> = <b class="text-blue-300">g<sup>15</sup></b></div>
</div>
</div>

<div class="border-l-2 border-yellow-500 pl-3">
<div class="text-yellow-400 font-bold mb-1">3. Create Witness (生成证据)</div>
<div>挑战点: <b>z=2</b>, 聚合权重 <b>v=4</b></div>
<div class="mt-1">计算值: y<sub>1</sub>=4, y<sub>2</sub>=6</div>
<div class="mt-1 text-gray-400">构造聚合多项式 & 商:</div>
<div class="bg-gray-800 p-2 rounded mt-1 space-y-1">
<div>h(X) = (X-2) + 4(3X-6) = 13(X-2)</div>
<div>商 q(X) = h(X) / (X-2) = <b>13</b></div>
<div>证据 W = (SRS<sub>0</sub>)<sup>13</sup> = <b class="text-yellow-300">g<sup>13</sup></b></div>
</div>
</div>

<div class="border-l-2 border-green-500 pl-3">
<div class="text-green-400 font-bold mb-1">4. Verify (Verifier 验证)</div>
<div>聚合承诺: C<sub>agg</sub> = g<sup>7</sup>·(g<sup>15</sup>)<sup>4</sup> = g<sup>67</sup></div>
<div>承诺差: D = g<sup>67</sup> · g<sup>-28</sup> = <b class="text-green-300">g<sup>39</sup></b></div>
<div class="mt-2 p-2 bg-gray-800 rounded border border-green-900 text-center">
<div class="mb-1 text-gray-500 text-[10px]">双线性配对检查: e(D, g) =? e(W, g<sup>&alpha;-z</sup>)</div>
<div class="text-green-300 font-bold">e(g<sup>39</sup>, g<sup>1</sup>) == e(g<sup>13</sup>, g<sup>3</sup>)</div>
<div class="text-white mt-1 text-sm">39 == 13 × 3 (成功)</div>
</div>
</div>

</div>
</div>

</div>

---
layout: default
---

# 方案逻辑

<div class="flex justify-center items-center mt-10">
  <img 
    src="./pic/image.png" 
    class="h-[400px] w-auto object-contain rounded-lg shadow-xl bg-white" 
  />
</div>


---
layout: default
hideInToc: false
---

# 方案内容

<div class="opacity-80 mb-8">
本方案主要包含以下三个核心实施阶段：
</div>

<div class="grid grid-cols-3 gap-6">

  <div class="bg-white text-gray-800 p-6 rounded-xl border-t-4 border-blue-500 shadow-xl h-full">
    <div class="text-4xl mb-4">🛠️</div>
    <h3 class="text-xl font-bold text-blue-700 mb-4">1. 初始化阶段</h3>
    <ul class="list-none pl-0 space-y-2 text-sm opacity-90">
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-400"></div> 密钥生成
      </li>
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-400"></div> 副本生成
      </li>
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-400"></div> 标签生成
      </li>
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-400"></div> 标签验证
      </li>
    </ul>
  </div>

  <div class="bg-white text-gray-800 p-6 rounded-xl border-t-4 border-purple-500 shadow-xl h-full">
    <div class="text-4xl mb-4">🔍</div>
    <h3 class="text-xl font-bold text-purple-700 mb-4">2. 审计阶段</h3>
    <ul class="list-none pl-0 space-y-2 text-sm opacity-90">
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-purple-400"></div> 区块链生成挑战
      </li>
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-purple-400"></div> SSP生成自己的证明
      </li>
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-purple-400"></div> 智能合约自动验证
      </li>
    </ul>
  </div>

  <div class="bg-white text-gray-800 p-6 rounded-xl border-t-4 border-emerald-500 shadow-xl h-full">
    <div class="text-4xl mb-4">⚡</div>
    <h3 class="text-xl font-bold text-emerald-700 mb-4">3. 高效审计方案</h3>
    <ul class="list-none pl-0 space-y-2 text-sm opacity-90">
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-emerald-400"></div> 挑战生成 (优化)
      </li>
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-emerald-400"></div> 证明生成 (聚合)
      </li>
      <li class="flex items-center gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-emerald-400"></div> 智能合约证明验证
      </li>
    </ul>
  </div>

</div>


---
layout: default
hideInToc: true
---

# 初始化阶段

## 1. 密钥生成

> $pk:=(v=g^x,u=g^{\alpha x},g,g^{\alpha},g^{{\alpha}^2}...g^{{\alpha}^{s-1}})$
>
> $sk:=(x,\alpha)$；$x,\alpha \in Z_p^*$
>
> 其中，公钥中的 $s$ 指文件副本个数；$x$ 是真正的私钥，$\alpha$ 是系统私钥，生成公钥之后就立即销毁。

## 2. 副本生成

> 副本计算：$Copy_i = \{m_{i,j,k}\}(1\le i \le N,1\le j\le n,1\le k\le s)$
>
>其中$m_{ijk}=E_K(b_{jk}||i)$，$b_{jk}$表示文件中第j块，第k个扇区。

## 3. 生成文件块标签

> $$\sigma_{ij} = (H(F_{id}||i||j)*g^{f_{m_{i,j}}(\alpha)})^x$$


其中 $f_{m_{i,j}}(\alpha)$ 由文件的第 $i$ 个副本的第 $j$ 个文件块的 $s$ 个块的扇区组成：


> $$f_{m_{i,j}}(X) = \sum_{k=1}^{s}m_{i,j,k}\cdot X^{k-1}$$


---
layout: default
hideInToc: true
---
# 初始化阶段
## 4. SSP验证标签
>`SSPi`需要对与用户提交的文件块标签进行验证,验证配对函数
>
$$e(\sigma_{ij}, g) = e\left( H(F_{id} \| i \| j) \cdot g^{f_{m_{ij}}(\alpha)}, v \right)$$
>
>由$\sigma_{ij} = (H(F_{id}||i||j)*g^{f_{m_{i,j}(\alpha)}})^x$带入$e(\sigma_{ij},g)$,  $g^x = v$可以直接得到：

$$e((H(F_{id}||i||j)*g^{f_{m_{i,j}(\alpha)}})^x,g) = e((H(F_{id}||i||j)*g^{f_{m_{i,j}(\alpha)}}),g^x)$$


---
layout: default
hideInToc: true
---

# 审计阶段

## 1. 生成挑战 $ChalGen(P ara, nounce) \to chal(Q,r,\gamma)$

>其中， 集合$Q = {(a_j,v_j)}$,$a_j$表示需要认证文件块的下标，$v_j$表示这个块对应的计算权重系数。
>
>r为PCS的评估点，$\gamma$用于隐藏直接生成的信息。这两个参数都是为随机生成的参数。

## 2. SSP证明生成$Proof_i(\sigma_i, w_i, s_i, R_i)$

>根据集合Q的权重与下标集合，进行聚合SSPi的认证标签

>$$\sigma_i = \left( \prod_{j=1}^{c} \sigma_{i a_j}^{v_j} \right)^{\gamma^{i-1}}$$


>计算挑战多项式
>$$f_{M_i}(X) = \sum_{j=1}^{c} v_j \cdot f_{m_{ia_j}}(X)$$
>
>其中，$f_{m_{ia_j}}(X)$计算方式为：
>$f_{m_{i,j}}(X) = \sum_{k=1}^{s}m_{i,j,k}*X^{k-1}$


---
layout: default
hideInToc: true
---

## 2. SSP证明生成$Proof_i(\sigma_i, w_i, s_i, R_i)$
>商多项式计算
>$$h_i(X) = \gamma^{i-1} \cdot \frac{f_{M_i}(X) - f_{M_i}(r)}{X - r}$$
>这个商多项式，后续用来计算在秘密私钥$\alpha$处的数值，即$w_i = g^{h_i(\alpha)}$.

>对于构造的信息进行隐藏
>
>$$\begin{cases}
s'_i = \gamma^{i-1} \cdot f_{M_i}(r) \\
R_i = v^{\varepsilon_i} = (g^x)^{\varepsilon_i} \\
s_i = s'_i + \varepsilon_i \cdot H'(R_i)
\end{cases}$$
>
>输出：$Proof_i = (\sigma_i, w_i, s_i, R_i)$


---
layout: default
hideInToc: true
---


## 3.合约自动验证：$Verify(pk, \{Proof_i\}, chal) \to result$
>计算文件配对函数：
>
>$$e(\sigma \cdot \eta, g) \cdot e(g^{-s}, v) = e(P, v) \cdot e(w, u \cdot v^{-r})$$

>计算单个文件块的配对函数：
>
>$$e(\sigma_i \cdot \eta_i, g) \cdot e(g^{-s_i}, v) = e(P_i, v) \cdot e(w_i, u \cdot v^{-r})$$

>其中，参数$\eta = \prod_{i=1}^{N} R_i^{H'(R_i)}$,$\eta_i =  R_i^{H'(R_i)}$;
>$w_i = g^{h_i(\alpha)}$,$w=\prod_{j=1}^dw_i$
>
>参数$P$计算：
>
>$$P=\prod_{i=1}^N(\prod_{j=1}^cH(F_{id}||i||j)^{v_j})^{\gamma^{i-1}}$$
>
>参数$P_i$计算:
>
>$$P_i = (\prod_{j=1}^cH(F_{id}||i||j)^{v_j})^{\gamma^{i-1}}$$


---
layout: default
hideInToc: true
---

# 高效审计(多文件审计)

## 1. 挑战生成：$ChalGen(Para, nounce) \rightarrow chal$
>$$chal = (\{Q_l\}, \{r_l\}, \gamma, z)$$
>
>$\{Q_l\}$是随机挑战集合，$\{r_l\}$是评估点的集合，$\gamma, z \in Z_p$

## 2.证明生成：$ProofGen(chal, \{f_{l, m_{ij}}(X)\}, pk) \rightarrow Proof_i$
>生成聚合认证标签：
>
>$$\sigma'_i = \prod_{l=1}^{d} \left( \prod_{\{a_j, v_j\} \in Q_l} \sigma_{l, i a_j}^{v_j} \right)^{\beta_l}$$

>计算参数多项式：
>
>$$\begin{cases}
F_i(X) = & \sum_{l=1}^{d} \gamma^{l-1} \cdot Z_{T \setminus S_l}(X)
\cdot (F_{l,M_i}(X) - F_{l,M_i}(r_l)) \\
H_i(X) = & \frac{F_i(X)}{Z_T(X)} \\
L_i(X) = & \sum_{l=1}^{d} \beta_l \cdot (F_{l,M_i}(X) - F_{l,M_i}(r_l))- Z_T(z) \cdot H_i(X)
\end{cases}$$

---
layout: default
hideInToc: true
---
## 2. 证明生成
>$$F_{l,M_i}(X) = \sum_{\{a_j,v_j\}\in Q_l} v_j \cdot f_{l,m_{ia_j}}(X)$$
>其中的$f_{l,m_{ia_j}}(X)$表示第$l$个文件的第$i$个副本$a_j$块的多项式，公式为：$f_{m_{ij}}(X) = \sum_{k=1}^{s} m_{ijk} \cdot X^{k-1}$
>
>$Z_S := \prod_{z \in S} (X - z)$
>
>$\beta_l = \gamma^{l-1} \cdot Z_{T \setminus S_l}(z)$

>计算证明参数：
>$$\begin{cases}
W_i = g^{H_i(\alpha)} \\
W'_i = g^{\frac{L_i(\alpha)}{\alpha-z}} \\
E_i = \sum_{l=1}^{d} \beta_l \cdot S_{l,i}
\end{cases}$$
>
>输出：$Proof_i = (\sigma'_i, W_i, W'_i, E_i)$


---
layout: default
hideInToc: true
---
## 3. 合约证明验证
>计算聚合参数：
>$$\begin{cases}
W = \prod_{i=1}^{N} W_i \\
W' = \prod_{i=1}^{N} W'_i \\
E = \sum_{i=1}^{N} E_i \\
\sigma' = \prod_{i=1}^{N} \sigma'_i
\end{cases}$$

>整体验证配对函数：
>
>$$e(\sigma', g) \cdot e(\psi, v) = e(\zeta, v) \cdot e(W', u \cdot v^{-z})$$
>其中，$\psi = g^{-E} \cdot W^{-Z_T(z)}$,$\zeta = \prod_{i=1}^{N} \prod_{l=1}^{d} \left( \prod_{\{v_j\} \in Q_l} H(F_{id} \| i \| j)^{v_j} \right)^{\beta_l}$

>单个证明配对验证(配对失败可以进行节点处罚):
>$$e(\sigma'_i, g) \cdot e(\psi_i, v) = e(\zeta_i, v) \cdot e(W'_i, u \cdot v^{-z})$$
>其中参数计算，$\psi_i=g^{-E_i} \cdot W_i^{-Z_T(z)}$,$\zeta_i = \prod_{l=1}^{d} \left( \prod_{\{v_j\} \in Q_l} H(F_{id} \| i \| j)^{v_j} \right)^{\beta_l}$


---
layout: default
hideInToc: false
---
# 实验结果
## Baseline
- Enabling secure and efficient decentralized storage auditing with blockchain
>只能验证一个副本。
- Efficient identity-based provable multi-copy data possession in multi-cloud storage
>基于数据持有性证明协议，但是副本都存储在同一个服务器上，验证时，需要对于副本分别验证，效率低下。
- 本文优势
> - 可以进行聚合计算，不需要对于各个副本进行单独计算。
> - 生成的证明大小固定，不随着文件数量的增多而增大。

- 本文不足
> - 设计的生成的证明大小确实固定，但是如果对于单个文件进行证明文件验证的代价比较大，文件越多，相对来说每个文件副本的代价就越小。
> - 智能合约运行双线性配对函数的开销比较大。
> - 性能对于扇区数量s依赖性高，需要权衡并自行调整s的大小，由于扇区大小固定，每一块的扇区数量增加，那么块会减少，然后认证标签就会减少，减少了标签生成与验证的时间，但是增加了证明生成的时间。

---
layout: default
hideInToc: true
---
# 参数生成时间
>优势就是证明生成的快一点。
>

![](./pic/EP1.png)


---
layout: default
hideInToc: true
---

# 证明生成大小

<div class="grid grid-cols-2 gap-8 mt-10 items-start">

<div class="flex flex-col items-center">
<img 
src="./pic/EP2.png" 
class="h-[350px] w-auto object-contain rounded-xl shadow-lg border border-gray-200"
/>
</div>

<div class="flex flex-col items-center">
<img 
src="./pic/EP4.png" 
class="h-[350px] w-auto object-contain rounded-xl shadow-lg border border-gray-200"
/>
</div>

</div>