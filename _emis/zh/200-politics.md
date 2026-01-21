---
title: "200 政治学索引 (Political Science Index)"
excerpt: "基于 EMIS 框架的政治学核心概念生成式重定义"
doc_id: 200
lang-ref: 200-politics
---

> 基于 **EMIS Framework (能量主义) v0.2.0**
>
> 政治学不是关于“正义”。
> 它是关于 **Root 权限、系统稳态与暴力垄断**。

---

# 政治学索引 - 20 核心词汇

> 变量体系切换：
>
> 从：
> 「权利、主权、合法性」
>
> 切换为：
> **「Root权限、边界、反馈回路」**

---

## 1.【国家 State】

*   **传统定义**：拥有暴力垄断权的政治实体。
*   **EMIS 定义**：领土内的 **中央处理器 (CPU)**，拥有对能量约束的独家写入权限。
*   **EMIS 伪代码**：
    ```typescript
    class State {
        // 对高能暴力的垄断
        private violence_monopoly: boolean = true;
        public territory: Spacetime_Boundary;
    }
    ```

## 2.【主权 Sovereignty】

*   **传统定义**：领土内的最高权威。
*   **EMIS 定义**：在特定能量-时空域内的 **Root 权限 (管理员权限)**。
*   **EMIS 伪代码**：
    ```python
    Sovereignty = sudo.has_permission(Root)
    # 外部干涉 = 防火墙入侵
    ```

## 3.【政府 Government】

*   **传统定义**：拥有治理权的群体。
*   **EMIS 定义**：执行国家能量分配算法的**运行时内核 (Runtime Kernel)**。
*   **EMIS 伪代码**：
    ```python
    Government = Runtime_Instance(State_Protocol)
    ```

## 4.【合法性 Legitimacy】

*   **传统定义**：统治的正当性与被认可。
*   **EMIS 定义**：统治结构与被统治节点之间的**协议兼容度 (Protocol Compatibility)**。
*   **EMIS 伪代码**：
    ```python
    Legitimacy = Consensus(Governing_Protocol) > Stability_Threshold
    # 低合法性 = 高摩擦（维稳成本激增）
    ```

## 5.【法律 Law】

*   **传统定义**：由机构制定并执行的规则。
*   **EMIS 定义**：硬编码进社会基质的**约束 (Constraints)**，用于预测能量流向。
*   **EMIS 伪代码**：
    ```python
    def Law(action):
        if action.violates(Constraint):
            System.trigger(Punishment)
    ```

## 6.【宪法 Constitution】

*   **传统定义**：国家的根本原则。
*   **EMIS 定义**：政治系统的 **引导加载程序 (Bootloader)** 和**核心架构定义**。
*   **EMIS 伪代码**：
    ```python
    Constitution = System.Init_Config()
    # 难以打补丁，更改核心需要重启（革命）
    ```

## 7.【民主 Democracy】

*   **传统定义**：人民统治。
*   **EMIS 定义**：一种用于能量分配决策的**分布式反馈回路 (Distributed Feedback Loop)**。
*   **EMIS 伪代码**：
    ```python
    Democracy = Aggregate(Signals_from_All_Nodes) -> Allocation_Vector
    ```

## 8.【独裁 Autocracy】

*   **传统定义**：一人拥有绝对权力的统治。
*   **EMIS 定义**：带宽极低的**中心化控制拓扑**。
*   **EMIS 伪代码**：
    ```python
    Autocracy = Single_Node.write(All_allocation_tables)
    ```

## 9.【强制 Coercion】

*   **传统定义**：以武力迫使某人行动。
*   **EMIS 定义**：施加**外部能量压力**以迫使节点状态改变。
*   **EMIS 伪代码**：
    ```python
    Coercion = Force_Vector > Node.Resistance
    ```

## 10.【自由 Liberty / Freedom】

*   **传统定义**：行动或言论的权利。
*   **EMIS 定义**：在系统约束内，节点可用的**可行结构路径 (Viable Paths)** 的数量。
*   **EMIS 伪代码**：
    ```python
    Freedom = count(Available_Energy_Paths)
    # 自由是能量盈余的函数
    ```

## 11.【权利 Rights】

*   **传统定义**：道德或法律上的资格。
*   **EMIS 定义**：为个体节点**预留的最小能量/信息带宽**。
*   **EMIS 伪代码**：
    ```python
    Rights = Reserved_Bandwidth(Node)
    ```

## 12.【正义 Justice】

*   **传统定义**：公正的行为或待遇。
*   **EMIS 定义**：恢复系统平衡与对称性的**纠错机制 (Error Correction)**。
*   **EMIS 伪代码**：
    ```python
    Justice = restore_equilibrium(System_State)
    ```

## 13.【战争 War】

*   **传统定义**：国家或集团间的武装冲突。
*   **EMIS 定义**：旨在强行重构边界或流向的最大化**熵注入 (Entropy Injection)**。
*   **EMIS 伪代码**：
    ```python
    War = Energy_Dump(Target_Structure) -> Structural_Rupture
    ```

## 14.【和平 Peace】

*   **传统定义**：没有动乱。
*   **EMIS 定义**：能量流动的**摩擦极小化**且无暴力的稳态。
*   **EMIS 伪代码**：
    ```python
    Peace = d(Structural_Stress) / dt ≈ 0
    ```

## 15.【政策 Policy】

*   **传统定义**：政府采取的行动方针。
*   **EMIS 定义**：将能量路由到特定子系统的**算法 (Algorithm)**。
*   **EMIS 伪代码**：
    ```python
    Policy = Route(Energy_Stream, Destination)
    ```

## 16.【税收 Taxation】

*   **传统定义**：对国家收入的强制贡献。
*   **EMIS 定义**：维持 Root 结构（国家）运行的系统性**能量收割 (Energy Harvest)**。
*   **EMIS 伪代码**：
    ```python
    Taxation = Energy_Harvest(Node_Output) -> System_Budget
    ```

## 17.【腐败 Corruption】

*   **传统定义**：当权者的不诚实行为。
*   **EMIS 定义**：管理结构内部未经授权的**能量泄漏 (Leakage)** 或路由旁路。
*   **EMIS 伪代码**：
    ```python
    Corruption = Admin_Node.divert(Public_Stream -> Private_Stream)
    ```

## 18.【投票 Voting】

*   **传统定义**：正式的选择表达。
*   **EMIS 定义**：一种周期性的、低成本的**信号聚合 (Signal Aggregation)** 事件。
*   **EMIS 伪代码**：
    ```python
    Voting = Batch_Process(User_Inputs) -> Update(Gov_State)
    ```

## 19.【意识形态 Ideology】

*   **传统定义**：观念体系。
*   **EMIS 定义**：编译“为什么我们这样分配能量”逻辑的**源代码 (Source Code)**。
*   **EMIS 伪代码**：
    ```python
    Ideology = Logic_Compiler(Allocation_Rules)
    ```

## 20.【地缘政治 Geopolitics】

*   **传统定义**：受地理影响的政治。
*   **EMIS 定义**：物理地图（物质/空间）施加的**能量约束博弈**。
*   **EMIS 伪代码**：
    ```python
    Geopolitics = Game_Theory(Map_Constraints, Resource_Locations)
    ```