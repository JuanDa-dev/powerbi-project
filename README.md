# Power BI Project Analyzer

> **Modular semantic model analysis for Power BI projects (.pbip)**

Extract and classify Power BI tables, relationships, measures, and pages into structured JSON outputs with **comprehensive Markdown + PDF documentation**.

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![PDF Export](https://img.shields.io/badge/PDF%20Export-✨%20NEW-green)
![Dependencies](https://img.shields.io/badge/optional%20deps-visualization%2C%20pdf-blue)

---

## 🎯 Features

- **Table Classification**: FACT, DIMENSION, BRIDGE, CALCULATION, PARAMETER tables with confidence scores
- **Relationship Analysis**: Extracts M:1 relationships with schema compliance scoring
- **Measure Analysis**: DAX complexity scoring and function analysis  
- **Report Pages**: Inventory of report pages and visualizations
- **Data Sources**: Identifies semantic model data sources
- **Modular Architecture**: 6 independent parser modules with JSON data contracts
- **📝 Dual Documentation**: 
  - `TECHNICAL_DOCUMENTATION.pdf` - Concise executive summary
  - `powerbi_analysis_*.pdf` - Comprehensive analysis with charts
- **📊 Advanced Visualizations**: Relationship graphs, complexity heatmaps, and DAG diagrams
- **Zero Core Dependencies**: Pure Python for core analysis

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd powerbi-project

# Install dependencies (including PDF export)
pip install -r requirements.txt

# Or minimal install (no PDF export)
pip install matplotlib seaborn networkx plotly pillow pydot
```

> **Note:** PDF export requires WeasyPrint. See [PDF_EXPORT_SETUP.md](PDF_EXPORT_SETUP.md) for system dependencies.

### Usage

```bash
# Analyze a .pbip project (from project root)
python main.py ../RecursosFuente/OnlineBaseline.pbip

# Output generates in: powerbi-project/
#   📊 JSON DATA
#   ├── tables.json
#   ├── relationships.json
#   ├── measures.json
#   ├── pages.json
#   ├── datasources.json
#   └── analysis.json
#
#   📝 MARKDOWN + PDF DOCUMENTATION  ✨ NEW
#   ├── TECHNICAL_DOCUMENTATION.md
#   ├── TECHNICAL_DOCUMENTATION.pdf ✨
#   ├── powerbi_analysis_TIMESTAMP.md
#   └── powerbi_analysis_TIMESTAMP.pdf ✨
#
#   📈 VISUALIZATIONS
#   ├── relationship_graph.png + .html
#   ├── measure_dependency.png
#   ├── complexity_heatmap.png
#   ├── schema_type_donut.png
#   └── datatype_distribution.png
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

## 📊 Outputs Explained

### Two-Tier Documentation System ✨ NEW

#### **1. TECHNICAL_DOCUMENTATION.pdf**
🎯 **Purpose:** Executive summary for quick reference  
📄 **Length:** 5-15 pages | Concise, copy-paste ready

**Contains:**
- General Description
- Dataset: Endpoint  
- Table Mapping (Semantic Model)
- Tables and Composition
- Relationships (table format)
- Pages

**Perfect for:**
- Stakeholder presentations
- Quick model reviews
- Non-technical audiences
- Email sharing

---

#### **2. powerbi_analysis_TIMESTAMP.pdf**
📊 **Purpose:** Comprehensive technical analysis  
📄 **Length:** 20-50 pages | Detailed with 5 embedded charts

**Contains:**
- Executive Overview with stats
- Model Complexity Analysis (with visualizations)
- Detailed Table Classifications
- Complete Relationships Analysis
- Measures Overview with DAX snippets
- Column-level inventory
- Data Quality Assessment

**Perfect for:**
- Data architects
- Deep technical reviews
- Model documentation
- Archival purposes

---

### File Structure

```
powerbi-project/
│
├── data/                          ← 📊 JSON data files (6 files)
│   ├── tables.json               # Table metadata, columns, datatypes
│   ├── relationships.json        # Model relationships with cardinality
│   ├── measures.json             # DAX measures with complexity scores
│   ├── pages.json                # Report pages and visualizations
│   ├── datasources.json          # Data source definitions
│   └── analysis.json             # Table classifications + schema analysis
│
├── reports/                       ← 📝 Markdown + PDF Documentation ✨
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── TECHNICAL_DOCUMENTATION.pdf ✨ NEW
│   ├── powerbi_analysis_20260427_120000.md
│   └── powerbi_analysis_20260427_120000.pdf ✨ NEW
│
└── graphs/                        ← 📈 Visualizations (5 PNG + 1 HTML)
    ├── relationship_graph.png
    ├── relationship_graph.html
    ├── measure_dependency.png
    ├── complexity_heatmap.png
    ├── schema_type_donut.png
    └── datatype_distribution.png
```

### PDF Documentation ✨ NEW

**Two-tier documentation for different audiences:**

| Document | Audience | Length | Includes | Format |
|----------|----------|--------|----------|--------|
| **TECHNICAL_DOCUMENTATION.pdf** | Executives, Stakeholders | 5-15 pages | General Description, Table Mapping, Relationships, Pages | MD + PDF |
| **powerbi_analysis_*.pdf** | Architects, Data Analysts | 20-50 pages | All above + 5 charts, detailed measures, columns inventory, quality metrics | MD + PDF |

All PDFs include professional styling and are ready for sharing or printing.

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

main.py                      # Orchestrator: runs all parsers + generates docs + PDF export
run.bat / run.sh             # Platform-specific convenience wrappers
```

---

## 📦 Installation & Dependencies

### Core Analysis (Always included)
- Python 3.6+
- No external dependencies - uses Python standard library only

### PDF Export ✨ NEW (Optional but recommended)
```bash
# Install full dependencies
pip install -r requirements.txt

# Or just PDF dependencies
pip install weasyprint markdown2
```

> See [PDF_EXPORT_SETUP.md](PDF_EXPORT_SETUP.md) for system-specific requirements.

### Visualizations (Optional)
- matplotlib, seaborn, networkx, plotly (included in requirements.txt)

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
