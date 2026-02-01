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

>**公共参数**：$$pp = (\varpi, v, H, h^\gamma, \dots, h^{\gamma^m}, n, s)$$

>**用户参数**：
>	私钥：
>	公钥：$pk = \{ spk_t, pk_t \}$. $$$$

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
>4. 验证成功，更新$C_F$。$$C_F = h^{\prod_{j=1}^{s_i} (\gamma + H_1(ID_j)) (\gamma + H_1(ID_y))}$$
>5. `CSP`返回给$ID_y$数据$$\{ d_F, Hdr, C_F, pk_F \}$$
>6. 接收到`CSP`返回的数据，$ID_y$重新计算，并上传：$(Hdr', K_{F,y}, \tau_y)$
>	1. 生成审计公钥：$K_{F,y} = pk_F^{x_y}$
>	2. 解密文件加密密钥：$k_F = Dec(K_c, d_F)$
>	3. 计算认证验证数据：$C'_{F2} = C_F^{k_F}$
>	4. 检查是否把自己的ID加入：$$e(C'_{F2}, h) = e(C_{F2}, h^{\gamma + H_1(ID)})$$
>	5. 更新IBBE header：$Hdr' = (C_{F1}, C'_{F2})$
>	6. 计算验证验证信息：$$\tau_1 \leftarrow H(Hdr' \| K_{F,y})$$ $$\tau_y \leftarrow \tau_1 \| SSig_{ssk_y}(\tau_1)$$
>	7. 上传信息给`CSP`，计算验证信息，没有问题则直接更新，并把$ID_y$加入到$S_F$。$$Hdr_F \leftarrow Hdr'$$

>**$S_F$成员恢复文件私钥$K_{IBF}$过程：**
>1.计算中间参数：$$p_s(\gamma) = \frac{1}{\gamma} \left( \prod_{j=1}^{s'_F} (\gamma + H(ID_j)) - \prod_{j=1}^{s'_F} H_1(ID_j) \right)$$ $$h^{p_s(\gamma)} = h^{\frac{1}{\gamma} \left( \prod_{j=1}^{s'_F} (\gamma + H_1(ID_j)) - \prod_{j=1}^{s'_F} H_1(ID_j) \right)}$$
>2.计算：$$\begin{aligned}
& \left[ e \left( C_{F1}, h^{p_s(\gamma)} \right) \cdot e \left( sk_{ID_y}, C_{F2} \right) \right]^{\frac{1}{\prod_{j=1}^{s'_F} H_1(ID_j)}} \\
= & \left[ e \left( \varpi^{-k_F}, h^{\frac{1}{\gamma} \left( \prod_{j=1}^{s'_F} (\gamma + H_1(ID_j)) - \prod_{j=1}^{s'_F} H_1(ID_j) \right)} \right) \cdot e \left( g^{\frac{1}{\gamma + H_1(ID_y)}}, h^{k_F \prod_{j=1}^{s_i} (\gamma + H(ID_j))} \right) \right]^{\frac{1}{\prod_{j=1}^{s'_F} H_1(ID_j)}} \\
= & \left[ e \left( g^{-\gamma k_F}, h^{\frac{1}{\gamma} \left( \prod_{j=1}^{s'_F} (\gamma + H_1(ID_j)) - \prod_{j=1}^{s'_F} H_1(ID_j) \right)} \right) \cdot e(g, h)^{\frac{1}{\gamma + H_1(ID_y)} \cdot k_i \prod_{j=1}^{s_i} (\gamma + H_1(ID_j))} \right]^{\frac{1}{\prod_{j=1}^{s'_F} H_1(ID_j)}} \\
= & \left[ e(g, h)^{k_F \prod_{j=1}^{s'_F} H_1(ID_j)} \right]^{\frac{1}{\prod_{j=1}^{s'_F} H_1(ID_j)}} \\
= & e(g, h)^{k_F} = v^{k_F} = K_{IBF}
\end{aligned}$$

## 3.3 数据审计

>1. `DO`授权给主节点，给出授权信息：$$Delegation = \langle ID_t, T(F) \rangle$$
>2. 主节点生成挑战参数：$Chal=(c,k_1,k_2)$，并把信息发送的区块链。
>	其中 $c\in [1,n]$，$k_1、k_2 \in Z_q^*$
>3. `CSP`生成证明：$Proof = \{ \sigma, \{ \mu_j \}_{j=1}^s \}$，并发送到交易池。
>	1. 计算：$I = \{b_i\}_{i=1}^c, b_i = \pi_{k_1}(i), 1 \leqslant i \leqslant c、C = \{v_i\}_{i=1}^c, v_i = f_{k_2}(i), 1 \leqslant i \leqslant c$
>	2. 计算参数：$$\begin{cases}
\sigma = \prod_{i=1}^{c} \sigma_{b_i}^{v_i} \\
\mu_j = \sum_{i=1}^{c} v_i \cdot c_{b_i j}, 1 \leqslant j \leqslant s.
\end{cases}$$
>4. 验证过程：$$e(\sigma, K_{F,t}) = e \left( \left( \prod_{i=1}^{c} H_4(\eta_l \| i)^{v_i} \cdot \prod_{j=1}^{s} u_s^{\mu_j} \right), pk_t \right)$$

## 3.4 批量数据审计
### 3.4.1 单用户多文件审计
> **设定条件**：`ID_y`想要去审计这些文件$\{F_1,F_2,...F_d\}$

>**授权阶段**：
>1. $ID_y$授权给主节点：$Delegation_{b1} = \langle ID, T(F_1), \cdots T(F_d) \rangle$
>2. 主节点生成挑战`Chal`，并发布到区块链上。$$Chal_{b1} = (c, k_1, k_2, k_3)$$
>	其中，$c \in [1, n] \text{ and } k_1, k_2, k_3 \in \mathbb{Z}_q^*$。

>**`CSP`生成证明：**$Proof_{b1} = \{ \sigma_{b1}, \{ \mu_{j1} \}_{j=1}^s \}$
>1. 算中间参数：$I_{b_1} = \{b_i\}_{i=1}^c, b_i = \pi_{k_1}(i) \text{ for } 1 \leqslant i \leqslant c$
>2. 计算：$C_{b_1} = \{v_i\}_{i=1}^c, X_{b_1} = \{x_i\}_{i=1}^c, v_i = f_{k_2}(i), x_i = f_{k_3}(i), 1 \leqslant i \leqslant c$
>3. 计算证明关键参数：$$\begin{cases}
\sigma_{b1} = \prod_{k=1}^{d} \prod_{i=1}^{c} \sigma_{b_i k}^{x_k \cdot v_i} \\
\mu_{j1} = \sum_{k=1}^{d} \sum_{i=1}^{c} x_k \cdot v_i \cdot c_{b_i j}, & 1 \leqslant j \leqslant s.
\end{cases}$$

>**验证证明过程**：$result = <Proof_{b1},true/false>$
>$$e \left( \sigma_{b1}, \prod_{k=1}^{d} K_{F_k,y} \right) = e \left( \left( \prod_{k=1}^{d} \prod_{i=1}^{c} H_4 (\eta_k \| i)^{x_k \cdot v_i} \cdot \prod_{j=1}^{s} u_s^{\mu_{j1}} \right), pk_y^d \right).$$
### 3.4.2 多用户单文件审计

>**授权阶段**：
>1. 用户生成授权集合：$Delegation_{b2} = \langle ID_1, \dots, ID_d, T(F_o) \rangle$
>2. 获得授权节点生成并发送挑战：$Chal_{b2}=(c,k_1,k_2),c\in[1,n],k_1，k_2 \in Z_q^*$

>**证明生成阶段**：$Proof_{b2} = \{ \sigma_{b2}, \{ \mu_{j2} \}_{j=1}^s \}$
>1. 计算中间参数：$I_{b_2} = \{b_i\}, b_i = \pi_{k_1}(i) \text{ for } 1 \leqslant i \leqslant c$
>2. 计算中间参数：$C_{b_2} = \{v_i\}_{i=1}^c, v_i = f_{k_2}(i) \text{ for } 1 \leqslant i \leqslant c$
>3. 证明参数生成：$$\begin{cases}
\sigma_{b2} = \prod_{i=1}^{c} \left( \prod_{k=1}^{d} \sigma_{b_i k}^{v_i} \right) \\
K_{F,U} = \prod_{j=1}^{d} K_{F,j} \\
\mu_{j2} = \sum_{i=1}^{c} d \cdot v_i \cdot c_{b_i j}, & 1 \leqslant j \leqslant s.
\end{cases}$$

>**验证阶段**：$$e(\sigma_{b2}, K_{F,U}) = e \left( \left( \prod_{i=1}^{c} H_4(\eta_o \| i)^{d v_i} \cdot \prod_{j=1}^{s} u_s^{\mu_{j2}} \right), \prod_{i=1}^{d} pk_i \right)$$


# 4. 安全性分析
## 4.1 审计正确性分析

## 4.2 满足文件去重

## 4.3 满足密钥去重




# 5. 实验


# 6. 复现实验

