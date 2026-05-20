# Americas Consolidated Balance Sheet — Performance Analysis & Bottleneck Resolution

This analysis identifies significant opportunities for performance improvement, data model simplification, and long-term maintenance reduction. The primary bottlenecks are **data model bloat** (unused columns) and **structural complexity** (isolated tables and complex relationships).

Here is the 5-point optimization roadmap, prioritized by impact and effort.

---

## 5-Point Optimization Roadmap

### 1. CRITICAL: Data Model Bloat & Isolation Cleanup (Highest Impact / Lowest Effort)

**Goal:** Immediately reduce the model size, improve refresh times, and eliminate orphaned assets.

**Action:** Remove all 11 isolated tables and clean up the identified unused columns.

| Table | Action | Rationale | Effort |
| :--- | :--- | :--- | :--- |
| **Pivot\_V2** | Remove 15 unused columns. | Reduces memory footprint and simplifies DAX calculations. | Quick |
| **Conso\_WorkingCapital** | Remove 14 unused columns. | Reduces memory footprint. | Quick |
| **derco\_seven\_levels** | Remove 14 unused columns. | Reduces memory footprint. | Quick |
| **WorkingCapital\_Derco** | Remove 14 unused columns. | Reduces memory footprint. | Quick |
| **WorkingCapital\_Inchcape** | Remove 14 unused columns. | Reduces memory footprint. | Quick |
| **11 Isolated Tables** | **Delete** all 11 tables that have no relationships. | Eliminates unnecessary data and maintenance overhead. | Quick |

**Estimated Effort:** Quick (This is a bulk cleanup operation that yields immediate performance gains.)

### 2. Relationship Issues: Resolve Ambiguity and Cardinality (High Impact / Medium Effort)

**Goal:** Eliminate ambiguity and potential calculation errors caused by complex relationship structures.

**Action:** Address the bidirectional filter and review all relationships for cardinality.

*   **Bidirectional Filter:** Investigate the source of the single bidirectional filter. If possible, convert this to a single, clear relationship (e.g., using a bridge table or a single direction) to simplify filter context and improve query performance.
*   **Cardinality Review:** Audit all relationships, especially those involving the Hub Tables (Movements, Calendar). Ensure all relationships are **One-to-Many (1:\*)** where possible. If many-to-many relationships exist, consider introducing bridge/junction tables to normalize the data structure.

**Estimated Effort:** Medium (Requires deep investigation into the data flow and potential structural changes.)

### 3. Hub Table Optimization: De-complexify Connections (High Impact / Medium Effort)

**Goal:** Reduce the complexity and potential fan-out issues within the central hub tables.

**Action:** Refactor the Hub Tables to minimize direct connections and leverage roles.

*   **Hub Table Strategy:** Instead of having 12 direct connections from the `Movements` table, consider introducing a **Star Schema** approach. If possible, create a central dimension table (e.g., a `Date` table and a `Hierarchy` table) and link all fact tables to these dimensions, rather than linking every fact table directly to the Hub tables.
*   **Role Implementation:** If the Hub tables are used for filtering, implement **Role-Playing Dimensions** (e.g., using DAX or Power BI roles) to manage context, rather than relying solely on complex, multi-directional relationships.

**Estimated Effort:** Medium (Requires model redesign and careful testing of the new structure.)

### 4. Model Simplification: Consolidate and Streamline (Medium Impact / Medium Effort)

**Goal:** Reduce the overall number of tables and improve data integrity.

**Action:** Consolidate related data and eliminate redundant tables.

*   **Consolidation:** Review the 5 tables related to Working Capital (`Conso_WorkingCapital`, `WorkingCapital_Derco`, `WorkingCapital_Inchcape`, etc.). Determine if these can be consolidated into a single, comprehensive fact table or a single dimension table, depending on their relationship.
*   **Hub Table Refinement:** Evaluate the necessity of the specific Hub tables (`derco_seven_levels`, `LocalDateTable_4a5bc742...`). If they are only used for simple date/hierarchy filtering, consider embedding this logic directly into the main fact tables or using a single, well-structured Date/Hierarchy dimension instead of multiple specialized hub tables.

**Estimated Effort:** Medium (Requires data analysis and careful merging/restructuring.)

### 5. Redesign & Governance: Future-Proofing the Model (Long-Term Impact / Large Effort)

**Goal:** Establish governance standards to prevent future bloat and complexity.

**Action:** Implement strict naming conventions and establish a formal data modeling standard.

*   **Naming Convention:** Enforce a strict naming convention (e.g., Fact, Dimension, Bridge) to prevent the creation of isolated tables and ambiguous relationships in the future.
*   **Data Flow Governance:** Implement a process where all new data sources must adhere to a pre-defined schema (e.g., all fact tables must link to a central Date table).
*   **Redesign:** If the complexity of the Hub tables remains unmanageable, plan a full **Redesign** to transition the model from a complex, highly connected structure to a cleaner, more scalable Star Schema.

**Estimated Effort:** Large (This is a strategic, long-term effort focused on governance and architectural change.)

---

## Summary of Prioritization

| Priority | Focus Area | Primary Action | Estimated Effort | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **1 (CRITICAL)** | Data Bloat & Isolation | Delete isolated tables and unused columns. | Quick | Immediate performance and maintenance gain. |
| **2** | Relationship Issues | Resolve bidirectional filters and check cardinality. | Medium | Fixes structural ambiguity and potential calculation errors. |
| **3** | Hub Table Optimization | Refactor connections and leverage roles. | Medium | Improves the efficiency of the central data flow. |
| **4** | Model Simplification | Consolidate redundant tables. | Medium | Reduces overall model size and complexity. |
| **5** | Redesign & Governance | Implement naming standards and architectural review. | Large | Long-term strategy for sustainable model health. |
