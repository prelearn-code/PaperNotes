# 方案H：性能监控完整实施方案

**版本：** v1.0  
**日期：** 2025-12-15  
**基于：** 方案H设计文档

---

## 📋 修改文件清单

| 文件               | 修改类型  | 修改数量 | 说明              |
| ---------------- | ----- | ---- | --------------- |
| client.h         | 新增    | 3处   | 添加回调结构、成员、方法    |
| client.cpp       | 新增+修改 | 5处   | 宏定义、构造函数、2个函数计时 |
| storage_node.h   | 新增    | 3处   | 添加回调结构、成员、方法    |
| storage_node.cpp | 新增+修改 | 6处   | 宏定义、构造函数、3个函数计时 |

---

## 一、client.h 修改方案

### 修改1.1：添加 PerformanceCallback 结构体

**位置：** 第13行之后（`#include <jsoncpp/json/json.h>` 之后）

**插入内容：**

```cpp
// ==================== 性能监控回调结构体 ====================
/**
 * @brief 性能监控回调接口（用于测试时精确测量时间和数据大小）
 * 
 * 设计原则：
 * 1. 时间测量在计算完成后立即回调
 * 2. 数据大小测量在计时结束后回调
 * 3. 正常使用时回调指针为nullptr，零性能开销
 */
struct PerformanceCallback {
    // 时间回调 (毫秒)
    std::function<void(const std::string& name, double time_ms)> on_phase_complete;
    
    // 数据大小回调 (字节)
    std::function<void(const std::string& name, size_t size_bytes)> on_data_size_recorded;
};
```

**说明：** 在所有include之后、class定义之前添加

---

### 修改1.2：添加私有成员变量

**位置：** 第382行左右（class StorageClient 的 private 部分末尾，在最后一个成员变量之后）

**插入内容：**

```cpp
    // 性能监控回调指针（默认nullptr，测试时设置）
    PerformanceCallback* perf_callback_;
```

**说明：** 在 `inline static constexpr size_t SECTORS_PER_BLOCK` 定义之后添加

---

### 修改1.3：添加公共方法

**位置：** 第175行左右（在 `std::string extractFileName(...)` 之后）

**插入内容：**

```cpp
    
    /**
     * @brief 设置性能监控回调（测试专用）
     * @param callback 回调函数指针，nullptr表示禁用监控
     * 
     * 使用示例：
     * PerformanceCallback callback;
     * callback.on_phase_complete = [](const std::string& phase, double time) {
     *     std::cout << phase << ": " << time << "ms" << std::endl;
     * };
     * callback.on_data_size_recorded = [](const std::string& name, size_t size) {
     *     std::cout << name << ": " << size << " bytes" << std::endl;
     * };
     * client.setPerformanceCallback(&callback);
     */
    void setPerformanceCallback(PerformanceCallback* callback) {
        perf_callback_ = callback;
    }
```

**说明：** 在public部分的最后添加

---

## 二、client.cpp 修改方案

### 修改2.1：添加计时宏定义

**位置：** 所有 `#include` 之后、第一个函数定义之前（约第30行左右）

**插入内容：**

```cpp
// ==================== 性能监控宏定义 ====================
/**
 * 使用方法：
 * PERF_TIMER_START(metric_name)
 * // ... 执行计算 ...
 * PERF_TIMER_END(metric_name)
 * // 在计时结束后记录数据大小：
 * if (perf_callback_) {
 *     perf_callback_->on_data_size_recorded("data_name", data.size());
 * }
 */
#define PERF_TIMER_START(name) \
    auto perf_##name##_start = std::chrono::high_resolution_clock::now();

#define PERF_TIMER_END(name) \
    if (perf_callback_) { \
        auto perf_##name##_end = std::chrono::high_resolution_clock::now(); \
        auto perf_##name##_duration = std::chrono::duration_cast<std::chrono::milliseconds>( \
            perf_##name##_end - perf_##name##_start).count(); \
        perf_callback_->on_phase_complete(#name, static_cast<double>(perf_##name##_duration)); \
    }
```

**说明：** 在第一个函数定义前添加，需要 `#include <chrono>` 支持

---

### 修改2.2：修改构造函数初始化列表

**位置：** 第31行（StorageClient::StorageClient() 构造函数）

**当前代码：**

```cpp
StorageClient::StorageClient() 
    : initialized_(false), states_loaded_(false) {
```

**修改为：**

```cpp
StorageClient::StorageClient() 
    : initialized_(false), states_loaded_(false), perf_callback_(nullptr) {
```

**说明：** 在初始化列表末尾添加 `perf_callback_(nullptr)`

---

### 修改2.3：encryptFile 函数修改（T1 + S1 + S2 + S3）

#### 修改2.3.1：添加计时起点

**位置：** 第558行（文件读取之前）

**当前代码：**

```cpp
    // 读取文件
    std::vector<unsigned char> plaintext;
    if (!readFile(file_path, plaintext)) {
```

**在此之前插入：**

```cpp
    // ========== 开始计时：T1 客户端加密总时间 ==========
    PERF_TIMER_START(client_encrypt_total)
    
    // 读取文件
```

**说明：** 在文件读取前启动计时

---

#### 修改2.3.2：处理失败情况

**位置：** 第559-561行

**当前代码：**

```cpp
    if (!readFile(file_path, plaintext)) {
        return false;
    }
```

**修改为：**

```cpp
    if (!readFile(file_path, plaintext)) {
        PERF_TIMER_END(client_encrypt_total)  // 失败也记录
        return false;
    }
```

**位置：** 第566-569行

**当前代码：**

```cpp
    if (!encryptFileData(plaintext, ciphertext)) {
        std::cerr << "[错误] 文件数据加密失败" << std::endl;
        return false;
    }
```

**修改为：**

```cpp
    if (!encryptFileData(plaintext, ciphertext)) {
        PERF_TIMER_END(client_encrypt_total)  // 失败也记录
        std::cerr << "[错误] 文件数据加密失败" << std::endl;
        return false;
    }
```

**位置：** 第589-595行

**当前代码：**

```cpp
    if (!writeFile(enc_file, ciphertext)) {
        std::cerr << "[错误] 无法保存加密文件: " << enc_file << std::endl;
        std::cerr << "       请检查:" << std::endl;
        std::cerr << "       1. 目录权限" << std::endl;
        std::cerr << "       2. 磁盘空间" << std::endl;
        return false;
    }
```

**修改为：**

```cpp
    if (!writeFile(enc_file, ciphertext)) {
        PERF_TIMER_END(client_encrypt_total)  // 失败也记录
        std::cerr << "[错误] 无法保存加密文件: " << enc_file << std::endl;
        std::cerr << "       请检查:" << std::endl;
        std::cerr << "       1. 目录权限" << std::endl;
        std::cerr << "       2. 磁盘空间" << std::endl;
        return false;
    }
```

**说明：** 所有可能return的地方都要先调用 PERF_TIMER_END

---

#### 修改2.3.3：添加计时终点和数据大小记录

**位置：** 第665行左右（在构建 insert_json 对象完成后，序列化之前）
**修改意见**:  修改为insert_json对象构建之前，在数据计算结束之后，insert_json对象构建之前。

**查找代码：**

```cpp
    insert_json["kt_w"] = kt_w_array;
    
    // 2. 生成唯一的 insert.json 路径并保存
    std::string base_name = original_filename;
```

**在此之间插入：**

```cpp
    insert_json["kt_w"] = kt_w_array;
    
    // ========== 结束计时：T1 客户端加密总时间 ==========
    PERF_TIMER_END(client_encrypt_total)
    
    // ========== 记录数据大小：S1, S2 ==========
    if (perf_callback_) {
        perf_callback_->on_data_size_recorded("plaintext_size", plaintext.size());
        perf_callback_->on_data_size_recorded("encrypted_file_size", ciphertext.size());
    }
    
    // 2. 生成唯一的 insert.json 路径并保存
```

**说明：** 计时在密文文件写入完成后结束，数据大小记录在计时结束后

---

#### 修改2.3.4：记录 JSON 大小

**位置：** 第677行（JSON写入文件后）
**当前代码：**

```cpp
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "  ";
    insert_file << Json::writeString(writer, insert_json);
    insert_file.close();
    std::cout << "[成功] insert.json 已生成: " << insert_json_path << std::endl;
```

**修改为：**

```cpp
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "  ";
    std::string insert_json_str = Json::writeString(writer, insert_json);
    insert_file << insert_json_str;
    insert_file.close();
    
    // ========== 记录数据大小：S3 ==========
    if (perf_callback_) {
        perf_callback_->on_data_size_recorded("insert_json_size", insert_json_str.length());
    }
    
    std::cout << "[成功] insert.json 已生成: " << insert_json_path << std::endl;
```

**说明：** 保存JSON字符串，用于记录大小

---

### 修改2.4：searchKeyword 函数修改（T2 + S4）

#### 修改2.4.1：添加计时

**位置：** 第1448-1454行

**当前代码：**

```cpp
    // 2. 生成搜索令牌
    std::string search_token = generateSearchToken(keyword);
    if (search_token.empty()) {
        std::cerr << "[错误] 搜索令牌生成失败" << std::endl;
        return false;
    }
    std::cout << "[搜索令牌] 步骤1: 计算 T = SE.Enc(mk, w) 完成" << std::endl;
```

**修改为：**

```cpp
    // 2. 生成搜索令牌
    // ========== 开始计时：T2 令牌生成 ==========
    PERF_TIMER_START(token_generation)
    
    std::string search_token = generateSearchToken(keyword);
    
    // ========== 结束计时：T2 令牌生成 ==========
    PERF_TIMER_END(token_generation)
    
    if (search_token.empty()) {
        std::cerr << "[错误] 搜索令牌生成失败" << std::endl;
        return false;
    }
    std::cout << "[搜索令牌] 步骤1: 计算 T = SE.Enc(mk, w) 完成" << std::endl;
```

**说明：** 只计时核心的 generateSearchToken 函数

---

#### 修改2.4.2：记录请求大小

**位置：** 第1485行（JSON写入后）

**当前代码：**

```cpp
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "    ";
    ofs << Json::writeString(writer, root);
    ofs.close();
    
    std::cout << "[成功] 搜索令牌已生成: " << output_path << std::endl;
```

**修改为：**

```cpp
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "    ";
    std::string search_json_str = Json::writeString(writer, root);
    ofs << search_json_str;
    ofs.close();
    
    // ========== 记录数据大小：S4 ==========
    if (perf_callback_) {
        perf_callback_->on_data_size_recorded("search_request_size", search_json_str.length());
    }
    
    std::cout << "[成功] 搜索令牌已生成: " << output_path << std::endl;
```

**说明：** 记录搜索请求JSON大小

---

## 三、storage_node.h 修改方案

### 修改3.1：添加 PerformanceCallback 结构体

**位置：** 第16行之后（`#include <jsoncpp/json/json.h>` 之后）

**插入内容：**

```cpp
// ==================== 性能监控回调结构体 ====================
/**
 * @brief 性能监控回调接口（与client.h保持一致）
 */
struct PerformanceCallback {
    // 时间回调 (毫秒)
    std::function<void(const std::string& name, double time_ms)> on_phase_complete;
    
    // 数据大小回调 (字节)
    std::function<void(const std::string& name, size_t size_bytes)> on_data_size_recorded;
};
```

**说明：** 与client.h保持一致，或者可以提取到单独的头文件

---

### 修改3.2：添加私有成员变量

**位置：** 第74行左右（class StorageNode 的 private 部分，在 `std::string generate_random_seed();` 之前）

**插入内容：**

```cpp
    // 性能监控回调指针（默认nullptr）
    PerformanceCallback* perf_callback_;
    
    // 辅助函数
```

**说明：** 在private部分添加成员变量

---

### 修改3.3：添加公共方法

**位置：** 第146行左右（在 `void print_detailed_status();` 之后）

**插入内容：**

```cpp
    
    /**
     * @brief 设置性能监控回调（测试专用）
     * @param callback 回调函数指针，nullptr表示禁用监控
     */
    void setPerformanceCallback(PerformanceCallback* callback) {
        perf_callback_ = callback;
    }
```

**说明：** 在public部分添加

---

## 四、storage_node.cpp 修改方案

### 修改4.1：添加计时宏定义

**位置：** 所有 `#include` 之后、第一个函数定义之前

**插入内容：**

```cpp
// ==================== 性能监控宏定义 ====================
#define PERF_TIMER_START(name) \
    auto perf_##name##_start = std::chrono::high_resolution_clock::now();

#define PERF_TIMER_END(name) \
    if (perf_callback_) { \
        auto perf_##name##_end = std::chrono::high_resolution_clock::now(); \
        auto perf_##name##_duration = std::chrono::duration_cast<std::chrono::milliseconds>( \
            perf_##name##_end - perf_##name##_start).count(); \
        perf_callback_->on_phase_complete(#name, static_cast<double>(perf_##name##_duration)); \
    }
```

**说明：** 与client.cpp保持一致

---

### 修改4.2：修改构造函数初始化列表

**位置：** 查找 `StorageNode::StorageNode` 构造函数

**当前代码示例：**

```cpp
StorageNode::StorageNode(const std::string& data_directory, int port)
    : crypto_initialized(false),
      node_id(""),
      data_dir(data_directory),
      server_port(port) {
```

**修改为：**

```cpp
StorageNode::StorageNode(const std::string& data_directory, int port)
    : crypto_initialized(false),
      node_id(""),
      data_dir(data_directory),
      server_port(port),
      perf_callback_(nullptr) {
```

**说明：** 在初始化列表末尾添加 `perf_callback_(nullptr)`

---

### 修改4.3：insert_file 函数修改（T3）

#### 修改4.3.1：添加计时起点

**位置：** 第929行（函数开始处，验证参数之后，开始读取密文文件之前）

**查找代码：**

```cpp
bool StorageNode::insert_file(const std::string& param_json_path, const std::string& enc_file_path) {
    std::cout << "\n🔍 开始插入文件..." << std::endl;
    
    // 步骤1: 加载并验证参数JSON
    if (!file_exists(param_json_path)) {
        std::cerr << "❌ 参数文件不存在: " << param_json_path << std::endl;
        return false;
    }
    
    Json::Value params = load_json_from_file(param_json_path);
    // ... 验证JSON参数 ...
```

**在参数验证完成后，开始读取密文之前插入：**

```cpp
    // ... 验证完所有JSON参数 ...
    
    // ========== 开始计时：T3 服务端插入总时间 ==========
    // 包含：读取密文文件 + 构建索引 + 更新内存数据库
    PERF_TIMER_START(server_insert_total)
    
    // 步骤2: 读取加密文件
    std::cout << "📂 读取加密文件..." << std::endl;
```

**说明：** 在读取密文文件前启动计时

---

#### 修改4.3.2：处理失败情况

在所有可能return false的地方，都要先调用 `PERF_TIMER_END(server_insert_total)`

**示例位置1：** 密文文件读取失败

```cpp
    std::string ciphertext = read_file_content(enc_file_path);
    if (ciphertext.empty()) {
        PERF_TIMER_END(server_insert_total)  // 失败也记录
        std::cerr << "❌ 加密文件读取失败: " << enc_file_path << std::endl;
        return false;
    }
```

**说明：** 需要在函数中所有return false之前添加 PERF_TIMER_END

---

#### 修改4.3.3：添加计时终点

**位置：** 在更新内存数据库完成后，保存数据库文件之前

**查找代码：**

```cpp
    // 更新搜索数据库
    for (const auto& kw : entry.keywords) {
        IndexSearchEntry search_entry;
        // ... 设置字段 ...
        search_database[search_entry.Ti_bar] = search_entry;
    }
    
    // 保存数据库
    if (!save_search_database()) {
```

**在此之间插入：**

```cpp
    // 更新搜索数据库
    for (const auto& kw : entry.keywords) {
        IndexSearchEntry search_entry;
        // ... 设置字段 ...
        search_database[search_entry.Ti_bar] = search_entry;
    }
    
    // ========== 结束计时：T3 服务端插入总时间 ==========
    // 内存数据库更新完成，排除磁盘持久化时间
    PERF_TIMER_END(server_insert_total)
    
    // 保存数据库（不计入计时）
    if (!save_search_database()) {
```

**说明：** 在内存操作完成后、磁盘写入前结束计时

---

### 修改4.4：SearchKeywordsAssociatedFilesProof 函数修改（T4 + S5）

#### 修改4.4.1：添加计时起点

**位置：** 第1245行（函数开始处，在加载数据库之前）

**查找代码：**

```cpp
bool StorageNode::SearchKeywordsAssociatedFilesProof(const std::string& search_json_path) {
    std::cout << "\n🔍 开始搜索文件证明..." << std::endl;
    
    // 步骤1: 加载搜索请求参数
    if (!file_exists(search_json_path)) {
        std::cerr << "❌ 搜索参数文件不存在: " << search_json_path << std::endl;
        return false;
    }
    
    Json::Value search_params = load_json_from_file(search_json_path);
    // ... 提取参数 ...
    
    // 步骤2: 加载数据库
    if (!load_index_database()) {
```

**在加载数据库之前插入：**

```cpp
    // ... 提取所有参数完成 ...
    
    // ========== 开始计时：T4 搜索证明生成总时间 ==========
    // 包含：加载数据库 + 搜索计算 + 证明生成
    PERF_TIMER_START(search_proof_total)
    
    // 步骤2: 加载数据库
    if (!load_index_database()) {
```

**说明：** 在加载数据库前启动计时

---

#### 修改4.4.2：处理失败情况

在所有可能return false的地方，都要先调用 `PERF_TIMER_END(search_proof_total)`

**示例：**

```cpp
    if (!load_index_database()) {
        PERF_TIMER_END(search_proof_total)  // 失败也记录
        std::cerr << "❌ 索引数据库加载失败" << std::endl;
        return false;
    }
```

---

#### 修改4.4.3：添加计时终点

**位置：** 在搜索和证明生成完成后，序列化JSON之前

**查找代码：**

```cpp
    }  // while循环结束
    
    std::cout << "✅ 搜索完成，共找到 " << AS.size() << " 个结果" << std::endl;
    
    // 步骤4: 生成输出JSON
    std::cout << "   生成输出文件..." << std::endl;
    Json::Value output;
```

**在此之间插入：**

```cpp
    }  // while循环结束
    
    std::cout << "✅ 搜索完成，共找到 " << AS.size() << " 个结果" << std::endl;
    
    // ========== 结束计时：T4 搜索证明生成总时间 ==========
    // 搜索和证明生成完成，排除序列化和文件写入
    PERF_TIMER_END(search_proof_total)
    
    // 步骤4: 生成输出JSON（不计入计时）
    std::cout << "   生成输出文件..." << std::endl;
    Json::Value output;
```

**说明：** 在证明生成完成后、JSON序列化前结束计时

---

#### 修改4.4.4：记录证明大小

**位置：** 在保存JSON文件后

**查找代码：**

```cpp
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "    ";
    if (!save_json_to_file(output, output_file)) {
        std::cerr << "❌ 无法保存输出文件: " << output_file << std::endl;
        return false;
    }
    
    std::cout << "✅ 搜索证明已生成: " << output_file << std::endl;
```

**修改为：**

```cpp
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "    ";
    std::string output_str = Json::writeString(writer, output);
    
    // ========== 记录数据大小：S5 ==========
    if (perf_callback_) {
        perf_callback_->on_data_size_recorded("search_proof_size", output_str.length());
    }
    
    // 保存文件
    std::ofstream ofs(output_file);
    if (!ofs.is_open()) {
        std::cerr << "❌ 无法保存输出文件: " << output_file << std::endl;
        return false;
    }
    ofs << output_str;
    ofs.close();
    
    std::cout << "✅ 搜索证明已生成: " << output_file << std::endl;
```

**说明：** 先序列化，记录大小，再保存文件

---

### 修改4.5：VerifySearchProof 函数修改（T5 + S6）

#### 修改4.5.1：添加计时起点

**位置：** 第1787行（函数开始处，在加载索引数据库之前）

**查找代码：**

```cpp
bool StorageNode::VerifySearchProof(const std::string& search_proof_json_path) {
    std::cout << "\n🔍 开始验证搜索证明..." << std::endl;
    
    // 步骤1: 加载证明文件
    if (!file_exists(search_proof_json_path)) {
        std::cerr << "❌ 证明文件不存在: " << search_proof_json_path << std::endl;
        return false;
    }
    
    Json::Value proof = load_json_from_file(search_proof_json_path);
    // ... 提取参数 ...
    
    // 步骤2: 加载索引数据库获取PK
    if (!load_index_database()) {
```

**在加载索引数据库之前插入：**

```cpp
    // ... 提取所有参数完成 ...
    
    // ========== 开始计时：T5 验证执行时间 ==========
    // 包含：加载索引数据库（获取PK）+ 验证计算
    PERF_TIMER_START(verify_execution_time)
    
    // 步骤2: 加载索引数据库获取PK
    if (!load_index_database()) {
```

**说明：** 在加载索引数据库前启动计时

---

#### 修改4.5.2：处理失败情况

在所有可能return false的地方，都要先调用 `PERF_TIMER_END(verify_execution_time)`

---

#### 修改4.5.3：添加计时终点和记录验证结果

**位置：** 在验证完成后，return之前

**查找代码：**

```cpp
    // 比较
    bool result = (element_cmp(left_side, right_side) == 0);
    
    if (result) {
        std::cout << "✅ 搜索证明验证通过" << std::endl;
    } else {
        std::cout << "❌ 搜索证明验证失败" << std::endl;
    }
    
    // 清理
    // ...
    
    return result;
}
```

**修改为：**

```cpp
    // 比较
    bool result = (element_cmp(left_side, right_side) == 0);
    
    // ========== 结束计时：T5 验证执行时间 ==========
    PERF_TIMER_END(verify_execution_time)
    
    // ========== 记录数据大小：S6 ==========
    if (perf_callback_) {
        perf_callback_->on_data_size_recorded("verify_result_size", 1);  // 验证结果1字节
    }
    
    if (result) {
        std::cout << "✅ 搜索证明验证通过" << std::endl;
    } else {
        std::cout << "❌ 搜索证明验证失败" << std::endl;
    }
    
    // 清理
    // ...
    
    return result;
}
```

**说明：** 在验证计算完成后结束计时，记录结果大小

---

## 五、修改总结

### 5.1 文件修改统计

|文件|新增行数|修改行数|修改位置数|
|---|---|---|---|
|client.h|~20行|0|3处|
|client.cpp|~40行|~10行|5处|
|storage_node.h|~15行|0|3处|
|storage_node.cpp|~50行|~15行|6处|
|**总计**|**~125行**|**~25行**|**17处**|

### 5.2 计时点汇总

|指标|计时点名称|所在函数|包含内容|排除内容|
|---|---|---|---|---|
|T1|client_encrypt_total|client::encryptFile|文件读取+加密+标签生成+密文写入|JSON序列化和写入|
|T2|token_generation|client::searchKeyword|generateSearchToken核心计算|状态查询、JSON操作|
|T3|server_insert_total|node::insert_file|密文读取+参数验证+内存数据库更新|数据库磁盘持久化|
|T4|search_proof_total|node::SearchKeywordsAssociatedFilesProof|加载数据库+搜索+证明生成|JSON序列化和文件写入|
|T5|verify_execution_time|node::VerifySearchProof|加载索引+验证计算|-|

### 5.3 数据大小记录汇总

|指标|记录点名称|记录时机|数据来源|
|---|---|---|---|
|S1|plaintext_size|T1结束后|plaintext.size()|
|S2|encrypted_file_size|T1结束后|ciphertext.size()|
|S3|insert_json_size|T1结束后+JSON序列化后|insert_json_str.length()|
|S4|search_request_size|T2结束后+JSON序列化后|search_json_str.length()|
|S5|search_proof_size|T4结束后+JSON序列化后|output_str.length()|
|S6|verify_result_size|T5结束后|固定值1|

---

## 六、注意事项

### 6.1 关键原则

1. **时间测量优先**：计时必须在计算完成后立即结束
2. **数据大小后置**：所有 `.size()`, `.length()`, `Json::writeString` 必须在 `PERF_TIMER_END` 之后
3. **失败也记录**：所有可能return false的地方都要先调用 `PERF_TIMER_END`
4. **零性能开销**：perf_callback_为nullptr时，只有一次指针判断

### 6.2 容易出错的地方

1. **忘记在失败路径添加 PERF_TIMER_END**
    
    - 解决方法：系统检查所有return false之前是否有PERF_TIMER_END
2. **在计时内调用 .size() 或序列化**
    
    - 解决方法：严格遵守"数据大小后置"原则
3. **计时范围不清晰**
    
    - 解决方法：参考上面的"计时点汇总"表

### 6.3 编译依赖

需要确保以下头文件被包含：

```cpp
#include <chrono>      // 用于 high_resolution_clock
#include <functional>  // 用于 std::function
```

---

## 七、测试验证清单

完成修改后，请检查：

### 7.1 编译检查

- [ ] 所有文件编译无错误
- [ ] 无警告信息
- [ ] 链接成功

### 7.2 功能检查

- [ ] 未启用监控时，功能正常
- [ ] 启用监控后，功能仍正常
- [ ] 所有回调被正确触发
- [ ] 时间和大小数值合理

### 7.3 逻辑检查

- [ ] 所有计时点位置正确
- [ ] 所有失败路径都有PERF_TIMER_END
- [ ] 数据大小记录在计时后
- [ ] 没有遗漏的计时点

---

## 八、使用示例

```cpp
#include "client.h"
#include "storage_node.h"

// 创建性能监控回调
PerformanceCallback callback;
std::map<std::string, double> times;
std::map<std::string, size_t> sizes;

callback.on_phase_complete = [&](const std::string& phase, double time_ms) {
    times[phase] = time_ms;
    std::cout << "[TIME] " << phase << ": " << time_ms << " ms" << std::endl;
};

callback.on_data_size_recorded = [&](const std::string& name, size_t size_bytes) {
    sizes[name] = size_bytes;
    std::cout << "[SIZE] " << name << ": " << size_bytes << " bytes" << std::endl;
};

// 启用监控
StorageClient client;
client.initialize("public_params.json");
client.setPerformanceCallback(&callback);

// 执行测试
client.encryptFile("test.txt", {"keyword1", "keyword2"});

// 获取结果
double t1 = times["client_encrypt_total"];
size_t s1 = sizes["plaintext_size"];
size_t s2 = sizes["encrypted_file_size"];
size_t s3 = sizes["insert_json_size"];

std::cout << "\n========== 性能报告 ==========" << std::endl;
std::cout << "T1 (加密总时间): " << t1 << " ms" << std::endl;
std::cout << "S1 (明文大小): " << s1 << " bytes" << std::endl;
std::cout << "S2 (密文大小): " << s2 << " bytes" << std::endl;
std::cout << "S3 (JSON大小): " << s3 << " bytes" << std::endl;

// 禁用监控
client.setPerformanceCallback(nullptr);
```

---

## 九、方案H完整性确认

此实施方案完全符合方案H的设计原则：

✅ **后置记录模式**：所有数据大小测量在PERF_TIMER_END之后  
✅ **服务端插入合并**：T3包含密文读取+内存更新，排除磁盘持久化  
✅ **服务端搜索闭环**：T4包含数据库加载+搜索+证明，排除序列化和保存  
✅ **服务端验证完整**：T5包含加载索引+验证计算  
✅ **双回调接口**：on_phase_complete + on_data_size_recorded  
✅ **零性能开销**：perf_callback_==nullptr时无性能损失

---

**请审核此方案，确认无误后即可开始修改代码！**