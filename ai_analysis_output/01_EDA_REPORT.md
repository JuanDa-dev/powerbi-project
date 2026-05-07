# Americas Consolidated Balance Sheet — Exploratory Data Analysis & Asset Utilization

## Semantic Model Health Analysis

### 1. Data Model Health — Structure Efficiency and Asset Utilization

The semantic model possesses a fundamentally sound structure, adhering to a typical star schema pattern with 30 tables and 16 active relationships, which provides a solid foundation for reporting. However, the model suffers from significant structural inefficiency due to excessive asset bloat. With 253 total columns, only 48.6% are actively utilized, meaning **130 columns are currently unused**. This high degree of unused assets indicates that the model is bloated and contains redundant data, increasing the risk of maintenance errors and slowing down query performance. While the structure is logically sound, the poor utilization of existing assets suggests a failure in the initial data modeling or subsequent data hygiene processes.

### 2. Technical Debt — Orphaned Columns, Unused Measures, and Disconnected Assets

The model is burdened by substantial technical debt, primarily manifested in unused assets. The fact that **17 tables contain unused columns**, contributing to a **51.4% unused column rate**, demands immediate attention. These orphaned columns represent unnecessary storage overhead and complicate data governance. Furthermore, the measure layer is highly inefficient: only 21.3% of the 47 measures are utilized, leaving **37 measures as cleanup candidates**. This suggests a significant amount of complex, potentially redundant DAX logic that is either unused or poorly defined. The high average measure complexity (12.11) further compounds this debt, indicating that the existing calculations are likely over-engineered and difficult to maintain.

### 3. Optimization Opportunities — Quick Wins and Major Improvements Needed

Optimization efforts should be prioritized to achieve immediate cleanup and long-term efficiency gains. The most immediate "quick win" is to address the unused assets: systematically review the 17 tables and delete all columns that are not referenced by any active relationship or report visual. This action will immediately reduce the column count and improve model size. The second priority is the measure cleanup: audit the 37 unused measures. Any measure that is not actively used in the final reports must be deleted, simplifying the model and reducing the complexity burden. For major improvements, focus on refactoring the high-complexity measures (those with complexity scores above 20) to simplify logic, and investigate the high volume of `string` data (205 columns) to determine if data types can be optimized or if redundant descriptive columns can be consolidated into dimension tables.

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
