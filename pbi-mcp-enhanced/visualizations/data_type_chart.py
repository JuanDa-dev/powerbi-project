"""
Data Type Chart Generator
Creates separate charts for each data type category
"""

from pathlib import Path
from typing import Tuple, Dict
import matplotlib.pyplot as plt
import seaborn as sns
from utils import DataTypeAnalyzer


class DataTypeChartGenerator:
    """
    Generates separate data type distribution charts by category
    Creates multiple PNG files (one per category) for maximum clarity
    """
    
    def __init__(self, data_type_stats):
        """
        Initialize chart generator
        
        Args:
            data_type_stats: DataTypeStats object (not analyzer)
        """
        self.stats = data_type_stats
        self.output_dir = None
    
    def generate(self, output_path: str, figsize: Tuple[int, int] = (14, 8),
                 dpi: int = 150) -> str:
        """
        Generate separate data type distribution charts (4 independent files)
        
        Args:
            output_path: Base path to save charts (will create multiple files)
            figsize: Figure size (width, height)
            dpi: Resolution
        
        Returns:
            Path to output directory
        """
        if not self.stats or not self.stats.data_type_counts:
            return self._generate_empty_chart(output_path, figsize, dpi)
        
        # Setup output directory
        output_file = Path(output_path)
        self.output_dir = output_file.parent
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate 4 separate charts
        self._generate_numeric_chart(figsize, dpi)
        self._generate_text_chart(figsize, dpi)
        self._generate_datetime_chart(figsize, dpi)
        self._generate_other_chart(figsize, dpi)
        
        # Return directory path
        return str(self.output_dir)
    
    def _generate_numeric_chart(self, figsize: Tuple[int, int], dpi: int):
        """Generate chart for numeric data types"""
        numeric_types = {
            'Int64': self.stats.data_type_counts.get('Int64', 0),
            'Int32': self.stats.data_type_counts.get('Int32', 0),
            'Int16': self.stats.data_type_counts.get('Int16', 0),
            'Decimal': self.stats.data_type_counts.get('Decimal', 0),
            'Double': self.stats.data_type_counts.get('Double', 0),
            'Single': self.stats.data_type_counts.get('Single', 0),
            'Currency': self.stats.data_type_counts.get('Currency', 0),
            'Percentage': self.stats.data_type_counts.get('Percentage', 0),
        }
        
        numeric_types = {k: v for k, v in numeric_types.items() if v > 0}
        
        if not numeric_types:
            return
        
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        types = list(numeric_types.keys())
        counts = list(numeric_types.values())
        
        # Gradient of blues
        colors = ['#1f77b4', '#2ca02c', '#3498db', '#2980b9', '#1abc9c', '#16a085', '#3498db', '#2c3e50']
        colors = colors[:len(types)]
        
        bars = ax.bar(types, counts, color=colors, alpha=0.85, edgecolor='black', linewidth=2)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            percentage = (count / self.stats.total_columns) * 100
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(counts) * 0.02,
                f'{count}\n({percentage:.1f}%)',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )
        
        ax.set_ylabel('Number of Columns', fontsize=12, fontweight='bold')
        ax.set_xlabel('Data Type', fontsize=12, fontweight='bold')
        ax.set_title('Numeric Data Types Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.8)
        ax.set_ylim(0, max(counts) * 1.2)
        
        plt.xticks(rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=11)
        plt.tight_layout()
        
        output_file = self.output_dir / 'data_type_numeric.png'
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
    
    def _generate_text_chart(self, figsize: Tuple[int, int], dpi: int):
        """Generate chart for text data types"""
        text_types = {
            'String': self.stats.data_type_counts.get('String', 0),
            'Text': self.stats.data_type_counts.get('Text', 0),
        }
        
        text_types = {k: v for k, v in text_types.items() if v > 0}
        
        if not text_types:
            return
        
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        types = list(text_types.keys())
        counts = list(text_types.values())
        
        colors = ['#2ecc71', '#27ae60']
        colors = colors[:len(types)]
        
        bars = ax.bar(types, counts, color=colors, alpha=0.85, edgecolor='black', linewidth=2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            percentage = (count / self.stats.total_columns) * 100
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(counts) * 0.02,
                f'{count}\n({percentage:.1f}%)',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )
        
        ax.set_ylabel('Number of Columns', fontsize=12, fontweight='bold')
        ax.set_xlabel('Data Type', fontsize=12, fontweight='bold')
        ax.set_title('Text Data Types Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.8)
        ax.set_ylim(0, max(counts) * 1.2)
        
        plt.xticks(rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=11)
        plt.tight_layout()
        
        output_file = self.output_dir / 'data_type_text.png'
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
    
    def _generate_datetime_chart(self, figsize: Tuple[int, int], dpi: int):
        """Generate chart for date/time data types"""
        datetime_types = {
            'DateTime': self.stats.data_type_counts.get('DateTime', 0),
            'Date': self.stats.data_type_counts.get('Date', 0),
            'Time': self.stats.data_type_counts.get('Time', 0),
        }
        
        datetime_types = {k: v for k, v in datetime_types.items() if v > 0}
        
        if not datetime_types:
            return
        
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        types = list(datetime_types.keys())
        counts = list(datetime_types.values())
        
        colors = ['#e74c3c', '#c0392b', '#e67e22']
        colors = colors[:len(types)]
        
        bars = ax.bar(types, counts, color=colors, alpha=0.85, edgecolor='black', linewidth=2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            percentage = (count / self.stats.total_columns) * 100
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(counts) * 0.02,
                f'{count}\n({percentage:.1f}%)',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )
        
        ax.set_ylabel('Number of Columns', fontsize=12, fontweight='bold')
        ax.set_xlabel('Data Type', fontsize=12, fontweight='bold')
        ax.set_title('Date/Time Data Types Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.8)
        ax.set_ylim(0, max(counts) * 1.2)
        
        plt.xticks(rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=11)
        plt.tight_layout()
        
        output_file = self.output_dir / 'data_type_datetime.png'
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
    
    def _generate_other_chart(self, figsize: Tuple[int, int], dpi: int):
        """Generate chart for boolean and other data types"""
        other_types = {
            'Boolean': self.stats.data_type_counts.get('Boolean', 0),
            'Binary': self.stats.data_type_counts.get('Binary', 0),
        }
        
        known_types = {'Int64', 'Int32', 'Int16', 'Decimal', 'Double', 'Single', 
                      'Currency', 'Percentage', 'String', 'Text', 'DateTime', 
                      'Date', 'Time', 'Boolean', 'Binary'}
        
        for dtype, count in self.stats.data_type_counts.items():
            if dtype not in known_types:
                other_types[dtype] = count
        
        other_types = {k: v for k, v in other_types.items() if v > 0}
        
        if not other_types:
            return
        
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        types = list(other_types.keys())
        counts = list(other_types.values())
        
        colors = ['#f39c12', '#d35400', '#95a5a6', '#34495e', '#9b59b6', '#16a085']
        colors = colors[:len(types)]
        
        bars = ax.bar(types, counts, color=colors, alpha=0.85, edgecolor='black', linewidth=2)
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            percentage = (count / self.stats.total_columns) * 100
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(counts) * 0.02,
                f'{count}\n({percentage:.1f}%)',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )
        
        ax.set_ylabel('Number of Columns', fontsize=12, fontweight='bold')
        ax.set_xlabel('Data Type', fontsize=12, fontweight='bold')
        ax.set_title('Other Data Types Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.8)
        ax.set_ylim(0, max(counts) * 1.2)
        
        plt.xticks(rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=11)
        plt.tight_layout()
        
        output_file = self.output_dir / 'data_type_other.png'
        plt.savefig(output_file, bbox_inches='tight', dpi=dpi)
        plt.close()
    
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
