# Americas Consolidated Balance Sheet — DAX Optimization & Measure Cleanup

As a senior DAX optimization specialist, my analysis focuses on reducing calculation overhead, eliminating redundant logic, and improving the overall maintainability of the data model. The current statistics indicate significant room for improvement, particularly in unused code and complex measure logic.

Here are four actionable recommendations based on the provided data, complete with concrete refactoring examples.

---

## 1. Unused Measure Cleanup (The Quick Win)

**Recommendation:** Immediately remove all measures that are not actively used in reports or further calculations.

**Why:** Unused measures contribute to model bloat, increase the time required for data refresh, and introduce unnecessary complexity for model maintenance. Removing them directly improves performance and maintainability.

**Action:** Target the 37 unused measures, especially those identified in the `00_Metricas` group.

**Example Action (Conceptual):**
If `Dynamic (00_Metricas)` is not used, delete the measure entirely.

**DAX Principle:** *If a measure does not drive a visual or a subsequent calculation, it is dead code.*

---

## 2. High-Complexity Refactoring (The Performance Win)

The complexity in measures like `Balance`, `WorkingCapital`, and `Dynamic` suggests opportunities to simplify context transitions and ensure calculations are performed efficiently.

### A. Refactoring `Balance` (Complexity: 51.0)

The complexity often arises from nested context handling. We need to ensure the base calculation is as efficient as possible.

**Original Pattern (Inferred):**
```dax
Balance = 
VAR _currency = SELECTEDVALUE ( 'Currency Conversion'[Currency] )
VAR _Scale = SELECTEDVALUE(Scaling...)
RETURN 
    [Base_Calculation] * _currency * _Scale 
```

**Refactored Pattern (Focus on Context):**
If the goal is simply to apply context-dependent scaling, ensure the context is applied at the lowest possible level.

```dax
Balance_Optimized = 
VAR CurrentCurrency = SELECTEDVALUE('Currency Conversion'[Currency])
VAR CurrentScale = SELECTEDVALUE('Scaling'[Scale_Value])

RETURN
    -- Ensure the base calculation is performed efficiently, avoiding unnecessary context shifts
    [Base_Calculation] * CurrentCurrency * CurrentScale
```
**Optimization Note:** If `SELECTEDVALUE` returns BLANK, the entire measure will fail or return BLANK. Consider using `IF(ISBLANK(...), BLANK(), ...)` or `COALESCE` if handling missing context is critical.

### B. Refactoring `WorkingCapital` (Complexity: 42.0)

The use of `VAR ValorRenglon = [Balance] //if([Balance]<0,[Balance]*-1,[Balance])` is a good start, but we must ensure the subsequent `CALCULATE` is efficient.

**Refactored Pattern (Focus on Calculation Flow):**
Ensure the intermediate steps are calculated once and avoid redundant context transitions within the `CALCULATE`.

```dax
WorkingCapital_Optimized = 
VAR BaseBalance = [Balance]
VAR AdjustedBalance = IF(BaseBalance < 0, BaseBalance * -1, BaseBalance)

VAR InventoryValue = 
    CALCULATE(
        [Balance],
        -- Apply necessary filters here, rather than relying on implicit context
        'Inventory Table'[Status] = "In Stock" 
    )

RETURN
    AdjustedBalance - InventoryValue
```
**Optimization Note:** By explicitly defining the filter context within `CALCULATE`, we prevent potential ambiguity and ensure the filter is applied precisely where needed, improving performance over implicit context transitions.

---

## 3. Variable Strategy (The Maintainability Win)

**Recommendation:** Adopt a strict policy for `VAR` usage. Variables should store intermediate results that are used only within the current measure definition, promoting clarity and preventing unintended side effects.

**Best Practice:**
1. **Avoid Global Variables:** Do not use variables to store results that are intended to be reused across multiple measures (unless explicitly designed as reusable calculation blocks).
2. **Use for Intermediate Steps:** Use `VAR` for complex, multi-step calculations that improve readability (e.g., calculating a ratio, then using that ratio in a final aggregation).
3. **Minimize VAR Scope:** Keep the scope of variables as narrow as possible.

**Example (Applying to `Dynamic`):**
The `Dynamic` measure uses `VAR _CurrentDate = MAX('Calendar'[Date])`. This is good, but ensure the subsequent logic uses this variable efficiently.

```dax
Dynamic_Optimized = 
VAR CurrentDate = MAX('Calendar'[Date])
VAR AccountLevel = SELECTEDVALUE(Pivot_V2[GL_ACCOUNT])

RETURN
    -- Use the variables directly for the final calculation
    SWITCH(
        TRUE(),
        CurrentDate = TODAY(), "Today's Metrics",
        AccountLevel = "High Value", "High Value Metrics",
        "Default Metrics"
    )
```

---

## 4. Dependency Simplification (The Performance & Maintainability Win)

**Recommendation:** Address the 29 cross-measure dependencies by restructuring logic and considering the use of **Calculated Columns** instead of measures where appropriate.

**Why:** Cross-measure dependencies force the engine to evaluate multiple, potentially complex, measures repeatedly, leading to performance bottlenecks and making debugging extremely difficult.

**Action Plan:**

1. **Identify Redundant Logic:** Review the 29 measures. If a measure is simply a filtered version of another (e.g., `Sales_Region_A` vs. `Sales_Region_B`), consider if this can be a **Calculated Column** in the dimension table instead.
    *   **Calculated Columns** are calculated at data refresh time and stored in the model, drastically reducing runtime calculation load compared to measures that rely on complex filter context transitions.

2. **Consolidate Logic:** If multiple measures rely on the same complex calculation (e.g., the logic within `Balance`), refactor that logic into a single, highly optimized base measure. All dependent measures should then reference this base measure.

**Example (Conceptual Dependency Reduction):**
Instead of having 10 measures that all calculate a complex ratio involving `Balance`, create one master measure:

```dax
Master_Balance_Ratio = 
-- Complex logic defined once, optimized for performance
VAR _currency = SELECTEDVALUE('Currency Conversion'[Currency])
VAR _scale = SELECTEDVALUE('Scaling'[Scale_Value])
VAR Base = [Balance] // Assume [Balance] is the optimized base measure

RETURN
    Base * _currency * _scale
```
All 10 dependent measures would then simply be:
`Measure_A = [Master_Balance_Ratio]`
`Measure_B = CALCULATE([Master_Balance_Ratio], 'Table'[Filter])`

This reduces the dependency count from 29 to 1, significantly improving model health and query performance.
