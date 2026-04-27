# Power BI Project Analyzer

> **Modular semantic model analysis for Power BI projects (.pbip)**

Extract and classify Power BI tables, relationships, measures, and pages into structured JSON outputs with comprehensive Markdown documentation.

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none%20required-brightgreen)

---

## 🎯 Features

- **Table Classification**: FACT, DIMENSION, BRIDGE, CALCULATION, PARAMETER tables with confidence scores
- **Relationship Analysis**: Extracts M:1 relationships with schema compliance scoring
- **Measure Analysis**: DAX complexity scoring and function analysis  
- **Report Pages**: Inventory of report pages and visualizations
- **Data Sources**: Identifies semantic model data sources
- **Modular Architecture**: 6 independent parser modules with JSON data contracts
- **Zero External Dependencies**: Pure Python standard library implementation

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd powerbi-project

# No dependencies needed - uses Python standard library only
```

### Usage

```bash
# Analyze a .pbip project (from project root)
python main.py ../RecursosFuente/OnlineBaseline.pbip

# Output generates in: powerbi-project/
#   - tables.json
#   - relationships.json
#   - measures.json
#   - pages.json
#   - datasources.json
#   - analysis.json
#   - TECHNICAL_DOCUMENTATION.md
#   - powerbi_analysis_TIMESTAMP.md
```

### Platform-Specific Wrappers

**Windows:**
```bash
run.bat ../RecursosFuente/OnlineBaseline.pbip
```

**Linux/macOS:**
```bash
./run.sh ../RecursosFuente/OnlineBaseline.pbip
```

---

## 📊 Outputs

### JSON Data Files (6 outputs)
- **tables.json**: Table metadata (columns, dataypes, measures list)
- **relationships.json**: Model relationships with cardinality
- **measures.json**: Measures with DAX complexity scores (1-10)
- **pages.json**: Report pages and visualization inventory
- **datasources.json**: Data source definitions
- **analysis.json**: Table classifications + schema analysis

### Markdown Documentation (2 outputs)
- **TECHNICAL_DOCUMENTATION.md**: Executive summary with model overview
- **powerbi_analysis_TIMESTAMP.md**: Extended analysis with detailed classifications

---

## 🏗️ Architecture

```
parsers/
├── parse_tables.py         # Extract tables, columns, measures
├── parse_relationships.py  # Extract relationships with cardinality
├── parse_measures.py       # Extract measures with DAX complexity
├── parse_pages.py          # Extract report pages and visualizations
├── parse_datasources.py    # Extract data source definitions
└── parse_analysis.py       # Table classification + schema analysis

main.py                      # Orchestrator: runs all parsers + generates docs
run.bat / run.sh             # Platform-specific convenience wrappers
```

---

## 📝 Example

```python
# main.py orchestrates the complete pipeline:
1. parse_tables.py        → tables.json
2. parse_relationships.py → relationships.json
3. parse_measures.py      → measures.json
4. parse_pages.py         → pages.json
5. parse_datasources.py   → datasources.json
6. parse_analysis.py      → analysis.json

# Then generates documentation:
7. TECHNICAL_DOCUMENTATION.md
8. powerbi_analysis_TIMESTAMP.md
```

---

## 🔍 Example Analysis Output

**Table Classification:**
- 13 tables identified
- STAR schema (1 fact + 8 dimensions + 4 isolated)
- 85/100 schema compliance score

**Relationships:**
- 10 M:1 relationships extracted
- 4 disconnected components identified

**Measures:**
- 34 measures documented
- Complexity range: 1-10 (avg complexity score: 4.2)

**Report Pages:**
- 6 pages identified
- 120 total visualizations

---

## 📋 Requirements

- Python 3.6+
- **No external dependencies** - uses Python standard library only

---

## 🛠️ Development

### Adding New Parsers

1. Create `parsers/parse_newfeature.py`
2. Implement parser class extending base pattern
3. Output to JSON file
4. Register in `main.py` DocumentationGenerator

### Testing

```bash
# Test with the included OnlineBaseline.pbip
python main.py ../RecursosFuente/OnlineBaseline.pbip
```

---

## 📄 License

MIT

---

## 📧 Support

For issues or questions, please open an issue in the repository.
