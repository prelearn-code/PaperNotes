---
title: Blockchain-Based Shared Data Integrity Auditing and Deduplication
year: 2022-02-02
venue: IEEE Transactions on Dependable and Secure Computing
field:
  - Authentication
pdf: "[[Blockchain-Based Shared Data Integrity Auditing and Deduplication]]"
Read_date: 2025-12-16
detailes: "[[Blockchain-Based Shared Data Integrity Auditing and Deduplication]]"
---
# 1. 相关知识

# 2. 技术背景


# 3. 方案详细内容


## 3.1 系统初始化

**输入**：安全参数$\lambda$
**公共函数：**
>双线性配对函数：$G*G \to G_T$
>哈希函数：$H_1:\{0,1\}^* \to Z_q^*;H_2:\{0,1\}^* \to Z_q^*;H_3:\{0,1\}^* \to Z_q^*$
>	$H_1$：生成标签、参与IBBE头的生成。
>	$H_2$：用于生成收敛密钥。
>	$H_3$：用来生成私钥。
>对称加密：`AES`


SPG操作：
>
## 3.2 数据上传与去重

**DO上传数据**：$(ID_t,T(F))$
>$H_2(F)\to K_c$
>$T(F)=H_1(Enc(K_c,F))$

**首次上传操作**：
>1. 数据加密：
>	1. $ID_t$ 随机选择一个$k_l\in Z_q^*$
>	2. 计算：$Enc(k_l,F)\to c_l$
>	3. 计算：$k_l \oplus K_c \to K_l$
>	4. 密文分块：$c_l =\{C_{ij}\}_{(1\le i \le n,1\le j \le s)}$
>2. 生成认证标签：$\Omega_l = \{\sigma_i\}$
>	1. 首次生成文件的私钥：$sk_F = H_3(k_l)$
>	2. 文件公钥：$pk_F = g^{\frac{1}{sk_F}}$
>	3. 生成$ID_t$的认证公钥：$K_{F,t}=pk_F^{x_t}$
>	4. 计算混淆密钥$K_l$的数据标识: $\eta_l = H_1(K_l)$
>	5. 计算认证标签：$$\sigma_i = \left( H_4(\eta_l \| i) \cdot g^{\sum_{j=1}^{s} a_j c_{ij}} \right)^{sk_F}, 1 \leqslant i \leqslant n.$$
>3. IBBE加密：并上传$(ID_t, c_l, K_l, pk_F, K_{F,t}, d_F, ck_F, \{\sigma_i\}_{i=1}^n, \mathrm{Hdr}_F, \tau_t)$
>	1. 随机选择一个参数$k_F \in Z_q^*$
>	2. 计算IBBE header：$$Hdr_i = (C_{F1}, C_{F2}) = \left( \varpi^{-k_F}, \left( h^\gamma \cdot h^{H_1(ID_t)} \right)^{k_F} \right)$$
>	3. 计算：$ck_F = Enc(K_{IBF},K_c)$
>	4. 计算：$d_F = Enc(K_c, k_F)$
>	5. 计算数据标签：$\tau_t \leftarrow \tau_0 \| SSig_{ssk_t}(\tau_0)$,其中 $\tau_0$ 如下计算；$$\tau_0 \leftarrow H(ID_t \| \eta_l \| n \| u_1 \| \cdots \| u_s \| K_l \| pk_F \| K_{F,t} \| Hdr_F)$$
>	6. $SSig_{ssk_t}(\tau_0)$是用用户私钥$ssk_t$进行的签名。
>4. `CSP`接收到上传数据进行验证：$\tau_t$，成功则把$ID_t\in S_F$，计算配对函数$$e\left( \prod_{i=1}^n \sigma_i, K_{F,t} \right) = e\left( \prod_{i=1}^n H_4(\eta_l \| i) \cdot \prod_{i=1}^n \prod_{j=1}^s u_j^{c_{ij}}, pk_t \right)$$


**后续上传(去重)**:后续上传的用户为$ID_y$
>1. `CSP`随机选择挑战：`chal` and $K_l$
>	1. $chal = (c,k_1,k_2)$
>	2. $k_1、k_2 \in Z_q^*$
>	3. $c \in [1,n]$
>2. $ID_y$进行证明生成：$$\mathbf{PoW.Proof} = \{\{\mu_j\}_{1 \leqslant j \leqslant s}\}$$
>	1. 先计算文件的收敛密钥：$K_c = H_2(F)$
>	2. 解密文件加密密钥：$k_l = K_l \oplus K_c$
>	3. 然后对于原文件进行加密：$c_l \leftarrow E(k_l, F)$，然后分成`n`块，每块`s`个扇区。
>	4. 生成挑战内容：随机抽取`c`个块进行生成$$\mu_j = \sum_{i=1}^{c} v_i \cdot c_{b_{ij}}, 1 \leqslant j \leqslant s.$$
>		其中 $I = \{b_i\}_{i=1}^c$，$b_i = \pi_{k_1}(i)$
>		其中$C = \{v_i\}_{i=1}^c$，$v_i = f_{k_2}(i)$
>3. `CSP`证明验证:$$\begin{cases}
\sigma = \prod_{i=1}^{c} \sigma_{b_i}^{v_i} \\
e(\sigma, K_{F,y}) = e\left( \prod_{i=1}^{c} H_4(\eta_l \| i)^{v_i} \cdot \prod_{j=1}^{s} u_s^{\mu_j}, pk_y \right).
\end{cases}$$
## 3.3 数据审计


## 3.4 批量数据审计