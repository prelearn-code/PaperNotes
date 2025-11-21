---
title: Enabling Verifiable Search and Integrity Auditing in Encrypted Decentralized Storage Using One Proof
year: 2024
venue: CVPR
field:
  - Crypto/AES
  - Crypto/HASH
  - Crypto/Pairing
  - Authentication
  - Integrity
  - Blockchain
  - Crypto/Searchable Encryption
pdf: "[[Enabling Verifiable Search and Integrity Auditing in Encrypted Decentralized Storage Using One Proof.pdf]]"
Read date: 2025-10-10
detailes: "[[设计方案]]"
---
# 方法

本文通过将 **搜索验证与完整性审计统一到一个证明中** 的技巧性结构设计，将原本需要分别进行的两类验证操作合并，大幅降低 DSN 场景下的链上开销与节点计算成本，实现加密条件下的高效可验证搜索与完整性审计。同时设计状态链信息，来保证文件更新的前向安全性。

# 主要贡献

## 安全性贡献


## 实验贡献

# 主要问题

1. **仅支持单关键词搜索**：当前仅支持 single-keyword，复杂查询（如相似性检索、多条件搜索）无法直接扩展。
2. **依赖链式状态结构**：搜索时必须遍历状态链，若同一关键词关联文件过多，检索延迟会增长；
3. **未处理访问模式泄露问题**：仍需引入 dummy 技术才能应对频率分析与访问模式攻击；
4. **需要节点额外执行搜索证明**：相比传统 PoS 仅验证完整性，本方案对资源较弱的节点仍存在一定额外负担。