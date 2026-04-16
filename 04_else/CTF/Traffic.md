# Traffic Hunt Writeup

首先阅读题目给出的 `traffic_hunt.pcapng`。

整道题其实不是单纯地“在流量里搜 flag”，而是一个比较完整的攻击链恢复过程。前半段是攻击者通过 Web 入口植入内存马并投递木马，后半段才是木马真正回连攻击端并回传数据。因此，这道题的真正思路分成明确的四个步骤：

1. 先在 Web 流量中定位攻击入口与异常通信路径；
2. 识别 `/favicondemo.ico` 实际上是 Behinder (冰蝎) 内存马通信，并还原其密钥；
3. 从解密后的会话中恢复攻击者上传并执行的样本 `/var/tmp/out`；
4. 顺着样本启动后的新连接，解密真正的数据外传通道，拿到最终 flag。

也就是说，这题本质上分成两层：**第一层是 WebShell / 内存马控制链**，**第二层是落地木马的反连窃密链**。而最终的 flag 实际藏在第二层中。

---

## 题目分析

### 一、整体流量初判

打开 `traffic_hunt.pcapng` 后，先在 Wireshark 中观察整体会话。最明显的两台主机是：

| 角色 | IP 地址 |
| :--- | :--- |
| **攻击端** | `10.1.243.155` |
| **受害端** | `10.1.33.69` |

首先关注受害端 `10.1.33.69:8080` 上的流量，因为这里存在大量 HTTP 请求。在 Wireshark 中可以直接使用如下过滤条件：

```wireshark
ip.addr == 10.1.33.69 && tcp.port == 8080
# 或者直接过滤：
http
```

观察后可以发现，这些请求前半段主要是一些接口探测与路径摸排，例如 `/api/docs` 和 Swagger 相关路径。而后半段则出现了大量对同一路径的反复访问，并且大多是 `POST` 请求：

```text
/favicondemo.ico
```

正常情况下，`favicon.ico` 这类资源应当是被浏览器 `GET` 请求，而不应当出现这种高频、大体积、连续的 `POST`。因此可以很快判断：**/favicondemo.ico 并不是一个正常的静态资源，而是攻击者伪装出来的恶意通信接口。**

### 二、锁定 /favicondemo.ico 为内存马通信

选中任意一条访问 `/favicondemo.ico` 的请求，右键 Follow TCP Stream。在 HTTP 头部中可以看到一个非常关键的自定义字段：

```http
p: HWmc2TLDoihdlr0N
```

这个 `p` 不是标准 HTTP 字段，而且在后续多次请求中都存在。结合以下特征：
* 路径伪装成静态资源
* 请求方式为高频 `POST`
* 请求体明显是密文或二进制数据
* 存在自定义参数头 `p`

可以判断这条链路并不是普通 Web 请求，而是 **Behinder（冰蝎）风格的内存马通信**。即攻击者已经利用 Web 入口打进了服务，将 `/favicondemo.ico` 作为后续控制接口。

### 三、Behinder 会话密钥恢复

接下来需要将 `/favicondemo.ico` 的请求体和响应体解开。核心在于请求头中的 `p = HWmc2TLDoihdlr0N`。

结合 Behinder 的常见实现方式，可以尝试将其 MD5 值的前 16 位作为 AES 会话密钥：

```python
import hashlib

p = "HWmc2TLDoihdlr0N"
key = hashlib.md5(p.encode()).hexdigest()[:16]
print(key)
```

> **运行结果：**
> `1f2c8075acd3d118`

因此，这一层 Behinder 会话使用的 AES Key 为 `1f2c8075acd3d118`。有了这把 Key，就可以继续去解密通信内容。

---

## 第一阶段：Behinder 会话解密

### 四、从内存马会话中恢复攻击者操作

把 `/favicondemo.ico` 的请求与响应体按对应方式解密之后，可以还原出攻击者在目标主机上的一系列操作。关键步骤如下：

#### 1. 确认权限
攻击者执行：`whoami`
> **返回：** `root`

说明攻击者已经可以在目标主机上以高权限执行命令。

#### 2. 目录与环境探测
攻击者执行了若干环境探测命令（查看当前目录、目录内容、系统环境信息），主要是为后续落地样本做准备。

#### 3. 上传木马文件
攻击者通过 WebShell 将一个 ELF 可执行文件上传到了：`/var/tmp/out`。这说明 `/favicondemo.ico` 只是一个投递器，用来把真正的木马放到受害主机上。

#### 4. 赋予执行权限并启动
上传完成后，攻击者赋予其执行权限并真正启动样本：

```bash
chmod +x out
./out --aes-key IhbJfHI98nuSvs5JweD5qsNvSQ/HHcE/SNLyEBU9Phs=
```

这里最关键的是获取到了后续的**通信密钥**。攻击者启动了一个新的独立木马进程，并传入了一把专门用于后续通信的 AES Key。

### 五、第一阶段结论

第一阶段得到的关键情报如下：

| 情报                   | 内容                                             |
| :------------------- | :--------------------------------------------- |
| **WebShell 路径**      | `/favicondemo.ico`                             |
| **Behinder 头参数**     | `HWmc2TLDoihdlr0N`                             |
| **Behinder AES Key** | `1f2c8075acd3d118`                             |
| **落地木马路径**           | `/var/tmp/out`                                 |
| **木马运行 Key**         | `IhbJfHI98nuSvs5JweD5qsNvSQ/HHcE/SNLyEBU9Phs=` |

**结论：** 真正的 flag 不在 Behinder 控制链里，而在样本启动后的第二阶段通信里。

---

## 第二阶段：反连通道解密

### 六、定位真正的数据外传连接

沿着时间线继续向后看，会发现一个新的 TCP 连接：
`10.1.33.69:38162  ->  10.1.243.155:7788`

这条连接有两个非常关键的特征：
1. 是受害主机主动发起的。
2. 目标是攻击端的高位端口 `7788`。

这说明 `/var/tmp/out` 已经成功启动，其真实作用是反连攻击端。真正的窃密数据将沿着这条 `7788` 连接回传。后续解题重点完全转移到这条流量上。

### 七、反连协议结构分析

分析 `7788` 连接上的数据格式。首先，对启动参数中给出的 Base64 格式的 Key 进行解码：

```python
import base64

key_b64 = "IhbJfHI98nuSvs5JweD5qsNvSQ/HHcE/SNLyEBU9Phs="
key = base64.b64decode(key_b64)
print(f"Length: {len(key)}")
print(f"Hex: {key.hex()}")
```

将该 Key 用于尝试解密 `7788` 的二进制流量后，可以确定这条链路使用的是 **AES-GCM** 加密。进一步分析帧结构，恢复出的自定义通信协议格式如下：

| 字段 | 大小 | 说明 |
| :--- | :--- | :--- |
| **Length** | 4 Bytes (小端) | 当前帧的总长度 |
| **Nonce** | 12 Bytes | AES-GCM 使用的 Nonce |
| **Payload** | Variable | 密文数据 + 认证标签 (Ciphertext + Tag) |

### 八、7788 通道解密代码

根据上述协议结构，编写完整的解密脚本：

```python
import base64
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_B64 = "IhbJfHI98nuSvs5JweD5qsNvSQ/HHcE/SNLyEBU9Phs="
KEY = base64.b64decode(KEY_B64)

aesgcm = AESGCM(KEY)

def decode_frames(raw: bytes):
    pos = 0
    result = []

    while pos + 4 <= len(raw):
        # 读 4 字节小端整数，得到当前帧长度
        frame_len = struct.unpack("<I", raw[pos:pos+4])[0]
        pos += 4

        if pos + frame_len > len(raw):
            break

        frame = raw[pos:pos + frame_len]
        pos += frame_len

        # 解析 Nonce 和 密文
        nonce = frame[:12]
        ciphertext = frame[12:]

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            result.append(plaintext)
        except Exception:
            result.append(b"[DECRYPT FAILED]")

    return result

# client_to_server.bin 和 server_to_client.bin 可通过 Wireshark Follow TCP Stream 导出原始字节流
with open("client_to_server.bin", "rb") as f:
    c2s = f.read()

with open("server_to_client.bin", "rb") as f:
    s2c = f.read()

print("=== C2S ===")
for i, x in enumerate(decode_frames(c2s), 1):
    print(i, repr(x))

print("=== S2C ===")
for i, x in enumerate(decode_frames(s2c), 1):
    print(i, repr(x))
```

---

## 第三阶段：明文交互恢复

### 九、解密后得到的关键命令与返回结果

解密 `7788` 会话后，可以得到一组明文交互。

攻击端测试当前目录与文件：
> **Command:** `pwd`
> **Response:** `/var/tmp`
> 
> **Command:** `ls`
> **Response:** `out`
*(说明该会话与 WebShell 中启动的进程完全对应)*

通信测试：
> **Command:** `echo Congratulations`
> **Response:** `Congratulations`

**关键数据回传：**
> **Command:** `echo 3SoX7GyGU1KBVYS3DYFbfqQ2CHqH2aPGwpfeyvv5MPY5Dm1Wt9VYRumoUvzdmoLw6FUm4AMqR5zoi`
> **Response:** `3SoX7GyGU1KBVYS3DYFbfqQ2CHqH2aPGwpfeyvv5MPY5Dm1Wt9VYRumoUvzdmoLw6FUm4AMqR5zoi`

结束连接：
> **Command:** `echo bye`
> **Response:** `bye`

至此可以确定，这串长字符串就是本题最终要处理的目标数据。

---

## 第四阶段：编码恢复与最终 Flag

### 十、识别长字符串的编码方式

拿到的关键字符串为：
`3SoX7GyGU1KBVYS3DYFbfqQ2CHqH2aPGwpfeyvv5MPY5Dm1Wt9VYRumoUvzdmoLw6FUm4AMqR5zoi`

观察其字符集，发现**没有数字 0、字母 O、字母 I、字母 l**。这非常符合 **Base58** 的字符集特征。我们对其进行 Base58 解码：

```python
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58decode(s: str) -> bytes:
    num = 0
    for ch in s:
        num = num * 58 + ALPHABET.index(ch)

    data = num.to_bytes((num.bit_length() + 7) // 8, "big") if num > 0 else b""

    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break

    return b"\x00" * pad + data

cipher = "3SoX7GyGU1KBVYS3DYFbfqQ2CHqH2aPGwpfeyvv5MPY5Dm1Wt9VYRumoUvzdmoLw6FUm4AMqR5zoi"
decoded = b58decode(cipher)
print(decoded.decode())
```

> **解码结果：** > `ZGFydHtkOTg1MGIyNy04NWNiLTQ3NzctODVlMC1kZjBiNzhmZGI3MjJ9`

这是一串明显的 Base64 文本。

### 十一、Base64 解码得到最终结果

最后，对上一阶段的结果进行 Base64 解码：

```python
import base64

s = "ZGFydHtkOTg1MGIyNy04NWNiLTQ3NzctODVlMC1kZjBiNzhmZGI3MjJ9"
flag = base64.b64decode(s).decode()
print(flag)
```

> **输出最终 Flag：**
> **`dart{d9850b27-85cb-4777-85e0-df0b78fdb722}`**