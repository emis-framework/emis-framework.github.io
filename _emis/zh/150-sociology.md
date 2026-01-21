---
title: "150 社会学索引 (Sociology Index)"
excerpt: "基于 EMIS 框架的社会学核心概念生成式重定义"
doc_id: 150
lang-ref: 150-sociology
---

> 基于 **EMIS Framework (能量主义) v0.2.0**
>
> 社会学不是关于“人际关系”。
> 它是关于 **能量流动的几何学与结构约束**。

---

# 社会学索引 - 20 核心词汇

> 变量体系切换：
>
> 从：
> 「认同、规范、能动性」
>
> 切换为：
> **「协议、约束、梯度」**

---

## 1.【社会 Society】

*   **传统定义**：一群互动个体的集合。
*   **EMIS 定义**：一个用于能量捕获、分配和耗散的有界**网络 (Network)**。
*   **EMIS 伪代码**：
    ```typescript
    class Society {
        members: Node[];
        connections: Edge[];
        total_energy_budget: float;
    }
    ```

## 2.【结构 Structure】

*   **传统定义**：模式化的社会安排。
*   **EMIS 定义**：靠持续能量输入维持的**低熵配置 (Low-entropy configuration)**。
*   **EMIS 伪代码**：
    ```python
    def maintain_structure(structure):
        # 若能量输入 < 维护成本，结构衰退（熵增）
        if Energy_Input < Maintenance_Cost:
            structure.decay()
    ```

## 3.【权力 Power】

*   **传统定义**：影响他人或控制结果的能力。
*   **EMIS 定义**：控制能量分配**矢量 (Vector)** 的能力。
*   **EMIS 伪代码**：
    ```python
    Power = Control(Energy_Flow_Vector)
    # 权力越大 = 分配控制的带宽越高
    ```

## 4.【权威 Authority】

*   **传统定义**：合法的权力。
*   **EMIS 定义**：被**协议 (Protocol)** 授权的能量开关访问权。
*   **EMIS 伪代码**：
    ```python
    Authority = Protocol.verify(User_Permission) == True
    ```

## 5.【阶级 Class】

*   **传统定义**：基于社会经济地位的分组。
*   **EMIS 定义**：由能量获取能力定义的离散**热力学状态 (Thermodynamic States)**。
*   **EMIS 伪代码**：
    ```python
    Class_Level = log(Energy_Capture_Rate)
    # 对数标度，类似于地震震级
    ```

## 6.【分层 Stratification】

*   **传统定义**：社会分层。
*   **EMIS 定义**：能量梯度**结晶 (Crystallization)** 为刚性结构层的过程。
*   **EMIS 伪代码**：
    ```python
    Stratification = Gradient_Lock(High_Energy_Node, Low_Energy_Node)
    ```

## 7.【制度 Institution】

*   **传统定义**：法律、习俗或惯例。
*   **EMIS 定义**：一套硬编码的**规则集 (Algorithm)**，用于降低互动的计算成本。
*   **EMIS 伪代码**：
    ```python
    Institution = Shared_Algorithm(Interaction_Rules)
    # 减少谈判开销（交易成本）
    ```

## 8.【文化 Culture】

*   **传统定义**：共享的价值观和信仰。
*   **EMIS 定义**：一种分布式的社会信息**压缩协议 (Compression Protocol)**。
*   **EMIS 伪代码**：
    ```python
    Culture = Compression_Scheme(Social_Data)
    # 共同文化 = 共享的解码器
    ```

## 9.【规范 Norms】

*   **传统定义**：行为准则。
*   **EMIS 定义**：为系统稳定性优化的**软约束 (Soft Constraints)**。
*   **EMIS 伪代码**：
    ```python
    if Behavior != Norm:
        Social_Penalty++ # 纠正偏差的反馈回路
    ```

## 10.【社会资本 Social Capital】

*   **传统定义**：有助于社会运作的关系网络。
*   **EMIS 定义**：存储在**网络拓扑 (Network Topology)** 中的势能。
*   **EMIS 伪代码**：
    ```python
    Social_Capital = count(Trusted_Connections) * Connection_Bandwidth
    ```

## 11.【信任 Trust】

*   **传统定义**：对他人的信赖。
*   **EMIS 定义**：**零验证成本 (Zero-verification cost)** 的低摩擦状态。
*   **EMIS 伪代码**：
    ```python
    Trust = 1 / Verification_Energy_Cost
    # 高信任 = 检查成本极低
    ```

## 12.【合作 Cooperation】

*   **传统定义**：共同工作。
*   **EMIS 定义**：结构的**协同耦合 (Synergistic Coupling)**，以最大化总能量捕获。
*   **EMIS 伪代码**：
    ```python
    if (Capture(A+B) > Capture(A) + Capture(B)):
        Cooperation.init()
    ```

## 13.【冲突 Conflict】

*   **传统定义**：分歧或斗争。
*   **EMIS 定义**：有限空间内互斥能量矢量的**碰撞 (Collision)**。
*   **EMIS 伪代码**：
    ```python
    Conflict = Vector_A.collision(Vector_B)
    # 结果：能量耗散（热/战争）
    ```

## 14.【革命 Revolution】

*   **传统定义**：推翻政权。
*   **EMIS 定义**：结构约束（时空）断裂导致的**相变 (Phase Transition)**。
*   **EMIS 伪代码**：
    ```python
    if Pressure_Gradient > Structure.tensile_strength:
        Phase_Transition(Order -> Chaos -> New_Order)
    ```

## 15.【意识形态 Ideology】

*   **传统定义**：思想体系。
*   **EMIS 定义**：定义社会“目标函数”的 **OS 内核 (OS Kernel)**。
*   **EMIS 伪代码**：
    ```python
    Ideology = System.Goal_Function
    # 例如：Maximize(平等) vs Maximize(增长)
    ```

## 16.【官僚主义 Bureaucracy】

*   **传统定义**：层级森严的管理体系。
*   **EMIS 定义**：**内部信息处理成本**超过外部功输出的结构。
*   **EMIS 伪代码**：
    ```python
    is_bureaucratic = Internal_Entropy > External_Work
    ```

## 17.【异化 Alienation】

*   **传统定义**：与劳动或人性的疏离。
*   **EMIS 定义**：能量输出与信息反馈之间的**回路切断 (Feedback Loop Severance)**。
*   **EMIS 伪代码**：
    ```python
    Alienation = Broken_Link(Action, Consequence)
    ```

## 18.【流动性 Mobility】

*   **传统定义**：阶级间的移动。
*   **EMIS 定义**：跨越能量层的**扩散系数 (Diffusion Coefficient)**。
*   **EMIS 伪代码**：
    ```python
    Mobility = Diffusion_Coefficient(Layer_Low, Layer_High)
    ```

## 19.【地位 Status】

*   **传统定义**：社会声望。
*   **EMIS 定义**：个人能量预算水平的可见**信号 (Signal)**。
*   **EMIS 伪代码**：
    ```python
    Status = Signal(Energy_Stock)
    # 例如：奢侈品是高成本信号
    ```

## 20.【网络 Network】

*   **传统定义**：互联群体。
*   **EMIS 定义**：能量与信息通道的**拓扑结构 (Topology)**。
*   **EMIS 伪代码**：
    ```python
    Network = Graph(Nodes, Edges, Channel_Capacity)
    ```