from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DocPaths:
    output_dir: Path

    @property
    def data_dir(self) -> Path:
        return self.output_dir / "data"

    @property
    def reports_dir(self) -> Path:
        return self.output_dir / "reports"

    @property
    def graphs_dir(self) -> Path:
        return self.output_dir / "graphs"


class DocumentationGenerator:
    """
    Generates Markdown documentation from parsed Power BI JSON outputs.

    Produces:
    - reports/TECHNICAL_DOCUMENTATION.md (executive)
    - reports/powerbi_analysis_TIMESTAMP.md (extended)
    """

    def __init__(self, output_dir: Path, pbip_name: str):
        self.paths = DocPaths(output_dir=Path(output_dir))
        self.pbip_name = pbip_name

        # Ensure expected folders exist
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.reports_dir.mkdir(parents=True, exist_ok=True)

        # Loaded data
        self.tables_raw: Any = []
        self.relationships_raw: Any = []
        self.measures_raw: Any = []
        self.pages_raw: Any = []
        self.datasources_raw: Any = []
        self.analysis_data: dict[str, Any] = {}

    # -----------------------------
    # Public API used by main.py
    # -----------------------------
    def generate_all(self) -> None:
        """Loads JSON and writes both markdown documents to disk."""
        self.load_all_data()

        tech_md = self.generate_technical_documentation()
        (self.paths.reports_dir / "TECHNICAL_DOCUMENTATION.md").write_text(tech_md, encoding="utf-8")

        extended_md, filename = self.generate_extended_documentation()
        (self.paths.reports_dir / filename).write_text(extended_md, encoding="utf-8")

    # -----------------------------
    # Data loading
    # -----------------------------
 
    def load_all_data(self) -> None:
        self.tables_raw = self._load_json("tables.json", default=[])
        self.relationships_raw = self._load_json("relationships.json", default=[])
        self.measures_raw = self._load_json("measures.json", default=[])
        self.pages_raw = self._load_json("pages.json", default=[])
        self.datasources_raw = self._load_json("datasources.json", default=[])
        self.analysis_data = self._load_json("analysis.json", default={})

        self.tables_data = self._as_list(self.tables_raw, "tables")
        self.relationships_data = self._as_list(self.relationships_raw, "relationships")
        self.measures_data = self._as_list(self.measures_raw, "measures")
        self.pages_data = self._as_list(self.pages_raw, "pages")
        self.datasources_data = self._as_list(self.datasources_raw, "datasources")
    
    def _as_list(self, data: Any, key: str) -> list[dict[str, Any]]:
        """
        Normalize parser outputs.

        Supports:
        - Old contract: [...]
        - New contract: {"key": [...]}
        - Invalid/missing data: []
        """
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

        if isinstance(data, dict):
            values = data.get(key, [])
            if isinstance(values, list):
                return [item for item in values if isinstance(item, dict)]

        return []

    def _get_summary(self, raw_data: Any) -> dict[str, Any]:
        """
        Safely extract summary section from structured parser outputs.
        """
        if isinstance(raw_data, dict):
            summary = raw_data.get("summary", {})
            if isinstance(summary, dict):
                return summary
        return {}


    def _get_issues(self, raw_data: Any) -> list[str]:
        """
        Safely extract issues section from structured parser outputs.
        """
        if isinstance(raw_data, dict):
            issues = raw_data.get("issues", [])
            if isinstance(issues, list):
                return [str(issue) for issue in issues]
        return []


    def _get_recommendations(self, raw_data: Any) -> list[str]:
        """
        Safely extract recommendations section from structured parser outputs.
        """
        if isinstance(raw_data, dict):
            recommendations = raw_data.get("recommendations", [])
            if isinstance(recommendations, list):
                return [str(item) for item in recommendations]
        return []


    def _escape_md_cell(self, value: Any) -> str:
        """
        Escape markdown table cell content.
        """
        text = "" if value is None else str(value)
        return text.replace("\n", " ").replace("|", "\\|").strip()


    def _load_json(self, filename: str, default: Any) -> Any:
        path = self.paths.data_dir / filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return default

    # -----------------------------
    # Document 1: Executive
    # -----------------------------
    def generate_technical_documentation(self) -> str:
        """Generate concise TECHNICAL_DOCUMENTATION.md - ready to copy/paste."""
        doc: list[str] = []

        doc.append("# Power BI Semantic Model Documentation")
        doc.append("")
        doc.append(f"**Generated:** {datetime.now():%Y-%m-%d %H:%M:%S}")
        doc.append("")
        doc.append("## General Description")
        doc.append("")
        doc.append(f"**Semantic Model:** {self.pbip_name}")

        summary = self.analysis_data.get("summary", {}) if isinstance(self.analysis_data, dict) else {}
        total_tables = summary.get("total_tables", len(self.tables_data))
        total_measures = summary.get("total_measures", len(self.measures_data))
        doc.append(f"**Tables:** {total_tables} | **Measures:** {total_measures}")
        doc.append("")

        # Dataset: Endpoint
        doc.append("## Dataset: Endpoint")
        doc.append("")
        if self.datasources_data:
            for ds in self.datasources_data:
                ds_type = ds.get("type", "Unknown")
                connector = ds.get("connector")
                ds_def = ds.get("definition", "N/A")
                confidence = ds.get("confidence")
                attributes = ds.get("attributes", {}) or {}

                details = []

                if connector:
                    details.append(f"Connector: `{connector}`")

                if attributes.get("server"):
                    details.append(f"Server: `{attributes.get('server')}`")

                if attributes.get("database"):
                    details.append(f"Database: `{attributes.get('database')}`")

                if attributes.get("domain"):
                    details.append(f"Domain: `{attributes.get('domain')}`")

                if attributes.get("path"):
                    details.append(f"Path: `{attributes.get('path')}`")

                if confidence is not None:
                    details.append(f"Confidence: {confidence}")

                detail_text = f" ({'; '.join(details)})" if details else ""

                doc.append(
                    f"- **{self._escape_md_cell(ds_type)}**: "
                    f"{self._escape_md_cell(ds_def)}{detail_text}"
                )
        else:
            doc.append("- No explicit data sources defined")

        # Table Mapping
        doc.append("## Table Mapping (Semantic Model)")
        doc.append("")
        classifications = self.analysis_data.get("table_classifications", []) if isinstance(self.analysis_data, dict) else []
        if classifications:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for cls in classifications:
                ctype = cls.get("classification", "UNKNOWN")
                grouped.setdefault(ctype, []).append(cls)

            for table_type in ["FACT", "DIMENSION", "BRIDGE", "CALCULATION", "PARAMETER"]:
                if table_type in grouped:
                    table_list = grouped[table_type]
                    doc.append(f"**{table_type} Tables** ({len(table_list)})")
                    for t in sorted(table_list, key=lambda x: x.get("table_name", "")):
                        doc.append(f"- {t.get('table_name', 'Unknown')}")
                    doc.append("")
        else:
            doc.append("- No table classifications found in analysis.json")
            doc.append("")

        # Tables and Composition
        doc.append("## Tables and Composition")
        doc.append("")
        doc.append("| Table Name | Type | Columns | Measures | Description |")
        doc.append("|------------|------|---------|----------|-------------|")

        if classifications:
            for cls in sorted(classifications, key=lambda x: x.get("table_name", "")):
                table_name = cls.get("table_name", "Unknown")
                table_type = cls.get("classification", "UNKNOWN")
                metadata = cls.get("metadata", {}) or {}
                columns = metadata.get("columns", 0)
                measures = metadata.get("measures", 0)
                reasoning = (cls.get("reasoning", "") or "").replace("\n", " ").replace("|", "\\|")
                doc.append(f"| {table_name} | {table_type} | {columns} | {measures} | {reasoning} |")
        else:
            # Fallback using tables.json only
            for t in sorted(self.tables_data, key=lambda x: x.get("name", "")):
                doc.append(f"| {t.get('name','Unknown')} | N/A | {t.get('column_count',0)} | {t.get('measure_count',0)} | |")

        doc.append("")

        # Relationships
        if self.relationships_data:
            doc.append("## Relationships")
            doc.append("")
            doc.append(f"**Total Relationships:** {len(self.relationships_data)}")
            doc.append("")
            doc.append("| From Table | From Column | To Table | To Column | Cardinality |")
            doc.append("|------------|------------|----------|-----------|-------------|")
            for rel in self.relationships_data:
                doc.append(
                    f"| {rel.get('from_table','')} | {rel.get('from_column','')} | "
                    f"{rel.get('to_table','')} | {rel.get('to_column','')} | {rel.get('cardinality','')} |"
                )
            doc.append("")

        # Pages
        if self.pages_data:
            doc.append("## Pages")
            doc.append("")
            doc.append(f"**Total Pages:** {len(self.pages_data)}")
            doc.append("")
            doc.append("| Page Name | Visualizations |")
            doc.append("|-----------|-----------------|")
            for page in self.pages_data:
                doc.append(f"| {page.get('display_name','Unknown')} | {page.get('visuals_count',0)} |")
            doc.append("")

        return "\n".join(doc)

    # -----------------------------
    # Document 2: Extended
    # -----------------------------
    def generate_extended_documentation(self) -> tuple[str, str]:
        """Generate comprehensive powerbi_analysis_TIMESTAMP.md with charts and details."""
        doc: list[str] = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"powerbi_analysis_{timestamp}.md"

        doc.append("# Power BI Semantic Model - Comprehensive Analysis")
        doc.append(f"**Project:** {self.pbip_name}")
        doc.append(f"**Generated:** {datetime.now():%Y-%m-%d %H:%M:%S}")
        doc.append("")
        doc.append("---")
        doc.append("")

        # TOC
        doc.append("## Table of Contents")
        doc.append("1. [Executive Overview](#executive-overview)")
        doc.append("2. [Model Complexity Analysis](#model-complexity-analysis)")
        doc.append("3. [Tables Summary](#tables-summary)")
        doc.append("4. [Detailed Table Classifications](#detailed-table-classifications)")
        doc.append("5. [Relationships Analysis](#relationships-analysis)")
        doc.append("6. [Measures Overview](#measures-overview)")
        doc.append("7. [Columns Details](#columns-details)")
        doc.append("8. [Report Pages](#report-pages)")
        doc.append("9. [Data Quality](#data-quality)")
        doc.append("")

        # 1. EXECUTIVE OVERVIEW
        doc.append("---")
        doc.append("## Executive Overview")
        doc.append("")

        summary = self.analysis_data.get("summary", {}) if isinstance(self.analysis_data, dict) else {}
        rel_analysis = self.analysis_data.get("relationship_analysis", {}) if isinstance(self.analysis_data, dict) else {}

        doc.append("### Model Statistics")
        doc.append("")
        doc.append(f"- **Total Tables:** {summary.get('total_tables', len(self.tables_data))}")
        doc.append(f"- **Total Relationships:** {len(self.relationships_data)}")
        doc.append(f"- **Total Measures:** {summary.get('total_measures', len(self.measures_data))}")
        doc.append(f"- **Schema Type:** {rel_analysis.get('schema_type', 'N/A')}")
        doc.append(f"- **Compliance Score:** {rel_analysis.get('compliance_score', 0)}/100")
        doc.append(f"- **Report Pages:** {len(self.pages_data)}")
        doc.append("")

        doc.append("### Table Distribution")
        doc.append("")
        doc.append(f"- **Fact Tables:** {summary.get('fact_tables', 0)}")
        doc.append(f"- **Dimension Tables:** {summary.get('dimension_tables', 0)}")
        doc.append(f"- **Bridge Tables:** {summary.get('bridge_tables', 0)}")
        doc.append(f"- **Calculation Tables:** {summary.get('calculation_tables', 0)}")
        doc.append(f"- **Parameter Tables:** {summary.get('parameter_tables', 0)}")
        doc.append("")

        # 2. MODEL COMPLEXITY ANALYSIS
        doc.append("---")
        doc.append("## Model Complexity Analysis")
        doc.append("")
        doc.append("### Visual Representations")
        doc.append("")

        # IMPORTANT: md is in reports/, graphs are in ../graphs
        charts = [
            ("relationship_graph.png", "Relationship Diagram"),
            ("schema_type_donut.png", "Table Type Distribution"),
            ("complexity_heatmap.png", "Model Complexity Heatmap"),
            ("datatype_distribution.png", "Data Type Distribution"),
            ("measure_dependency.png", "Measure Dependencies"),
        ]

        for chart_file, chart_title in charts:
            chart_path = self.paths.graphs_dir / chart_file
            if chart_path.exists():
                doc.append(f"#### {chart_title}")
                doc.append(f"![{chart_title}](../graphs/{chart_file})")
                doc.append("")

        # 3. TABLES SUMMARY
        doc.append("---")
        doc.append("## Tables Summary")
        doc.append("")

        if self.tables_data:
            doc.append("| Table | Columns | Measures | Data Types |")
            doc.append("|-------|---------|----------|------------|")

            for table in sorted(self.tables_data, key=lambda x: x.get("name", "")):
                data_types = set()
                for col in table.get("columns", []) or []:
                    if not col.get("is_calculated", False):
                        data_types.add(col.get("dataType", "Unknown"))
                data_types_str = ", ".join(sorted(data_types)) if data_types else "N/A"

                doc.append(
                    f"| {table.get('name','Unknown')} | {table.get('column_count',0)} | "
                    f"{table.get('measure_count',0)} | {data_types_str} |"
                )
            doc.append("")

        # 4. DETAILED TABLE CLASSIFICATIONS
        doc.append("---")
        doc.append("## Detailed Table Classifications")
        doc.append("")

        classifications = self.analysis_data.get("table_classifications", []) if isinstance(self.analysis_data, dict) else []
        if classifications:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for cls in classifications:
                grouped.setdefault(cls.get("classification", "UNKNOWN"), []).append(cls)

            for table_type in ["FACT", "DIMENSION", "BRIDGE", "CALCULATION", "PARAMETER"]:
                if table_type in grouped:
                    tables_of_type = grouped[table_type]
                    doc.append(f"### {table_type} Tables ({len(tables_of_type)})")
                    doc.append("")
                    for table in sorted(tables_of_type, key=lambda x: x.get("table_name", "")):
                        doc.append(f"#### {table.get('table_name','Unknown')}")
                        doc.append(f"- **Classification:** {table.get('classification','UNKNOWN')}")
                        doc.append(f"- **Confidence:** {table.get('confidence','N/A')}")
                        doc.append(f"- **Reasoning:** {(table.get('reasoning','') or '').replace('|','\\|')}")
                        metadata = table.get("metadata", {}) or {}
                        doc.append(f"- **Columns:** {metadata.get('columns', 0)}")
                        doc.append(f"- **Numeric Columns:** {metadata.get('numeric_columns', 0)}")
                        doc.append(f"- **String Columns:** {metadata.get('string_columns', 0)}")
                        doc.append(f"- **Date Columns:** {metadata.get('date_columns', 0)}")
                        doc.append(f"- **Measures:** {metadata.get('measures', 0)}")
                        doc.append("")
        else:
            doc.append("No classifications found in analysis.json.")
            doc.append("")

        # 5. RELATIONSHIPS ANALYSIS
        doc.append("---")
        doc.append("## Relationships Analysis")
        doc.append("")

        if self.relationships_data:
            doc.append(f"**Total Relationships:** {len(self.relationships_data)}")
            doc.append("")
            doc.append("| From Table | From Column | To Table | To Column | Cardinality |")
            doc.append("|------------|------------|----------|-----------|-------------|")
            for rel in self.relationships_data:
                doc.append(
                    f"| {rel.get('from_table','')} | {rel.get('from_column','')} | "
                    f"{rel.get('to_table','')} | {rel.get('to_column','')} | {rel.get('cardinality','')} |"
                )
            doc.append("")
        else:
            doc.append("No relationships defined in the model.")
            doc.append("")

        # 6. MEASURES OVERVIEW
        doc.append("---")
        doc.append("## Measures Overview")
        doc.append("")
        if self.measures_data:
            measures_summary = self._get_summary(self.measures_raw)

            total_measures = measures_summary.get("total_measures", len(self.measures_data))
            avg_complexity = measures_summary.get("average_complexity_score")

            doc.append(f"**Total Measures:** {total_measures}")

            if avg_complexity is not None:
                doc.append(f"**Average Complexity Score:** {avg_complexity}/10")

            doc.append("")
            doc.append("| Table | Measure Name | Complexity | DAX Snippet |")
            doc.append("|-------|--------------|-----------|------------|")

            for measure in self.measures_data:
                table_name = self._escape_md_cell(measure.get("table", "Unknown"))
                measure_name = self._escape_md_cell(measure.get("name", "Unknown"))

                complexity = measure.get("complexity_score", measure.get("complexity", 0))
                complexity_level = measure.get("complexity_level", "")
                complexity_display = f"{complexity_level} {complexity}/10" if complexity_level else f"{complexity}/10"

                dax = (
                    measure.get("expression_preview")
                    or measure.get("expression", "")
                    or ""
                )
                dax = self._escape_md_cell(dax)
                dax_snippet = (dax[:80] + "...") if len(dax) > 80 else dax

                doc.append(f"| {table_name} | {measure_name} | {complexity_display} | {dax_snippet} |")

            doc.append("")
        else:
            doc.append("No measures defined in the model.")
            doc.append("")

        # 7. COLUMNS DETAILS
        doc.append("---")
        doc.append("## Columns Details")
        doc.append("")

        if self.tables_data:
            for table in sorted(self.tables_data, key=lambda x: x.get("name", "")):
                cols = table.get("columns", []) or []
                if not cols:
                    continue

                doc.append(f"### {table.get('name','Unknown')}")
                doc.append("")
                doc.append("| Column Name | Data Type | Calculated | Key |")
                doc.append("|------------|-----------|-----------|-----|")

                for col in cols:
                    col_name = col.get("name", "Unknown")
                    data_type = col.get("dataType", "Unknown")
                    is_calc = "✓" if col.get("is_calculated", False) else ""
                    is_key = "✓" if col.get("is_key", False) else ""
                    doc.append(f"| {col_name} | {data_type} | {is_calc} | {is_key} |")
                doc.append("")

        # 8. REPORT PAGES
        doc.append("---")
        doc.append("## Report Pages")
        doc.append("")

        if self.pages_data:
            pages_summary = self._get_summary(self.pages_raw)
            total_pages = pages_summary.get("total_pages", len(self.pages_data))
            total_visuals = pages_summary.get("total_visuals", sum(p.get("visuals_count", 0) for p in self.pages_data))

            doc.append(f"**Total Pages:** {total_pages}")
            doc.append(f"**Total Visuals:** {total_visuals}")
            doc.append("")
            doc.append("| Page Name | Visualizations | Charts | Tables | Slicers | Complexity |")
            doc.append("|-----------|-----------------|--------|--------|---------|------------|")
            for page in self.pages_data:
                doc.append(
                    f"| {self._escape_md_cell(page.get('display_name','Unknown'))} "
                    f"| {page.get('visuals_count',0)} "
                    f"| {page.get('chart_count',0)} "
                    f"| {page.get('table_count',0)} "
                    f"| {page.get('slicer_count',0)} "
                    f"| {self._escape_md_cell(page.get('page_complexity_level','N/A'))} |"
                )
            doc.append("")
        else:
            doc.append("No report pages found.")
            doc.append("")

        # 9. DATA QUALITY
        doc.append("---")
        doc.append("## Data Quality")
        doc.append("")

        doc.append(f"- **Schema Compliance Score:** {rel_analysis.get('compliance_score', 0)}/100")
        doc.append(f"- **Schema Type:** {rel_analysis.get('schema_type', 'N/A')}")
        isolated_tables = rel_analysis.get("isolated_tables", [])
        if isinstance(isolated_tables, list):
            orphaned_count = len(isolated_tables)
        else:
            orphaned_count = rel_analysis.get("orphaned_tables", 0)

        doc.append(f"- **Orphaned / Isolated Tables:** {orphaned_count}")
        analysis_issues = rel_analysis.get("issues", [])
        analysis_recommendations = rel_analysis.get("recommendations", [])

        if analysis_issues:
            doc.append("")
            doc.append("### Detected Issues")
            doc.append("")
            for issue in analysis_issues:
                doc.append(f"- {issue}")

        if analysis_recommendations:
            doc.append("")
            doc.append("### Recommendations")
            doc.append("")
            for recommendation in analysis_recommendations:
                doc.append(f"- {recommendation}")
        doc.append("")
        doc.append("---")
        doc.append("*End of Report*")

        return "\n".join(doc), filename