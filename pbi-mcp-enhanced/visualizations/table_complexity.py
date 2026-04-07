"""
Table Complexity Chart Generator
Creates visualizations of table complexity metrics
"""

from pathlib import Path
from typing import Tuple, List
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from analyzers import TableAnalyzer


class TableComplexityChartGenerator:
    """
    Generates table complexity charts
    """
    
    def __init__(self, table_analyzer: TableAnalyzer):
        """
        Initialize generator
        
        Args:
            table_analyzer: Analyzed table data
        """
        self.table_analyzer = table_analyzer
    
    def generate(self, output_path: str, figsize: Tuple[int, int] = (14, 10),
                 dpi: int = 150, max_tables: int = 20) -> str:
        """
        Generate table complexity chart
        
        Args:
            output_path: Path to save the chart
            figsize: Figure size (width, height)
            dpi: Resolution
            max_tables: Maximum number of tables to show
        
        Returns:
            Path to saved chart
        """
        analyses = list(self.table_analyzer.analyses.values())
        
        if not analyses:
            return self._generate_empty_chart(output_path, figsize, dpi)
        
        # Sort by total complexity (columns + measures + relationships)
        analyses = sorted(
            analyses,
            key=lambda a: a.column_count + a.measure_count + a.relationship_count,
            reverse=True
        )[:max_tables]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, dpi=dpi, 
                                       gridspec_kw={'height_ratios': [2, 1]})
        
        # Chart 1: Stacked bar chart of complexity components
        self._create_stacked_chart(ax1, analyses)
        
        # Chart 2: Table type distribution
        self._create_type_chart(ax2)
        
        plt.suptitle(
            'Table Complexity Analysis',
            fontsize=16,
            fontweight='bold',
            y=0.995
        )
        
        plt.tight_layout()
        
        # Save
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
        
        return str(output_file)
    
    def _create_stacked_chart(self, ax, analyses):
        """Create stacked bar chart of complexity components"""
        table_names = [a.name for a in analyses]
        columns = [a.column_count for a in analyses]
        measures = [a.measure_count for a in analyses]
        relationships = [a.relationship_count for a in analyses]
        
        # Truncate long table names
        table_names_short = [
            name[:20] + '...' if len(name) > 20 else name
            for name in table_names
        ]
        
        x = np.arange(len(table_names))
        width = 0.8
        
        # Create stacked bars
        p1 = ax.barh(x, columns, width, label='Columns', color='#3498db', alpha=0.9)
        p2 = ax.barh(x, measures, width, left=columns, label='Measures', color='#2ecc71', alpha=0.9)
        p3 = ax.barh(x, relationships, width, 
                     left=np.array(columns) + np.array(measures),
                     label='Relationships', color='#e74c3c', alpha=0.9)
        
        # Add value labels
        for i, (c, m, r) in enumerate(zip(columns, measures, relationships)):
            total = c + m + r
            if total > 0:
                ax.text(
                    total + max(columns + measures + relationships) * 0.02,
                    i,
                    f'{total}',
                    va='center',
                    fontsize=8,
                    fontweight='bold'
                )
        
        ax.set_ylabel('Table', fontsize=11, fontweight='bold')
        ax.set_xlabel('Complexity Score (Columns + Measures + Relationships)', 
                     fontsize=11, fontweight='bold')
        ax.set_title('Top Tables by Complexity', fontsize=12, fontweight='bold', pad=10)
        ax.set_yticks(x)
        ax.set_yticklabels(table_names_short, fontsize=9)
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.invert_yaxis()
    
    def _create_type_chart(self, ax):
        """Create bar chart of table type distribution"""
        summary = self.table_analyzer.get_summary()
        
        categories = ['Fact', 'Dimension', 'Calculated', 'Unknown', 'Hidden']
        counts = [
            summary.get('fact', 0),
            summary.get('dimension', 0),
            summary.get('calculated', 0),
            summary.get('unknown', 0),
            summary.get('hidden', 0)
        ]
        
        # Filter out zero counts
        categories = [cat for cat, count in zip(categories, counts) if count > 0]
        counts = [count for count in counts if count > 0]
        
        if not categories:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            ax.axis('off')
            return
        
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95A5A6', '#34495E']
        colors = colors[:len(categories)]
        
        bars = ax.bar(categories, counts, color=colors, alpha=0.8, edgecolor='black')
        
        # Add value labels
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + max(counts) * 0.02,
                f'{count}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold'
            )
        
        ax.set_ylabel('Count', fontsize=11, fontweight='bold')
        ax.set_title('Table Type Distribution', fontsize=12, fontweight='bold', pad=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    def _generate_empty_chart(self, output_path: str, figsize: Tuple[int, int],
                             dpi: int) -> str:
        """Generate chart when no data available"""
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        ax.text(
            0.5, 0.5,
            'No Table Data Available',
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=16,
            color='#7F8C8D'
        )
        
        ax.set_title('Table Complexity Analysis', fontsize=16, fontweight='bold')
        ax.axis('off')
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
        
        return str(output_file)
    
    def __repr__(self) -> str:
        """String representation"""
        count = len(self.table_analyzer.analyses)
        return f"TableComplexityChartGenerator(tables={count})"
