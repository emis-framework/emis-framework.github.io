---
title: "200 Political Science Index"
excerpt: "A Generative Redefinition of Core Political Concepts under the EMIS Framework"
doc_id: 200
lang-ref: 200-politics
---

> Based on **EMIS Framework v0.2.0**
>
> Politics is not about "Justice".
> It is about **Root Access, System Stability, and Coercive Energy Control.**

---

# Political Science Index - 20 Core Concepts

> Switching the variable system:
>
> From:  
> "Rights, Sovereignty, Legitimacy"
>
> To:  
> **"Root_Access, Boundary, Feedback_Loop"**

---

## 1. [State]

*   **Legacy Definition**: A political entity with a monopoly on violence.
*   **EMIS Definition**: The **Central Processing Unit (CPU)** of a territory, holding exclusive write access to energy constraints.
*   **EMIS Code**:
    ```typescript
    class State {
        // Monopoly on high-energy coercion
        private violence_monopoly: boolean = true;
        public territory: Spacetime_Boundary;
    }
    ```

## 2. [Sovereignty]

*   **Legacy Definition**: Supreme authority within a territory.
*   **EMIS Definition**: **Root Access** (Administrator Privileges) over a defined energy-spacetime domain.
*   **EMIS Code**:
    ```python
    Sovereignty = sudo.has_permission(Root)
    # External interference = Firewall breach
    ```

## 3. [Government]

*   **Legacy Definition**: The group of people with the authority to govern.
*   **EMIS Definition**: The active **runtime kernel** executing the state's energy allocation algorithms.
*   **EMIS Code**:
    ```python
    Government = Runtime_Instance(State_Protocol)
    ```

## 4. [Legitimacy]

*   **Legacy Definition**: Right and acceptance of an authority.
*   **EMIS Definition**: The degree of **protocol compatibility** between the ruling structure and the ruled nodes (Low Friction).
*   **EMIS Code**:
    ```python
    Legitimacy = Consensus(Governing_Protocol) > Stability_Threshold
    # Low legitimacy = High friction (Police cost spikes)
    ```

## 5. [Law]

*   **Legacy Definition**: Rules created and enforced by social institutions.
*   **EMIS Definition**: **Hard-coded constraints** written into the social substrate to predictable energy flows.
*   **EMIS Code**:
    ```python
    def Law(action):
        if action.violates(Constraint):
            System.trigger(Punishment)
    ```

## 6. [Constitution]

*   **Legacy Definition**: Fundamental principles of a state.
*   **EMIS Definition**: The **Bootloader** and **Core Architecture** definition of the political system.
*   **EMIS Code**:
    ```python
    Constitution = System.Init_Config()
    # Hard to patch, requires reboot (Revolution) to change core
    ```

## 7. [Democracy]

*   **Legacy Definition**: Rule by the people.
*   **EMIS Definition**: A **distributed feedback loop** mechanism for energy allocation decisions.
*   **EMIS Code**:
    ```python
    Democracy = Aggregate(Signals_from_All_Nodes) -> Allocation_Vector
    ```

## 8. [Autocracy]

*   **Legacy Definition**: Rule by one person with absolute power.
*   **EMIS Definition**: A **centralized control topology** with minimal feedback bandwidth.
*   **EMIS Code**:
    ```python
    Autocracy = Single_Node.write(All_allocation_tables)
    ```

## 9. [Coercion]

*   **Legacy Definition**: Persuading someone to do something by force.
*   **EMIS Definition**: Applying **external energy pressure** to force a node's state change.
*   **EMIS Code**:
    ```python
    Coercion = Force_Vector > Node.Resistance
    ```

## 10. [Liberty / Freedom]

*   **Legacy Definition**: The power or right to act, speak, or think.
*   **EMIS Definition**: The volume of **viable structural paths** available to a node within system constraints.
*   **EMIS Code**:
    ```python
    Freedom = count(Available_Energy_Paths)
    # Freedom is a function of Energy Surplus
    ```

## 11. [Rights]

*   **Legacy Definition**: Moral or legal entitlements.
*   **EMIS Definition**: Guaranteed **minimum energy/information access** reserved for individual nodes.
*   **EMIS Code**:
    ```python
    Rights = Reserved_Bandwidth(Node)
    ```

## 12. [Justice]

*   **Legacy Definition**: Just behavior or treatment.
*   **EMIS Definition**: **Error correction** mechanism to restore system equilibrium and symmetry.
*   **EMIS Code**:
    ```python
    Justice = restore_equilibrium(System_State)
    ```

## 13. [War]

*   **Legacy Definition**: Armed conflict between different nations or groups.
*   **EMIS Definition**: Maximum **entropy injection** to forcibly restructure boundaries or energy flows.
*   **EMIS Code**:
    ```python
    War = Energy_Dump(Target_Structure) -> Structural_Rupture
    ```

## 14. [Peace]

*   **Legacy Definition**: Freedom from disturbance.
*   **EMIS Definition**: A **steady state** where energy flow friction is minimized without violence.
*   **EMIS Code**:
    ```python
    Peace = d(Structural_Stress) / dt ≈ 0
    ```

## 15. [Policy]

*   **Legacy Definition**: A course of action adopted by a government.
*   **EMIS Definition**: A specific **algorithm** for routing energy to specific sub-systems.
*   **EMIS Code**:
    ```python
    Policy = Route(Energy_Stream, Destination)
    ```

## 16. [Taxation]

*   **Legacy Definition**: Compulsory contribution to state revenue.
*   **EMIS Definition**: Systemic **energy harvest** to maintain the root structure (State).
*   **EMIS Code**:
    ```python
    Taxation = Energy_Harvest(Node_Output) -> System_Budget
    ```

## 17. [Corruption]

*   **Legacy Definition**: Dishonest conduct by those in power.
*   **EMIS Definition**: **Unauthorized energy leakage** or routing bypass within the admin structure.
*   **EMIS Code**:
    ```python
    Corruption = Admin_Node.divert(Public_Stream -> Private_Stream)
    ```

## 18. [Voting]

*   **Legacy Definition**: Formal indication of choice.
*   **EMIS Definition**: A periodic, low-cost **signal aggregation** event.
*   **EMIS Code**:
    ```python
    Voting = Batch_Process(User_Inputs) -> Update(Gov_State)
    ```

## 19. [Ideology]

*   **Legacy Definition**: System of ideas.
*   **EMIS Definition**: The **Source Code** compiling the logic of "Why we allocate energy this way".
*   **EMIS Code**:
    ```python
    Ideology = Logic_Compiler(Allocation_Rules)
    ```

## 20. [Geopolitics]

*   **Legacy Definition**: Politics influenced by geography.
*   **EMIS Definition**: The interaction of **energy constraints** imposed by the physical map (Matter/Space).
*   **EMIS Code**:
    ```python
    Geopolitics = Game_Theory(Map_Constraints, Resource_Locations)
    ```