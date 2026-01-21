---
title: "100 经济学索引 (Economics Index)"
excerpt: "基于 EMIS 框架的经济学核心概念生成式重定义"
doc_id: 100
lang-ref: 100-economics
---

> 基于 **EMIS Framework (能量主义) v0.2.0**
>
> 经济学不是关于“钱”，
> 而是关于 **能量如何在结构中被分配、延迟与放大**。

---

# 经济学索引 - 20 核心词汇

> 本索引不试图“解释现实经济现象”，
> 而是**替换经济学的底层变量体系**。
>
> 从「偏好、效用、均衡」
> 切换为
> **能量、结构、时间筛选**。

---

## 1.【通胀 Inflation】

*   **传统定义**：价格水平持续上升，归因于货币供给或需求。
*   **EMIS 定义**：**符号层（Token Layer）**与**物理能量层（Physical Energy Layer）**的脱钩。
*   **EMIS 伪代码**：
    ```python
    def is_inflation(economy):
        # 通胀 = 符号增量 > 物理捕获增量
        return d(Token_Supply) / dt > d(Real_Energy_Capture) / dt
    ```

## 2.【货币 Money】

*   **传统定义**：交换媒介，价值储藏。
*   **EMIS 定义**：跨时间、跨结构调用能量的通用**接口 (Interface)**。
*   **EMIS 伪代码**：
    ```typescript
    interface Money {
        // 货币是对未来能量的索取权
        claim_energy(amount: number, time: Future): Energy;
    }
    ```

## 3.【价格 Price】

*   **传统定义**：供需均衡点。
*   **EMIS 定义**：在特定结构中获取能量的**阻抗 (Impedance)** 信号。
*   **EMIS 伪代码**：
    ```python
    Price = Energy_Cost / Structural_Efficiency
    # 结构效率低 -> 价格高（高阻抗）
    ```

## 4.【价值 Value】

*   **传统定义**：效用或主观偏好。
*   **EMIS 定义**：某一结构**降低局部熵 (节省能量)** 的能力。
*   **EMIS 伪代码**：
    ```python
    Value(structure) = -d(Entropy_Local) / dt
    # 价值即负熵率
    ```

## 5.【效率 Efficiency】

*   **传统定义**：资源的最优配置。
*   **EMIS 定义**：功能输出与能量耗散之比。
*   **EMIS 伪代码**：
    ```python
    Efficiency = Function_Output / (Energy_Input + Heat_Loss)
    ```

## 6.【增长 Growth】

*   **传统定义**：GDP 上升。
*   **EMIS 定义**：系统对能量流进行**结构化**能力的提升。
*   **EMIS 伪代码**：
    ```python
    Growth = d(Structured_Energy_Stock) / dt
    # 增长不仅是流量，更是存量的结构化
    ```

## 7.【生产 Production】

*   **传统定义**：劳动和资本创造产品。
*   **EMIS 定义**：消耗**能量**，将**信息**编码进**物质**的过程。
*   **EMIS 伪代码**：
    ```python
    Production(Raw_Matter, Info) -> Structured_Matter:
        consume(Energy)
        return Matter.inject(Info)
    ```

## 8.【消费 Consumption】

*   **传统定义**：使用产品和服务。
*   **EMIS 定义**：存储在结构中的能量**释放**为热（耗散）的过程。
*   **EMIS 伪代码**：
    ```python
    Consumption(Structure) -> Heat:
        Entropy += Structure.dissolve()
    ```

## 9.【储蓄 Saving】

*   **传统定义**：未消费的收入。
*   **EMIS 定义**：为未来分配而存储的**潜势 (Latent Potential)**。
*   **EMIS 伪代码**：
    ```python
    Saving = integral(Energy_Capture - Energy_Dissipation, dt)
    ```

## 10.【投资 Investment】

*   **传统定义**：投入资本以获利。
*   **EMIS 定义**：注入能量以构建更高阶的**负熵结构**。
*   **EMIS 伪代码**：
    ```python
    Investment(Energy) -> New_Structure:
        if New_Structure.efficiency > Current_Structure.efficiency:
            return Profit
    ```

## 11.【资本 Capital】

*   **传统定义**：生产资料。
*   **EMIS 定义**：一种已结晶的、能捕获外部能量流的**结构 (Structure)**。
*   **EMIS 伪代码**：
    ```typescript
    class Capital extends Structure {
        capture_energy(environment): Flow;
    }
    ```

## 12.【劳动 Labor】

*   **传统定义**：人的生产活动。
*   **EMIS 定义**：将化学能转化为物理功的生物**接口 (API)**。
*   **EMIS 伪代码**：
    ```python
    Labor = Bio_System.execute(Work_Command)
    ```

## 13.【技术 Technology】

*   **传统定义**：科学知识的应用。
*   **EMIS 定义**：一种最小化能量路径**阻力 (Resistance)** 的算法。
*   **EMIS 伪代码**：
    ```python
    Technology = minimize(Path_Resistance(Energy_Source, Goal))
    ```

## 14.【市场 Market】

*   **传统定义**：买卖场所。
*   **EMIS 定义**：一种分布式的**信号同步 (Signal Synchronization)** 协议。
*   **EMIS 伪代码**：
    ```python
    Market = Distributed_Network.sync(Signal_Price)
    ```

## 15.【竞争 Competition】

*   **传统定义**：争夺利润。
*   **EMIS 定义**：结构间为了**最大化能量捕获**而进行的演化筛选压力。
*   **EMIS 伪代码**：
    ```python
    while True:
        if Structure_A.capture_rate > Structure_B.capture_rate:
            Structure_B.die() # 自然选择
    ```

## 16.【垄断 Monopoly】

*   **传统定义**：独家控制。
*   **EMIS 定义**：在能量源周围建立的人为**高阻抗壁垒**。
*   **EMIS 伪代码**：
    ```python
    Monopoly = Barrier(Energy_Source).set_permission(Only_Me)
    ```

## 17.【风险 Risk】

*   **传统定义**：损失的可能性。
*   **EMIS 定义**：未来能量回收路径的**熵 (不确定性)**。
*   **EMIS 伪代码**：
    ```python
    Risk = Entropy(Future_Energy_Paths)
    # 熵越高 = 不可预测性越高
    ```

## 18.【不平等 Inequality】

*   **传统定义**：分配不均。
*   **EMIS 定义**：乘性能量系统（Yakovenko）中**帕累托分布**的必然数学结果。
*   **EMIS 伪代码**：
    ```python
    Inequality = PowerLaw(Capital_Accumulation)
    # 乘性动力学的必然结果，非加性
    ```

## 19.【危机 Crisis】

*   **传统定义**：经济衰退。
*   **EMIS 定义**：**相变 (Phase Transition)** 失败。结构刚性过大，无法适应能量流的波动。
*   **EMIS 伪代码**：
    ```python
    if Energy_Fluctuation > Structure.elasticity:
        raise SystemCollapseError("Crisis Initiated")
    ```

## 20.【经济 Economy】

*   **传统定义**：生产消费体系。
*   **EMIS 定义**：一个文明的总**代谢 (Metabolism)** 系统。
*   **EMIS 伪代码**：
    ```python
    Economy = sum(all_structures.metabolism())
    ```