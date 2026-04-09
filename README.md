# Power BI Project EDA Tool

> **Comprehensive Exploratory Data Analysis for Power BI Projects (.pbip)**

Analyze your Power BI semantic models locally without requiring Power BI Desktop or Fabric connection. Generate detailed Markdown reports with visualizations covering tables, measures, relationships, DAX complexity, and best practice recommendations.

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 Features

### Complete Model Analysis
- **Tables Classification**: Automatically identifies Fact, Dimension, and Calculated tables
- **Measures Analysis**: DAX complexity scoring, function usage, dependency graphs
- **Relationships Mapping**: Graph theory metrics, hub detection, connectivity analysis
- **Data Types Distribution**: Column type analysis and statistics
- **Security Roles**: RLS (Row-Level Security) analysis
- **Hierarchies**: Complete hierarchy structure analysis

### Visual Reports
- 📊 **Relationship Diagrams**: NetworkX-based model visualization
- 📈 **Complexity Charts**: Measure and table complexity analysis
- 🔗 **Dependency Graphs**: DAX measure dependencies
- 📉 **Data Type Charts**: Type distribution visualizations

### Best Practices
- ⚠️ Detects isolated tables
- 🔴 Identifies disconnected model components
- 💡 Provides optimization recommendations
- ✅ Validates model structure

---

## 🚀 Quick Start

### Installation

1. **Clone or download this repository**

```bash
git clone <repository-url>
cd powerbi-project
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

**Requirements:**
- Python 3.7+
- pandas, matplotlib, seaborn, networkx, tqdm

### Usage

**Basic usage:**
```bash
cd pbi-mcp-enhanced
python main.py <path-to-pbip-file>
```

**With custom output directory:**
```bash
python main.py ./my-project.pbip -o ./reports
```

**With verbose logging:**
```bash
python main.py ./my-project.pbip --verbose
```

### Command Line Arguments

```
positional arguments:
  pbip_path             Path to .pbip project file or directory

optional arguments:
  -h, --help            Show help message
  -o OUTPUT, --output OUTPUT
                        Output directory (default: output/)
  -v, --verbose         Enable verbose logging
  --version             Show version number
```

---

## 📁 Input Format

### What is a .pbip Project?

A `.pbip` (Power BI Project) file is a JSON pointer that references a version control-friendly Power BI project made up of sibling folders.

**Required structure:**
```
my-project/
├── my-project.pbip        # JSON pointer file (pass this to the tool)
├── my-project.Report/
│   └── definition.pbir    # Report definition
└── my-project.SemanticModel/
    ├── definition.pbism   # Dataset metadata
    └── model.bim          # JSON tabular model
```

Pass the `.pbip` file directly to the tool — no need to point at a directory.

Works with **local .pbip files** - no Power BI Desktop or Fabric connection required.

---

## 📊 Output

### Generated Files

```
output/
├── powerbi_analysis_YYYYMMDD_HHMMSS.md
└── images/
    ├── relationship_diagram.png
    ├── data_type_distribution.png
    ├── measure_dependencies.png
    └── table_complexity.png
```

### Report Sections

1. **Executive Summary** - Quick stats and key insights
2. **Data Model Diagram** - Visual relationship graph
3. **Tables Analysis** - Fact/Dimension classification
4. **Measures Analysis** - DAX complexity and dependencies
5. **Relationships Analysis** - Graph metrics and connectivity
6. **Data Type Distribution** - Column type statistics
7. **Recommendations** - Best practices and optimization

---

## 🏗️ Architecture

```
pbi-mcp-enhanced/
├── parsers/              # PBIP and model.bim parsers
├── analyzers/            # Analysis engines
├── utils/                # Statistics generators
├── visualizations/       # Chart generators
├── report/               # Markdown report generators
└── main.py               # CLI entry point
```

### Analysis Pipeline

```
Parse → Analyze → Calculate Stats → Generate Visuals → Export Report
```

---

## 🔧 Based On

This tool is based on [powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp) by Microsoft, extended for comprehensive offline EDA.

---

## 📄 License

MIT License

---

**Happy analyzing! 📊✨**

## Project Structure

```
powerbi-project/
├── pbi-mcp-enhanced/
│   ├── parsers/         # PBIP file parsers
│   ├── analyzers/       # Data model analyzers
│   ├── visualizations/  # Chart generators
│   ├── report/          # Report generators
│   └── utils/           # Helper utilities
├── tests/               # Unit tests
├── output/              # Generated reports
└── docs/                # Documentation
```

## Requirements

- Python 3.8+
- See requirements.txt for dependencies

## License

MIT License
