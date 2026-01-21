---
title: "100 Economics Index"
excerpt: "A Generative Redefinition of Core Economic Concepts under the EMIS Framework"
doc_id: 100
lang-ref: 100-economics
---

> Based on **EMIS Framework v0.2.0**
>
> Economics is not about Money.
> It is about **how Energy is captured, structured, and allocated over Time.**

---

# Economics Index - 20 Core Concepts

> This index does not attempt to "explain economic phenomena" in the traditional sense.
> Instead, it **replaces the underlying variable system** of economics.
>
> Switching from:  
> "Preferences, Utility, Equilibrium"
>
> To:  
> **"Energy, Structure, Time Selection"**

---

## 1. [Inflation]

*   **Legacy Definition**: Sustained increase in price levels due to money supply or demand.
*   **EMIS Definition**: Decoupling of the **Token Layer** from the **Physical Energy Layer**.
*   **EMIS Code**:
    ```python
    def is_inflation(economy):
        # Inflation = Token Delta > Energy Capture Delta
        return d(Token_Supply) / dt > d(Real_Energy_Capture) / dt
    ```

## 2. [Money]

*   **Legacy Definition**: Medium of exchange, store of value.
*   **EMIS Definition**: A generic **interface** for invoking energy across time and structure.
*   **EMIS Code**:
    ```typescript
    interface Money {
        // Money is a claim on future energy
        claim_energy(amount: number, time: Future): Energy;
    }
    ```

## 3. [Price]

*   **Legacy Definition**: Equilibrium of supply and demand.
*   **EMIS Definition**: The **impedance (resistance)** signal of accessing energy within a specific structure.
*   **EMIS Code**:
    ```python
    Price = Energy_Cost / Structural_Efficiency
    # Low efficiency structure -> High Price (High Impedance)
    ```

## 4. [Value]

*   **Legacy Definition**: Utility or subjective preference.
*   **EMIS Definition**: The capacity of a structure to **reduce local entropy** (save energy).
*   **EMIS Code**:
    ```python
    Value(structure) = -d(Entropy_Local) / dt
    # Value is Negentropy rate
    ```

## 5. [Efficiency]

*   **Legacy Definition**: Optimal allocation of resources.
*   **EMIS Definition**: Ratio of functional output to energy dissipation.
*   **EMIS Code**:
    ```python
    Efficiency = Function_Output / (Energy_Input + Heat_Loss)
    ```

## 6. [Growth]

*   **Legacy Definition**: Increase in GDP.
*   **EMIS Definition**: Increase in the system's capacity to **structure** energy flows.
*   **EMIS Code**:
    ```python
    Growth = d(Structured_Energy_Stock) / dt
    # Not just flow, but structured stock
    ```

## 7. [Production]

*   **Legacy Definition**: Creating goods/services using labor and capital.
*   **EMIS Definition**: The process of encoding **Information** into **Matter** using **Energy**.
*   **EMIS Code**:
    ```python
    Production(Raw_Matter, Info) -> Structured_Matter:
        consume(Energy)
        return Matter.inject(Info)
    ```

## 8. [Consumption]

*   **Legacy Definition**: Utilizing goods/services.
*   **EMIS Definition**: The **release** of stored energy structure into heat (dissipation).
*   **EMIS Code**:
    ```python
    Consumption(Structure) -> Heat:
        Entropy += Structure.dissolve()
    ```

## 9. [Saving]

*   **Legacy Definition**: Income not consumed.
*   **EMIS Definition**: **Latent** energy potential stored for future allocation.
*   **EMIS Code**:
    ```python
    Saving = integral(Energy_Capture - Energy_Dissipation, dt)
    ```

## 10. [Investment]

*   **Legacy Definition**: Allocating money for future profit.
*   **EMIS Definition**: Injecting energy to build higher-order **negative entropy structures**.
*   **EMIS Code**:
    ```python
    Investment(Energy) -> New_Structure:
        if New_Structure.efficiency > Current_Structure.efficiency:
            return Profit
    ```

## 11. [Capital]

*   **Legacy Definition**: Assets used for production.
*   **EMIS Definition**: A **crystallized structure** capable of capturing external energy streams.
*   **EMIS Code**:
    ```typescript
    class Capital extends Structure {
        capture_energy(environment): Flow;
    }
    ```

## 12. [Labor]

*   **Legacy Definition**: Human effort in production.
*   **EMIS Definition**: The biological **API** for converting chemical energy into physical work.
*   **EMIS Code**:
    ```python
    Labor = Bio_System.execute(Work_Command)
    ```

## 13. [Technology]

*   **Legacy Definition**: Application of scientific knowledge.
*   **EMIS Definition**: An algorithm to minimize the **resistance** of energy paths.
*   **EMIS Code**:
    ```python
    Technology = minimize(Path_Resistance(Energy_Source, Goal))
    ```

## 14. [Market]

*   **Legacy Definition**: Place where buyers and sellers meet.
*   **EMIS Definition**: A distributed protocol for **signal synchronization** (Price Discovery).
*   **EMIS Code**:
    ```python
    Market = Distributed_Network.sync(Signal_Price)
    ```

## 15. [Competition]

*   **Legacy Definition**: Rivalry for profit.
*   **EMIS Definition**: Evolutionary selection pressure on structures for **maximum energy capture**.
*   **EMIS Code**:
    ```python
    while True:
        if Structure_A.capture_rate > Structure_B.capture_rate:
            Structure_B.die() # Natural Selection
    ```

## 16. [Monopoly]

*   **Legacy Definition**: Exclusive control of supply.
*   **EMIS Definition**: Artificial **high-impedance barrier** erected around an energy source.
*   **EMIS Code**:
    ```python
    Monopoly = Barrier(Energy_Source).set_permission(Only_Me)
    ```

## 17. [Risk] (风险)

*   **Legacy Definition**: Probability of loss.
*   **EMIS Definition**: The **entropy (uncertainty)** of future energy return paths.
*   **EMIS Code**:
    ```python
    Risk = Entropy(Future_Energy_Paths)
    # Higher entropy = Higher unpredictability
    ```

## 18. [Inequality]

*   **Legacy Definition**: Unequal distribution of income.
*   **EMIS Definition**: The inevitable result of **Pareto distribution** in multiplicative energy systems (Yakovenko).
*   **EMIS Code**:
    ```python
    Inequality = PowerLaw(Capital_Accumulation)
    # Result of multiplicative dynamics, not additive
    ```

## 19. [Crisis]

*   **Legacy Definition**: Economic downturn.
*   **EMIS Definition**: **Phase transition** failure. The structure is too rigid to handle energy flux volatility.
*   **EMIS Code**:
    ```python
    if Energy_Fluctuation > Structure.elasticity:
        raise SystemCollapseError("Crisis Initiated")
    ```

## 20. [Economy]

*   **Legacy Definition**: System of production and consumption.
*   **EMIS Definition**: The aggregate **metabolism** of a civilization.
*   **EMIS Code**:
    ```python
    Economy = sum(all_structures.metabolism())
    ```