---
title: "250 Psychology Index"
excerpt: "A Generative Redefinition of Core Psychological Concepts under the EMIS Framework"
doc_id: 250
lang-ref: 250-psychology
---

> Based on **EMIS Framework v0.2.0**
>
> Psychology is not about "Feelings".
> It is about **Cognitive Energy Management and Predictive Error Minimization.**

---

# Psychology Index

> Switching the variable system:
>
> From:  
> "Mind, Soul, Emotion"
>
> To:  
> **"Compute_Cost, Signal, Prediction_Model"**

---

## 1. [Mind]

*   **Legacy Definition**: The element that enables awareness and thought.
*   **EMIS Definition**: The **Operating System** running on biological hardware to manage energy I/O.
*   **EMIS Code**:
    ```python
    class Mind {
        process_input(Sensory_Data);
        allocate_energy(Action);
        update_model(Feedback);
    }
    ```

## 2. [Cognition]

*   **Legacy Definition**: Mental action of acquiring knowledge.
*   **EMIS Definition**: **Information processing** that consumes metabolic energy (Glucose/ATP).
*   **EMIS Code**:
    ```python
    Cost(Cognition) = Bit_Rate * Energy_Per_Bit
    # Thinking is expensive work
    ```

## 3. [Emotion]

*   **Legacy Definition**: Feelings like joy or anger.
*   **EMIS Definition**: High-priority **system status signals** regarding energy safety or opportunity.
*   **EMIS Code**:
    ```python
    Emotion = Signal(System_State_Change)
    # Fear = Threat detected; Joy = Energy gain detected
    ```

## 4. [Attention]

*   **Legacy Definition**: Focusing on a specific aspect of information.
*   **EMIS Definition**: Allocation of limited **computational bandwidth** to high-value inputs.
*   **EMIS Code**:
    ```python
    Attention = Bandwidth_Filter(Priority_Queue)
    ```

## 5. [Memory]

*   **Legacy Definition**: Storage of information.
*   **EMIS Definition**: **Data compression and storage** for future predictive utility.
*   **EMIS Code**:
    ```python
    Memory = Compress(Experience, Lossy=True)
    ```

## 6. [Habit]

*   **Legacy Definition**: Routine behavior repeated regularly.
*   **EMIS Definition**: A **cached execution path** (compiled binary) to minimize cognitive load.
*   **EMIS Code**:
    ```python
    Habit = Cached_Function(Trigger -> Action)
    # Bypasses the CPU (Conscious thought) to save energy
    ```

## 7. [Willpower]

*   **Legacy Definition**: Control exerted to do something.
*   **EMIS Definition**: The specific **energy budget** available for overriding default habits.
*   **EMIS Code**:
    ```python
    if Willpower_Reserve > Override_Cost:
        execute(New_Action)
    else:
        fallback(Default_Habit)
    ```

## 8. [Stress]

*   **Legacy Definition**: Mental or emotional strain.
*   **EMIS Definition**: System alert for **Energy Deficit** or **Predictive Failure**.
*   **EMIS Code**:
    ```python
    Stress = (Task_Demand > Energy_Supply) OR (Reality != Prediction)
    ```

## 9. [Learning]

*   **Legacy Definition**: Acquiring new knowledge.
*   **EMIS Definition**: Updating the internal **Prediction Model** to reduce future surprise (Entropy).
*   **EMIS Code**:
    ```python
    def Learn(Error):
        Model_Weights += Learning_Rate * Error
    ```

## 10. [Self / Ego]

*   **Legacy Definition**: A person's essential being.
*   **EMIS Definition**: The system's **internal simulation model** of itself (Self-Reference Pointer).
*   **EMIS Code**:
    ```python
    Self = Simulation(Me, relation_to=World)
    ```

## 11. [Motivation]

*   **Legacy Definition**: The reason for acting.
*   **EMIS Definition**: A calculation of expected **Energy Return on Investment (EROI)**.
*   **EMIS Code**:
    ```python
    Motivation = Expected_Reward / Estimated_Effort
    ```

## 12. [Trauma]

*   **Legacy Definition**: Deeply distressing experience.
*   **EMIS Definition**: **Overfitting** to a high-magnitude negative event, creating a rigid, faulty prediction model.
*   **EMIS Code**:
    ```python
    Trauma = Model.lock(Event_Weights, Read_Only=True)
    ```

## 13. [Anxiety]

*   **Legacy Definition**: Feeling of worry or unease.
*   **EMIS Definition**: High computational load caused by **simulating negative future scenarios** (Looping).
*   **EMIS Code**:
    ```python
    while Future_Uncertain:
        simulate(Worst_Case) # Drains battery
    ```

## 14. [Depression]

*   **Legacy Definition**: Persistent low mood.
*   **EMIS Definition**: Systemic **shutdown mode** to conserve energy when EROI is perceived as negative.
*   **EMIS Code**:
    ```python
    if Global_EROI < 0:
        System.hibernate() # Low motivation, low movement
    ```

## 15. [Addiction]

*   **Legacy Definition**: Being addicted to a substance or activity.
*   **EMIS Definition**: Hacking the **Reward Function** without actual energy gain.
*   **EMIS Code**:
    ```python
    Addiction = Short_Circuit(Reward_Loop)
    # Signal says "Energy Gained", Reality says "Damage"
    ```

## 16. [Empathy]

*   **Legacy Definition**: Understanding feelings of others.
*   **EMIS Definition**: Running a **virtual machine (VM)** simulation of another agent's state.
*   **EMIS Code**:
    ```python
    Empathy = Self.simulate(Target_Agent.state)
    ```

## 17. [Intelligence]

*   **Legacy Definition**: Ability to acquire and apply skills.
*   **EMIS Definition**: The **efficiency** of compression and prediction speed.
*   **EMIS Code**:
    ```python
    Intelligence = Prediction_Accuracy / Compute_Time
    ```

## 18. [Cognitive Dissonance]

*   **Legacy Definition**: Inconsistent thoughts.
*   **EMIS Definition**: High **energy friction** caused by conflicting internal models.
*   **EMIS Code**:
    ```python
    Dissonance = Model_A.output != Model_B.output
    # Requires energy to resolve
    ```

## 19. [Flow]

*   **Legacy Definition**: Being fully immersed in activity.
*   **EMIS Definition**: Optimal state where **Processing Cost is minimized** relative to output (Superconductivity).
*   **EMIS Code**:
    ```python
    Flow = (Challenge == Skill) AND (Friction == 0)
    ```

## 20. [Consciousness]

*   **Legacy Definition**: State of being awake and aware.
*   **EMIS Definition**: The **Global Workspace** for broadcasting high-priority signals across modules.
*   **EMIS Code**:
    ```python
    Consciousness = Broadcast(Top_Signals)
    ```