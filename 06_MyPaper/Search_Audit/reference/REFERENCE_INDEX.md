# Search-Audit reference index

文件名中的 `R01`–`R10` 与《三项核心贡献：验证实验、Baseline 与代码实施计划》一致。

| ID | 年份 | 论文 | 标识 | 实验角色 |
|---|---:|---|---|---|
| R01 | 2025 | Song et al., *Enabling Verifiable Search and Integrity Auditing in Encrypted Decentralized Storage Using One Proof* | DOI `10.1109/TC.2025.3569182` | C1 原文核心一致性 |
| R02 | 2008 | Shacham and Waters, *Compact Proofs of Retrievability* | ePrint `2008/073` | C1 数据层 SW-HLA-core |
| R03 | 2020 | Boneh et al., *Efficient Polynomial Commitment Schemes for Multiple Points and Polynomials* | ePrint `2020/081` | C1 的 PCS-PUB 主后端 |
| R04 | 2020 | Gorbunov et al., *Pointproofs: Aggregating Proofs for Multiple Vector Commitments* | ePrint `2020/419` | C1 的 PCS-PUB 扩展后端 |
| R05 | 2025 | Miao et al., *Blockchain-Empowered Keyword Searchable Provable Data Possession for Large Similar Data* | DOI `10.1109/TIFS.2024.3516563` | C2 安全模型与核心一致性 |
| R06 | 2026 | Xu et al., *MPA: Lightweight and Updatable Integrity Auditing for Decentralized Storage Using Merkle Trees and Polynomial Commitments* | DOI `10.1109/TIFS.2026.3664004` | C3 MPA-core/MPA-adapted |
| R07 | 2026 | Huang et al., *FiDD: Secure Fine-Grained Deduplication and Dynamic Auditing Scheme for Cloud Storage* | DOI `10.1109/TON.2025.3614191` | C3 FiDD 核心一致性 |
| R08 | 2026 | Pan et al., *Blockchain-Enabled Efficient Deduplication and Mixed Auditing for Dynamic Cloud Data* | DOI `10.1109/TDSC.2025.3638157` | C3 去重审计核心一致性 |
| R09 | 2024 | Shen et al., *Keyword-Based Remote Data Integrity Auditing Supporting Full Data Dynamics* | DOI `10.1109/TSC.2023.3339521` | C3 关键词动态审计核心一致性 |
| R10 | 2023 | Wang et al., *BalanceProofs: Maintainable Vector Commitments with Fast Aggregation* | ePrint `2022/864` | C3 LOCAL-PCS |

实现标签统一使用：`PaperSpec` 表示原文算法，`Core` 表示明确列出的原文子集，`Adapted` 表示接入共同数据模型或密码后端后的版本。
