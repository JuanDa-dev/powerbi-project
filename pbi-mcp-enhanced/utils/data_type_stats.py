"""
Data Type Distribution Statistics
Analyzes distribution of data types across columns
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict


@dataclass
class DataTypeStats:
    """Statistics about data type distribution"""
    # Overall distribution
    total_columns: int = 0
    data_type_counts: Dict[str, int] = field(default_factory=dict)
    data_type_percentages: Dict[str, float] = field(default_factory=dict)
    
    # Most/least common
    most_common_type: Optional[str] = None
    most_common_count: int = 0
    least_common_type: Optional[str] = None
    least_common_count: int = 0
    
    # Category analysis
    numeric_columns: int = 0  # int64, decimal, double
    text_columns: int = 0  # string
    date_columns: int = 0  # datetime, date
    boolean_columns: int = 0  # boolean
    other_columns: int = 0
    
    # Percentages
    numeric_percentage: float = 0.0
    text_percentage: float = 0.0
    date_percentage: float = 0.0
    boolean_percentage: float = 0.0
    
    # Calculated columns by type
    calculated_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Data categories (if available)
    data_categories: Dict[str, int] = field(default_factory=dict)


class DataTypeAnalyzer:
    """
    Analyzes data types used in the model
    """
    
    # Type categorization
    NUMERIC_TYPES = {'int64', 'decimal', 'double', 'currency', 'int', 'number'}
    TEXT_TYPES = {'string', 'text'}
    DATE_TYPES = {'datetime', 'date'}
    BOOLEAN_TYPES = {'boolean', 'bool'}
    
    def __init__(self, tables: List):
        """
        Initialize the data type analyzer
        
        Args:
            tables: List of Table objects
        """
        self.tables = tables
        self.stats: Optional[DataTypeStats] = None
    
    def analyze(self) -> DataTypeStats:
        """
        Analyze data types across all columns
        
        Returns:
            DataTypeStats object
        """
        type_counts = Counter()
        type_by_table = defaultdict(Counter)
        calculated_by_type = Counter()
        data_categories = Counter()
        
        # Collect all columns from tables
        total_columns = 0
        for table in self.tables:
            for column in (table.columns or []):
                total_columns += 1
                dtype = column.data_type or 'Unknown'
                # Clean the dtype: extract just the type name
                dtype_clean = self._clean_dtype_string(str(dtype))
                type_counts[dtype_clean] += 1
                type_by_table[table.name][dtype_clean] += 1
                
                # Track calculated columns
                if column.expression:
                    calculated_by_type[dtype_clean] += 1
                
                # Track data categories
                if column.data_category:
                    data_categories[column.data_category] += 1
        
        if total_columns == 0:
            return DataTypeStats()
        
        # Calculate percentages
        type_percentages = {
            dtype: (count / total_columns) * 100
            for dtype, count in type_counts.items()
        }
        
        # Find most/least common
        if type_counts:
            most_common = type_counts.most_common(1)[0]
            least_common = type_counts.most_common()[-1]
            most_common_type, most_common_count = most_common
            least_common_type, least_common_count = least_common
        else:
            most_common_type = least_common_type = None
            most_common_count = least_common_count = 0
        
        # Categorize types
        numeric_cols = sum(count for dtype, count in type_counts.items() 
                          if dtype.lower() in self.NUMERIC_TYPES)
        text_cols = sum(count for dtype, count in type_counts.items() 
                       if dtype.lower() in self.TEXT_TYPES)
        date_cols = sum(count for dtype, count in type_counts.items() 
                       if dtype.lower() in self.DATE_TYPES)
        boolean_cols = sum(count for dtype, count in type_counts.items() 
                          if dtype.lower() in self.BOOLEAN_TYPES)
        other_cols = total_columns - (numeric_cols + text_cols + date_cols + boolean_cols)
        
        # Build stats
        self.stats = DataTypeStats(
            total_columns=total_columns,
            data_type_counts=dict(type_counts),
            data_type_percentages=type_percentages,
            most_common_type=most_common_type,
            most_common_count=most_common_count,
            least_common_type=least_common_type,
            least_common_count=least_common_count,
            numeric_columns=numeric_cols,
            text_columns=text_cols,
            date_columns=date_cols,
            boolean_columns=boolean_cols,
            other_columns=other_cols,
            numeric_percentage=round((numeric_cols / total_columns) * 100, 2) if total_columns > 0 else 0,
            text_percentage=round((text_cols / total_columns) * 100, 2) if total_columns > 0 else 0,
            date_percentage=round((date_cols / total_columns) * 100, 2) if total_columns > 0 else 0,
            boolean_percentage=round((boolean_cols / total_columns) * 100, 2) if total_columns > 0 else 0,
            calculated_by_type=dict(calculated_by_type),
            data_categories=dict(data_categories)
        )
        
        return self.stats
    
    def _clean_dtype_string(self, dtype_str: str) -> str:
        """
        Clean data type string by extracting just the type name
        Removes metadata like lineageTag, summarizeBy, sourceColumn, etc
        
        Args:
            dtype_str: Raw data type string that may contain metadata
            
        Returns:
            Cleaned data type name
        """
        if not dtype_str:
            return 'Unknown'
        
        # Extract just the first line
        dtype_clean = dtype_str.split('\n')[0].strip()
        
        # Extract just the first tab-separated part
        dtype_clean = dtype_clean.split('\t')[0].strip()
        
        # Extract just the first word/token
        parts = dtype_clean.split()
        if parts:
            dtype_clean = parts[0].strip()
        
        # Remove any remaining metadata markers
        for marker in ['lineageTag', 'summarizeBy', 'sourceColumn', 'formatString']:
            if marker in dtype_clean:
                dtype_clean = dtype_clean.split(marker)[0].strip()
        
        return dtype_clean if dtype_clean else 'Unknown'
    
    def get_stats(self) -> Optional[DataTypeStats]:
        """Get the generated statistics"""
        return self.stats
    
    def get_type_distribution(self) -> Dict[str, int]:
        """Get the full type distribution"""
        if not self.stats:
            return {}
        return self.stats.data_type_counts
    
    def get_category_distribution(self) -> Dict[str, int]:
        """Get distribution by category"""
        if not self.stats:
            return {}
        
        return {
            'Numeric': self.stats.numeric_columns,
            'Text': self.stats.text_columns,
            'Date/Time': self.stats.date_columns,
            'Boolean': self.stats.boolean_columns,
            'Other': self.stats.other_columns
        }
    
    def get_sorted_types(self, reverse: bool = True) -> List[Tuple[str, int]]:
        """
        Get data types sorted by frequency
        
        Args:
            reverse: If True, sort descending (most common first)
        
        Returns:
            List of (type, count) tuples
        """
        if not self.stats:
            return []
        
        return sorted(
            self.stats.data_type_counts.items(),
            key=lambda x: x[1],
            reverse=reverse
        )
    
    def __repr__(self) -> str:
        """String representation"""
        if self.stats:
            return f"DataTypeAnalyzer(types={len(self.stats.data_type_counts)})"
        return "DataTypeAnalyzer(not analyzed)"
