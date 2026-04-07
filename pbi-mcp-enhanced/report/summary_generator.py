"""
Executive Summary Generator
Creates the executive summary section of the report
"""

from typing import Dict, Any
from utils import ModelSummary, DAXComplexityStats, DataTypeStats, GraphMetrics


class ExecutiveSummaryGenerator:
    """
    Generates executive summary section
    """
    
    def __init__(self, summary: ModelSummary, dax_stats: DAXComplexityStats,
                 data_type_stats: DataTypeStats, graph_metrics: GraphMetrics):
        """
        Initialize summary generator
        
        Args:
            summary: Model summary statistics
            dax_stats: DAX complexity statistics
            data_type_stats: Data type statistics
            graph_metrics: Graph metrics
        """
        self.summary = summary
        self.dax_stats = dax_stats
        self.data_type_stats = data_type_stats
        self.graph_metrics = graph_metrics
    
    def generate(self) -> str:
        """
        Generate executive summary
        
        Returns:
            Markdown string for summary
        """
        sections = []
        
        # Title
        sections.append("## Executive Summary\n")
        
        # Overview
        sections.append(self._generate_overview())
        
        # Key metrics table
        sections.append(self._generate_key_metrics())
        
        # Insights
        sections.append(self._generate_insights())
        
        return "\n".join(sections)
    
    def _generate_overview(self) -> str:
        """Generate overview paragraph"""
        overview = [
            "### Overview\n",
            f"This Power BI semantic model contains **{self.summary.total_tables} tables** ",
            f"with **{self.summary.total_columns} columns** and **{self.summary.total_measures} measures**. ",
            f"The model has **{self.summary.total_relationships} relationships** connecting the tables",
        ]
        
        if self.summary.has_security:
            overview.append(f" and **{self.summary.total_roles} security roles** implementing row-level security")
        
        overview.append(".\n")
        
        return "".join(overview)
    
    def _generate_key_metrics(self) -> str:
        """Generate key metrics table"""
        metrics = [
            "### Key Metrics\n",
            "| Category | Metric | Value |",
            "|----------|--------|-------|",
            "| **Tables** | Total Tables | " + str(self.summary.total_tables) + " |",
            "| | Fact Tables | " + str(self.summary.fact_tables) + " |",
            "| | Dimension Tables | " + str(self.summary.dimension_tables) + " |",
            "| | Calculated Tables | " + str(self.summary.calculated_tables) + " |",
            "| **Columns** | Total Columns | " + str(self.summary.total_columns) + " |",
            "| | Calculated Columns | " + str(self.summary.calculated_columns) + " |",
            "| | Avg Columns/Table | " + str(self.summary.avg_columns_per_table) + " |",
            "| **Measures** | Total Measures | " + str(self.summary.total_measures) + " |",
            "| | Avg Complexity Score | " + str(self.dax_stats.avg_complexity_score) + " |",
            "| | Measures with Dependencies | " + str(self.dax_stats.measures_with_dependencies) + " |",
            "| **Relationships** | Total Relationships | " + str(self.summary.total_relationships) + " |",
            "| | Active Relationships | " + str(self.summary.active_relationships) + " |",
            "| | Bidirectional | " + str(self.summary.bidirectional_relationships) + " |",
            "| **Graph Structure** | Connected Components | " + str(self.graph_metrics.connected_components) + " |",
            "| | Graph Density | " + str(self.graph_metrics.graph_density) + " |",
            "| | Isolated Tables | " + str(self.graph_metrics.isolated_nodes) + " |",
            ""
        ]
        
        return "\n".join(metrics)
    
    def _generate_insights(self) -> str:
        """Generate key insights"""
        insights = []
        
        insights.append("### Key Insights\n")
        
        # Model composition
        if self.summary.fact_tables > 0 and self.summary.dimension_tables > 0:
            ratio = round(self.summary.dimension_tables / self.summary.fact_tables, 1)
            insights.append(f"- **Model Composition**: {self.summary.fact_tables} fact table(s) and {self.summary.dimension_tables} dimension table(s) (ratio 1:{ratio})")
        
        # Data types
        if self.data_type_stats.most_common_type:
            insights.append(f"- **Most Common Data Type**: {self.data_type_stats.most_common_type} ({self.data_type_stats.most_common_count} columns, {self.data_type_stats.data_type_percentages.get(self.data_type_stats.most_common_type, 0)}%)")
        
        # DAX complexity
        if self.dax_stats.complex_measures > 0:
            insights.append(f"- **DAX Complexity**: {self.dax_stats.complex_measures} complex measures (score > 30), {self.dax_stats.simple_measures} simple measures")
        
        # Most used DAX function
        if self.dax_stats.most_common_functions:
            top_func = self.dax_stats.most_common_functions[0]
            insights.append(f"- **Most Used DAX Function**: {top_func[0]} (used {top_func[1]} times)")
        
        # Graph connectivity
        if self.graph_metrics.isolated_nodes > 0:
            insights.append(f"- ⚠️ **Warning**: {self.graph_metrics.isolated_nodes} table(s) are not connected to any other tables")
        
        if self.graph_metrics.connected_components > 1:
            insights.append(f"- ⚠️ **Warning**: Model has {self.graph_metrics.connected_components} disconnected components")
        
        # Security
        if self.summary.has_security:
            insights.append(f"- **Security**: Row-level security is implemented with {self.summary.roles_with_rls} active role(s)")
        else:
            insights.append("- ℹ️ **Info**: No row-level security roles defined")
        
        insights.append("")
        
        return "\n".join(insights)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ExecutiveSummaryGenerator(tables={self.summary.total_tables})"
