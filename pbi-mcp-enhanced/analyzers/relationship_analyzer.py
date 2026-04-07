"""
Relationship Analyzer
Analyzes relationships between tables
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from parsers.model_bim_parser import Relationship, ModelBIM


@dataclass
class RelationshipAnalysis:
    """Analysis results for a single relationship"""
    name: Optional[str]
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cross_filtering: str
    is_active: bool
    cardinality: Optional[str]
    relationship_type: str  # 'one-to-many', 'many-to-one', 'one-to-one', 'many-to-many'


@dataclass
class RelationshipStatistics:
    """Statistics about relationships in the model"""
    total_relationships: int
    active_relationships: int
    inactive_relationships: int
    bidirectional_relationships: int
    one_to_many_count: int
    many_to_many_count: int
    tables_with_most_relationships: List[Tuple[str, int]]
    hub_tables: List[str]  # Tables with many connections
    isolated_tables: List[str]  # Tables with no relationships


class RelationshipAnalyzer:
    """
    Analyzes relationships in a Power BI model
    """
    
    def __init__(self, model: ModelBIM):
        """
        Initialize the relationship analyzer
        
        Args:
            model: Parsed ModelBIM object
        """
        self.model = model
        self.analyses: List[RelationshipAnalysis] = []
        self.statistics: Optional[RelationshipStatistics] = None
        self.table_connections: Dict[str, int] = {}
    
    def analyze(self) -> List[RelationshipAnalysis]:
        """
        Analyze all relationships in the model
        
        Returns:
            List of RelationshipAnalysis objects
        """
        self.analyses = []
        
        for rel in self.model.relationships:
            analysis = self._analyze_relationship(rel)
            self.analyses.append(analysis)
        
        # Calculate statistics
        self._calculate_statistics()
        
        return self.analyses
    
    def _analyze_relationship(self, rel: Relationship) -> RelationshipAnalysis:
        """
        Analyze a single relationship
        
        Args:
            rel: Relationship object to analyze
        
        Returns:
            RelationshipAnalysis object
        """
        # Determine relationship type based on cardinality
        rel_type = self._determine_relationship_type(rel)
        
        return RelationshipAnalysis(
            name=rel.name,
            from_table=rel.from_table,
            from_column=rel.from_column,
            to_table=rel.to_table,
            to_column=rel.to_column,
            cross_filtering=rel.cross_filtering_behavior,
            is_active=rel.is_active,
            cardinality=rel.cardinality,
            relationship_type=rel_type
        )
    
    def _determine_relationship_type(self, rel: Relationship) -> str:
        """Determine the type of relationship"""
        # This is a simplified version
        # In real model.bim, cardinality is more complex
        
        if rel.cardinality:
            if 'many' in rel.cardinality.lower():
                return 'many-to-many'
            elif 'one' in rel.cardinality.lower():
                return 'one-to-one'
        
        # Default assumption based on Power BI conventions
        # From table is typically the "many" side
        return 'many-to-one'
    
    def _calculate_statistics(self):
        """Calculate statistics about relationships"""
        if not self.model.tables:
            return
        
        # Count connections per table
        connections = defaultdict(int)
        for rel in self.analyses:
            connections[rel.from_table] += 1
            connections[rel.to_table] += 1
        
        self.table_connections = dict(connections)
        
        # Find hub tables (tables with many connections)
        sorted_connections = sorted(
            connections.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        hub_tables = [
            table for table, count in sorted_connections 
            if count >= 3  # Tables with 3+ connections
        ]
        
        # Find isolated tables (no relationships)
        all_tables = {table.name for table in self.model.tables}
        connected_tables = set(connections.keys())
        isolated_tables = list(all_tables - connected_tables)
        
        # Counts
        bidirectional = sum(
            1 for a in self.analyses 
            if 'both' in a.cross_filtering.lower()
        )
        
        one_to_many = sum(
            1 for a in self.analyses 
            if a.relationship_type in ['one-to-many', 'many-to-one']
        )
        
        many_to_many = sum(
            1 for a in self.analyses 
            if a.relationship_type == 'many-to-many'
        )
        
        self.statistics = RelationshipStatistics(
            total_relationships=len(self.analyses),
            active_relationships=sum(1 for a in self.analyses if a.is_active),
            inactive_relationships=sum(1 for a in self.analyses if not a.is_active),
            bidirectional_relationships=bidirectional,
            one_to_many_count=one_to_many,
            many_to_many_count=many_to_many,
            tables_with_most_relationships=sorted_connections[:10],
            hub_tables=hub_tables,
            isolated_tables=isolated_tables
        )
    
    def get_relationships_for_table(self, table_name: str) -> List[RelationshipAnalysis]:
        """Get all relationships involving a specific table"""
        return [
            a for a in self.analyses 
            if a.from_table == table_name or a.to_table == table_name
        ]
    
    def get_bidirectional_relationships(self) -> List[RelationshipAnalysis]:
        """Get all bidirectional relationships"""
        return [
            a for a in self.analyses 
            if 'both' in a.cross_filtering.lower()
        ]
    
    def get_inactive_relationships(self) -> List[RelationshipAnalysis]:
        """Get all inactive relationships"""
        return [a for a in self.analyses if not a.is_active]
    
    def get_hub_tables(self) -> List[str]:
        """Get tables that are connection hubs"""
        if self.statistics:
            return self.statistics.hub_tables
        return []
    
    def get_isolated_tables(self) -> List[str]:
        """Get tables with no relationships"""
        if self.statistics:
            return self.statistics.isolated_tables
        return []
    
    def get_statistics(self) -> Optional[RelationshipStatistics]:
        """Get relationship statistics"""
        return self.statistics
    
    def build_graph_data(self) -> Dict[str, List[str]]:
        """
        Build graph data for visualization
        
        Returns:
            Dictionary mapping table to list of connected tables
        """
        graph = defaultdict(list)
        
        for rel in self.analyses:
            graph[rel.from_table].append(rel.to_table)
            graph[rel.to_table].append(rel.from_table)
        
        return dict(graph)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"RelationshipAnalyzer(relationships={len(self.analyses)})"
