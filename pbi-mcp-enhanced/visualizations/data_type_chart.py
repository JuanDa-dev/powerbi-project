"""
Data Type Chart Generator
Creates histograms of data type distribution
"""

from pathlib import Path
from typing import Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from utils import DataTypeAnalyzer


class DataTypeChartGenerator:
    """
    Generates data type distribution charts
    """
    
    def __init__(self, data_type_stats):
        """
        Initialize chart generator
        
        Args:
            data_type_stats: DataTypeStats object (not analyzer)
        """
        self.stats = data_type_stats
    
    def generate(self, output_path: str, figsize: Tuple[int, int] = (12, 8),
                 dpi: int = 150) -> str:
        """
        Generate data type distribution chart
        
        Args:
            output_path: Path to save the chart
            figsize: Figure size (width, height)
            dpi: Resolution
        
        Returns:
            Path to saved chart
        """
        if not self.stats or not self.stats.data_type_counts:
            return self._generate_empty_chart(output_path, figsize, dpi)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, dpi=dpi)
        
        # Chart 1: Detailed type distribution (bar chart)
        self._create_detailed_chart(ax1)
        
        # Chart 2: Category distribution (pie chart)
        self._create_category_chart(ax2)
        
        plt.suptitle(
            'Data Type Distribution Analysis',
            fontsize=16,
            fontweight='bold',
            y=0.98
        )
        
        plt.tight_layout()
        
        # Save
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
        
        return str(output_file)
    
    def _create_detailed_chart(self, ax):
        """Create detailed bar chart of data types"""
        # Get sorted types
        sorted_types = sorted(self.stats.data_type_counts.items(), 
                            key=lambda x: x[1], reverse=True)
        
        if not sorted_types:
            return
        
        types = [t[0] for t in sorted_types]
        counts = [t[1] for t in sorted_types]
        
        # Color palette
        colors = sns.color_palette("husl", len(types))
        
        # Create horizontal bar chart
        bars = ax.barh(types, counts, color=colors, alpha=0.8, edgecolor='black')
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            percentage = (count / self.stats.total_columns) * 100
            ax.text(
                bar.get_width() + max(counts) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'{count} ({percentage:.1f}%)',
                va='center',
                fontsize=9,
                fontweight='bold'
            )
        
        ax.set_xlabel('Number of Columns', fontsize=11, fontweight='bold')
        ax.set_ylabel('Data Type', fontsize=11, fontweight='bold')
        ax.set_title('Detailed Type Distribution', fontsize=12, fontweight='bold', pad=10)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Invert y-axis to show most common at top
        ax.invert_yaxis()
    
    def _create_category_chart(self, ax):
        """Create pie chart of data type categories"""
        # Build category distribution from stats
        categories = {
            'Numeric': self.stats.numeric_columns,
            'Text': self.stats.text_columns,
            'Date/Time': self.stats.date_columns,
            'Boolean': self.stats.boolean_columns
        }
        
        if not categories:
            return
        
        # Filter out zero values
        categories = {k: v for k, v in categories.items() if v > 0}
        
        labels = list(categories.keys())
        sizes = list(categories.values())
        
        # Colors for categories
        category_colors = {
            'Numeric': '#3498db',
            'Text': '#2ecc71',
            'Date/Time': '#e74c3c',
            'Boolean': '#f39c12',
            'Other': '#95a5a6'
        }
        colors = [category_colors.get(label, '#95a5a6') for label in labels]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )
        
        # Make percentage text white
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
        
        ax.set_title('Category Distribution', fontsize=12, fontweight='bold', pad=10)
    
    def _generate_empty_chart(self, output_path: str, figsize: Tuple[int, int],
                             dpi: int) -> str:
        """Generate chart when no data available"""
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        ax.text(
            0.5, 0.5,
            'No Data Type Information Available',
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=16,
            color='#7F8C8D'
        )
        
        ax.set_title('Data Type Distribution', fontsize=16, fontweight='bold')
        ax.axis('off')
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
        
        return str(output_file)
    
    def __repr__(self) -> str:
        """String representation"""
        types = len(self.stats.data_type_counts) if self.stats else 0
        return f"DataTypeChartGenerator(types={types})"
