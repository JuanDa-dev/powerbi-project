# Power BI Project EDA Tool Documentation

## .pbip File Structure

### Directory Structure
```
MiProyecto.pbip/
├── .pbi/
│   ├── localSettings.json
│   └── cache.abf
├── report/
│   ├── definition.pbir
│   ├── StaticResources/
│   └── PageLayouts/
└── semantic-model/
    ├── definition.pbism
    ├── model.bim
    ├── tables/
    └── relationships.json
```

### Key Files

#### model.bim (JSON)
Contains the complete tabular model:
- `model.tables[]` - All tables
- `model.tables[].columns[]` - Columns per table
- `model.tables[].measures[]` - DAX measures
- `model.relationships[]` - Table relationships
- `model.dataSources[]` - Data sources
- `model.roles[]` - RLS security roles

#### definition.pbir (JSON)
Report metadata:
- Report configuration
- Visual containers
- Page layouts
- Static resources

### Data Types
- string
- int64
- double
- datetime
- boolean
- decimal

### Relationship Properties
- fromTable/toTable
- fromColumn/toColumn
- crossFilteringBehavior: "oneDirection" | "bothDirections"
- cardinality: "one" | "many"

### Measure Structure
```json
{
  "name": "MeasureName",
  "expression": "SUM(Table[Column])",
  "formatString": "#,##0.00",
  "lineageTag": "uuid"
}
```
