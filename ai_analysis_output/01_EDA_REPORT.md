# Americas Consolidated Balance Sheet — Exploratory Data Analysis & Asset Utilization

## Semantic Model Health Analysis

### 1. Data Model Health — Structure Efficiency and Asset Utilization

The semantic model exhibits a fundamentally sound structure, adhering to a typical star schema design with 30 tables and 16 active relationships, which is a strong foundation for analytical reporting. However, the efficiency of this structure is severely compromised by poor asset utilization. The model contains 253 columns, yet only 48.6% are actively used, resulting in **130 unused columns**. This indicates significant data redundancy or poorly defined dimensions/facts that are not contributing to the current reporting needs. While the core structure is correct, the sheer volume of unused assets suggests that the model is bloated and inefficient, increasing the risk of maintenance overhead and potential confusion for end-users.

### 2. Technical Debt — Orphaned Columns, Unused Measures, and Disconnected Assets

The model is burdened by substantial technical debt, primarily manifested in unused assets. Specifically, **17 tables** contain unused columns, accounting for **51.4%** of the total unused columns. This is a critical area for immediate cleanup, as these columns consume storage and complicate data lineage without providing analytical value. Furthermore, the measure layer is equally inefficient: **37 measures** are currently unused, representing a significant cleanup candidate. This disparity between the complexity of the measures (ranging from an average of 12.11 to a maximum of 51.0) and their actual utilization (only 21.3% utilized) suggests that many complex calculations are either obsolete or not being leveraged by the reports.

### 3. Optimization Opportunities — Quick Wins and Major Improvements Needed

Optimization efforts should focus on immediate cleanup to improve model performance and maintainability. The highest priority action is to systematically identify and **delete the 130 unused columns** across the 17 tables. This cleanup will immediately reduce the model size and simplify the data structure. Following this, the team must audit the **37 unused measures**. For measures that are not actively used in the 125 visuals, they should be either simplified, deprecated, or removed entirely. Finally, to address the complexity issue, review the measures with the highest complexity scores (e.g., those near the maximum of 51.0) to determine if their logic can be refactored into simpler, more efficient DAX calculations, thereby improving both performance and end-user comprehension.

## Key Metrics

| Metric | Value |
|--------|-------|
| Tables | 30 |
| Total Columns | 253 |
| Column Usage | 48.6% |
| Unused Columns | 130 |
| Active Relationships | 16 |
| Total Measures | 47 |
| Measure Utilization | 21.3% |
| Unused Measures | 37 |
