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
### **论文真问题**

在去中心化存储网络中，现有基于区块链的审计方案通常将区块链视为透明数据库存储审计日志，导致**链上存储开销（On-chain Storage Overhead）随审计文件数量及请求规模呈线性增长**，造成区块链网络拥塞与资源浪费；本文首次在去中心化场景下，通过引入多项式承诺方案（PCS-MPAP），实现了针对多文件多副本的**常数级链上存储开销（Constant On-chain Storage Overhead）**批量审计机制。 

---
### **方案背景**

- **领域瓶颈**：
    
    - **传统 TPA 方案的信任失效**：现有非区块链方案（如 Li et al. ）依赖第三方审计者（TPA），存在单点故障风险，且难以保证 TPA 与云服务商（CSP）不合谋，无法适应去中心化环境（见 Section I Introduction）。
        
    - **现有区块链方案的扩展性缺陷**：现有区块链方案（如 Du et al. ）虽然解决了信任问题，但在批量审计时，链上存储开销随文件数量线性增加。例如，当审计文件数增加时，证明大小（Proof Size）会迅速膨胀，导致高昂的 Gas 费和存储压力（见 Section VI.A Table VIII）。
        
- **作者动机**：
    
    - 作者旨在设计一种去中心化的审计范式，利用智能合约替代 TPA 进行验证，同时解决由此带来的链上资源瓶颈。
        
    - 核心目标是提出一种高效的批量审计方案，使得无论审计多少文件，**链上存储开销始终保持为常数**，并显著降低存储服务提供商（SSP）的计算负担（见 Section I.A）。
        

---

### **创新点**

1. **[核心] 基于 PCS-MPAP 的高效批量审计机制 (Efficient Batch Auditing Scheme)**：
    
    - **突破性**：与现有使用 PCS-PLONK 或简单聚合的方案不同，本文利用 **PCS-MPAP (Polynomial Commitment Scheme for Multiple Points and Polynomials)** 技术，允许在不同挑战点对不同文件的多项式进行批量验证。通过构造插值多项式计算权重 $\beta_l$，将多个文件的评估值压缩为一个单一的聚合评估值 $E_i$，从而使提交到链上的证明大小不再随文件数量 $d$ 增加。
        
    - **关键证据**：
        
        - 聚合逻辑见 **Equation (9)** 至 **Equation (11)**，其中 SSP 计算聚合标签 $\sigma'_i$ 和聚合评估值 $E_i = \sum_{l=1}^d \beta_l \cdot S_{l,i}$。
            
        - 链上开销对比见 **Table VIII**，本文方案的链上存储开销恒定为 $3|\mathbb{G}_1| + |Z_p|$，而 Scheme 和 均为线性增长。
            
2. **[辅助] 基于同态验证标签与扇区划分的基本方案 (Basic Scheme with HVT & Sectoring)**：
    
    - **技术改进**：在数据预处理阶段，将每个数据块进一步划分为 $s$ 个扇区（Sector），构建多项式 $f_{m_{ij}}(X)$。结合同态验证标签（HVT），允许 SSP 将多个块的标签聚合成一个 $\sigma_i$。虽然这是针对单文件多副本的基础设计，但扇区化处理有效分摊了模幂运算的计算成本。
        
    - **关键证据**：
        
        - 标签生成公式见 **Equation (1)**：$\sigma_{ij}=(H(F_{id}||i||j)\cdot g^{f_{m_{ij}}(\alpha)})^{x}$。
            
        - 扇区对计算效率的影响分析见 **Figure 2**。
            

---

### **方案架构**

- 核心流程（输入→处理→输出）：
    
    用户生成带扇区划分的数据副本与多项式标签 $\rightarrow$ SSP 存储副本与标签 $\rightarrow$ 智能合约发起包含随机数 nonce 的挑战 $chal$ $\rightarrow$ SSP 基于 PCS-MPAP 聚合多文件证据并生成零知识证明 $Proof_i$ $\rightarrow$ 智能合约执行双线性对验证并记录日志。
    
- **关键设计**：
    
    - 差异化副本生成与多项式绑定：
        
        为了防止 SSP 存储单一副本欺骗用户，用户使用 AES 加密生成内容不同的副本 $Copy_i$，并将数据块的 $s$ 个扇区作为系数构建多项式 $f_{m_{ij}}(X)$。标签 $\sigma_{ij}$ 通过 BLS 签名结构绑定了文件 ID、副本索引 $i$ 和多项式在秘密点 $\alpha$ 的承诺值（见 Section IV.B.2 Eq 1）。
        
    - 跨文件聚合证明生成 (ProofGen)：
        
        SSP 不直接发送每个文件的评估值，而是利用拉格朗日插值思想构造权重 $\beta_l = \gamma^{l-1} \cdot Z_{T \setminus S_l}(z)$。通过该权重将不同文件在不同挑战点 $r_l$ 的评估值 $S_{l,i}$ 线性组合为 $E_i$。同时生成商多项式承诺 $W_i$ 和 $W'_i$，仅需上传 $(\sigma'_i, W_i, W'_i, E_i)$ 即可证明所有文件完整性（见 Section IV.C Eq 9-11）。
        
    - 随机掩码隐私保护：
        
        为了防止证明过程泄露原始数据，SSP 引入随机数 $\epsilon_i$ 计算盲化因子 $R_i = v^{\epsilon_i}$ 和混淆后的评估值 $s_i$（或批量方案中的对应处理），确保链上数据的零知识性（见 Section IV.B.3 Eq 5）。
        

---

### **实验环境**

- **硬件**：
    
    - SSP 节点：Intel Core i5-10500 CPU @ 3.10 GHz, 12.0 GB RAM, Linux。
        
    - User 节点：Intel Core i5-12400F CPU @ 2.50 GHz, 8.0 GB RAM, Windows。
        
    - 区块链环境：使用 **Ganache** 模拟以太坊网络，部署于阿里云 ECS s6 服务器。
        
- **基线对比方法**：
    
    - **Scheme (Li et al.)**：（传统基线）基于身份密码学的高效多副本审计方案，但在去中心化场景下证明过大。
        
    - **Scheme (Du et al.)**：（作者认为为 SOTA）基于区块链与 PCS-PLONK 的审计方案，但在多文件审计时缺乏聚合能力。
        
- **评估指标**：
    
    - 主指标：链上存储开销（Proof Size，单位 Byte）、Gas 开销（Gas Costs）、计算时间（Time）。
        
    - 次指标：扇区数量（Sector number）对性能的影响。
        
- **关键结果**：
    
    - **证明大小恒定**：在批量审计 20 个文件时，Scheme 的证明大小激增至约 6000 Bytes（线性增长），而本文方案始终稳定在 **128 Bytes**（常数级）（见 Section VI.B.1 Figure 4）。
        
    - **Gas 开销大幅降低**：在审计 10 个文件时，本文方案的 Gas 开销约为 5 Million，远低于 Scheme 的 >250 Million（见 Section VI.B.2 Figure 7）。
        
    - **SSP 计算效率**：随着文件数增加，本文方案的 ProofGen 时间增长明显缓于对比方案（见 Section VI.B.1 Figure 5）。
        

---

### **致命局限**

- **链上密码学原语实现的昂贵成本**：作者承认，受限于 Solidity 语言和 EVM 特性，在区块链上实现复杂的密码学原语（如双线性对运算）成本极高且困难，当前的实现高度依赖以太坊预编译合约的支持（见 Section VI.B.2）。
    
- **链上验证计算开销仍有优化空间**：尽管存储开销降为常数，但验证过程的计算逻辑（Verification Computation）在极端并发下仍可能成为瓶颈，作者在结论中表示未来工作旨在“进一步减轻链上验证的计算开销”（见 Section VII Conclusion）。