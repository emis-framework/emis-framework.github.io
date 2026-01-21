---
title: "450 传媒学索引 (Media Index)"
excerpt: "基于 EMIS 框架的传媒学核心概念生成式重定义"
doc_id: 450
lang-ref: 450-media
---

> 基于 **EMIS Framework (能量主义) v0.2.0**
>
> 媒体不是“内容”。
> 它是社会网络的 **带宽、延迟与信噪比**。

---

# 450 传媒学索引

> 变量体系切换：
>
> 从：
> 「信息、受众、真相」
>
> 切换为：
> **「数据包、节点、信号保真度」**

---

## 1.【媒介 Media】

*   **传统定义**：大众传播的主要手段。
*   **EMIS 定义**：承载节点间信息流的**物理信道 (Physical Channel)**。
*   **EMIS 伪代码**：
    ```python
    Media = Channel(Type, Bandwidth, Latency)
    ```

## 2.【传播 Communication】

*   **传统定义**：信息的交换。
*   **EMIS 定义**：通过信号传输实现的两个节点间**内部状态同步 (Synchronization)**。
*   **EMIS 伪代码**：
    ```python
    Comm = Sync(State_A -> State_B)
    ```

## 3.【信息 Information】(传媒)

*   **传统定义**：提供的事实。
*   **EMIS 定义**：降低接收者预测模型不确定性的**负熵 (Negative Entropy)**。
*   **EMIS 伪代码**：
    ```python
    Info = -d(Uncertainty) / dt
    ```

## 4.【噪音 Noise】

*   **传统定义**：无关或无意义的数据。
*   **EMIS 定义**：降低信号保真度并增加处理成本的**信道熵 (Channel Entropy)**。
*   **EMIS 伪代码**：
    ```python
    Noise = Signal_Input - Signal_Output
    ```

## 5.【宣传 Propaganda】

*   **传统定义**：用于推广某种事业的偏见信息。
*   **EMIS 定义**：旨在改变目标节点目标函数或能量分配的**信号注入 (Signal Injection)**。
*   **EMIS 伪代码**：
    ```python
    Propaganda = Inject(Bias_Vector, Target=Opinion_Model)
    ```

## 6.【回声室 Echo Chamber】

*   **传统定义**：信仰得到强化的环境。
*   **EMIS 定义**：具有正反馈和零外部熵输入的**闭环反馈系统**。
*   **EMIS 伪代码**：
    ```python
    Echo_Chamber = Loop(Output -> Input) where Filter(External) = Block
    ```

## 7.【把关 Gatekeeping】

*   **传统定义**：控制信息的获取。
*   **EMIS 定义**：控制进入网络信息流速的**高阻抗过滤器 (High-Impedance Filter)**。
*   **EMIS 伪代码**：
    ```python
    Gatekeeper = Filter(Permission_Rule)
    ```

## 8.【议程设置 Agenda Setting】

*   **传统定义**：影响话题重要性的能力。
*   **EMIS 定义**：操纵网络节点的**注意力分配优先级**。
*   **EMIS 伪代码**：
    ```python
    Agenda = Priority_Queue.reorder(Top_Items)
    ```

## 9.【舆论 Public Opinion】

*   **传统定义**：公众普遍的看法。
*   **EMIS 定义**：给定时间内所有个体节点状态的**聚合矢量和 (Vector Sum)**。
*   **EMIS 伪代码**：
    ```python
    Public_Opinion = Average(Node_Vectors)
    ```

## 10.【病毒式传播 Virality】

*   **传统定义**：信息快速传播的趋势。
*   **EMIS 定义**：具有**高复制系数**和低传输摩擦的消息包。
*   **EMIS 伪代码**：
    ```python
    Virality = Replication_Rate > 1 (R0 > 1)
    ```

## 11.【审查 Censorship】

*   **传统定义**：言论压制。
*   **EMIS 定义**：基于内容模式匹配的**丢包 (Packet Dropping)** 或信道阻断。
*   **EMIS 伪代码**：
    ```python
    if Packet.matches(Banned_Pattern): drop()
    ```

## 12.【社交媒体 Social Media】

*   **传统定义**：网络社交网站。
*   **EMIS 定义**：具有算法路由优化的**多对多网状网络 (Mesh Network)**。
*   **EMIS 伪代码**：
    ```python
    Social_Media = Mesh_Network(Routing=Algo)
    ```

## 13.【算法 Algorithm】(传媒)

*   **传统定义**：计算规则。
*   **EMIS 定义**：决定哪个信息包到达哪个节点以最大化参与度（能量捕获）的**路由协议**。
*   **EMIS 伪代码**：
    ```python
    Algo = Maximize(Engagement_Time)
    ```

## 14.【信息茧房 Filter Bubble】

*   **传统定义**：算法导致的智力隔离。
*   **EMIS 定义**：限制输入熵方差的**算法约束**。
*   **EMIS 伪代码**：
    ```python
    Bubble = Input_Stream.variance() -> 0
    ```

## 15.【真相 Truth】

*   **传统定义**：真实的事物。
*   **EMIS 定义**：**高保真信号 (High Fidelity Signal)**。内部模型与外部现实完全匹配的状态（零预测误差）。
*   **EMIS 伪代码**：
    ```python
    Truth = (Model == Reality)
    ```

## 16.【新闻 Journalism】

*   **传统定义**：报道新闻。
*   **EMIS 定义**：**信号验证 (Verification)** 和降噪的系统功能。
*   **EMIS 伪代码**：
    ```python
    Journalism = Verify(Signal_Source) -> Publish
    ```

## 17.【媒介 Medium】

*   **传统定义**：内容格式。
*   **EMIS 定义**：信息的**编码格式 (Codec)**。
*   **EMIS 伪代码**：
    ```python
    Medium = Codec(Type)
    # 媒介即讯息 = 编解码器定义带宽
    ```

## 18.【注意力经济 Attention Economy】

*   **传统定义**：将注意力视为稀缺商品。
*   **EMIS 定义**：以**认知处理时间 (能量)** 换取信息的市场。
*   **EMIS 伪代码**：
    ```python
    Market.trade(Time, Info)
    ```

## 19.【信号 Signal】

*   **传统定义**：手势或指示。
*   **EMIS 定义**：携带**意义 (负熵)** 的结构化能量波动。
*   **EMIS 伪代码**：
    ```python
    Signal = Structured_Wave - Background_Noise
    ```

## 20.【模因 Meme】

*   **传统定义**：文化传播单位。
*   **EMIS 定义**：文化信息的最小**自复制单元**（病毒）。
*   **EMIS 伪代码**：
    ```python
    class Meme {
        replicate();
        mutate();
    }
    ```