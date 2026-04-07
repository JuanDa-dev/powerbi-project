"""
Column Analyzer
Analyzes columns in the data model
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter
from parsers.model_bim_parser import Column, ModelBIM


@dataclass
class ColumnAnalysis:
    """Analysis results for a single column"""
    table_name: str
    column_name: str
    data_type: str
    is_calculated: bool = False
    is_hidden: bool = False
    is_key: bool = False
    has_format: bool = False
    format_string: Optional[str] = None
    data_category: Optional[str] = None
    source_column: Optional[str] = None
    expression: Optional[str] = None


@dataclass
class ColumnStatistics:
    """Statistics about columns in the model"""
    total_columns: int
    calculated_columns: int
    hidden_columns: int
    key_columns: int
    data_type_distribution: Dict[str, int]
    columns_with_format: int
    columns_by_category: Dict[str, int]
    avg_columns_per_table: float


class ColumnAnalyzer:
    """
    Analyzes columns in a Power BI model
    """
    
    def __init__(self, model: ModelBIM):
        """
        Initialize the column analyzer
        
        Args:
            model: Parsed ModelBIM object
        """
        self.model = model
        self.analyses: List[ColumnAnalysis] = []
        self.statistics: Optional[ColumnStatistics] = None
    
    def analyze(self) -> List[ColumnAnalysis]:
        """
        Analyze all columns in the model
        
        Returns:
            List of ColumnAnalysis objects
        """
        self.analyses = []
        
        for table in self.model.tables:
            for column in table.columns:
                analysis = self._analyze_column(table.name, column)
                self.analyses.append(analysis)
        
        # Calculate statistics
        self._calculate_statistics()
        
        return self.analyses
    
    def _analyze_column(self, table_name: str, column: Column) -> ColumnAnalysis:
        """
        Analyze a single column
        
        Args:
            table_name: Name of the table containing the column
            column: Column object to analyze
        
        Returns:
            ColumnAnalysis object
        """
        return ColumnAnalysis(
            table_name=table_name,
            column_name=column.name,
            data_type=column.data_type,
            is_calculated=column.expression is not None,
            is_hidden=column.is_hidden,
            is_key=column.is_key,
            has_format=column.format_string is not None,
            format_string=column.format_string,
            data_category=column.data_category,
            source_column=column.source_column,
            expression=column.expression
        )
    
    def _calculate_statistics(self):
        """Calculate statistics about columns"""
        if not self.analyses:
            return
        
        # Count data types
        data_types = Counter(a.data_type for a in self.analyses)
        
        # Count categories
        categories = Counter(
            a.data_category for a in self.analyses 
            if a.data_category is not None
        )
        
        # Calculate averages
        table_column_counts = Counter(a.table_name for a in self.analyses)
        avg_columns = sum(table_column_counts.values()) / len(table_column_counts) if table_column_counts else 0
        
        self.statistics = ColumnStatistics(
            total_columns=len(self.analyses),
            calculated_columns=sum(1 for a in self.analyses if a.is_calculated),
            hidden_columns=sum(1 for a in self.analyses if a.is_hidden),
            key_columns=sum(1 for a in self.analyses if a.is_key),
            data_type_distribution=dict(data_types),
            columns_with_format=sum(1 for a in self.analyses if a.has_format),
            columns_by_category=dict(categories),
            avg_columns_per_table=round(avg_columns, 2)
        )
    
    def get_columns_by_table(self, table_name: str) -> List[ColumnAnalysis]:
        """Get all columns for a specific table"""
        return [a for a in self.analyses if a.table_name == table_name]
    
    def get_calculated_columns(self) -> List[ColumnAnalysis]:
        """Get all calculated columns"""
        return [a for a in self.analyses if a.is_calculated]
    
    def get_key_columns(self) -> List[ColumnAnalysis]:
        """Get all key columns"""
        return [a for a in self.analyses if a.is_key]
    
    def get_columns_by_type(self, data_type: str) -> List[ColumnAnalysis]:
        """Get all columns of a specific data type"""
        return [a for a in self.analyses if a.data_type == data_type]
    
    def get_statistics(self) -> Optional[ColumnStatistics]:
        """Get column statistics"""
        return self.statistics
    
    def get_data_type_summary(self) -> Dict[str, int]:
        """Get summary of data types"""
        if self.statistics:
            return self.statistics.data_type_distribution
        return {}
    
    def get_most_common_data_type(self) -> Optional[Tuple[str, int]]:
        """Get the most common data type"""
        if self.statistics and self.statistics.data_type_distribution:
            return max(
                self.statistics.data_type_distribution.items(),
                key=lambda x: x[1]
            )
        return None
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ColumnAnalyzer(columns={len(self.analyses)})"
