"""
Relationship Diagram Generator
Creates visual diagrams of table relationships
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
from analyzers import RelationshipAnalyzer, TableAnalyzer


class RelationshipDiagramGenerator:
    """
    Generates relationship diagrams using NetworkX and Matplotlib
    """
    
    def __init__(self, relationship_analyzer: RelationshipAnalyzer,
                 table_analyzer: TableAnalyzer):
        """
        Initialize diagram generator
        
        Args:
            relationship_analyzer: Analyzed relationship data
            table_analyzer: Analyzed table data
        """
        self.relationship_analyzer = relationship_analyzer
        self.table_analyzer = table_analyzer
        self.graph: Optional[nx.DiGraph] = None
    
    def generate(self, output_path: str, figsize: Tuple[int, int] = (16, 12),
                 dpi: int = 150) -> str:
        """
        Generate relationship diagram
        
        Args:
            output_path: Path to save the diagram
            figsize: Figure size (width, height)
            dpi: Resolution
        
        Returns:
            Path to saved diagram
        """
        # Build graph
        self._build_graph()
        
        if not self.graph or self.graph.number_of_nodes() == 0:
            return self._generate_empty_diagram(output_path, figsize, dpi)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        # Get node colors based on table type
        node_colors = self._get_node_colors()
        
        # Position nodes using spring layout
        pos = nx.spring_layout(self.graph, k=2, iterations=50, seed=42)
        
        # Draw nodes
        for node_type, color in [('fact', '#FF6B6B'), ('dimension', '#4ECDC4'), 
                                  ('calculated', '#FFE66D'), ('unknown', '#95A5A6')]:
            nodes = [n for n in self.graph.nodes() if node_colors.get(n) == color]
            if nodes:
                nx.draw_networkx_nodes(
                    self.graph, pos,
                    nodelist=nodes,
                    node_color=color,
                    node_size=3000,
                    alpha=0.9,
                    ax=ax
                )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color='#7F8C8D',
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            width=2,
            alpha=0.6,
            ax=ax,
            connectionstyle='arc3,rad=0.1'
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            self.graph, pos,
            font_size=9,
            font_weight='bold',
            font_color='white',
            ax=ax
        )
        
        # Add legend
        legend_elements = [
            mpatches.Patch(color='#FF6B6B', label='Fact Tables'),
            mpatches.Patch(color='#4ECDC4', label='Dimension Tables'),
            mpatches.Patch(color='#FFE66D', label='Calculated Tables'),
            mpatches.Patch(color='#95A5A6', label='Unknown Type')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        # Set title
        rel_count = self.graph.number_of_edges()
        table_count = self.graph.number_of_nodes()
        ax.set_title(
            f'Data Model Relationship Diagram\n{table_count} Tables, {rel_count} Relationships',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        
        ax.axis('off')
        plt.tight_layout()
        
        # Save
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
        
        return str(output_file)
    
    def _build_graph(self):
        """Build NetworkX directed graph from relationships"""
        self.graph = nx.DiGraph()
        
        # Add all tables as nodes
        for analysis in self.table_analyzer.analyses.values():
            self.graph.add_node(analysis.name)
        
        # Add relationships as edges
        for rel in self.relationship_analyzer.analyses:
            # Add edge with attributes
            self.graph.add_edge(
                rel.from_table,
                rel.to_table,
                active=rel.is_active,
                cross_filter=rel.cross_filtering,
                type=rel.relationship_type
            )
    
    def _get_node_colors(self) -> Dict[str, str]:
        """Get color mapping for nodes based on table type"""
        colors = {}
        
        for table_name, analysis in self.table_analyzer.analyses.items():
            if analysis.table_type == 'fact':
                colors[table_name] = '#FF6B6B'  # Red
            elif analysis.table_type == 'dimension':
                colors[table_name] = '#4ECDC4'  # Teal
            elif analysis.table_type == 'calculated':
                colors[table_name] = '#FFE66D'  # Yellow
            else:
                colors[table_name] = '#95A5A6'  # Gray
        
        return colors
    
    def _generate_empty_diagram(self, output_path: str, figsize: Tuple[int, int],
                                dpi: int) -> str:
        """Generate diagram when no relationships exist"""
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        ax.text(
            0.5, 0.5,
            'No Relationships Found\n\nThe model contains no table relationships.',
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=16,
            color='#7F8C8D'
        )
        
        ax.set_title('Data Model Relationship Diagram', fontsize=16, fontweight='bold')
        ax.axis('off')
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
        
        return str(output_file)
    
    def __repr__(self) -> str:
        """String representation"""
        nodes = self.graph.number_of_nodes() if self.graph else 0
        edges = self.graph.number_of_edges() if self.graph else 0
        return f"RelationshipDiagramGenerator(nodes={nodes}, edges={edges})"
