---
title: MPA-Lightweight and Updatable Integrity Auditing for Decentralized Storage Using Merkle Trees and  Polynomial Commitments
year: 2021-01-01
venue: TIFS
field:
  - Integrity
pdf:
Read_date: 2026-07-03
detailes:
---
# 方案概述


轻量级 公共审计 多副本 动态更新 多项式承诺

我认为，本方案，只是一个简单的多副本完整性审计方案，加了一个动态更新，更新的还是哈希树。



## 贡献点
1. 第一个使用默克尔树认证的多项式承诺的紧密完整性审计方案，专门适用于去中心化多副本的云存储。
2. 先提交后披露的协议。
3. 扩展方案，支持多多文件、多供应商的批量审计。
4. 聚合需要一个专门的验证者。

## 特点
1. 智能合约验证
2. 

## 问题
1. 到底是怎么实现的这些性能或者提升
2. 为什么可以用多项式承诺KGZ方案，不能用其他的方法吗？
3. 贡献点1的专门适配去中心化的多副本云存储优化是什么？


## 方案流程

>数据外包阶段：用户加密、生成不同副本的区块，并生成扇区的标签，生成一个最终的MHT的根$Root_i$，上传到合约。

>CSP验证阶段：每一个CSP都进行跑一下本地验证，对于收到的副本标签与合约公开的$Root_i$根跑一下验证，符合就可以接受。

>挑战生成阶段：合约随机生成挑战的区块下标与挑战权重$\{a_j,v_j\}_{j=1}^c$，以及评估点$r$。

>证明生成：生成多项式承诺的结果。$$val = \sum_{j=1}^cv_j*f_{m_{a_j}}(r)$$
>$$h(X) = \frac{f_M(X)-val}{X-r}$$
>$$w = g^{h(\alpha)}$$

>证明验证阶段：
>$$e(\frac{\sigma^{agg}}{g^val},g)\overset{?}{=}e(w,g^{\alpha-r})$$
>$$\sigma^{\mathrm{agg}} = \prod_{j=1}^{c} \sigma_{a_j}^{v_j}, \sigma_{a_j} = g^{f m_{a_j}(\alpha)}$$

