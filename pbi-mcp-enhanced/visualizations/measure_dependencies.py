"""
Measure Dependencies Graph Generator
Creates dependency graphs for DAX measures
"""

from pathlib import Path
from typing import Tuple, Dict, List, Set
import matplotlib.pyplot as plt
import networkx as nx
from analyzers import MeasureAnalyzer


class MeasureDependencyGenerator:
    """
    Generates measure dependency graphs
    """
    
    def __init__(self, measure_analyzer: MeasureAnalyzer):
        """
        Initialize generator
        
        Args:
            measure_analyzer: Analyzed measure data
        """
        self.measure_analyzer = measure_analyzer
        self.graph = None
    
    def generate(self, output_path: str, figsize: Tuple[int, int] = (16, 12),
                 dpi: int = 150, max_measures: int = 30) -> str:
        """
        Generate measure dependency graph
        
        Args:
            output_path: Path to save the diagram
            figsize: Figure size (width, height)
            dpi: Resolution
            max_measures: Maximum number of measures to show (most complex)
        
        Returns:
            Path to saved diagram
        """
        # Build dependency graph
        self._build_dependency_graph(max_measures)
        
        if not self.graph or self.graph.number_of_nodes() == 0:
            return self._generate_empty_diagram(output_path, figsize, dpi)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        # Position nodes
        # Use hierarchical layout if possible
        try:
            pos = nx.spring_layout(self.graph, k=3, iterations=50, seed=42)
        except:
            pos = nx.circular_layout(self.graph)
        
        # Get node sizes based on complexity
        node_sizes = self._get_node_sizes()
        
        # Get node colors based on number of dependencies
        node_colors = self._get_node_colors()
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos,
            node_size=node_sizes,
            node_color=node_colors,
            cmap=plt.cm.YlOrRd,
            alpha=0.9,
            ax=ax
        )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color='#7F8C8D',
            arrows=True,
            arrowsize=15,
            arrowstyle='->',
            width=1.5,
            alpha=0.5,
            ax=ax,
            connectionstyle='arc3,rad=0.1'
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            self.graph, pos,
            font_size=7,
            font_weight='bold',
            ax=ax
        )
        
        # Set title
        measure_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()
        ax.set_title(
            f'Measure Dependency Graph\n{measure_count} Measures, {edge_count} Dependencies',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        
        # Add note about filtering
        if len(self.measure_analyzer.analyses) > max_measures:
            ax.text(
                0.02, 0.02,
                f'Note: Showing top {max_measures} most complex measures',
                transform=ax.transAxes,
                fontsize=9,
                style='italic',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
        
        ax.axis('off')
        plt.tight_layout()
        
        # Save
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
        
        return str(output_file)
    
    def _build_dependency_graph(self, max_measures: int):
        """Build dependency graph"""
        self.graph = nx.DiGraph()
        
        # Get top complex measures
        all_measures = self.measure_analyzer.analyses
        
        # Sort by complexity and take top N
        sorted_measures = sorted(
            all_measures,
            key=lambda m: m.complexity_score,
            reverse=True
        )[:max_measures]
        
        # Build set of measure names to include
        included_measures = {m.name for m in sorted_measures}
        
        # Add nodes and edges
        for measure in sorted_measures:
            self.graph.add_node(
                measure.name,
                complexity=measure.complexity_score,
                table=measure.table
            )
            
            # Add edges to dependencies (only if dependency is also included)
            for dep in measure.referenced_measures:
                if dep in included_measures:
                    self.graph.add_edge(measure.name, dep)
    
    def _get_node_sizes(self) -> List[int]:
        """Get node sizes based on complexity"""
        sizes = []
        for node in self.graph.nodes():
            complexity = self.graph.nodes[node].get('complexity', 0)
            # Scale: complexity 0-10 = size 500, 10-30 = size 1500, 30+ = size 3000
            if complexity < 10:
                size = 800
            elif complexity < 30:
                size = 1500
            else:
                size = 2500
            sizes.append(size)
        return sizes
    
    def _get_node_colors(self) -> List[float]:
        """Get node colors based on number of dependencies"""
        colors = []
        for node in self.graph.nodes():
            # Number of outgoing edges (measures this depends on)
            out_degree = self.graph.out_degree(node)
            colors.append(out_degree)
        return colors
    
    def _generate_empty_diagram(self, output_path: str, figsize: Tuple[int, int],
                                dpi: int) -> str:
        """Generate diagram when no dependencies exist"""
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        ax.text(
            0.5, 0.5,
            'No Measure Dependencies Found\n\nMeasures do not reference other measures.',
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=16,
            color='#7F8C8D'
        )
        
        ax.set_title('Measure Dependency Graph', fontsize=16, fontweight='bold')
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
        return f"MeasureDependencyGenerator(measures={nodes}, dependencies={edges})"
