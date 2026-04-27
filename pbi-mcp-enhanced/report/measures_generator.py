"""
Measures Section Generator
Creates measures analysis section of the report
"""

from typing import List
from analyzers import MeasureAnalyzer
from utils import DAXComplexityStats


class MeasuresSectionGenerator:
    """
    Generates measures analysis section
    """
    
    def __init__(self, measure_analyzer: MeasureAnalyzer, dax_stats: DAXComplexityStats):
        """
        Initialize generator
        
        Args:
            measure_analyzer: Analyzed measure data
            dax_stats: DAX complexity statistics
        """
        self.measure_analyzer = measure_analyzer
        self.dax_stats = dax_stats
    
    def generate(self, dependency_image_path: str = None) -> str:
        """
        Generate measures section
        
        Args:
            dependency_image_path: Path to dependency graph (relative for Markdown)
        
        Returns:
            Markdown string
        """
        sections = []
        
        # Title
        sections.append("## Measures Analysis\n")
        
        # Summary
        sections.append(self._generate_summary())
        
        # DAX complexity stats
        sections.append(self._generate_complexity_stats())
        
        # Dependency graph
        if dependency_image_path:
            sections.append(f"### Measure Dependencies\n")
            sections.append(f"![Measure Dependencies]({dependency_image_path})\n")
        
        # Most complex measures
        sections.append(self._generate_complex_measures())
        
        # Most used functions
        sections.append(self._generate_function_usage())
        
        # All measures (collapsible)
        sections.append(self._generate_all_measures())
        
        return "\n".join(sections)
    
    def _generate_summary(self) -> str:
        """Generate summary"""
        total = len(self.measure_analyzer.analyses)
        
        text = [
            f"The model contains **{total} measures** with varying levels of complexity.\n"
        ]
        
        return "\n".join(text)
    
    def _generate_complexity_stats(self) -> str:
        """Generate complexity statistics"""
        stats = self.dax_stats
        
        lines = [
            "### DAX Complexity Statistics\n",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Total Measures** | {len(self.measure_analyzer.analyses)} |",
            f"| **Average Complexity Score** | {stats.avg_complexity_score:.2f} |",
            f"| **Average Expression Length** | {stats.avg_expression_length:.0f} characters |",
            f"| **Average Nesting Level** | {stats.avg_nesting_level:.1f} |",
            f"| **Measures with Dependencies** | {stats.measures_with_dependencies} |",
            "",
            "**Complexity Distribution:**",
            f"- Simple (score < 10): {stats.simple_measures} measures",
            f"- Moderate (score 10-30): {stats.moderate_measures} measures",
            f"- Complex (score > 30): {stats.complex_measures} measures",
            ""
        ]
        
        return "\n".join(lines)
    
    def _generate_complex_measures(self) -> str:
        """Generate most complex measures"""
        complex_measures = self.dax_stats.top_complex_measures[:10]
        
        if not complex_measures:
            return ""
        
        lines = [
            "### Top 10 Most Complex Measures\n",
            "| Rank | Measure | Table | Complexity | Expression Length | Functions |",
            "|------|---------|-------|------------|-------------------|-----------|"
        ]
        
        for i, measure in enumerate(complex_measures, 1):
            lines.append(
                f"| {i} | {measure['name']} | {measure['table']} | "
                f"{measure['complexity']:.1f} | {measure['length']} | {measure['functions']} |"
            )
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_function_usage(self) -> str:
        """Generate function usage statistics"""
        functions = self.dax_stats.most_common_functions[:15]
        
        if not functions:
            return ""
        
        lines = [
            "### Most Used DAX Functions\n",
            "| Function | Usage Count |",
            "|----------|-------------|"
        ]
        
        for func, count in functions:
            lines.append(f"| {func} | {count} |")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_all_measures(self) -> str:
        """Generate all measures list (collapsible)"""
        measures = sorted(
            self.measure_analyzer.analyses,
            key=lambda m: m.complexity_score,
            reverse=True
        )
        
        lines = [
            "### All Measures (Detailed)\n",
            "<details>",
            "<summary>Click to expand full measures list</summary>\n"
        ]
        
        for measure in measures:
            # Add placeholder label if needed
            measure_label = measure.name
            if measure.is_placeholder:
                measure_label = f"{measure.name} ⚠️ Sin implementar"
            
            lines.append(f"#### {measure_label}")
            lines.append(f"- **Table**: {measure.table}")
            lines.append(f"- **Complexity Score**: {measure.complexity_score:.2f}")
            lines.append(f"- **Expression Length**: {measure.expression_length} characters")
            lines.append(f"- **Nesting Level**: {measure.nesting_level}")
            
            if measure.dax_functions:
                funcs = ", ".join(measure.dax_functions[:5])
                if len(measure.dax_functions) > 5:
                    funcs += f" (+{len(measure.dax_functions) - 5} more)"
                lines.append(f"- **Functions Used**: {funcs}")
            
            if measure.referenced_measures:
                refs = ", ".join(measure.referenced_measures[:3])
                if len(measure.referenced_measures) > 3:
                    refs += f" (+{len(measure.referenced_measures) - 3} more)"
                lines.append(f"- **Dependencies**: {refs}")
            
            # Show placeholder message or truncated expression
            if measure.is_placeholder:
                lines.append(f"- **Expression**: *{measure.name} no tiene expresión DAX implementada*")
            else:
                expr = measure.expression[:200]
                if len(measure.expression) > 200:
                    expr += "..."
                lines.append(f"- **Expression**: `{expr}`")
            
            lines.append("")
        
        lines.append("</details>\n")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"MeasuresSectionGenerator(measures={len(self.measure_analyzer.analyses)})"
