# Project Structure Overview

## Directory Layout

```
powerbi-project/
│   ├── main.py                    # Master orchestrator
│   ├── analyzers/                 # Table/measure/relationship analysis
│   ├── parsers/                   # TMDL, JSON, model parsing
│   ├── visualizers/               # PNG/HTML visualizations generator
│   ├── power-bi-project/          # Documentation generation
    ├── scripts/                   # several scripts
│
│
├── scripts/                       # 🆕 Utility scripts
│   ├── ollama_client.py           # Ollama HTTP client
│   ├── ollama_generator.py        # AI documentation generator
│   ├── check_types.py             # Verify datatype extraction
│   ├── check_classification.py    # Verify AI classifications
    ├── documentation_generator.py # Generates separately the documentation
│   ├── inspect_tmdl.py            # Inspect TMDL structure
│   ├── README.md                  # Scripts documentation
│   ├── QUICKSTART.md              # Quick start guide
│   └── __init__.py                # Package marker
│
├── powerbi-project/              # Pipeline outputs
│   ├── data/                     # JSON analysis
│   │   ├── tables.json
│   │   ├── relationships.json
│   │   ├── measures.json
│   │   └── ...
│   ├── reports/                 # Markdown documentation
│   │   ├── TECHNICAL_DOCUMENTATION.md
│   │   └── powerbi_analysis_*.md
│   └── graphs/                  # Visualizations (PNG + HTML)
│       ├── relationship_graph.png
│       ├── measure_dependency.png
│       ├── complexity_heatmap.png
│       ├── schema_type_donut.png
│       └── datatype_distribution.png
│
└── output_ai/                    # 🆕 AI-enriched outputs
    └── AI_DOCUMENTATION.md
```

## Data Flow

```
RecursosFuente/
  ├── OnlineBaseline.pbip
  │   ├── SemanticModel/
  │   │   └── definition/ (TMDL files)
  │   └── Report/
  │       └── definition/ (JSON pages)
  └── aaa.csv (data source)
         ↓
    [main.py Parsers]
         ↓
    ├─→ tables.json
    ├─→ relationships.json
    ├─→ measures.json
    ├─→ pages.json
    ├─→ datasources.json
    └─→ analysis.json
         ↓
    [1. Documentation Generator]
    ├─→ TECHNICAL_DOCUMENTATION.md
    └─→ powerbi_analysis_*.md
         ↓
    [2. Visualizers]
    ├─→ relationship_graph.png
    ├─→ measure_dependency.png
    ├─→ complexity_heatmap.png
    ├─→ schema_type_donut.png
    └─→ datatype_distribution.png
         ↓
    [3. 🆕 Ollama Generator] (Optional)
    ├─→ tables_enriched.json (+ AI classifications)
    └─→ AI_DOCUMENTATION.md
```

## Workflow

### Basic Pipeline (Always)
```bash
python main.py ../RecursosFuente/OnlineBaseline.pbip
```
✅ Parses PBIP
✅ Generates documentation
✅ Creates visualizations

### AI Enhancement (Optional)
```bash
python scripts/ollama_generator.py
```
✅ Classifies tables with AI
✅ Generates measure descriptions
✅ Enriches JSON with AI annotations
✅ Creates AI-powered documentation

### Verification (Debugging)
```bash
python scripts/check_types.py
python scripts/check_classification.py
python scripts/inspect_tmdl.py
```
✅ Verify datatype extraction
✅ Verify AI classifications
✅ Inspect TMDL structure

## Key Components

### Parsers (pbi-mcp-enhanced/parsers/)
- `pbip_parser.py` - PBIP file structure
- `tmdl_parser.py` - Table definitions
- `model_bim_parser.py` - Binary model
- `definition_parser.py` - Relationships/measures
- `parse_tables.py` - Column extraction
- `parse_measures.py` - Measure DAX
- `parse_pages.py` - Report pages
- `parse_relationships.py` - Table relationships
- `parse_analysis.py` - Table classification

### Analyzers (pbi-mcp-enhanced/analyzers/)
- `table_analyzer.py`
- `measure_analyzer.py`
- `column_analyzer.py`
- `relationship_analyzer.py`
- `role_analyzer.py`
- `hierarchy_analyzer.py`

### Visualizers (pbi-mcp-enhanced/visualizations/)
- `relationship_diagram.py` → relationship_graph.png
- `measure_dependencies.py` → measure_dependency.png
- `table_complexity.py` → complexity_heatmap.png
- `data_type_chart.py` → datatype_distribution.png

### Report Generators (pbi-mcp-enhanced/report/)
- `header_generator.py`
- `summary_generator.py`
- `tables_generator.py`
- `measures_generator.py`
- `relationships_generator.py`
- `recommendations_generator.py`
- `datatype_generator.py`
- `report_exporter.py`

### Scripts (scripts/)
- `ollama_client.py` - AI connectivity
- `ollama_generator.py` - AI enrichment
- `check_types.py` - Type verification
- `check_classification.py` - Classification verification
- `inspect_tmdl.py` - TMDL inspection

## File Formats

### Input (RecursosFuente/)
- `*.pbip` - Power BI Project (ZIP container)
- `*.tmdl` - Tabular Model Definition Language
- `*.json` - Page/visual definitions

### Output (powerbi-project/)
- `*.json` - Structured data exports
- `*.md` - Markdown documentation
- `*.png` - Static visualizations
- `*.html` - Interactive visualizations

### AI Output (output_ai/)
- `tables_enriched.json` - JSON with AI annotations
- `AI_DOCUMENTATION.md` - AI-generated markdown

## Dependencies

### Core (Built-in)
- `json`, `re`, `pathlib`, `collections`

### Analysis
- `matplotlib` 3.7.0+
- `seaborn` 0.12.0+
- `networkx` 3.1+

### Visualization (Optional)
- `pyvis` 0.3.0
- `plotly` 5.17.0+

### AI Integration
- `urllib` (built-in)
- Ollama local instance

## Environment

Python 3.6+
No virtual environment required (uses system Python)

## Recent Changes

### ✅ Completed
1. Output organization (data/, reports/, graphs/)
2. Datatype detection & classification
3. Measure DAX extraction
4. Visual metadata parsing
5. 5 visualization types
6. GitHub integration (3 commits)

### 🆕 Added
1. `/scripts` directory organization
2. Ollama AI integration
3. Table classification with AI
4. Measure description generation
5. Enriched documentation output

### 📅 Timeline
- Feb-Apr 2026: Core pipeline development
- Apr 27 2026: Datatype detection fix
- Apr 27 2026: Ollama integration
