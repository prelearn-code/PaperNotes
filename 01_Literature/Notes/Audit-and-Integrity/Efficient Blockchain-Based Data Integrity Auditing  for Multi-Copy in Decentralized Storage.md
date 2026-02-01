---
title: Efficient Blockchain-Based Data Integrity Auditing  for Multi-Copy in Decentralized Storage
year: 2022-02-02
venue: IEEE TRANSACTIONS ON PARALLEL AND DISTRIBUTED SYSTEMS
field:
  - Authentication
pdf: "[[../../PDF/Audit-and-Integrity/Efficient_Blockchain-Based_Data_Integrity_Auditing_for_Multi-Copy_in_Decentralized_Storage.pdf|Efficient_Blockchain-Based_Data_Integrity_Auditing_for_Multi-Copy_in_Decentralized_Storage]]"
Read_date: 2025-12-16
detailes: "[[../../../02_Projects/Efficient_Blockchain-Based_Data_Integrity_Auditing_for_Multi-Copy_in_Decentralized_Storage/设计方案|设计方案]]"
---
# 1.背景知识
## PCS-PLONK
>PCS-PLONK 就是：把一个程序的正确执行，转成“几个多项式是否满足某些关系”的问题，再用多
>式承诺来让验证者只花很小代价就能检查这些关系是否真的成立。

缺陷：公共数据很大，可能是几百兆或者几个G。
## PCS-MPAP
>有很多个多项式，  在很多个点上，  
>它们都应该满足某些关系，  
>我不想一个一个证明，  
>能不能一次性打包证明

## 想法
能不能在之前那个可搜索加密与文件完整性的认证与副本同时生成。

将所有涉及到的关键词文件以及所有副本都进行审计，其中保证每个存储节点存储的认证信息不同，文件ID也不同。

在可搜索加密时，对于涉及到的存储节点生成这种客户端可验证的方案，然后客户但可以进行验证。

## 问题 
1. 谁是验证节点？Q: 智能合约


## 背景
在去中心化网络存储时代的的背景中，文件信息的安全性是十分重要的。然而现在的审计方案大多基于可证明数据拥有权PDP、可检索性证明POR，然而这两种方案架构都需要一个第三方审计员，对于审计证明进行验证。在多副本的存储要求一下，云存储服务商会内部节点勾结，只存储一个文件，而不存储副本。

基于第三方审计的方案。产生以下三个问题
（1）第三方的不可信。
（2）第三方故障，导致审计服务停滞。
（3）相信云存储管理器与存储服务提供商是不可靠的。


本方案基于智能合约，要求每个指定的存储副本的节点，都要生成自己的证明信息，然后上链，最后，智能合约自动审计，不依赖不可靠的可信第三方，并且实现多文件、多副本的同态审计方案。

# 2. Basic Scheme
## 2.0 在什么样的环境 解决了什么样的问题
**环境**
> 现在借助区块链辅助的文件审计方案环境下，出现了审计请求越来越多，然后区块链开销变大。
> 

**解决了什么问题**
> 本方案是在区块链的存储中，提出一种高效的方案，实现多复制文本的审计。
> 单文件多副本的审计。

## 2.1 $Setup(1^{\lambda}) \to Para$
$Return(G_1,G_2,g,e,H,H')$ on blockchain

>1. 输入安全参数：$\lambda$ 
>2. 选择阶为q(**应该是素数**)的群$G_1,G_2$，满足群映射$G_1 * G_1 \to G_2$，g是$G_1$的一个生成元。
>3. 选择两个哈希函数$H,H'$
>	1. $H:\{0,1\}^* \to G_1$
>	2. $H':G_1 \to Z_p$


## 2.2 Preprocessing and Storage Phase

### 2.2.1 KeyGen(λ)
_KeyGen($\lambda$) -> (pk, sk)_
>$pk:=(v=g^x,u=g^{\alpha x},g,g^{\alpha},g^{{\alpha}^2}...g^{{\alpha}^{s-1}})$
>$sk:=(x,\alpha)$；$x,\alpha \in Z_p^*$

### 2.2.2 RepGen(F)
 
生成N个副本

计算副本的值
> $Copy_i = \{m_{i,j,k}\}(1<=i<=N,1<=j<=n,1<=k<=s)$

计算副本中元素的值
>$m_{ijk}=E_K(b_{jk}||i)$
>	$b_{jk}$表示源文件的第j块的第k个扇区。

### 2.2.3 TagGen(sk, $f_{mij} (X)$, $F_{id}$) $\to$ $σ_{ij}$

**计算文件块的认证标签**：
> $$\sigma_{ij} = (H(F_{id}||i||j)*g^{f_{m_{i,j}(\alpha)}})^x$$

>其中$f_{m_{i,j}}(\alpha)$是通过文件的第`i`个副本的第`j`个文件块的`s`个块的扇区组成：
> $$f_{m_{i,j}}(X) = \sum_{k=1}^{s}m_{i,j,k}*X^{k-1}$$
> 其中，客户端可以自己计算，服务端也可以通过密文文件进行计算，然后使得这个函数信息保密。目的就是为了不可伪造，不能公用一个认证函数。


### 2.2.4 TagVerfication(pk, $m_{ijk}$, $F_{id}$, $σ_{ij})$ → 0/1
>*服务节点验证客户端是否是诚实的，相当于私钥签名，公钥验证*

>**验证配对函数**：$$e(\sigma_{ij}, g) = e\left( H(F_{id} \| i \| j) \cdot g^{f_{m_{ij}}(\alpha)}, v \right)$$
>**Prove**:
>	由$\sigma_{ij} = (H(F_{id}||i||j)*g^{f_{m_{i,j}(\alpha)}})^x$带入$e(\sigma_{ij},g)$,得$$e((H(F_{id}||i||j)*g^{f_{m_{i,j}(\alpha)}})^x,g) = e((H(F_{id}||i||j)*g^{f_{m_{i,j}(\alpha)}}),g^x) $$
>	进而由$g^x = v$得到，$$e(\sigma_{ij}, g) = e\left( H(F_{id} \| i \| j) \cdot g^{f_{m_{ij}}(\alpha)}, v \right)$$

## 2.3 Auditing Phase
**阶段概述**：智能合约验证文件的所有副本的完整性。

### 2.3.1 $ChalGen(P ara, nounce) \to chal(Q,r,\gamma)$
>**目的**：生成随机挑战，让生成的数据尽可能的保密。
>**随机数**：合约选择最新的block的nonce数。
>**生成**：Generate a  c-elements set $Q = {(a_j,v_j)}$ and select $r,\gamma \in Z_p$ generate by pseudo-random functions
>	c：需要证明的文件块的个数。     
>	$a_j$: $a_j \in [1,...,n]$. 要证明的文件块的下标。
>	$v_j$: $v_j\in Z_p$ . 表明这个块对应的权重系数。
>	$r,\gamma$: 用来隐藏直接生成的相关信息。
>**Out**: $$chal = (Q,r,\gamma)$$

### 2.3.2 $ProofGen(chal, {f_{m_{ij}} (X)}, pk) \to Proof_i(\sigma_i, w_i, s_i, R_i)$
>节点$SSP_i$接收到`chal`之后，计算自己单独的$Proof_i$

>计算聚合认证标签：$$\sigma_i = \left( \prod_{j=1}^{c} \sigma_{i a_j}^{v_j} \right)^{\gamma^{i-1}}$$

>基于$Q = {(a_j,v_j)}$,计算`PCS`的聚合函数函数
>把`r`作为**评估点**，最终匹配成功与否，就是与这个评估点的计算结果正确性匹配。
>把$v_j$作为$f_{m_{ia_j}}(X)$的权重，计算挑战的集合函数，证明$SSP_i$节点拥有这个文件副本的加密内容。

>**计算挑战函数**: 这个挑战函数是拥有这个文件副本的节点，通过文件认证标签获得
>$$f_{M_i}(X) = \sum_{j=1}^{c} v_j \cdot f_{m_{ia_j}}(X)$$
>$$f_{m_{i,j}}(X) = \sum_{k=1}^{s}m_{i,j,k}*X^{k-1}$$
>**计算商多项式**：用于后面的类似于`PCS`中`W`的计算，用来证明聚合多项式在秘密点$\alpha$处的值，用于后面对于评估点进行验证。这个是真不能伪造，$\alpha$整个过程，只有在生成公钥的时候采用上，然后立即消除，谁都不知道这个内容，若是没有对应的多项式与公钥组个，谁都不能计算出来这个值。
>$$h_i(X) = \gamma^{i-1} \cdot \frac{f_{M_i}(X) - f_{M_i}(r)}{X - r}$$
>**计算W**：$$w_i = g^{h_i(\alpha)}$$
>


**对于构造的信息进行隐藏**
> $SSP_i$选择一个随机数$\varepsilon_i$，利用随机数与合约发出的$chal = (Q,r,\gamma)$的随机数$\gamma$，进行隐藏。

>$$\begin{cases}
s'_i = \gamma^{i-1} \cdot f_{M_i}(r) \\
R_i = v^{\varepsilon_i} = (g^x)^{\varepsilon_i} \\
s_i = s'_i + \varepsilon_i \cdot H'(R_i)
\end{cases}$$

>**Return:  $Proof_i = (\sigma_i, w_i, s_i, R_i)$**

### 2.3.3 $Verify(pk, \{Proof_i\}, chal) \to result$

>中间变量1：$$\eta = \prod_{i=1}^{N} R_i^{H'(R_i)}$$ $$\eta_i =  R_i^{H'(R_i)}$$

> 中间变量2：$$P=\prod_{i=1}^N(\prod_{j=1}^cH(F_{id}||i||j)^{v_j})^{\gamma^{i-1}}$$ $$P_i = (\prod_{j=1}^cH(F_{id}||i||j)^{v_j})^{\gamma^{i-1}}$$

>集合验证：$$e(\sigma \cdot \eta, g) \cdot e(g^{-s}, v) = e(P, v) \cdot e(w, u \cdot v^{-r})$$

>单个验证：$$e(\sigma_i \cdot \eta_i, g) \cdot e(g^{-s_i}, v) = e(P_i, v) \cdot e(w_i, u \cdot v^{-r})$$
# 3. Efficient Batch Auditing Scheme
>前置条件：副本个数为`d`

>挑战生成：$ChalGen(Para, nounce) \rightarrow chal.$
>$$chal = (\{Q_l\}, \{r_l\}, \gamma, z)$$
>其中,$\{Q_l\}$是随机挑战集合，$\{r_l\}$是评估点的集合，$\gamma, z \in Z_p$

>`SSPi`证明生成：$ProofGen(chal, \{f_{l, m_{ij}}(X)\}, pk) \rightarrow Proof_i$
>1. 根据挑战聚合认证标签：$$\sigma'_i = \prod_{l=1}^{d} \left( \prod_{\{a_j, v_j\} \in Q_l} \sigma_{l, i a_j}^{v_j} \right)^{\beta_l}$$
>2. 计算参数多项式：$$\begin{cases}
F_i(X) = & \sum_{l=1}^{d} \gamma^{l-1} \cdot Z_{T \setminus S_l}(X)
\cdot (F_{l,M_i}(X) - F_{l,M_i}(r_l)) \\
H_i(X) = & \frac{F_i(X)}{Z_T(X)} \\
L_i(X) = & \sum_{l=1}^{d} \beta_l \cdot (F_{l,M_i}(X) - F_{l,M_i}(r_l))- Z_T(z) \cdot H_i(X)
\end{cases}$$
>	1. 挑战多项式：$F_{l,M_i}(X) = \sum_{\{a_j,v_j\}\in Q_l} v_j \cdot f_{l,m_{ia_j}}(X)$，其中$f_{l,m_{ia_j}}(X)$表示第$l$个文件的第$i$个副本$a_j$块的多项式，公式为：$f_{m_{ij}}(X) = \sum_{k=1}^{s} m_{ijk} \cdot X^{k-1}$
>	2. 计算多项式：$Z_S := \prod_{z \in S} (X - z)$
>	3. 中间参数：$\beta_l = \gamma^{l-1} \cdot Z_{T \setminus S_l}(z)$
>3. 计算证明参数 :$$\begin{cases}
W_i = g^{H_i(\alpha)} \\
W'_i = g^{\frac{L_i(\alpha)}{\alpha-z}} \\
E_i = \sum_{l=1}^{d} \beta_l \cdot S_{l,i}
\end{cases}$$
>4. Publish $Proof_i = (\sigma'_i, W_i, W'_i, E_i)$ to blockchain.


>智能合约验证证明：$Verify(pk, \{ Proof_i \}, chal) \rightarrow result$
>1. 计算聚合参数：$$\begin{cases}
W = \prod_{i=1}^{N} W_i \\
W' = \prod_{i=1}^{N} W'_i \\
E = \sum_{i=1}^{N} E_i \\
\sigma' = \prod_{i=1}^{N} \sigma'_i
\end{cases}$$
>2. 配对验证函数：$$e(\sigma', g) \cdot e(\psi, v) = e(\zeta, v) \cdot e(W', u \cdot v^{-z})$$
>	其中$\psi = g^{-E} \cdot W^{-Z_T(z)}$,$\zeta = \prod_{i=1}^{N} \prod_{l=1}^{d} \left( \prod_{\{v_j\} \in Q_l} H(F_{id} \| i \| j)^{v_j} \right)^{\beta_l}$
>3. 配对失败则溯源每一个$Proof_i$：$$e(\sigma'_i, g) \cdot e(\psi_i, v) = e(\zeta_i, v) \cdot e(W'_i, u \cdot v^{-z})$$
>	参数计算：$\psi_i=g^{-E_i} \cdot W_i^{-Z_T(z)}$,$\zeta_i = \prod_{l=1}^{d} \left( \prod_{\{v_j\} \in Q_l} H(F_{id} \| i \| j)^{v_j} \right)^{\beta_l}$

# 4. SECURITY ANALYSIS

# 5. Experiment

