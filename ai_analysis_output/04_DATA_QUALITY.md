# Americas Consolidated Balance Sheet — Data Quality Audit & Column Coverage

This audit reveals significant technical debt that directly impacts operational costs, data integrity, and user experience. The high percentage of unused columns (48.6% average) is not just a technical metric; it represents wasted storage, increased ETL complexity, and a higher risk of introducing errors during maintenance.

Here are three actionable recommendations, focused on maximizing the business value of this cleanup:

---

## 1. Priority Columns to Remove (Focus: Cost Reduction & Performance)

**Action:** Immediately identify and deprecate the columns with the highest usage waste, prioritizing tables where the unused data is likely historical or redundant.

**Business Impact Assessment:**
*   **Cost Savings:** Removing unused columns directly reduces the storage footprint of the Power BI model, potentially lowering cloud storage costs (e.g., Azure/Power BI capacity).
*   **Performance Improvement:** Fewer columns mean smaller data sets for refresh operations and query processing, leading to faster data refresh times and improved report interactivity.
*   **Reduced Maintenance Risk:** Less clutter reduces the surface area for potential errors during future ETL updates or data source changes.

**Specific Targets:**
1.  **`Pivot_V2` (83.3% waste):** Investigate the 15 unused columns. If these columns are no longer required for any current report or analytical need, they should be archived or deleted immediately.
2.  **`Conso_WorkingCapital` and `WorkingCapital_Derco`/`WorkingCapital_Inchcape` (82.4% waste):** These tables are core financial constructs. A thorough review is needed to determine if the unused columns represent historical snapshots or redundant calculations. If they are historical, they should be moved to a separate, archived data store rather than remaining in the active model.

---

## 2. Documentation Improvements (Focus: Maintainability & Trust)

**Action:** Implement a standardized metadata layer to clearly distinguish between active, deprecated, and intentionally hidden columns.

**Business Impact Assessment:**
*   **Reduced User Confusion:** Clear documentation eliminates ambiguity for report developers and end-users, reducing the time spent investigating data sources and preventing incorrect assumptions.
*   **Improved Data Trust:** When data lineage and column purpose are explicitly documented, the overall trust in the data model increases, which is critical for executive decision-making.
*   **Streamlined Onboarding:** New team members can quickly understand the model structure and avoid unnecessary exploration of dead data.

**Implementation Strategy:**
*   **Use Power BI Metadata:** Utilize the "Description" field within the Power BI data model to add explicit notes for columns marked as deprecated (e.g., "DEPRECATED - Archive in Q3 2024").
*   **Establish a Data Dictionary:** Create a centralized glossary that maps every table and column to its business definition, usage status (Active/Deprecated/Archived), and ownership.

---

## 3. Governance Rules (Focus: Prevention & Long-Term Health)

**Action:** Establish mandatory governance rules within the ETL/Data Modeling process to prevent the accumulation of unused columns in the future.

**Business Impact Assessment:**
*   **Proactive Health:** Shifting from reactive cleanup (fixing debt) to proactive governance (preventing debt) saves significant time and resources over the long term.
*   **Standardized Development:** Enforcing rules ensures that all data pipelines adhere to a consistent standard, making the entire data ecosystem more reliable and scalable.
*   **Reduced Technical Debt Cycle:** By embedding checks into the development lifecycle, the organization avoids the continuous cycle of accumulating technical debt.

**Governance Rules to Implement:**
1.  **Mandatory Column Review Gate:** Implement a mandatory step in the ETL/Data Modeling process where a data steward must explicitly approve the retention or deletion of any new column before the model is published.
2.  **Deprecation Policy:** Institute a formal policy stating that any column not referenced by an active report or analytical requirement must be flagged for archival or deletion within 30 days of its creation.
3.  **Schema Review Checklist:** Require a mandatory schema review checklist for all new table creations, specifically requiring justification for every column added, linking it back to a defined business requirement.
