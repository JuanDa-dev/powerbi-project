"""
Data Type Distribution Table Generator
Generates Markdown table for data type statistics
"""

from utils import DataTypeStats


class DataTypeTableGenerator:
    """
    Generates a Markdown table with data type distribution summary
    """
    
    def __init__(self, data_type_stats: DataTypeStats, table_analyzer=None):
        """
        Initialize generator
        
        Args:
            data_type_stats: DataTypeStats object
            table_analyzer: TableAnalyzer object (optional, for table distribution)
        """
        self.stats = data_type_stats
        self.table_analyzer = table_analyzer
    
    def generate(self) -> str:
        """
        Generate Markdown table for data type distribution
        
        Returns:
            Markdown formatted table
        """
        if not self.stats or not self.stats.data_type_counts:
            return "## Data Type Distribution\n\nNo data type information available.\n"
        
        markdown = "## Data Type Distribution\n\n"
        
        # Group types into categories
        type_categories = self._categorize_types()
        
        # Summary table by category
        markdown += "### Distribution by Category\n\n"
        markdown += self._generate_category_table(type_categories)
        markdown += "\n"
        
        # Insights
        markdown += self._generate_insights()
        
        return markdown
    
    def _categorize_types(self) -> dict:
        """
        Group data types into INT, FLOAT, TEXT, DATETIME, BOOLEAN, OTHER
        
        Returns:
            Dict with category as key and (count, types_list) as value
        """
        categories = {
            'INT': {'count': 0, 'types': []},
            'FLOAT': {'count': 0, 'types': []},
            'TEXT': {'count': 0, 'types': []},
            'DATETIME': {'count': 0, 'types': []},
            'BOOLEAN': {'count': 0, 'types': []},
            'OTHER': {'count': 0, 'types': []}
        }
        
        # Type mappings
        int_types = {'int64', 'int', 'int32', 'int16', 'int8'}
        float_types = {'double', 'decimal', 'float', 'currency', 'percentage'}
        text_types = {'string', 'text'}
        datetime_types = {'datetime', 'date', 'datetime2'}
        boolean_types = {'boolean', 'bool'}
        
        # Categorize each type
        for dtype, count in sorted(self.stats.data_type_counts.items(), key=lambda x: x[1], reverse=True):
            # Clean dtype: extract just the type name (remove metadata like lineageTag, etc)
            dtype_clean = self._clean_dtype(str(dtype))
            
            if not dtype_clean:
                continue
                
            dtype_lower = dtype_clean.lower()
            
            if dtype_lower in int_types:
                categories['INT']['count'] += count
                if dtype_clean not in categories['INT']['types']:
                    categories['INT']['types'].append(dtype_clean)
            elif dtype_lower in float_types:
                categories['FLOAT']['count'] += count
                if dtype_clean not in categories['FLOAT']['types']:
                    categories['FLOAT']['types'].append(dtype_clean)
            elif dtype_lower in text_types:
                categories['TEXT']['count'] += count
                if dtype_clean not in categories['TEXT']['types']:
                    categories['TEXT']['types'].append(dtype_clean)
            elif dtype_lower in datetime_types:
                categories['DATETIME']['count'] += count
                if dtype_clean not in categories['DATETIME']['types']:
                    categories['DATETIME']['types'].append(dtype_clean)
            elif dtype_lower in boolean_types:
                categories['BOOLEAN']['count'] += count
                if dtype_clean not in categories['BOOLEAN']['types']:
                    categories['BOOLEAN']['types'].append(dtype_clean)
            else:
                categories['OTHER']['count'] += count
                if dtype_clean not in categories['OTHER']['types']:
                    categories['OTHER']['types'].append(dtype_clean)
        
        # Filter out zero categories
        return {k: v for k, v in categories.items() if v['count'] > 0}
    
    def _clean_dtype(self, dtype_str: str) -> str:
        """
        Clean data type string by extracting just the type name
        Handles cases where dtype contains metadata like lineageTag, summarizeBy, etc
        
        Args:
            dtype_str: Raw data type string
            
        Returns:
            Cleaned data type name
        """
        if not dtype_str:
            return 'Unknown'
        
        # Extract just the first line/word (the actual type)
        dtype_clean = dtype_str.split('\n')[0].strip()
        dtype_clean = dtype_str.split('\t')[0].strip()
        
        # Handle cases where there are multiple words
        parts = dtype_clean.split()
        if parts:
            dtype_clean = parts[0]
        
        # Remove any trailing metadata markers
        for marker in ['lineageTag', 'summarizeBy', 'sourceColumn', 'formatString']:
            if marker in dtype_clean:
                dtype_clean = dtype_clean.split(marker)[0].strip()
        
        return dtype_clean if dtype_clean else 'Unknown'
    
    def _generate_category_table(self, type_categories: dict) -> str:
        """Generate summary table by category"""
        markdown = "| Data Type Category | Count | % of Total | Types |\n"
        markdown += "|-------------------|-------|-----------|-------|\n"
        
        total = self.stats.total_columns
        
        # Sort by count descending
        for category in sorted(type_categories.items(), key=lambda x: x[1]['count'], reverse=True):
            cat_name, cat_data = category
            count = cat_data['count']
            percentage = (count / total * 100) if total > 0 else 0
            
            # Build types string with max 2 types shown
            types_list = cat_data['types'][:2]
            types_str = ', '.join(types_list)
            
            if len(cat_data['types']) > 2:
                types_str += f", +{len(cat_data['types'])-2} more"
            
            markdown += f"| **{cat_name}** | {count} | {percentage:.1f}% | {types_str} |\n"
        
        # Total row
        markdown += f"| **TOTAL** | **{total}** | **100.0%** | |\n"
        
        return markdown
    
    def _generate_insights(self) -> str:
        """Generate insights about data types"""
        if not self.stats.data_type_counts:
            return ""
        
        insights = "### Key Insights\n\n"
        
        # Most common type
        if self.stats.most_common_type:
            most_pct = (self.stats.most_common_count / self.stats.total_columns) * 100
            insights += f"- **Most Common Type**: {self.stats.most_common_type} ({self.stats.most_common_count} columns, {most_pct:.1f}%)\n"
        
        # Category percentages
        if self.stats.text_columns > 0:
            text_pct = (self.stats.text_columns / self.stats.total_columns) * 100
            insights += f"- **Text Columns**: {self.stats.text_columns} ({text_pct:.1f}%)\n"
        
        if self.stats.numeric_columns > 0:
            num_pct = (self.stats.numeric_columns / self.stats.total_columns) * 100
            insights += f"- **Numeric Columns**: {self.stats.numeric_columns} ({num_pct:.1f}%)\n"
        
        if self.stats.date_columns > 0:
            date_pct = (self.stats.date_columns / self.stats.total_columns) * 100
            insights += f"- **Date/Time Columns**: {self.stats.date_columns} ({date_pct:.1f}%)\n"
        
        if self.stats.boolean_columns > 0:
            bool_pct = (self.stats.boolean_columns / self.stats.total_columns) * 100
            insights += f"- **Boolean Columns**: {self.stats.boolean_columns} ({bool_pct:.1f}%)\n"
        
        # Type variety
        variety = len([v for v in self.stats.data_type_counts.values() if v > 0])
        insights += f"- **Type Variety**: {variety} different data types used\n"
        
        # Warnings
        if self.stats.text_columns > (self.stats.total_columns * 0.6):
            insights += f"- ⚠️ **Alert**: Heavy reliance on text types (>60%)\n"
        
        return insights
    
    def __repr__(self) -> str:
        """String representation"""
        return f"DataTypeTableGenerator(types={len(self.stats.data_type_counts) if self.stats else 0})"
