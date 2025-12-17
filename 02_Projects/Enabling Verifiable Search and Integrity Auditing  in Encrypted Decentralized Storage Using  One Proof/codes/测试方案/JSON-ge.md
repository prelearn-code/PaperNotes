
## 一、 核心设计原则

1. **后置记录模式 (Post-Measurement)**：任何涉及 `size()`、`length()`、`Json::writeString`（序列化）的操作，必须在 `PERF_TIMER_END` 之后执行。
    
2. **服务端插入 (Insert)**：**合并计时**。测量“密文读取 + 内存索引更新”的总时间，排除磁盘数据库持久化。
    
3. **服务端搜索 (Search)**：**逻辑闭环计时**。测量“加载数据库 + 搜索计算 + 证明生成”的时间，**排除** 结果序列化和结果文件写入磁盘的时间。
    
4. **服务端验证 (Verify)**：**完整验证计时**。测量“加载索引(获取PK) + 验证计算”的时间。
    

---

## 二、 监控指标定义表

### 2.1 计算时间 (Latency, ms)

|**ID**|**指标名称**|**测量范围说明**|**对应函数**|
|---|---|---|---|
|**T1**|`client_encrypt_total`|文件读取 + 加密 + 标签生成 + 写入密文文件|`client::encryptFile`|
|**T2**|`token_generation`|仅 `generateSearchToken` 核心计算|`client::searchKeyword`|
|**T3**|`server_insert_total`|**(合并)** 读取密文文件 + 解析参数 + 更新内存数据库|`node::insert_file`|
|**T4**|`search_proof_total`|**(修改)** **加载数据库** + 搜索计算 + 生成证明 (排除序列化/保存)|`node::Search...Proof`|
|**T5**|`verify_execution_time`|**(修改)** **加载索引数据库** + 核心验证逻辑|`node::VerifySearchProof`|

### 2.2 数据大小 (Size, bytes) - 始终在计时结束后记录

|**ID**|**指标名称**|**数据源**|**用途**|
|---|---|---|---|
|**S1**|`plaintext_size`|`plaintext` vector 大小|通信开销|
|**S2**|`encrypted_file_size`|`ciphertext` vector 大小|通信开销|
|**S3**|`insert_json_size`|序列化后的 `insert.json` 字符串长度|通信开销|
|**S4**|`search_request_size`|序列化后的搜索请求 JSON 字符串长度|Gas 计算|
|**S5**|`search_proof_size`|序列化后的搜索证明 JSON 字符串长度|Gas 计算|
|**S6**|`verify_result_size`|验证结果 (1 byte)|Gas 计算|

---

## 三、 详细代码实施逻辑

### 3.1 客户端修改 (`client.cpp`)

#### 1. 函数 `encryptFile` (涉及 T1, S1, S2, S3)

_逻辑：包含文件I/O和加密计算，但不包含JSON序列化和JSON写入。_

C++

```
// 1. [START] T1
PERF_TIMER_START(client_encrypt_total)

// 2. [EXECUTE] 业务逻辑
readFile(...);        // -> plaintext
encryptFileData(...); // -> ciphertext
writeFile(...);       // 保存密文到磁盘
generateAuthTags(...);
// ... 生成 insert_json 对象 (仅内存对象操作) ...

// 3. [STOP] T1
PERF_TIMER_END(client_encrypt_total)

// 4. [MEASURE & RECORD] S1, S2 (计时外)
if (perf_callback_) {
    perf_callback_->on_data_size_recorded("plaintext_size", plaintext.size());
    perf_callback_->on_data_size_recorded("encrypted_file_size", ciphertext.size());
}

// 5. [EXECUTE] 序列化 JSON (为了获取 S3，且比较耗时，故放在计时外)
std::string json_str = Json::writeString(writer, insert_json);

// 6. [RECORD] S3 (计时外)
if (perf_callback_) {
    perf_callback_->on_data_size_recorded("insert_json_size", json_str.length());
}

// 7. 保存 JSON 文件
writeFile(json_str);
```

#### 2. 函数 `searchKeyword` (涉及 T2, S4)

_逻辑：仅测量令牌生成算法时间。_

C++

```
// 1. [START] T2
PERF_TIMER_START(token_generation)

// 2. [EXECUTE] 核心算法
std::string Ti = generateSearchToken(keyword);

// 3. [STOP] T2
PERF_TIMER_END(token_generation)

// 4. [EXECUTE] 构建 JSON 并序列化 (计时外)
Json::Value root;
root["T"] = Ti; 
// ...
std::string output_json = Json::writeString(writer, root);

// 5. [RECORD] S4 (计时外)
if (perf_callback_) {
    perf_callback_->on_data_size_recorded("search_request_size", output_json.length());
}

// 6. 保存文件
```

---

### 3.2 服务端修改 (`storage_node.cpp`)

#### 1. 函数 `insert_file` (涉及 T3)

_逻辑：测量从读取密文到内存更新完成的时间。_

C++

```
// 1. [START] T3 (包含读取密文和处理)
PERF_TIMER_START(server_insert_total)

// [EXECUTE] 读取密文 (I/O)
std::string ciphertext = read_file_content(enc_file_path);

// [EXECUTE] 构建索引条目 (内存操作)
IndexEntry entry;
entry.ID_F = ID_F;
// ...

// [EXECUTE] 更新内存数据库 (Map操作)
index_database[ID_F] = entry;
// ... 更新 search_database ...

// 2. [STOP] T3 (内存更新完毕即停止)
PERF_TIMER_END(server_insert_total)

// 3. 保存数据库到磁盘 (不计入时间)
save_index_database();
save_search_database();
```

#### 2. 函数 `SearchKeywordsAssociatedFilesProof` (涉及 T4, S5)

_逻辑：测量加载数据库、搜索、生成证明的时间。**排除**结果序列化和写入磁盘的时间。_

C++

```
// 1. [START] T4 (从加载数据库开始)
PERF_TIMER_START(search_proof_total)

// [EXECUTE] 加载数据库 (I/O + 解析)
load_index_database();
load_search_database();

// [EXECUTE] 执行搜索与证明生成 (计算)
// ... while loop ...
// ... compute psi, phi ...
// ... 填充 PS, AS 内存对象 ...

// 2. [STOP] T4 (在序列化和保存文件之前停止)
PERF_TIMER_END(search_proof_total)

// 3. [EXECUTE] 生成输出 JSON 字符串 (计时外)
Json::Value output;
output["PS"] = ...;
std::string output_str = Json::writeString(writer, output);

// 4. [RECORD] S5 (计时外)
if (perf_callback_) {
    // 记录上链数据大小
    perf_callback_->on_data_size_recorded("search_proof_size", output_str.length());
}

// 5. [EXECUTE] 保存结果文件
save_json_to_file(output_path, output_str);
```

#### 3. 函数 `VerifySearchProof` (涉及 T5, S6)

_逻辑：测量加载索引数据库（获取PK）和验证计算的时间。_

C++

```
// [PREPARE] 加载证明文件 (作为输入参数，不计入验证时间)
Json::Value proof_data = load_json_from_file(search_proof_json_path);
// ... 提取 AS, PS, T, phi ...

// 1. [START] T5 (验证过程开始，包含加载索引以获取PK)
PERF_TIMER_START(verify_execution_time)

// [EXECUTE] 加载索引数据库 (模拟验证节点查询PK)
load_index_database(); 

// [EXECUTE] 配对计算与等式验证
// ... 计算 zeta1, zeta2 ...
// ... pairing_apply ...
bool result = (element_cmp(left, right) == 0);

// 2. [STOP] T5
PERF_TIMER_END(verify_execution_time)

// 3. [RECORD] S6 (计时外)
if (perf_callback_) {
    perf_callback_->on_data_size_recorded("verify_result_size", 1);
}

return result;
```

---

## 四、 接口定义

在 `client.h` 和 `storage_node.h` 中包含以下结构：

C++

```
#include <functional>
#include <string>

struct PerformanceCallback {
    // 时间回调 (ms)
    std::function<void(const std::string& name, double time_ms)> on_phase_complete;
    
    // 大小回调 (bytes)
    std::function<void(const std::string& name, size_t size_bytes)> on_data_size_recorded;
};
```

---

## 五、 方案确认

此方案 (方案 H) 已经完全吸收了您的修改：

1. **Strict Decoupling**: 所有数据大小计算均在 `TIMER_END` 之后。
    
2. **T3 (Insert)**: 合并了读取密文和内存处理。
    
3. **T4 (Search)**: 包含了数据库加载，但**排除**了结果保存。
    
4. **T5 (Verify)**: 包含了数据库加载（获取PK）。
    

这是一个完整且逻辑自洽的方案，可以直接用于代码生成。