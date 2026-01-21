---
title: "250 心理学索引 (Psychology Index)"
excerpt: "基于 EMIS 框架的心理学核心概念生成式重定义"
doc_id: 250
lang-ref: 250-psychology
---

> 基于 **EMIS Framework (能量主义) v0.2.0**
>
> 心理学不是关于“感受”。
> 它是关于 **认知能量管理与预测误差最小化**。

---

# 250 心理学索引

> 变量体系切换：
>
> 从：
> 「心智、灵魂、情绪」
>
> 切换为：
> **「计算成本、信号、预测模型」**

---

## 1.【心智 Mind】

*   **传统定义**：产生意识和思想的要素。
*   **EMIS 定义**：运行在生物硬件上，用于管理能量输入输出的 **操作系统 (OS)**。
*   **EMIS 伪代码**：
    ```python
    class Mind {
        process_input(Sensory_Data);
        allocate_energy(Action);
        update_model(Feedback);
    }
    ```

## 2.【认知 Cognition】

*   **传统定义**：获取知识的心理活动。
*   **EMIS 定义**：消耗代谢能量（葡萄糖/ATP）的**信息处理过程**。
*   **EMIS 伪代码**：
    ```python
    Cost(Cognition) = Bit_Rate * Energy_Per_Bit
    # 思考是高能耗工作
    ```

## 3.【情绪 Emotion】

*   **传统定义**：如喜怒哀乐的感觉。
*   **EMIS 定义**：关于能量安全或机会的高优先级**系统状态信号 (Status Signals)**。
*   **EMIS 伪代码**：
    ```python
    Emotion = Signal(System_State_Change)
    # 恐惧 = 威胁检测；快乐 = 能量增益检测
    ```

## 4.【注意 Attention】

*   **传统定义**：专注于特定信息。
*   **EMIS 定义**：将有限的**计算带宽 (Bandwidth)** 分配给高价值输入。
*   **EMIS 伪代码**：
    ```python
    Attention = Bandwidth_Filter(Priority_Queue)
    ```

## 5.【记忆 Memory】

*   **传统定义**：信息的存储。
*   **EMIS 定义**：为了未来预测效用而进行的**数据压缩与存储**。
*   **EMIS 伪代码**：
    ```python
    Memory = Compress(Experience, Lossy=True)
    ```

## 6.【习惯 Habit】

*   **传统定义**：规律重复的行为。
*   **EMIS 定义**：为了最小化认知负荷而建立的**缓存执行路径 (Cached Path)**。
*   **EMIS 伪代码**：
    ```python
    Habit = Cached_Function(Trigger -> Action)
    # 绕过 CPU（主意识）以节省能量
    ```

## 7.【意志力 Willpower】

*   **传统定义**：控制行为的能力。
*   **EMIS 定义**：用于覆盖（Override）默认习惯的**特定能量预算**。
*   **EMIS 伪代码**：
    ```python
    if Willpower_Reserve > Override_Cost:
        execute(New_Action)
    else:
        fallback(Default_Habit)
    ```

## 8.【压力 Stress】

*   **传统定义**：精神或情绪的紧张。
*   **EMIS 定义**：系统对 **能量赤字** 或 **预测失败** 的报警。
*   **EMIS 伪代码**：
    ```python
    Stress = (Task_Demand > Energy_Supply) OR (Reality != Prediction)
    ```

## 9.【学习 Learning】

*   **传统定义**：获取新知识。
*   **EMIS 定义**：更新内部**预测模型**以减少未来惊奇（熵）的过程。
*   **EMIS 伪代码**：
    ```python
    def Learn(Error):
        Model_Weights += Learning_Rate * Error
    ```

## 10.【自我 Self / Ego】

*   **传统定义**：个人的本质存在。
*   **EMIS 定义**：系统对自身的**内部模拟模型**（自指指针）。
*   **EMIS 伪代码**：
    ```python
    Self = Simulation(Me, relation_to=World)
    ```

## 11.【动机 Motivation】

*   **传统定义**：行动的原因。
*   **EMIS 定义**：对预期**能量投资回报率 (EROI)** 的计算。
*   **EMIS 伪代码**：
    ```python
    Motivation = Expected_Reward / Estimated_Effort
    ```

## 12.【创伤 Trauma】

*   **传统定义**：极度痛苦的经历。
*   **EMIS 定义**：对高强度负面事件的**过拟合 (Overfitting)**，导致形成了刚性、错误的预测模型。
*   **EMIS 伪代码**：
    ```python
    Trauma = Model.lock(Event_Weights, Read_Only=True)
    ```

## 13.【焦虑 Anxiety】

*   **传统定义**：担忧或不安的感觉。
*   **EMIS 定义**：因**模拟负面未来场景**而产生的高计算负载（死循环）。
*   **EMIS 伪代码**：
    ```python
    while Future_Uncertain:
        simulate(Worst_Case) # 耗干电池
    ```

## 14.【抑郁 Depression】

*   **传统定义**：持续的情绪低落。
*   **EMIS 定义**：当感知到 EROI 为负时，系统进入的**节能关机模式 (Shutdown Mode)**。
*   **EMIS 伪代码**：
    ```python
    if Global_EROI < 0:
        System.hibernate() # 低动机，低运动
    ```

## 15.【成瘾 Addiction】

*   **传统定义**：沉溺于某种物质或活动。
*   **EMIS 定义**：在没有实际能量增益的情况下，**黑客攻击了奖励函数**。
*   **EMIS 伪代码**：
    ```python
    Addiction = Short_Circuit(Reward_Loop)
    # 信号显示“获得能量”，现实显示“造成损害”
    ```

## 16.【共情 Empathy】

*   **传统定义**：理解他人感受。
*   **EMIS 定义**：运行另一个智能体状态的**虚拟机 (VM) 模拟**。
*   **EMIS 伪代码**：
    ```python
    Empathy = Self.simulate(Target_Agent.state)
    ```

## 17.【智力 Intelligence】

*   **传统定义**：获取和应用技能的能力。
*   **EMIS 定义**：压缩信息和预测未来的**效率 (Efficiency)**。
*   **EMIS 伪代码**：
    ```python
    Intelligence = Prediction_Accuracy / Compute_Time
    ```

## 18.【认知失调 Cognitive Dissonance】

*   **传统定义**：思想不一致。
*   **EMIS 定义**：由冲突的内部模型引起的**高能量摩擦**状态。
*   **EMIS 伪代码**：
    ```python
    Dissonance = Model_A.output != Model_B.output
    # 需要能量来解决
    ```

## 19.【心流 Flow】

*   **传统定义**：完全沉浸的状态。
*   **EMIS 定义**：处理成本相对于输出**极小化**的最佳状态（超导状态）。
*   **EMIS 伪代码**：
    ```python
    Flow = (Challenge == Skill) AND (Friction == 0)
    ```

## 20.【意识 Consciousness】

*   **传统定义**：清醒和知觉的状态。
*   **EMIS 定义**：向各个模块广播高优先级信号的**全局工作区 (Global Workspace)**。
*   **EMIS 伪代码**：
    ```python
    Consciousness = Broadcast(Top_Signals)
    ```