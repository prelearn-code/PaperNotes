# 分解n的方法

## 1. 费马分解

**核心思想：** 任何奇合数 $n$ 都可以表示为两个平方数之差：$n = x^2 - y^2$。

* **数学原理：** 基于恒等式 $n = (\frac{p+q}{2})^2 - (\frac{p-q}{2})^2$。
* **过程：** 1. 从 $x = \lceil\sqrt{n}\rceil$ 开始向上遍历。
  2. 计算 $y^2 = x^2 - n$。
  3. 检查 $y^2$ 是否为完全平方数。如果是，则 $p = x-y, q = x+y$。
* **适用场景：** **$p$ 和 $q$ 极其接近时**。正如你刚才处理的 $n$，它们的差值只有 822，算法几乎在第一步就命中了结果。

```python
import gmpy2

def fermat_factorization(n):
    n = gmpy2.mpz(n)
    if n % 2 == 0: return 2, n // 2
    
    # x 从 sqrt(n) 向上取整开始
    x = gmpy2.isqrt(n)
    if x * x < n:
        x += 1
    i = 0
    while i<10000:
        y2 = x*x - n
        if gmpy2.is_square(y2):
            y = gmpy2.isqrt(y2)
            p, q = x - y, x + y
            return p, q
        x += 1
        i += 1
```

## 2. Pollard's Rho 算法

**核心思想：** 基于“生日悖论”，在模 $n$ 的空间内寻找碰撞。

* **数学原理：** 构造一个伪随机序列 $x\_{i+1} = f(x\_i) \pmod n$（通常 $f(x) = x^2 + c$）。如果存在因子 $p$，那么序列在模 $p$ 下会比在模 $n$ 下更快出现循环（即“Rho”字形的路径）。
* **过程：** 1. 使用 Floyd 判圈算法（快慢指针）寻找 $x\_i \equiv x\_j \pmod p$。
  2. 计算 $gcd(|x\_i - x\_j|, n)$。如果结果在 $1$ 和 $n$ 之间，则找到了因子。
* **适用场景：** 寻找**中等大小的质因子**。它的复杂度约等于 $O(n^{1/4})$。

```python
import gmpy2
import random

def pollard_rho(n):
    n = gmpy2.mpz(n)
    if n % 2 == 0: return 2
    if gmpy2.is_prime(n): return n
    
    x = gmpy2.mpz(random.randint(2, n-1))
    y = x
    c = gmpy2.mpz(random.randint(1, n-1))
    g = 1
    
    # 定义伪随机函数 f(x) = x^2 + c
    f = lambda x, c, n: (x*x + c) % n
    
    while g == 1:
        x = f(x, c, n)
        y = f(f(y, c, n), c, n)
        g = gmpy2.gcd(abs(x - y), n)
        
        # 如果 g==n，说明 c 选取不当，需要重试
        if g == n:
            return pollard_rho(n)
    return g
```

## 3. Pollard's $p-1$ 算法

**核心思想：** 利用费马小定理的特性。

* **数学原理：** 如果 $p$ 是 $n$ 的因子，且 $p-1$ 的所有质因子都小于某个界限 $B$（即 $p-1$ 是 $B$-smooth 的），那么 $B!$ 必定是 $p-1$ 的倍数。
* **过程：** 1. 选取一个基数 $a$（通常为 2）。
  2. 计算 $M = \prod q\_i^{e\_i}$（所有小于 $B$ 的质幂之积）。
  3. 计算 $g = gcd(a^M - 1, n)$。如果 $g > 1$，则 $g$ 是 $n$ 的因子。
* **适用场景：** **$p-1$ 容易被分解**的情况。很多 CTF 题目会故意构造这样的 $p$ 来引导选手使用此方法。

```python
import gmpy2

def pollard_p_minus_1(n, B1=100000):
    n = gmpy2.mpz(n)
    a = gmpy2.mpz(2) # 基数
    
    # 计算 B1! 的幂次过程
    for j in range(2, B1 + 1):
        a = pow(a, j, n)
        g = gmpy2.gcd(a - 1, n)
        
        if 1 < g < n:
            return g
    return None # 若未找到，可尝试增大 B1
```

#### 4. 椭圆曲线分解法 (ECM)

**核心思想：** $p-1$ 算法的升级版，将模群从乘法群扩展到椭圆曲线群。

* **数学原理：** 在有限域 $\mathbb{F}\_p$ 上的椭圆曲线点群的阶（点数）分布在 $\[p+1-2\sqrt{p}, p+1+2\sqrt{p}]$ 之间。
* **过程：** 1. 随机选取一条椭圆曲线 $E$ 和一个点 $P$。
  2. 尝试计算 $\[k]P$，其中 $k$ 是一个很大的合数。
  3. 如果在点加运算中求逆元失败（即 $gcd(\text{坐标差}, n) > 1$），则分解成功。
* **适用场景：** 寻找 **40-60 位（十进制）左右的因子**。它是目前已知分解这类因子的最强算法。

```python
import gmpy2
import random

def ecm_factor(n, B1=2000):
    """简化版 ECM：在椭圆曲线上寻找阶的倍数"""
    n = gmpy2.mpz(n)
    
    # 随机选择曲线参数 a 和点 P(x, y)
    x = gmpy2.mpz(random.randint(1, n-1))
    y = gmpy2.mpz(random.randint(1, n-1))
    a = gmpy2.mpz(random.randint(1, n-1))
    # 确保曲线非奇异：4a^3 + 27b^2 != 0
    b = (y*y - x*x*x - a*x) % n
    
    # 定义点加运算 (此处仅为逻辑演示，完整 ECM 需要处理无穷远点和斜率计算)
    # 在实际 CTF 中，通常直接调用集成好的库或工具
    # 以下为抽象过程：
    def add_points(P1, P2, a, n):
        # 核心在于计算斜率 lambda = (y2-y1)/(x2-x1)
        # 如果 gcd(x2-x1, n) 不为 1 且不为 n，则找到因子
        pass

    print("[*] ECM 过程通常由底层库如 GMP-ECM 实现，Python 层手动实现性能较低。")
    return None
```
