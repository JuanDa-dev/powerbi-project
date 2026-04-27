#!/usr/bin/env python3
"""
Datatype distribution visualization - Column datatypes distribution.
"""

import json
from pathlib import Path
from typing import Dict, Any
from collections import Counter
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')


class DatatypeDistributionBuilder:
    def __init__(self, tables_json: str):
        self.tables_json = tables_json
        self.tables = []
        self._load_data()
    
    def _load_data(self):
        """Load tables data from JSON file"""
        with open(self.tables_json, 'r', encoding='utf-8') as f:
            self.tables = json.load(f)
    
    def _extract_datatype_distribution(self) -> Dict[str, int]:
        """Extract datatype distribution from all tables"""
        datatypes = Counter()
        
        for table in self.tables:
            for column in table.get('columns', []):
                datatype = column.get('datatype', 'Unknown')
                datatypes[datatype] += 1
        
        return dict(datatypes)
    
    def create_visualization(self, output_file: str, figsize: tuple = (12, 8)):
        """Create bar chart visualization"""
        datatype_dist = self._extract_datatype_distribution()
        
        if not datatype_dist:
            print("No datatype data available")
            return None
        
        # Sort by frequency
        sorted_types = sorted(datatype_dist.items(), key=lambda x: x[1], reverse=True)
        types, counts = zip(*sorted_types)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, dpi=150)
        
        # Color palette
        colors = plt.cm.Set3(range(len(types)))
        
        # Create bar chart
        bars = ax.bar(types, counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{int(height)}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold'
            )
        
        # Styling
        ax.set_xlabel('Data Type', fontsize=12, fontweight='bold')
        ax.set_ylabel('Column Count', fontsize=12, fontweight='bold')
        ax.set_title(
            'Semantic Model Datatype Distribution\nColumn Types Across All Tables',
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        
        plt.xticks(rotation=45, ha='right')
        
        # Add grid for readability
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=150)
        plt.close()
        
        return output_file
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get datatype distribution statistics"""
        datatype_dist = self._extract_datatype_distribution()
        
        total_columns = sum(datatype_dist.values())
        most_common = max(datatype_dist.items(), key=lambda x: x[1]) if datatype_dist else (None, 0)
        
        return {
            'total_columns': total_columns,
            'unique_datatypes': len(datatype_dist),
            'most_common_type': most_common[0],
            'most_common_count': most_common[1],
            'distribution': datatype_dist
        }


def create_datatype_distribution(
    tables_json: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Create datatype distribution visualization.
    
    Args:
        tables_json: Path to tables.json
        output_file: Output PNG file path
    
    Returns:
        Dict with file path and statistics
    """
    builder = DatatypeDistributionBuilder(tables_json)
    
    png_file = builder.create_visualization(output_file)
    stats = builder.get_statistics()
    
    return {
        'png': png_file,
        'statistics': stats
    }
