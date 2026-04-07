"""
Recommendations Generator
Creates best practices recommendations section
"""

from typing import List, Dict
from utils import ModelSummary, GraphMetrics, DAXComplexityStats
from analyzers import TableAnalyzer, RelationshipAnalyzer


class RecommendationsGenerator:
    """
    Generates recommendations section based on analysis
    """
    
    def __init__(self, summary: ModelSummary, graph_metrics: GraphMetrics,
                 dax_stats: DAXComplexityStats, table_analyzer: TableAnalyzer,
                 relationship_analyzer: RelationshipAnalyzer):
        """
        Initialize generator
        
        Args:
            summary: Model summary
            graph_metrics: Graph metrics
            dax_stats: DAX complexity stats
            table_analyzer: Table analyzer
            relationship_analyzer: Relationship analyzer
        """
        self.summary = summary
        self.graph_metrics = graph_metrics
        self.dax_stats = dax_stats
        self.table_analyzer = table_analyzer
        self.relationship_analyzer = relationship_analyzer
    
    def generate(self) -> str:
        """
        Generate recommendations section
        
        Returns:
            Markdown string
        """
        sections = []
        
        # Title
        sections.append("## Recommendations\n")
        
        # Collect recommendations
        recommendations = self._collect_recommendations()
        
        if not recommendations:
            sections.append("✅ **Great work!** No major issues detected in this model.\n")
            return "\n".join(sections)
        
        # Group by priority
        critical = [r for r in recommendations if r['priority'] == 'critical']
        warnings = [r for r in recommendations if r['priority'] == 'warning']
        suggestions = [r for r in recommendations if r['priority'] == 'suggestion']
        
        if critical:
            sections.append(self._format_priority_section("🔴 Critical Issues", critical))
        
        if warnings:
            sections.append(self._format_priority_section("⚠️ Warnings", warnings))
        
        if suggestions:
            sections.append(self._format_priority_section("💡 Suggestions", suggestions))
        
        return "\n".join(sections)
    
    def _collect_recommendations(self) -> List[Dict]:
        """Collect all recommendations"""
        recommendations = []
        
        # Check isolated tables
        isolated = self.relationship_analyzer.get_isolated_tables()
        if isolated:
            recommendations.append({
                'priority': 'warning',
                'title': 'Isolated Tables Detected',
                'description': f"{len(isolated)} table(s) have no relationships: {', '.join(isolated[:5])}",
                'action': "Review if these tables should be connected or removed from the model."
            })
        
        # Check disconnected components
        if self.graph_metrics.connected_components > 1:
            recommendations.append({
                'priority': 'critical',
                'title': 'Disconnected Model Components',
                'description': f"The model has {self.graph_metrics.connected_components} separate disconnected groups of tables.",
                'action': "Add relationships to connect all tables into a single model."
            })
        
        # Check bidirectional relationships
        if self.summary.bidirectional_relationships > 0:
            recommendations.append({
                'priority': 'warning',
                'title': 'Bidirectional Cross-Filter Relationships',
                'description': f"{self.summary.bidirectional_relationships} relationship(s) use bidirectional filtering.",
                'action': "Review if bidirectional filtering is necessary. It can cause performance issues and ambiguous filter context."
            })
        
        # Check complex DAX measures
        if self.dax_stats.complex_measures > self.summary.total_measures * 0.3:
            recommendations.append({
                'priority': 'suggestion',
                'title': 'High DAX Complexity',
                'description': f"{self.dax_stats.complex_measures} measures have high complexity (>30 score).",
                'action': "Consider breaking down complex measures into intermediate calculations for better maintainability."
            })
        
        # Check measures with many dependencies
        high_dep = [m for m in self.dax_stats.top_complex_measures if m.get('dependencies', 0) > 5]
        if high_dep:
            recommendations.append({
                'priority': 'suggestion',
                'title': 'Highly Dependent Measures',
                'description': f"{len(high_dep)} measure(s) depend on more than 5 other measures.",
                'action': "Review dependency chains to avoid circular references and improve calculation performance."
            })
        
        # Check if no fact tables detected
        if self.summary.fact_tables == 0 and self.summary.total_tables > 1:
            recommendations.append({
                'priority': 'warning',
                'title': 'No Fact Tables Detected',
                'description': "No tables were classified as fact tables.",
                'action': "Verify that transactional/event tables contain measures and are properly configured."
            })
        
        # Check security
        if not self.summary.has_security and self.summary.total_tables > 3:
            recommendations.append({
                'priority': 'suggestion',
                'title': 'No Row-Level Security',
                'description': "No security roles are defined in the model.",
                'action': "Consider implementing row-level security (RLS) if data access needs to be restricted by user."
            })
        
        # Check many-to-many relationships
        many_to_many = [r for r in self.relationship_analyzer.analyses if 'Many' in r.cardinality and r.cardinality.count('Many') == 2]
        if many_to_many:
            recommendations.append({
                'priority': 'warning',
                'title': 'Many-to-Many Relationships',
                'description': f"{len(many_to_many)} many-to-many relationship(s) detected.",
                'action': "Review if bridge tables can be used instead for better performance."
            })
        
        # Check calculated columns vs measures
        if self.summary.calculated_columns > self.summary.total_measures:
            recommendations.append({
                'priority': 'suggestion',
                'title': 'High Calculated Column Count',
                'description': f"{self.summary.calculated_columns} calculated columns vs {self.summary.total_measures} measures.",
                'action': "Consider converting calculated columns to measures when possible for better compression and performance."
            })
        
        return recommendations
    
    def _format_priority_section(self, title: str, items: List[Dict]) -> str:
        """Format a priority section"""
        lines = [f"### {title}\n"]
        
        for i, item in enumerate(items, 1):
            lines.append(f"#### {i}. {item['title']}")
            lines.append(f"**Issue**: {item['description']}\n")
            lines.append(f"**Action**: {item['action']}\n")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """String representation"""
        return "RecommendationsGenerator()"
