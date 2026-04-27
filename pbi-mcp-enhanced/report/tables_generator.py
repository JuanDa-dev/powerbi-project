"""
Tables Section Generator
Creates detailed tables section of the report
"""

from typing import Dict, List
from analyzers import TableAnalyzer, TableAnalysis


class TablesSectionGenerator:
    """
    Generates tables analysis section
    """
    
    def __init__(self, table_analyzer: TableAnalyzer):
        """
        Initialize generator
        
        Args:
            table_analyzer: Analyzed table data
        """
        self.table_analyzer = table_analyzer
    
    def generate(self, image_path: str = None) -> str:
        """
        Generate tables section
        
        Args:
            image_path: Path to table complexity chart (relative for Markdown)
        
        Returns:
            Markdown string
        """
        sections = []
        
        # Title
        sections.append("## Tables Analysis\n")
        
        # Summary
        sections.append(self._generate_summary())
        
        # Chart
        if image_path:
            sections.append(f"### Table Complexity Visualization\n")
            sections.append(f"![Table Complexity]({image_path})\n")
        
        # Tables by type
        sections.append(self._generate_fact_tables())
        sections.append(self._generate_dimension_tables())
        sections.append(self._generate_calculation_tables())  # BUG FIX #3
        sections.append(self._generate_parameter_tables())     # BUG FIX #4
        
        # Detailed table list
        sections.append(self._generate_detailed_list())
        
        return "\n".join(sections)
    
    def _generate_summary(self) -> str:
        """Generate summary paragraph"""
        summary = self.table_analyzer.get_summary()
        
        text = [
            f"The model contains **{summary['total']} tables** classified as follows:\n",
            f"- **{summary['fact']} Fact Table(s)**: Transactional/event tables containing measures",
            f"- **{summary['dimension']} Dimension Table(s)**: Descriptive/reference tables",
            f"- **{summary['calculation']} Calculation Table(s)**: DAX measure containers",
            f"- **{summary['parameter']} Parameter Table(s)**: Filter and selector controls",
            f"- **{summary['calculated']} Calculated Table(s)**: Created via DAX expressions",
            f"- **{summary['unknown']} Unclassified Table(s)**: Could not be confidently classified",
        ]
        
        if summary['hidden'] > 0:
            text.append(f"- **{summary['hidden']} Hidden Table(s)**: Not visible in report view")
        
        text.append("")
        
        return "\n".join(text)
    
    def _generate_fact_tables(self) -> str:
        """Generate fact tables section"""
        fact_tables = self.table_analyzer.get_fact_tables()
        
        if not fact_tables:
            return ""
        
        lines = [
            "### Fact Tables\n",
            "| Table Name | Columns | Measures | Relationships | Confidence |",
            "|------------|---------|----------|---------------|------------|"
        ]
        
        for table in sorted(fact_tables, key=lambda t: t.measure_count, reverse=True):
            confidence_pct = int(table.confidence * 100)
            lines.append(
                f"| {table.name} | {table.column_count} | "
                f"{table.measure_count} | {table.relationship_count} | {confidence_pct}% |"
            )
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_dimension_tables(self) -> str:
        """Generate dimension tables section"""
        dim_tables = self.table_analyzer.get_dimension_tables()
        
        if not dim_tables:
            return ""
        
        lines = [
            "### Dimension Tables\n",
            "| Table Name | Columns | Hierarchies | Relationships | Confidence |",
            "|------------|---------|-------------|---------------|------------|"
        ]
        
        for table in sorted(dim_tables, key=lambda t: t.column_count, reverse=True):
            confidence_pct = int(table.confidence * 100)
            lines.append(
                f"| {table.name} | {table.column_count} | "
                f"{table.hierarchy_count} | {table.relationship_count} | {confidence_pct}% |"
            )
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_calculation_tables(self) -> str:
        """BUG FIX #3: Generate calculation tables section"""
        calc_tables = self.table_analyzer.get_calculation_tables()
        
        if not calc_tables:
            return ""
        
        lines = [
            "### Calculation Tables\n",
            "| Table Name | Columns | Measures | Description |",
            "|------------|---------|----------|-------------|"
        ]
        
        for table in sorted(calc_tables, key=lambda t: t.measure_count, reverse=True):
            description = "DAX measure container" if table.measure_count > 0 else "Empty measure table"
            lines.append(
                f"| {table.name} | {table.column_count} | "
                f"{table.measure_count} | {description} |"
            )
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_parameter_tables(self) -> str:
        """BUG FIX #4: Generate parameter tables section"""
        param_tables = self.table_analyzer.get_parameter_tables()
        
        if not param_tables:
            return ""
        
        lines = [
            "### 🎛️ Parameter Tables\n",
            "Tables de parámetros para control de filtros y selectores dinámicos en visuals.\n",
            "| Table Name | Columns | Description |",
            "|------------|---------|-------------|"
        ]
        
        for table in sorted(param_tables, key=lambda t: t.name):
            description = "Parameter selector" if table.column_count == 0 else f"Parameter table ({table.column_count} cols)"
            lines.append(
                f"| {table.name} | {table.column_count} | {description} |"
            )
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_detailed_list(self) -> str:
        """Generate detailed table list"""
        lines = [
            "### All Tables (Detailed)\n",
            "<details>",
            "<summary>Click to expand full table details</summary>\n"
        ]
        
        for table_name, analysis in sorted(self.table_analyzer.analyses.items()):
            lines.append(f"#### {table_name}")
            lines.append("")
            lines.append(f"- **Type**: {analysis.table_type.title()}")
            lines.append(f"- **Columns**: {analysis.column_count}")
            lines.append(f"- **Measures**: {analysis.measure_count}")
            lines.append(f"- **Hierarchies**: {analysis.hierarchy_count}")
            lines.append(f"- **Relationships**: {analysis.relationship_count}")
            lines.append(f"- **Hidden**: {'Yes' if analysis.is_hidden else 'No'}")
            lines.append(f"- **Calculated**: {'Yes' if analysis.is_calculated else 'No'}")
            
            if analysis.reasons:
                lines.append(f"- **Classification Reasons**:")
                for reason in analysis.reasons:
                    lines.append(f"  - {reason}")
            
            lines.append("")
        
        lines.append("</details>\n")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"TablesSectionGenerator(tables={len(self.table_analyzer.analyses)})"
