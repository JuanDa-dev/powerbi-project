# Americas Consolidated Balance Sheet — Data Quality Audit & Column Coverage

This audit reveals significant technical debt that directly impacts operational efficiency, data storage costs, and end-user trust. The high percentage of unused columns (48.6% average) indicates a lack of rigorous data lifecycle management.

Here are three actionable recommendations, focused on maximizing business value through data model cleanup:

---

## 1. Priority Columns to Remove (Focus: Performance & Cost Reduction)

The primary goal of this step is to immediately reduce storage footprint and improve the efficiency of ETL processes, which directly translates to lower infrastructure costs and faster report delivery.

**Action:** Prioritize the removal of columns identified in the tables with the highest column waste.

| Priority Table | Action | Business Impact Assessment |
| :--- | :--- | :--- |
| **Pivot\_V2** (83.3% unused) | **Immediate Deletion.** Review the context of these columns. If they are historical snapshots or intermediate calculations that are no longer required for reporting, delete them immediately. | **Cost & Performance:** Reduces storage footprint and speeds up data refresh times (ETL/Power BI refresh). Eliminates potential confusion for report developers. |
| **Conso\_WorkingCapital** (82.4% unused) | **Immediate Deletion.** Focus on columns that are not referenced by any active measure or visual. | **Data Integrity & Clarity:** Simplifies the model, making it easier for business users to understand the core financial metrics, reducing the risk of misinterpretation. |
| **WorkingCapital\_Derco / WorkingCapital\_Inchcape** (82.4% unused) | **Phased Review & Deletion.** Investigate if these columns are necessary for specific regulatory or deep-dive analysis. If they are only used for internal ETL, consider archiving the data rather than deleting it immediately. | **Maintenance Efficiency:** Reduces the complexity of the model, lowering the maintenance burden for the data engineering team. |

**Business Rationale:** By focusing on the most wasteful tables first, we achieve the fastest return on investment (ROI) by immediately reducing storage costs and improving the speed of data delivery.

---

## 2. Documentation Improvements (Focus: Transparency & Trust)

Unused columns create "dark data" that increases confusion and slows down onboarding for new analysts. Documentation must be used to manage the remaining, intentionally hidden columns.

**Action:** Implement a standardized metadata layer across the entire model.

1. **Establish a Column Status Standard:** Define three clear states for every column:
    *   **Active/Required:** Used in DAX measures or visuals.
    *   **Deprecated/Hidden:** Intentionally kept for historical context or ETL lineage, but not for direct reporting.
    *   **Orphaned/Candidate for Removal:** Unused and slated for deletion (as identified in Recommendation 1).
2. **Implement Data Lineage Comments:** Use the Power BI model view or external documentation (e.g., a dedicated SharePoint list or Excel sheet) to document the lineage and status of columns. For deprecated columns, add a clear note explaining *why* they exist (e.g., "Historical snapshot from Q4 2022 ETL, no longer used for current reporting").
3. **Mandate Documentation in ETL:** Ensure that the ETL process explicitly flags columns that are intentionally hidden or deprecated, linking the data quality status directly to the data source.

**Business Rationale:** This shifts the model from being a source of confusion to a source of reliable information. It builds trust among business users and reduces the time analysts spend guessing the purpose of data.

---

## 3. Governance Rules (Focus: Prevention & Long-Term Health)

To prevent this technical debt from recurring, governance rules must be implemented at the point of data ingestion and model deployment.

**Action:** Implement mandatory checks and workflow gates for all new data model deployments.

1. **Establish a Column Retention Policy:** Define a maximum age or usage threshold for columns. Any column not referenced in the last 12 months must be flagged for review or deletion during the next scheduled maintenance cycle.
2. **Mandatory Data Model Review Gate:** Implement a mandatory step in the deployment pipeline (e.g., using Power BI Deployment Pipelines or Azure DevOps) that requires a Data Steward sign-off confirming that all new or modified tables adhere to the established column retention policy and that all new columns are justified.
3. **Automated Health Checks:** Develop automated scripts (using Power Query M or Python/R) that run on every refresh to scan tables for unused columns. If the count of unused columns exceeds a predefined threshold (e.g., 5% of total columns), the refresh should fail, triggering an alert to the Data Owner.

**Business Rationale:** This moves the organization from reactive cleanup to proactive data stewardship. By embedding these rules into the workflow, we ensure that data quality is maintained automatically, reducing manual intervention and preventing future accumulation of technical debt.
