# Americas Consolidated Balance Sheet — Performance Analysis & Bottleneck Resolution

This analysis identifies significant opportunities for performance improvement, data model simplification, and long-term maintenance reduction. The primary bottlenecks are **data model bloat** (unused columns) and **structural complexity** (isolated tables and complex relationships).

Here is the 5-point optimization roadmap, prioritized by impact and effort.

---

## 5-Point Optimization Roadmap

### 1. CRITICAL: Model Simplification & Data Bloat Removal
**Focus:** Immediate reduction of model size, memory footprint, and refresh time by eliminating orphaned assets.

*   **Action:** **Remove the 11 isolated tables** that have no relationships. These tables are dead weight, increase the model size unnecessarily, and complicate maintenance.
*   **Action:** **Execute Column Cleanup** (See Section 2).
*   **Estimated Effort:** **Quick** (High immediate gain, low complexity).

### 2. Column Cleanup: Removing Unused Columns
**Focus:** Reducing memory footprint and improving query performance by eliminating unnecessary data.

| Table Name | Unused Columns to Remove | Rationale | Estimated Effort |
| :--- | :--- | :--- | :--- |
| **Pivot\_V2** | 15 columns | These columns are likely not used in current reports or calculations. | Quick |
| **Conso\_WorkingCapital** | 14 columns | Remove columns that are not directly used for KPI calculation. | Quick |
| **derco\_seven\_levels** | 14 columns | If this table is purely a dimension, ensure only necessary attributes remain. | Medium |
| **WorkingCapital\_Derco** | 14 columns | Review if these columns are necessary for the final derived metrics. | Medium |
| **WorkingCapital\_Inchcape** | 14 columns | Review if these columns are necessary for the final derived metrics. | Medium |

### 3. Relationship Issues: Resolving Cardinality and Ambiguity
**Focus:** Ensuring data integrity, predictable filtering, and avoiding ambiguous calculations.

*   **Action on Bidirectional Filter:** **Identify the source of the bidirectional filter.** If possible, convert the filter to a single, clear direction (e.g., filter flows only from the dimension table to the fact table). If the bidirectional flow is necessary for specific context, ensure it is explicitly documented and justified.
*   **Action on Cardinality:** Review all relationships, especially those involving the Hub Tables (Movements, Calendar). Ensure all relationships are **one-to-many (1:\*)** where possible. If many-to-many relationships exist, consider introducing **bridge tables** to normalize the structure, which improves performance and simplifies filtering logic.
*   **Estimated Effort:** **Medium** (Requires deep investigation of the model structure).

### 4. Hub Table Optimization: Breaking Down Complexity
**Focus:** Reducing the complexity and fan-out risk associated with large hub tables.

*   **Action:** **Decompose Complex Hubs.** The high number of connections (e.g., Movements: 12 connections) suggests a potential fan-out issue. Instead of relying on these large hubs for all calculations, consider breaking them down into smaller, more focused dimension tables.
    *   *Example:* If `Movements` is a hub, separate the transactional details (facts) from the dimensional attributes (dimensions) and link them via a central key.
*   **Action:** **Implement Role-Based Filtering.** Use DAX roles or explicit filtering logic (e.g., using `USERELATIONSHIP`) instead of relying on complex, multi-directional relationships for filtering.
*   **Estimated Effort:** **Large** (Requires significant data modeling redesign and re-writing of DAX measures).

### 5. Final Model Simplification: Establishing a Clean Structure
**Focus:** Achieving a clean, scalable, and maintainable data model.

*   **Action:** **Establish a Star Schema Foundation.** Aim to structure the model around clear Fact tables (containing measures/metrics) and Dimension tables (containing descriptive attributes).
*   **Action:** **Consolidate Hubs.** If the Hub Tables are causing excessive complexity, consolidate the necessary attributes into a single, well-defined dimension table, rather than relying on multiple, interconnected hubs.
*   **Estimated Effort:** **Large** (Requires strategic architectural planning and execution).

---

## Summary of Prioritization

| Priority | Recommendation | Primary Bottleneck Addressed | Estimated Effort |
| :--- | :--- | :--- | :--- |
| **1 (CRITICAL)** | Remove 11 Isolated Tables & Execute Column Cleanup | Data Model Bloat, Memory Footprint | Quick |
| **2** | Resolve Bidirectional Filter & Review Cardinality | Relationship Complexity, Ambiguity | Medium |
| **3** | Decompose Complex Hub Tables | Connection Bottlenecks, Fan-out Risk | Large |
| **4** | Establish Star Schema Foundation | Long-term Maintainability, Scalability | Large |
| **5** | Final Model Review & Documentation | Overall Performance & Governance | Medium |
