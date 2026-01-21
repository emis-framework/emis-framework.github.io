---
title: "150 Social Science Index"
excerpt: "A Generative Redefinition of Core Sociological Concepts under the EMIS Framework"
doc_id: 150
lang-ref: 150-sociology
---

> Based on **EMIS Framework v0.2.0**
>
> Sociology is not about "Human Relations".
> It is about **the Geometry of Energy Flows and Structural Constraints.**

---

# Sociology Index - 20 Core Concepts

> Switching the variable system:
>
> From:  
> "Identity, Norms, Agency"
>
> To:  
> **"Protocol, Constraint, Gradient"**

---

## 1. [Society]

*   **Legacy Definition**: A group of individuals involved in persistent social interaction.
*   **EMIS Definition**: A bounded **network** for energy capture, distribution, and dissipation.
*   **EMIS Code**:
    ```typescript
    class Society {
        members: Node[];
        connections: Edge[];
        total_energy_budget: float;
    }
    ```

## 2. [Structure]

*   **Legacy Definition**: Patterned social arrangements.
*   **EMIS Definition**: A **low-entropy configuration** maintained by constant energy input.
*   **EMIS Code**:
    ```python
    def maintain_structure(structure):
        # Without energy input, structure decays (Entropy)
        if Energy_Input < Maintenance_Cost:
            structure.decay()
    ```

## 3. [Power]

*   **Legacy Definition**: The ability to influence others or control outcomes.
*   **EMIS Definition**: The capacity to **direct the vector** of energy allocation.
*   **EMIS Code**:
    ```python
    Power = Control(Energy_Flow_Vector)
    # Higher power = Higher bandwidth of allocation control
    ```

## 4. [Authority]

*   **Legacy Definition**: Legitimate power.
*   **EMIS Definition**: **Protocol-authorized** access to energy switches.
*   **EMIS Code**:
    ```python
    Authority = Protocol.verify(User_Permission) == True
    ```

## 5. [Class]

*   **Legacy Definition**: Grouping based on social or economic status.
*   **EMIS Definition**: Distinct **thermodynamic states** defined by energy access capabilities.
*   **EMIS Code**:
    ```python
    Class_Level = log(Energy_Capture_Rate)
    # Logarithmic scale, similar to Richter magnitude
    ```

## 6. [Stratification]

*   **Legacy Definition**: Categorization of people into socioeconomic layers.
*   **EMIS Definition**: The **crystallization** of energy gradients into rigid structural layers.
*   **EMIS Code**:
    ```python
    Stratification = Gradient_Lock(High_Energy_Node, Low_Energy_Node)
    ```

## 7. [Institution]

*   **Legacy Definition**: Established laws, practices, or customs.
*   **EMIS Definition**: A hard-coded **rule set (Algorithm)** to reduce the computational cost of interaction.
*   **EMIS Code**:
    ```python
    Institution = Shared_Algorithm(Interaction_Rules)
    # Reduces negotiation overhead (Transaction Cost)
    ```

## 8. [Culture]

*   **Legacy Definition**: Shared values, beliefs, and practices.
*   **EMIS Definition**: A distributed **compression protocol** for social information.
*   **EMIS Code**:
    ```python
    Culture = Compression_Scheme(Social_Data)
    # Common culture = Shared decoder ring
    ```

## 9. [Norms]

*   **Legacy Definition**: Rules of conduct.
*   **EMIS Definition**: **Soft constraints** optimized for system stability.
*   **EMIS Code**:
    ```python
    if Behavior != Norm:
        Social_Penalty++ # Feedback loop to correct deviation
    ```

## 10. [Social Capital]

*   **Legacy Definition**: Networks of relationships that enable society to function.
*   **EMIS Definition**: Potential energy stored in **network topology**.
*   **EMIS Code**:
    ```python
    Social_Capital = count(Trusted_Connections) * Connection_Bandwidth
    ```

## 11. [Trust]

*   **Legacy Definition**: Reliance on the integrity of others.
*   **EMIS Definition**: A state of **zero-verification cost** (Low Friction).
*   **EMIS Code**:
    ```python
    Trust = 1 / Verification_Energy_Cost
    # High trust = Low energy waste on checking
    ```

## 12. [Cooperation]

*   **Legacy Definition**: Working together for a common goal.
*   **EMIS Definition**: **Synergistic coupling** of structures to maximize total energy capture.
*   **EMIS Code**:
    ```python
    if (Capture(A+B) > Capture(A) + Capture(B)):
        Cooperation.init()
    ```

## 13. [Conflict]

*   **Legacy Definition**: Disagreement or struggle.
*   **EMIS Definition**: **Collision** of conflicting energy vectors in a finite space.
*   **EMIS Code**:
    ```python
    Conflict = Vector_A.collision(Vector_B)
    # Result: Energy dissipation (Heat/War)
    ```

## 14. [Revolution]

*   **Legacy Definition**: Forcible overthrow of government.
*   **EMIS Definition**: **Phase transition** caused by the rupture of structural constraints (Spacetime).
*   **EMIS Code**:
    ```python
    if Pressure_Gradient > Structure.tensile_strength:
        Phase_Transition(Order -> Chaos -> New_Order)
    ```

## 15. [Ideology]

*   **Legacy Definition**: System of ideas and ideals.
*   **EMIS Definition**: An **OS Kernel** that defines the "Goal Function" of the society.
*   **EMIS Code**:
    ```python
    Ideology = System.Goal_Function
    # e.g., Maximize(Equality) vs Maximize(Growth)
    ```

## 16. [Bureaucracy]

*   **Legacy Definition**: System of government with many departments.
*   **EMIS Definition**: A structure where **internal information processing cost** exceeds external output.
*   **EMIS Code**:
    ```python
    is_bureaucratic = Internal_Entropy > External_Work
    ```

## 17. [Alienation]

*   **Legacy Definition**: Isolation from one's work or humanity.
*   **EMIS Definition**: **Severance of the feedback loop** between energy output and information input.
*   **EMIS Code**:
    ```python
    Alienation = Broken_Link(Action, Consequence)
    ```

## 18. [Mobility]

*   **Legacy Definition**: Movement between social classes.
*   **EMIS Definition**: The coefficient of **diffusion** across energy layers.
*   **EMIS Code**:
    ```python
    Mobility = Diffusion_Coefficient(Layer_Low, Layer_High)
    ```

## 19. [Status]

*   **Legacy Definition**: Social standing.
*   **EMIS Definition**: A visible **signal** of one's energy budget level.
*   **EMIS Code**:
    ```python
    Status = Signal(Energy_Stock)
    # e.g., Luxury goods are high-cost signals
    ```

## 20. [Network]

*   **Legacy Definition**: Interconnected group.
*   **EMIS Definition**: The **topology** of energy and information channels.
*   **EMIS Code**:
    ```python
    Network = Graph(Nodes, Edges, Channel_Capacity)
    ```