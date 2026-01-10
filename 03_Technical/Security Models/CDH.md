### CDH 难题 (Computational Diffie-Hellman Problem)

在论文的 **Theorem 5** 3 中，**CDH 假设**是保证审计标签（Tags）不可伪造性的基石。
#### 1. 什么是 CDH 问题？

这是公钥密码学中最经典的难题之一。
- **输入**：$(g, \quad g^a, \quad g^b)$
    - $g$ 是生成元。
    - $a, b$ 是随机的秘密整数。
        
- **挑战**：计算 $g^{ab}$。
    

**直觉**：攻击者虽然知道 $g^a$ 和 $g^b$，但他没法做“指数乘法”。他只能做群乘法得到 $g^{a+b}$，这并不是目标。要算出 $g^{ab}$，目前唯一已知的方法是先解出 $a$ 或 $b$（即解决 DLOG 问题），但这非常难。

#### 2. CDH 的安全性证明 (标签不可伪造性归约)

这是对 **Theorem 5** 证明的详细逻辑回顾，展示如何利用“伪造标签”来“解决 CDH”。

证明逻辑 (归约法)：
目标：证明如果攻击者 $\mathcal{A}$ 能伪造标签 $\sigma$，模拟器 $\mathcal{S}$ 就能解出 CDH 难题（算出 $g^{ab}$）。

- 步骤 1：设置陷阱 (Embedding the Challenge)
    
    模拟器 $\mathcal{S}$ 拿到 CDH 难题 $(g, g^a, g^b)$。
    
    它把 $g^a$ 设为系统公钥（假装私钥是 $a$）。
    
    它把 $g^b$ 偷偷埋进某个哈希查询的结果中：$H^* \approx g^b$。
    
- 步骤 2：利用攻击者
    
    攻击者 $\mathcal{A}$ 并在不知情的情况下，对这个含有 $g^b$ 的哈希值进行了伪造。
    
    标签的数学定义是：$\sigma = (H^* \cdot \dots)^a$（用私钥 $a$ 签名）。
    
- 步骤 3：数学提取 (Extraction)
    攻击者输出的伪造标签实际上等于：
    $$\sigma = (g^b \cdot \dots)^a = g^{ab} \cdot (\dots)^a$$
    $\mathcal{S}$ 知道后面那部分干扰项 $(\dots)^a$，它通过除法将其除去，剩下的核心就是 $g^{ab}$。
- 结论：
    因为 $\mathcal{A}$ 伪造了标签 $\Rightarrow$ $\mathcal{S}$ 算出了 $g^{ab}$ $\Rightarrow$ CDH 问题被解决了。
    矛盾：CDH 是难解的 $\Rightarrow$ $\mathcal{A}$ 无法伪造标签。