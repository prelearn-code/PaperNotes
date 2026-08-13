# 签名算法

# 密钥协商算法

# 对称加密算法

## KDF密钥派生函数
```C
Algorithm KDF(Z, klen):
    // 输入参数：
    // Z:    共享的秘密比特串
    // klen: 期望生成的密钥比特长度，要求 klen < (2^32 - 1) * v
    // 
    // 输出参数：
    // K:    长度为 klen 的派生密钥比特串
    //
    // 外部依赖：
    // H_v:  输出长度固定为 v 比特的密码杂凑函数（如 SM3，此时 v = 256）

    // 1. 计数器初始化
    ct = 0x00000001                   // 这是一个 32 比特的计数器
    n = CEIL(klen / v)                // 计算需要执行杂凑函数的总次数
    
    // 2. 循环杂凑计算
    For i = 1 to n do:
        Ha[i] = H_v(Z || ct)          // 将秘密串 Z 与计数器 ct 拼接后进行杂凑计算
        ct = ct + 1                   // 计数器递增
    End For
    
    // 3. 尾部数据截断处理
    If (klen MOD v == 0) then:
        // 如果需要的长度正好是 v 的整数倍，直接取最后一块完整杂凑值
        Ha_last = Ha[n]               
    Else:
        // 否则，计算剩余需要的比特数，并截取最后一块杂凑值的最左侧指定比特
        rem_bits = klen - (v * FLOOR(klen / v))
        Ha_last = LEFTMOST_BITS(Ha[n], rem_bits)
    End If
    
    // 4. 拼接最终输出
    K = Ha[1] || Ha[2] || ... || Ha[n-1] || Ha_last
    
    Return K
```


## 加密算法的伪代码
```C
Algorithm SM2_Encrypt(M, P_B, params):
    // 输入参数：
    // M:      待加密的明文消息（比特串）
    // P_B:    接收方的公钥（椭圆曲线上的一个点）
    // params: 椭圆曲线系统参数（包含基点 G, 基点的阶 n, 余因子 h）
    //
    // 输出参数：
    // C:      密文（比特串）
    //
    // 外部依赖：
    // RAND(min, max):           产生区间内的安全随机数
    // POINT_TO_BITSTRING(P):    将曲线点转换为比特串（通常为 04 || X || Y 未压缩格式）
    // ELEMENT_TO_BITSTRING(e):  将域元素（如坐标）转换为指定长度的比特串
    // KDF(Z, klen):             密钥派生函数
    // Hash(data):               密码杂凑函数（如 SM3）
    
    klen = LENGTH(M)                        // 步骤 A0：获取明文消息 M 的比特长度

    While True do:
        // 步骤 A1：产生随机数 k
        k = RAND(1, n - 1)                  // k ∈ [1, n-1]

        // 步骤 A2：计算椭圆曲线点 C1
        (x1, y1) = [k]G                     // 计算点乘
        C1 = POINT_TO_BITSTRING(x1, y1)     // 将点 C1 的数据类型转换为比特串

        // 步骤 A3：验证协商安全性
        S = [h]P_B                          // 用余因子 h 乘以接收方公钥
        If S == O then:                     // O 为无穷远点
            Return ERROR("公钥无效或已被破坏")
        End If

        // 步骤 A4：计算协商点
        (x2, y2) = [k]P_B
        x2_bits = ELEMENT_TO_BITSTRING(x2)  // 将坐标 x2 转换为比特串
        y2_bits = ELEMENT_TO_BITSTRING(y2)  // 将坐标 y2 转换为比特串

        // 步骤 A5：利用 KDF 派生密钥流 t
        t = KDF(x2_bits || y2_bits, klen)
        
        // 若派生出的密钥流 t 为全 0 比特串，则必须返回步骤 A1 重新开始
        If t == ALL_ZEROS(klen) then:
            Continue
        End If
        
        // 成功获取有效密钥流，跳出循环
        Break
    End While

    // 步骤 A6：计算密文真实数据部分 C2
    C2 = M XOR t                            // 明文与密钥流按位异或

    // 步骤 A7：计算完整性校验码 C3
    C3 = Hash(x2_bits || M || y2_bits)      // 注意：拼接顺序为 x2 || M || y2

    // 步骤 A8：输出最终密文 C
    // 注意：按照新版标准，密文的拼接顺序为 C1 || C3 || C2
    C = C1 || C3 || C2
    
    Return C
```