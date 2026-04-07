"""
Relationships Section Generator
Creates relationships analysis section of the report
"""

from typing import List
from analyzers import RelationshipAnalyzer
from utils import GraphMetrics


class RelationshipsSectionGenerator:
    """
    Generates relationships analysis section
    """
    
    def __init__(self, relationship_analyzer: RelationshipAnalyzer, graph_metrics: GraphMetrics):
        """
        Initialize generator
        
        Args:
            relationship_analyzer: Analyzed relationship data
            graph_metrics: Graph metrics
        """
        self.relationship_analyzer = relationship_analyzer
        self.graph_metrics = graph_metrics
    
    def generate(self, diagram_path: str = None) -> str:
        """
        Generate relationships section
        
        Args:
            diagram_path: Path to relationship diagram (relative for Markdown)
        
        Returns:
            Markdown string
        """
        sections = []
        
        # Title
        sections.append("## Relationships Analysis\n")
        
        # Summary
        sections.append(self._generate_summary())
        
        # Diagram
        if diagram_path:
            sections.append(f"### Data Model Diagram\n")
            sections.append(f"![Data Model]({diagram_path})\n")
        
        # Graph metrics
        sections.append(self._generate_graph_metrics())
        
        # Hub tables
        sections.append(self._generate_hub_tables())
        
        # Isolated tables
        sections.append(self._generate_isolated_tables())
        
        # All relationships
        sections.append(self._generate_all_relationships())
        
        return "\n".join(sections)
    
    def _generate_summary(self) -> str:
        """Generate summary"""
        # Build summary from analyzer analyses
        analyses = self.relationship_analyzer.analyses
        total = len(analyses)
        active = sum(1 for r in analyses if r.is_active)
        inactive = total - active
        bidirectional = sum(1 for r in analyses if hasattr(r, 'cross_filtering') and r.cross_filtering == 'Both')
        
        # Count cardinalities
        one_to_many = sum(1 for r in analyses if r.cardinality == 'One-to-Many')
        many_to_one = sum(1 for r in analyses if r.cardinality == 'Many-to-One')
        one_to_one = sum(1 for r in analyses if r.cardinality == 'One-to-One')
        many_to_many = sum(1 for r in analyses if r.cardinality == 'Many-to-Many')
        
        # Count unique tables
        tables = set()
        for r in analyses:
            tables.add(r.from_table)
            tables.add(r.to_table)
        
        text = [
            f"The model contains **{total} relationships** connecting {len(tables)} tables.\n",
            f"- **Active Relationships**: {active}",
            f"- **Inactive Relationships**: {inactive}",
            f"- **Bidirectional Cross-Filter**: {bidirectional}",
            f"- **One-to-Many**: {one_to_many}",
            f"- **Many-to-One**: {many_to_one}",
            f"- **One-to-One**: {one_to_one}",
            f"- **Many-to-Many**: {many_to_many}",
            ""
        ]
        
        return "\n".join(text)
    
    def _generate_graph_metrics(self) -> str:
        """Generate graph metrics"""
        metrics = self.graph_metrics
        
        lines = [
            "### Graph Structure Metrics\n",
            "| Metric | Value | Interpretation |",
            "|--------|-------|----------------|",
            f"| **Connected Components** | {metrics.connected_components} | {'✅ Single connected model' if metrics.connected_components == 1 else '⚠️ Disconnected tables exist'} |",
            f"| **Graph Density** | {metrics.graph_density:.3f} | {'Sparse' if metrics.graph_density < 0.1 else 'Moderate' if metrics.graph_density < 0.3 else 'Dense'} model |",
            f"| **Average Degree** | {metrics.avg_degree:.2f} | Avg connections per table |",
            f"| **Max Degree** | {metrics.max_degree} | Most connected table |",
            f"| **Isolated Nodes** | {metrics.isolated_nodes} | Tables with no relationships |",
            ""
        ]
        
        if metrics.normalization_score > 0:
            lines.append(f"**Normalization Score**: {metrics.normalization_score:.1f}% (Higher is better - indicates proper star schema)")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_hub_tables(self) -> str:
        """Generate hub tables (most connected)"""
        metrics = self.graph_metrics
        hub_tables = metrics.hub_tables[:10] if metrics.hub_tables else []
        
        if not hub_tables:
            return ""
        
        lines = [
            "### Hub Tables (Most Connected)\n",
            "| Table | Connections |",
            "|-------|-------------|"
        ]
        
        for table_name in hub_tables:
            # Count connections
            connections = sum(1 for r in self.relationship_analyzer.analyses 
                            if r.from_table == table_name or r.to_table == table_name)
            lines.append(f"| {table_name} | {connections} |")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_isolated_tables(self) -> str:
        """Generate isolated tables warning"""
        metrics = self.graph_metrics
        isolated = metrics.isolated_tables if hasattr(metrics, 'isolated_tables') else []
        
        if not isolated:
            return ""
        
        lines = [
            "### ⚠️ Isolated Tables (No Relationships)\n",
            "The following tables are not connected to any other tables:\n"
        ]
        
        for table in isolated:
            lines.append(f"- {table}")
        
        lines.append("\n> **Note**: Isolated tables may indicate missing relationships or standalone reference tables.\n")
        
        return "\n".join(lines)
    
    def _generate_all_relationships(self) -> str:
        """Generate all relationships list"""
        relationships = self.relationship_analyzer.analyses
        
        lines = [
            "### All Relationships (Detailed)\n",
            "<details>",
            "<summary>Click to expand full relationships list</summary>\n",
            "| From Table | From Column | To Table | To Column | Cardinality | Active | Cross Filter |",
            "|------------|-------------|----------|-----------|-------------|--------|--------------|"
        ]
        
        for rel in sorted(relationships, key=lambda r: r.from_table):
            active = "✅" if rel.is_active else "❌"
            lines.append(
                f"| {rel.from_table} | {rel.from_column} | {rel.to_table} | "
                f"{rel.to_column} | {rel.cardinality} | {active} | {rel.cross_filtering} |"
            )
        
        lines.append("")
        lines.append("</details>\n")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"RelationshipsSectionGenerator(relationships={len(self.relationship_analyzer.analyses)})"
