---
title: Coppersmith 相关攻击
date: 2025-07-31 10:00:00
categories:
  - Crypto
  - RSA
tags:
  - Crypto
  - RSA
---

# 1. 已知部分密文恢复完全密文（stereotyped）

## 当前只能使用e = 3

```python
def stereotyped(f, N):
    P.<x> = PolynomialRing(Zmod(N))
    beta = 1
    dd = f.degree()   # Degree of the polynomial
    epsilon = beta/7
    XX = ceil(N**((beta**2/dd) - epsilon))
    rt = f.small_roots(XX, beta, epsilon)
    return rt
```



# 2. 已知高位p或q的内容，分解N

```python
def N-factorize(f, N):
    P.<x> = PolynomialRing(Zmod(N))
    beta = 0.5
    dd = f.degree()    # Degree of the polynomial
    epsilon = beta/7
    XX = ceil(N**((beta**2/dd) - epsilon))
    rt = f.small_roots(XX, beta, epsilon)
    return rt
```
