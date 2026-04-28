# 🚀 Quick Start - Nueva Documentación

## En 3 pasos:

### 1️⃣ Instala las dependencias
```bash
cd powerbi-project
pip install -r requirements.txt
```

> ⏱️ **1 minuto**

### 2️⃣ Ejecuta el análisis

```bash
# Un .pbip específico
python main.py ../RecursosFuente/OnlineBaseline.pbip

# TODOS los .pbip en una carpeta ✨ NEW
python main.py ../RecursosFuente/

# Desde la carpeta actual
python main.py .
```

> ⏱️ **2-5 segundos por .pbip**

### 3️⃣ Abre los PDFs generados
```
powerbi-project/reports/
├── TECHNICAL_DOCUMENTATION.pdf ← Abre este para presentar
└── powerbi_analysis_20260427_120000.pdf ← Abre este para análisis
```

> ⏱️ **Al instante**

---

## 📄 ¿Qué documento debo usar?

### Necesito presentar rápido a ejecutivos
→ **TECHNICAL_DOCUMENTATION.pdf**
- 5-10 páginas, muy conciso
- Click aquí → [Ver estructura](#estructura-technical-documentation)

### Necesito documentar el modelo completo
→ **powerbi_analysis_*.pdf**
- 30-50 páginas, muy detallado
- Click aquí → [Ver estructura](#estructura-powerbi-analysis)

### Necesito editar algo
→ **TECHNICAL_DOCUMENTATION.md** o **powerbi_analysis_*.md**
- Abre en VS Code y edita
- Luego reconvierte a PDF si quieres

---

## 📋 Estructura TECHNICAL_DOCUMENTATION

```
TECHNICAL_DOCUMENTATION.pdf (5-15 páginas)

┌─────────────────────────────────────┐
│ Power BI Semantic Model Documentation│
│ Generated: 2026-04-27 12:00:00      │
└─────────────────────────────────────┘

1. General Description
   • Model name and key stats
   • Total tables, measures, relationships

2. Dataset: Endpoint
   • Data source definitions
   • Connection strings

3. Table Mapping (Semantic Model)
   • FACT Tables (list)
   • DIMENSION Tables (list)
   • BRIDGE Tables (list)
   • CALCULATION Tables (list)
   • PARAMETER Tables (list)

4. Tables and Composition
   ┌──────────────┬───────┬────┬──────┬─────────┐
   │ Table Name   │ Type  │ Col│Meas  │Description
   ├──────────────┼───────┼────┼──────┼─────────┤
   │ fact_spend   │ FACT  │ 15 │ 5    │ Main...
   │ dim_calendar │ DIM   │ 8  │ 0    │ Time...
   └──────────────┴───────┴────┴──────┴─────────┘

5. Relationships
   ┌───────────────┬──────┬──────────┬────┬─────┐
   │ From Table    │ From │ To Table │ To │ Card│
   ├───────────────┼──────┼──────────┼────┼─────┤
   │ fact_spend    │ supp │ dim_supp │ id │ M:1 │
   └───────────────┴──────┴──────────┴────┴─────┘

6. Pages
   ┌────────────────────┬──────────────┐
   │ Page Name          │ Visualizations
   ├────────────────────┼──────────────┤
   │ Executive Overview │ 12           │
   │ Supplier Analysis  │ 8            │
   └────────────────────┴──────────────┘
```

✅ **Perfecto para:** Presentaciones, stakeholders, email

---

## 📊 Estructura POWERBI_ANALYSIS

```
powerbi_analysis_20260427_120000.pdf (20-50 páginas)

┌────────────────────────────────────────────┐
│ Power BI Semantic Model - Comprehensive    │
│ Generated: 2026-04-27 12:00:00             │
└────────────────────────────────────────────┘

Table of Contents (clickable)
├─ Executive Overview
├─ Model Complexity Analysis
├─ Tables Summary
├─ Detailed Table Classifications
├─ Relationships Analysis
├─ Measures Overview
├─ Columns Details
├─ Report Pages
└─ Data Quality

1. Executive Overview
   • Model Statistics (tables, relationships, measures)
   • Table Distribution (FACT, DIMENSION, etc.)

2. Model Complexity Analysis
   ┌──────────────────────────────────┐
   │ 📊 Relationship Diagram          │ ← Gráfica 1
   │ [Visual network of tables]       │
   └──────────────────────────────────┘
   
   ┌──────────────────────────────────┐
   │ 📈 Table Type Distribution       │ ← Gráfica 2
   │ [Donut chart]                    │
   └──────────────────────────────────┘
   
   ┌──────────────────────────────────┐
   │ 🔥 Model Complexity Heatmap      │ ← Gráfica 3
   │ [Color-coded complexity]         │
   └──────────────────────────────────┘
   
   ┌──────────────────────────────────┐
   │ 🎨 Data Type Distribution        │ ← Gráfica 4
   │ [Bar chart]                      │
   └──────────────────────────────────┘
   
   ┌──────────────────────────────────┐
   │ 🔗 Measure Dependencies          │ ← Gráfica 5
   │ [DAG diagram]                    │
   └──────────────────────────────────┘

3. Tables Summary
   | Table | Columns | Measures | Data Types |
   |-------|---------|----------|------------|
   | fact_spend | 15 | 5 | Decimal, String... |

4. Detailed Table Classifications
   ### FACT Tables (2)
   #### fact_spend_transactions
   - Classification: FACT (Confidence: 0.95)
   - Reasoning: Primary transactional data
   - Columns: 15
   - Numeric Columns: 8
   - Measures: 5
   
   ### DIMENSION Tables (5)
   #### dim_calendar
   - Classification: DIMENSION (Confidence: 0.95)
   - Reasoning: Time dimension
   - Columns: 8
   - String Columns: 8
   - Measures: 0

5. Relationships Analysis
   | From Table | From Col | To Table | To Col | Card |
   |------------|----------|----------|--------|------|
   | fact_spend | supplier_id | dim_suppliers | id | M:1 |

6. Measures Overview
   | Table | Measure | Complexity | DAX |
   |-------|---------|-----------|-----|
   | Calculations | Total Spend | 8/10 | SUM([amount]) |

7. Columns Details
   ### fact_spend_transactions
   | Column | Data Type | Calculated | Key |
   |--------|-----------|-----------|-----|
   | amount | Decimal | | |
   | amt_adj | Decimal | ✓ | |

8. Report Pages
   | Page | Visualizations |
   |------|-----------------|
   | Executive Overview | 12 |

9. Data Quality
   - Schema Compliance: 85/100
   - Schema Type: STAR
   - Orphaned Tables: 0
```

✅ **Perfecto para:** Documentación, archives, análisis técnico

---

## 💾 Archivos Generados

```
powerbi-project/
├── data/
│   ├── tables.json
│   ├── relationships.json
│   ├── measures.json
│   ├── pages.json
│   ├── datasources.json
│   └── analysis.json
│
├── reports/
│   ├── TECHNICAL_DOCUMENTATION.md (editable)
│   ├── TECHNICAL_DOCUMENTATION.pdf ✨ SHARE THIS
│   ├── powerbi_analysis_20260427_120000.md (editable)
│   └── powerbi_analysis_20260427_120000.pdf ✨ ARCHIVE THIS
│
└── graphs/
    ├── relationship_graph.png
    ├── relationship_graph.html
    ├── measure_dependency.png
    ├── complexity_heatmap.png
    ├── schema_type_donut.png
    └── datatype_distribution.png
```

---

## 🎯 Casos de Uso

### Caso 1: Presentación a stakeholders
```bash
# 1. Genera análisis
python main.py ../RecursosFuente/OnlineBaseline.pbip

# 2. Abre y revisa
open powerbi-project/reports/TECHNICAL_DOCUMENTATION.pdf

# 3. Imprime o comparte
print → PDF file o send via email
```

### Caso 2: Documentación técnica
```bash
# 1. Genera análisis
python main.py ../RecursosFuente/OnlineBaseline.pbip

# 2. Abre el completo
open powerbi-project/reports/powerbi_analysis_*.pdf

# 3. Guarda para referencia
mv → Documentation archive
```

### Caso 3: Modificar modelo
```bash
# 1. Abre el MD
code powerbi-project/reports/TECHNICAL_DOCUMENTATION.md

# 2. Edita manualmente si necesitas
# agregar comentarios o cambios

# 3. Exporta nuevamente si cambió el modelo
python main.py ../RecursosFuente/OnlineBaseline.pbip
```

### Caso 4: Integrar en Wiki
```bash
# 1. Copia el contenido del MD
cat powerbi-project/reports/TECHNICAL_DOCUMENTATION.md | pbcopy

# 2. Pega en Confluence, Notion, GitHub
⌘+V → Wiki page

# 3. El Markdown se preserva automáticamente
```

---

## ⚠️ Si algo no funciona

### ❌ Error: "weasyprint not installed"
```bash
pip install weasyprint markdown2
```

### ❌ Los PDFs se generan pero están vacíos
```bash
# Verifica que markdown2 está instalado
pip show markdown2

# Si no, instálalo
pip install markdown2
```

### ❌ Las gráficas no se ven en el PDF
```bash
# Asegúrate que existen
ls powerbi-project/graphs/

# Si faltan, recorre el análisis
python main.py ../RecursosFuente/OnlineBaseline.pbip
```

### ✅ Todo funciona perfecto
```bash
# ¡Ya estás listo!
# Los PDFs están en powerbi-project/reports/
```

---

## 📚 Documentación Completa

- [README.md](README.md) - Descripción general
- [CHANGES.md](CHANGES.md) - Qué cambió
- [PDF_EXPORT_SETUP.md](PDF_EXPORT_SETUP.md) - Setup de PDF
- [DOCUMENTATION_STRUCTURE.md](DOCUMENTATION_STRUCTURE.md) - Estructura detallada

---

## 🎉 ¡Listo!

Ya tienes todo lo que necesitas. Solo:

1. ✅ Instala dependencias
2. ✅ Ejecuta análisis
3. ✅ Abre los PDFs
4. ✅ ¡Comparte o archiva!

---

**Version:** 2.0  
**Date:** Abril 2026  
**Status:** ✅ Production Ready
