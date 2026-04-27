"""
Relationship Graph Metrics
Analyzes the relationship graph structure
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from analyzers import RelationshipAnalyzer, TableAnalyzer


@dataclass
class GraphMetrics:
    """Metrics about the relationship graph"""
    # Basic metrics
    total_nodes: int = 0  # Tables
    total_edges: int = 0  # Relationships
    
    # Connectivity
    connected_components: int = 0
    largest_component_size: int = 0
    isolated_nodes: int = 0
    
    # Degree metrics
    avg_degree: float = 0.0  # Average connections per table
    max_degree: int = 0
    min_degree: int = 0
    
    # Hub tables (highly connected)
    hub_tables: List[Tuple[str, int]] = field(default_factory=list)  # (table, degree)
    
    # Specific table roles
    fact_table_avg_connections: float = 0.0
    dimension_table_avg_connections: float = 0.0
    
    # Graph density
    graph_density: float = 0.0  # Actual edges / possible edges
    
    # Centrality (simplified)
    most_central_tables: List[Tuple[str, int]] = field(default_factory=list)
    
    # Normalization estimate
    normalization_score: float = 0.0  # Higher = more normalized
    
    # Relationship types
    one_to_many_ratio: float = 0.0
    many_to_many_ratio: float = 0.0
    bidirectional_ratio: float = 0.0


class RelationshipGraphAnalyzer:
    """
    Analyzes the relationship graph structure and metrics
    """
    
    def __init__(self, relationship_analyzer: RelationshipAnalyzer,
                 table_analyzer: TableAnalyzer):
        """
        Initialize graph analyzer
        
        Args:
            relationship_analyzer: Analyzed relationship data
            table_analyzer: Analyzed table data
        """
        self.relationship_analyzer = relationship_analyzer
        self.table_analyzer = table_analyzer
        self.stats: Optional[GraphMetrics] = None
        self.graph: Dict[str, Set[str]] = {}
        self.degree_map: Dict[str, int] = {}
    
    def analyze(self) -> GraphMetrics:
        """
        Analyze relationship graph metrics

        Returns:
            GraphMetrics object
        """
        # Build graph
        self._build_graph()

        # Calculate metrics
        rel_stats = self.relationship_analyzer.get_statistics()
        table_stats = self.table_analyzer.get_summary()

        # Connected components
        components = self._find_connected_components()
        num_components = len(components)
        largest_component = max(len(c) for c in components) if components else 0

        # BUG FIX #4: Separate data tables from design tables (param_, Calculation)
        eligible_tables = [
            t for t in self.table_analyzer.tables
            if not (t.name.lower().startswith('param_') or t.name.lower() == 'calculations')
        ]

        # Degree analysis (on eligible tables only)
        eligible_degrees = [
            self.degree_map.get(t.name, 0) for t in eligible_tables
        ]
        avg_degree = sum(eligible_degrees) / len(eligible_degrees) if eligible_degrees else 0
        max_degree = max(eligible_degrees) if eligible_degrees else 0
        min_degree = min(eligible_degrees) if eligible_degrees else 0

        # Hub tables (top 10% by degree)
        sorted_degrees = sorted(self.degree_map.items(), key=lambda x: x[1], reverse=True)
        hub_threshold = max(3, int(len(sorted_degrees) * 0.1))  # Top 10% or at least 3 connections
        hubs = [(table, degree) for table, degree in sorted_degrees if degree >= hub_threshold][:10]

        # BUG FIX #4: Isolated tables reporting
        # Data tables with no relationships
        data_isolated = [
            t for t in eligible_tables
            if self.degree_map.get(t.name, 0) == 0
        ]
        design_isolated = [
            t for t in self.table_analyzer.tables
            if (t.name.lower().startswith('param_') or t.name.lower() == 'calculations')
            and self.degree_map.get(t.name, 0) == 0
        ]

        isolated_count = len(data_isolated)

        # Fact vs Dimension connectivity
        fact_tables = [a.name for a in self.table_analyzer.get_fact_tables()]
        dim_tables = [a.name for a in self.table_analyzer.get_dimension_tables()]

        fact_degrees = [self.degree_map.get(t, 0) for t in fact_tables]
        dim_degrees = [self.degree_map.get(t, 0) for t in dim_tables]

        avg_fact_conn = sum(fact_degrees) / len(fact_degrees) if fact_degrees else 0
        avg_dim_conn = sum(dim_degrees) / len(dim_degrees) if dim_degrees else 0

        # Graph density
        num_tables = table_stats.get('total', 0)
        max_edges = (num_tables * (num_tables - 1)) / 2  # Undirected graph
        density = (rel_stats.total_relationships / max_edges) if max_edges > 0 and rel_stats else 0

        # Normalization score (higher if dimensions are well-connected to facts)
        # Simple heuristic: ratio of dimension avg connections to fact avg connections
        norm_score = 0.0
        if avg_fact_conn > 0:
            norm_score = min(avg_dim_conn / avg_fact_conn, 1.0) * 100

        # Relationship type ratios
        total_rels = rel_stats.total_relationships if rel_stats else 1
        one_to_many = rel_stats.one_to_many_count if rel_stats else 0
        many_to_many = rel_stats.many_to_many_count if rel_stats else 0
        bidirectional = rel_stats.bidirectional_relationships if rel_stats else 0

        # Most central tables (by betweenness - simplified as degree for now)
        central_tables = sorted_degrees[:10]

        # Build statistics
        self.stats = GraphMetrics(
            total_nodes=num_tables,
            total_edges=rel_stats.total_relationships if rel_stats else 0,

            connected_components=num_components,
            largest_component_size=largest_component,
            isolated_nodes=isolated_count,  # BUG FIX #4: Now counts only data tables

            avg_degree=round(avg_degree, 2),
            max_degree=max_degree,
            min_degree=min_degree,

            hub_tables=hubs,

            fact_table_avg_connections=round(avg_fact_conn, 2),
            dimension_table_avg_connections=round(avg_dim_conn, 2),

            graph_density=round(density, 4),

            most_central_tables=central_tables,

            normalization_score=round(norm_score, 2),

            one_to_many_ratio=round((one_to_many / total_rels) * 100, 2) if total_rels > 0 else 0,
            many_to_many_ratio=round((many_to_many / total_rels) * 100, 2) if total_rels > 0 else 0,
            bidirectional_ratio=round((bidirectional / total_rels) * 100, 2) if total_rels > 0 else 0
        )

        # Log summary
        print(f"\n✓ Graph Metrics:")
        print(f"   - Isolated data tables: {isolated_count} (Fact/Dim/Bridge without relationships)")
        if design_isolated:
            print(f"   - Design-isolated tables: {len(design_isolated)} (param_/Calculation - expected)")

        return self.stats
    
    def _build_graph(self):
        """Build adjacency list representation of the graph"""
        self.graph = defaultdict(set)
        self.degree_map = {}
        
        # Add all tables as nodes (including isolated ones)
        for table in self.table_analyzer.tables:
            self.graph[table.name] = set()
        
        # Add edges from relationships
        for rel in self.relationship_analyzer.analyses:
            self.graph[rel.from_table].add(rel.to_table)
            self.graph[rel.to_table].add(rel.from_table)
        
        # Calculate degrees
        for table, neighbors in self.graph.items():
            self.degree_map[table] = len(neighbors)
    
    def _find_connected_components(self) -> List[Set[str]]:
        """Find connected components using BFS"""
        visited = set()
        components = []
        
        for node in self.graph:
            if node not in visited:
                component = set()
                queue = deque([node])
                
                while queue:
                    current = queue.popleft()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        queue.extend(self.graph[current] - visited)
                
                components.append(component)
        
        return components
    
    def get_stats(self) -> Optional[GraphMetrics]:
        """Get the generated statistics"""
        return self.stats
    
    def get_hub_tables(self) -> List[Tuple[str, int]]:
        """Get hub tables (highly connected)"""
        if not self.stats:
            return []
        return self.stats.hub_tables
    
    def is_well_connected(self) -> bool:
        """Check if the graph is well-connected (few components)"""
        if not self.stats:
            return False
        return self.stats.connected_components <= 2
    
    def __repr__(self) -> str:
        """String representation"""
        if self.stats:
            return f"GraphAnalyzer(nodes={self.stats.total_nodes}, edges={self.stats.total_edges})"
        return "GraphAnalyzer(not analyzed)"
