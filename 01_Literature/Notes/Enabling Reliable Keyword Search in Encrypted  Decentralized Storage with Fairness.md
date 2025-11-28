---
title: Enabling Reliable Keyword Search in Encrypted  Decentralized Storage with Fairness
year: 2021-01-01
venue: IEEE Trans. Dependable Secur. Comput
field:
  - Crypto/Searchable Encryption
pdf: "[[01_Literature/PDF/Enabling_Reliable_Keyword_Search_in_Encrypted_Decentralized_Storage_with_Fairness.pdf]]"
Read_date: 2025-11-28
detailes: "[[../../02_Projects/Enabling Reliable Keyword Search in Encrypted  Decentralized Storage with Fairness/note/设计方案|设计方案]]"
---
# 0.名词解释
1. SSE: Server-Sent Events,是一种在客户端和服务端之间实现**单向事件流**的机制，允许服务端主动向客户端发送事件数据.
2. **PoR**：服务方（如云存储提供商）能够向客户证明它仍然完整地保存着客户的数据，即使客户并不下载整个文件。
	- 你打电话问：“你还有我那份文件吗？” 对方说“有”，并告诉你第3页第5个字是什么——但这无法防止他们互相借文件应付检查。
3. **PoRep**：PoR的升级版本，为了验证是否是矿工有自己的副本文件，而不是请求时，信息相互传递。根据服务端的公钥与随机数、文件内容生成一个为一个副本ID.
	- 你要求每家公司**用专属模具把文件铸成一块独一无二的金属板**，且模具只能用一次。之后你只需看他们能否出示这块金属板的“指纹”（证明），就知道他们是否真的自己存了一份。 

# 1.研究背景

## 1.1 当前方案无法阻止双向作恶
客户端服务端双向恶意节点无法避免问题。
服务端：之前是定期服务端向客户端进行收费，服务端可以伪造验证信息，从其他的节点获得同样的验证文件存在的证明。
客户端：客户端也可以进行赖账，由于是客户端判断搜索的结果是否是正确，现在可以否认并赖账。

## 1.2 缺乏加密搜索与服务公平性
按次进行加密搜索收费。

## 1.3 公平支付的问题
没有生成锁之类的解决，现在都无法判断谁是恶意节点，无法自动执行公平的支付交易。


# 2. 本文的贡献

## 2.1 带公平支付的可靠加密关键词搜索协议

## 2.2 两层认证 + 仲裁分片投票的公平支付机制

## 2.3 保持“文件–索引共址”的动态 SSE 部署策略
把索引数据库与搜索结果数据库同时保存，加快搜索速度。
# 论文
**论文真问题**  
在区块链去中心化存储中，既要在加密文件上支持动态可更新的关键词搜索，又要在“客户与存储节点均可作恶”的条件下做到**按次公平付费（pay-per-authenticated-use）**，避免节点偷懒或客户赖账，而现有SSE/可验证SSE与现有去中心化存储都没有同时解决这两个问题。

---

**方案背景**

- **领域瓶颈**
    
    1. **SSE 假设中心化、半诚实服务器，无法对付去中心化环境下的双向作恶**：现有 SSE 与动态 SSE 工作（如 [6],[7],[8]）默认“云服务器”模型，仅防止半诚实或单方恶意服务器，既不考虑去中心化存储中的文件/索引分片部署问题，也不处理恶意客户端诬陷服务器的问题。文中明确指出：已有 SSE 方案“focus on a centralized setting”，且“all of these works address the security against a semi-honest adversary”，无法应对去中心化模型中“dishonest clients and dishonest service peers”的威胁。
        
    2. **去中心化存储仅支持按标识取文件，缺乏加密搜索与服务公平性**：如 Sia、Storj 等系统，要么缺乏隐私保护（如 Filecoin 仅用 PoR，无加密），要么只做端到端加密，不能按关键词检索，只能按文件标识取回；同时，仅用区块链记录合同与 PoR 无法确保“每次搜索按效果付费”的金融公平性。文中指出 Sia/Storj “can only retrieve outsourced files via their identifiers”，且 Filecoin “does not provide privacy protection on the outsourced files”。
        
    3. **现有可验证 SSE 只验证服务器，不解决“谁在说谎”与公平支付**：如 Bost 等的 verifiable SSE 只实现客户端侧对服务器返回结果的正确性验证，场景仍为 client–server；文中指出这些方案“only consider the typical client-server model and a honest client”，无法区分“节点作恶”还是“客户端诬陷”，更谈不上在区块链上做自动化公平结算。
        
- **作者动机**
    
    - 在已有去中心化存储“合约后选节点、端侧加密但无关键词搜索”的基础上，引入 SSE，使得每个被合约选中的 peer 既存放加密文件，又存放其加密索引，实现低延迟加密搜索，并兼容现有平台的工作流。
    - 
        
    - 在“客户端和服务节点都可能作恶”的假设下，用智能合约与链上日志实现公平付费：节点只有在“可证实地提供正确搜索结果”时才能从用户押金中自动收款；同时避免直接把复杂 ZKP 放到链上带来的巨大证明生成与 gas 成本。
        

---

**创新点**

1. **[核心] Vfair：带公平支付的可靠加密关键词搜索协议**
    
    - **本质改动**：在每个被合约选中的服务节点上，采用**文件索引式动态 SSE + 多集哈希（set hash）**构造整体搜索结构，并在区块链上只锚定“文件添加与检索摘要元数据”；把搜索正确性验证拆成“客户端本地验证 + 争议时仲裁分片重放搜索”，通过时间锁支付（time-locked payment）联动公平结算。这样避免了在链上执行高成本 ZKP，同时保证“正确服务 ⇔ 得到报酬”。
        
    - **关键证据**：
        
        - 设计理据中明确提出：相比直接使用 Hawk 式 ZKP 证明搜索正确性，“proof generation overhead”与链上验证 gas 过高，因此改为“anchor metadata as undeniable evidences”，只在争议时由 arbiter shard 重放搜索并通过 set hash 比较来裁决。
            
        - Vfair 的复杂度与对比方案列于 Table 1：在动态搜索上给出了搜索、更新、通信、客户端存储以及 soundness/fairness 的对比，Vfair 是表中唯一同时标记“soundness + fairness”的方案。
            
2. **[核心] 两层认证 + 仲裁分片投票的公平支付机制**
    
    - **机制要点**：
        
        - 第一层：客户端维护本地 $checklist (T_{\text{client}})$，通过多集哈希 H 聚合搜索结果的文件 ID，验证服务节点返回的 posting list；若哈希不符，则发起仲裁请求。
            
        - 第二层：arbiter shard(**仲裁分片**) 从链上取回此前锚定的文件添加元数据和搜索 token，重建索引并重放搜索，汇总得到挑战哈希 (h_c)，与服务节点此前上传的结果哈希 (h_m) 对比。若不一致，则在链上投票触发 `judge`，终止时间锁支付。
            
        - 使用 Byzantine 投票机制：设仲裁分片规模为 N，假设诚实节点比例 > 2/3，只要获得超过 (N \cdot g)（g>2/3）票数，就可达成共识并决定是否 halt payment。
            
    - **关键证据**：
        
        - Section 5.2–5.3 中给出完整 protocol：_Keyword search_ 和 _Fair judgement_ 两个过程，以及 Fig. 3、Fig. 4 的流程图，详细描述了 (T_{\text{client}})、(T_{\text{peer}})、(h_c)、(h_m) 的构造与比较。
            
        - Judgment fairness 小节明确证明：在 set hash 抗碰撞与 >2/3 诚实仲裁节点的前提下，“若节点作恶则锁定支付必被终止，若客户端诬陷则支付不会被终止”。
            
3. **[辅助] 保持“文件–索引共址”的动态 SSE 部署策略**
    
    - **策略内容**：在每个合约服务节点上，将文件密文与其对应的**文件索引 (z_f)** 和 **搜索索引 (z_w)** 共存，避免索引跨节点分片；如果关键词从未被查询，就线性扫描文件索引；一旦查询过，就将 posting list (I_w) 与其 set hash (h_m) 缓存在搜索索引与 digest index 中，实现后续 O(1) 查询。
        
    - **突破点**：
        
        - 避免了去中心化环境下的跨节点通信与索引重组开销，使现有动态 SSE 架构可以“原封不动地”部署在单节点上。
            
        - 通过 file-index → search-index 的“懒建索引”策略，使一开始查询成本是 O(N) 线性扫描，但在查询历史积累后，绝大多数热点关键词达到 O(1) 查询延迟。
            
    - **关键证据**：
        
        - Section 5.1 明确强调 preserving file and index locality 带来的三个好处：减少 peer 间交互、直接复用现有 SSE、复用 Storj 类平台的匹配机制。
            
        - Fig. 7(b) 的实验显示，随着查询次数增加，平均查询延迟快速下降，400k 记录数据集在 25,000 次随机查询后平均延迟约 460ms。
            
4. **[辅助] 经济成本显式评估的智能合约实现**
    
    - **内容**：用 Solidity 编写智能合约，集成 deposit、search（时间锁支付 + 调度调用）、judge（依据仲裁投票 halt 支付）函数，并在 Ethereum TestRPC 上评估部署、文件添加、搜索、仲裁的 gas 成本和链上存储字节数。
        
    - **关键证据**：
        
        - Fig. 6 给出了 search 相关的 Solidity 代码框架。
            
        - Fig. 8 量化了 gas 成本：部署合约、文件添加、搜索和仲裁分别约 $0.76、$0.59、$0.64、$0.15（按 410 USD/ETH）。Table 4 给出每类交易在链上存储的字节数。
            

---

**方案架构**

- **核心流程（输入→处理→输出）**
    
    1. **文件添加**：
        
        - 输入：明文文件 (f) 与内部解析出的唯一关键词集合 (s = {w_i})。
            
        - 处理：客户端用密钥 (k_1,k_2) 与 PRF/HMAC 构造关键词–ID 对的密文组，拼成文件索引密文 (c^*)，再加上文件 ID、历史搜索引用列表 (x)、文件密文 (c = \text{Enc}_{k_2}(f))，形成 add token (d_f)；同时用 set hash H 计算 (H(ID(f))) 并累加到本地 checklist (T_{\text{client}})。客户端与服务节点各自对 (d_f) 计算摘要 ((h_0, H(d_f)))，分别提交到链上，经比较一致后才确认本次添加。
            
        - 输出：服务节点更新其文件索引 (z_f)、搜索索引 (z_w) 与摘要索引 (T_{\text{peer}})，区块链中记录 ((h_0, H(d_f))) 作为后续仲裁的证据。
            
    2. **关键词搜索**：
        
        - 输入：查询关键词 (w)。
            
        - 处理：客户端生成 search token (t_w = F_{k_1}(w)) 并上链；服务节点从链上取回 (t_w)：
            
            - 若 (t_w) 已查询过：直接从 (z_w[t_w]) 取 posting list (I_w)，从 (T_{\text{peer}}[t_w]) 取结果摘要 (h_m)。
                
            - 若未查询过：线性扫描 (z_f) 中各文件索引密文，检查每个组件是否满足 (H_{t_w}(r_i) = l_i)，构建新的 (I_w)，并用 H 聚合对应文件 ID 得到 (h_m)，同时写入 (z_w,T_{\text{peer}})。
                
            - 服务节点返回 (I_w) 与文件密文集 ({c}) 给客户端，并在链上提交 ((t_w, h_m)) 触发 t 时间锁支付。
                
        - 输出：客户端解密 ({c})、比对 (I_w) 的正确性，并用 set hash 计算 (h^* = \sum_{ID \in I_w} H(ID))，与 (T_{\text{client}}[t_w]) 比较；若不一致则发起仲裁请求。
            
    3. **公平仲裁与支付**：
        
        - 输入：客户端的仲裁请求（包含争议搜索 token）。
            
        - 处理：仲裁分片向服务节点索取所有相关 add token ( {d_f} )，各节点：
            
            - 验证每个 (d_f) 的哈希与链上记录 (H(d_f)) 是否一致。
                
            - 重建挑战索引 (z_f^*)，对 token (t_w) 线性重放搜索得到 (I_w^*)。
                
            - 通过链上已锚定的各文件 ID 的 set hash，聚合得到 (h_c)，与服务节点在 search 交易中提交的 (h_m) 对比。
                
            - 若 (h_c \neq h_m)，则投出“halt payment”一票。
                
        - 输出：若 halt 票数 ≥ (N \cdot g)，智能合约执行 `judge`，终止该次时间锁支付；反之，锁定时间到期后自动执行 `Transfer`，节点获得报酬。
            
- **关键设计机制**
    
    1. **文件索引结构（file-index-based SSE）**
        
        - 每个文件独立生成索引密文 (c^*)，整体数据库是 ((w, id)) 对的集合，而非典型倒排索引；首次查询某关键词时必须扫描所有文件索引，之后该关键词的结果被缓存到 (z_w) 中，实现“线性首查 + O(1) 复查”的性能特征。
            
    2. **多集哈希驱动的结果认证**
        
        - 采用增量多集哈希 H：客户端在文件添加时将 H(ID(f)) 累加到 (T_{\text{client}})，服务节点在搜索时对结果中的 ID 做同样聚合得到 (h_m)，仲裁节点在重放搜索时用链上锚定的 H(ID(f)) 得到 (h_c)。由于 set hash 抗碰撞，两个不同的 ID 集合以极低概率生成相同摘要，从而提供 soundness。
            
    3. **时间锁支付 + 链上最小化存证**
        
        - 每次搜索只在链上存储 ((t_w, h_m)) 与必要的 H(ID(f)) 摘要，而不存放整个索引或 ZKP；时间锁 t 为客户端本地验证与可能的仲裁提供窗口，过期自动完成支付。链上交易字节数控制在几十字节级别（Table 4），降低状态膨胀。
            

---

**实验环境**

- **硬件 / 运行环境**
    
    - 桌面机：四核 3.4 GHz CPU、16 GB RAM、256 GB SSD、Linux 16.04。
        
    - 客户端与节点算法实现：Python + cryptography 库，Fernet 对称加密（256-bit key），SHA-256 作为哈希，HMAC-SHA256 实现 PRF。
        
    - 区块链环境：Solidity 智能合约，在本地 Ethereum TestRPC 模拟网络上测试。
        
- **基线对比方法（来自 Table 1）**
    
    - KPR12：Kamara et al. 动态 SSE [7] —— 无 soundness / fairness。
        
    - CJJ+14：Cash et al. 大规模动态 SSE [8] —— 无 soundness / fairness。
        
    - HK14：Hahn & Kerschbaum 动态 SSE [22] —— 具有客户端侧 search history 用于 update（soundness，但无 fairness）。
        
    - BFP16：Bost et al. verifiable dynamic SSE [12] —— 支持 soundness，无 fairness。
        
    - B16：Bost forward secure SSE [23] —— 支持 soundness，无 fairness。
        
    - 是否 SOTA：**[原文未详述]**（文中未使用 “SOTA/state-of-the-art” 描述上述方法）。
        
- **评估指标**
    
    - **主指标**：
        
        - 加密数据库构建（add token 构造）延迟 vs ((w,id)) 对数量。
            
        - 关键词搜索平均延迟 vs 查询次数与数据库规模（400k/700k/1,000k 对）。
            
        - 智能合约相关 gas 成本：部署、文件添加、搜索、仲裁。
            
    - **次指标**：
        
        - 加密数据库 EDB 大小（MB）。
            
        - 客户端本地 checklist (T_{\text{client}}) 存储开销。
            
        - 每类链上交易的存储字节数（search token、result metadata、file addition）。
            
- **关键结果（定量）**
    
    1. **加密数据库构建性能**
        
        - 单个文件含约 300,000 个不同关键词时，构造 add token 耗时 < 7 秒。
            
        - 构造包含 1,000,000 条 ((w,id)) 记录的 EDB（多文件）总耗时 < 25 秒，作者指出在相同测试环境下相对于基于基本倒排索引的方案 [8] 约提升 50 倍。
            
    2. **搜索延迟与仲裁重放开销**
        
        - 对三个规模数据集（400k/700k/1,000k 对）进行随机查询，每 5,000 次查询记录平均搜索时间。
            
        - 在 400k 对数据集上，执行 25,000 次随机查询后，最近 5,000 次查询的平均延迟降至约 460ms。
            
        - 对 1,000,000 对数据集进行一次线性扫描的延迟约 14 秒，对应仲裁节点在争议时重放一次搜索操作的时间成本。
            
    3. **存储开销**
        
        - 三个 EDB 规模对应的加密数据库大小分别约为 20.99 MB（400k 对）、36.01 MB（700k 对）、51.46 MB（1,000k 对）（Table 3）。
            
        - 客户端 checklist (T_{\text{client}}) 使用 set hash，每个摘要 ~4 bytes，即使覆盖 Google 10,000 常见词，整体约 39 MB。
            
    4. **链上成本**
        
        - 在 1 ETH ≈ 410 USD 汇率下，合约部署、单次文件添加（双 add 交易）、单次搜索、一次仲裁操作对应资金成本分别约 $0.76 / $0.59 / $0.64 / $0.15。
            
        - 每种交易的链上数据：search token 约 20 字节，search 结果元数据约 24 字节（HMAC token + 4 字节 set hash），文件添加交易约 36 字节（SHA-256 摘要 + set hash）（Table 4）。
            

---

**致命局限**

1. **缺乏前向安全（forward security），易受文件注入攻击**
    
    - 作者在 Discussion 指出：新近工作表明动态 SSE 在“文件注入攻击”下需要前向安全，否则攻击者可通过注入精心构造的文件推断过去查询内容；并明确表示现有 Vfair 方案未具备前向安全，仅给出如何在架构上“轻微修改”以引入 trapdoor permutation 的大致思路，详细构造留作未来工作。
        
    - 换言之，**当前 Vfair 协议本身不防文件注入导致的查询泄露**。
        
2. **链上元数据永久保存导致的存储开销问题未解决**
    
    - 作者承认：区块链为 append-only，即使文件在系统中被删除，之前锚定的文件添加和搜索元数据仍永久保留；文中称这是“unnecessary storage overhead (when a file is deleted)”，并表示未来考虑利用链下存储（如 [33]）以减轻区块链状态膨胀。
        
    - 当前实现中，所有 ((h_0, H(d_f)))、搜索 token 与结果摘要都长久写入链上，**缺乏具体的状态压缩 / 清理机制**。
        