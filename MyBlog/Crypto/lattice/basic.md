---
title: basic
date: 2025-08-01 10:00:00
categories:
  - Crypto
  - lattice
tags:
  - Crypto
  - lattice
---

# 1. 格基础

## 1.1 格定义

$$
定义：格是R^{n}的离散加法子群。
$$

通俗表示，即由格基向量的整数倍数的组合，形成的点集合，组成格空间。



## 1.2 格等价性质

$$
定义：若B, C是同一格基，则存在整系数行列式+/- 1的可逆矩阵U,使得B = CU。
$$

即，对于格基的向量进行交换，某一列整数倍增/减少加到另一列，某一列乘以-1都不影响格基的等价性。

## 1.3 施密特正交化

通过格基向量组B，得到正交化的向量组

```python
import numpy as np

def gso_for_lattices(B, tol=1e-18):
    """
    Gram-Schmidt Orthogonalization (GSO) for lattice basis.
    
    输入:
        B : ndarray, shape (m, n)，列向量是格基
    输出:
        b_star : 正交向量 b_i^* (m, r)
        mu     : 投影系数矩阵 (n, r)，mu[i,j] 定义在 j<=i
        norm2  : 各 b_i^* 的平方范数 (r,)
        idx_valid : 有效基向量索引（秩不足时跳过）
    """
    B = np.array(B, dtype=float)
    m, n = B.shape
    
    b_star_list = []
    mu = np.zeros((n, n))
    norm2 = []
    idx_valid = []

    for i in range(n):
        v = B[:, i].copy()
        for j, bstar_j in enumerate(b_star_list):
            mu[i, j] = np.dot(B[:, i], bstar_j) / np.dot(bstar_j, bstar_j)
            v -= mu[i, j] * bstar_j
        nrm2 = np.dot(v, v)
        if nrm2 > tol:  # 保留线性无关向量
            b_star_list.append(v)
            mu[i, i] = 1.0
            norm2.append(nrm2)
            idx_valid.append(i)

    if not b_star_list:
        return np.empty((m,0)), np.empty((0,0)), np.array([]), []

    b_star = np.column_stack(b_star_list)
    norm2 = np.array(norm2)
    return b_star, mu, norm2, idx_valid


# 示例
if __name__ == "__main__":
    B = np.array([[1,1,0],
                  [1,0,1],
                  [0,1,1]], dtype=float)
    b_star, mu, norm2, idx = gso_for_lattices(B)
    print("b* =\n", b_star)
    print("mu =\n", mu)
    print("||b*||^2 =", norm2)

```



## 1.4 格的行列式

$$
det(L(B))=∏​∥bi^{*}​∥
$$

性质：

	1. 与具体基无关。
	1. 表示格点在空间中的“密度”。

计算公式：
$$
det(L(B))=\sqrt{det(B^{T}B)}
$$

## 1.5 最短向量与最小距离

$$
最短距离定义：\lambda(L) = min{||v||: v\in L/\{0\}}
$$

界限定义

​	
$$
下界：\lambda(L)>= min_{i}||b_i^{*} ||
$$
​	
$$
上界：\lambda(L)<= O(\sqrt{n})det(L)^{1/n}
$$

## 1.6  Minkowski 定理

$$
定理内容：若凸对称体积>2^{n}det(L)，则其内含有非零格点。..................................................\\

证明: 令 S = \frac{1}{2}V = {x/2: x\in V},由体积的齐次性，vol(S) = \frac{vol(V)}{2^{n}} > det(L)...............................\\
令取两个向量点x!=y \in S,并且x-y \in L/\{0\}............................................................\\
由于V的中心对阵性与凸性，有............................................................................\\
S+S = \frac{1}{2}V + \frac{1}{2}V\\
其中-y\in S.........................................................................................\\
x-y = x+(-y) \in S+S = K\\
结合x-y \in L/\{0\}, 即V含有一个非零格点...............................................................\\
$$



# 2. 格算法

## 2.1 Gram-Schmidt orthogonalization（上述已有）

## 2.2 Hermite Normal Form (HNF)

介绍：对于格进行上三角的转化，通过列变化，转化为标准的上三角/下三角矩阵，并且不同的格基表示的结果是唯一的。

思想：

1. **选择主元（Pivot）**

   - 从左到右扫描列，从上到下扫描行。
   - 找到当前列中从未被处理的行的最小非零元素作为主元。
   - 如果当前列全为零，跳到下一列。

2. **行交换（Swap）**

   - 如果最小非零元素不在当前处理行，将其与当前行交换，保证主元在处理行上。

3. **整数消元（Reduction）**

   - 对主元所在列的其他行：

     - 用整倍数消去其他行对应列的元素。

     - 公式：若主元为 hhh，消去元素为 aaa，则用：

       rowi←rowi−⌊ah⌋⋅rowpivot\text{row}_i \gets \text{row}_i - \left\lfloor \frac{a}{h} \right\rfloor \cdot \text{row}_\text{pivot}rowi←rowi−⌊ha⌋⋅rowpivot

     - 保证所有消元后的元素在 [0,h−1][0, h-1][0,h−1] 范围内。

4. **递归处理子矩阵**

   - 对剩下的子矩阵（去掉已处理的行和列）重复上述步骤，直到处理完所有列。

5. **得到标准形式**

   - 最终矩阵就是 HNF，上三角形式（或下三角形式）。

code:

```python
import numpy as np

def integer_row_echelon_form(A):
    """
    简单整数行阶梯形，返回简化后的矩阵和秩。
    只做整数行变换（加减行，不除法），用于秩判断和基底选取。
    """
    A = A.copy()
    m, n = A.shape
    rank = 0
    for col in range(n):
        pivot_row = -1
        for r in range(rank, m):
            if A[r, col] != 0:
                pivot_row = r
                break
        if pivot_row == -1:
            continue
        # 交换到第rank行
        if pivot_row != rank:
            A[[rank, pivot_row]] = A[[pivot_row, rank]]
        # 用第rank行消去下面行该列元素
        pivot_val = A[rank, col]
        for r in range(rank + 1, m):
            if A[r, col] != 0:
                # 用整数倍消去
                q = A[r, col] // pivot_val
                A[r, :] = A[r, :] - q * A[rank, :]
        rank += 1
        if rank == m:
            break
    return A, rank

def matrix_rank_integer(A):
    """
    返回整数矩阵的行秩
    """
    _, rank = integer_row_echelon_form(A)
    return rank

def select_independent_columns(B):
    """
    从B中选择最大线性无关列集合，返回列索引列表和对应子矩阵
    使用基于秩增长的贪心算法。
    """
    m, n = B.shape
    selected_cols = []
    current_mat = np.zeros((m,0), dtype=int)
    def matrix_rank_safe(M):
        if M.size == 0:
            return 0
        return matrix_rank_integer(M)
    for j in range(n):
        candidate_mat = np.hstack([current_mat, B[:, j].reshape(-1,1)])
        if matrix_rank_safe(candidate_mat) > matrix_rank_safe(current_mat):
            current_mat = candidate_mat
            selected_cols.append(j)
    B_prime = B[:, selected_cols]
    return selected_cols, B_prime

def extended_gcd(a, b):
    if b == 0:
        return (a, 1, 0)
    else:
        g, x1, y1 = extended_gcd(b, a % b)
        x = y1
        y = x1 - (a // b) * y1
        return (g, x, y)

def mod_vec(v, diag):
    v_mod = np.copy(v)
    for i in range(len(v)):
        v_mod[i] = v_mod[i] % diag[i]
    return v_mod

def AddColumn(H, b):
    m = H.shape[0]
    if m == 0:
        return H
    a = H[0, 0]
    h = H[1:, 0]
    H_prime = H[1:, 1:]
    b0 = b[0]
    b_prime = b[1:]
    g, x, y = extended_gcd(a, b0)
    U = np.array([[x, -b0 // g],
                  [y, a // g]])
    new_h = x * h + y * b_prime
    new_b_prime = (-b0 // g) * h + (a // g) * b_prime
    diag_H_prime = np.diag(H_prime) if H_prime.size > 0 else np.array([])
    new_b_prime_mod = mod_vec(new_b_prime, diag_H_prime) if diag_H_prime.size > 0 else new_b_prime
    H_double_prime = AddColumn(H_prime, new_b_prime_mod) if H_prime.size > 0 else H_prime
    diag_H_double_prime = np.diag(H_double_prime) if H_double_prime.size > 0 else np.array([])
    new_h_mod = new_h % diag_H_double_prime if diag_H_double_prime.size > 0 else new_h
    top_row = np.hstack([np.array([[g]]), np.zeros((1, m-1), dtype=int)])
    bottom_rows = np.hstack([new_h_mod.reshape(-1,1), H_double_prime]) if H_double_prime.size > 0 else new_h_mod.reshape(-1,1)
    H_out = np.vstack([top_row, bottom_rows])
    return H_out.astype(int)

def compute_HNF_general(B):
    """
    支持非满秩和非方阵输入
    返回对应秩的HNF矩阵和秩
    """
    m, n = B.shape
    # 1. 选取最大线性无关列和对应基底矩阵
    selected_cols, B_prime = select_independent_columns(B)
    r = B_prime.shape[1]  # 基底矩阵列数，也就是秩
    if r == 0:
        # 零矩阵，返回空矩阵
        return np.zeros((0,0), dtype=int), 0
    # 2. 计算 d = |det(B_prime.T @ B_prime)|^(1/2) 简单取 abs(det(B_prime)) 可能为0，但矩阵满秩一般非零
    d = abs(round(np.linalg.det(B_prime))) if r == m else 1  # 不是满秩时d暂定1避免零矩阵初始化
    # 3. 初始化H0
    H = d * np.eye(r, dtype=int)
    # 4. 逐列AddColumn
    for j in range(n):
        b = B[:, j]
        # 投影到基底维度空间（长度r）
        # 如果r < m，需要映射b到秩空间
        if r < m:
            # 这里简化：用基底矩阵列构成子空间，做坐标变换
            # 用B_prime求伪逆获得坐标
            try:
                coords = np.linalg.lstsq(B_prime, b, rcond=None)[0]
                coords_int = np.round(coords).astype(int)
                b_proj = B_prime @ coords_int
                b_new = coords_int
            except:
                b_new = np.zeros(r, dtype=int)
        else:
            b_new = b
        H = AddColumn(H, b_new)
    return H, r

# 测试
if __name__ == "__main__":
    B = np.array([
    [1, 2, 3, 4, 5],
    [6, 7, 8, 9, 10],
    [11, 12, 13, 14, 15],
    [16, 17, 18, 19, 20]
], dtype=np.int64)
    H, rank = compute_HNF_general(B)
    print("输入矩阵 B:\n", B)
    print("矩阵秩:", rank)
    print("对应的HNF矩阵:\n", H)

```
