"""
Measure Analyzer
Analyzes DAX measures and their complexity
"""

import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import Counter
from parsers.model_bim_parser import Measure, ModelBIM


@dataclass
class MeasureAnalysis:
    """Analysis results for a single measure"""
    name: str
    table: str
    expression: str
    expression_length: int
    is_hidden: bool = False
    format_string: Optional[str] = None
    display_folder: Optional[str] = None
    complexity_score: float = 0.0
    dax_functions: List[str] = field(default_factory=list)
    referenced_measures: List[str] = field(default_factory=list)
    referenced_tables: List[str] = field(default_factory=list)
    nesting_level: int = 0
    is_placeholder: bool = False  # True if expression is empty/not implemented


@dataclass
class MeasureStatistics:
    """Statistics about measures in the model"""
    total_measures: int
    hidden_measures: int
    avg_expression_length: float
    max_expression_length: int
    min_expression_length: int
    most_common_functions: List[tuple[str, int]]
    avg_complexity: float
    measures_by_folder: Dict[str, int]
    measures_per_table: Dict[str, int]


class MeasureAnalyzer:
    """
    Analyzes DAX measures in a Power BI model
    """
    
    # Common DAX functions
    DAX_FUNCTIONS = [
        'SUM', 'SUMX', 'AVERAGE', 'AVERAGEX', 'COUNT', 'COUNTROWS', 'COUNTA',
        'CALCULATE', 'FILTER', 'ALL', 'ALLEXCEPT', 'ALLSELECTED',
        'RELATED', 'RELATEDTABLE', 'USERELATIONSHIP',
        'IF', 'SWITCH', 'AND', 'OR', 'NOT',
        'DIVIDE', 'MAX', 'MIN', 'MAXX', 'MINX',
        'RANKX', 'TOPN', 'EARLIER', 'EARLIEST',
        'VALUES', 'DISTINCT', 'CONCATENATEX',
        'DATEADD', 'SAMEPERIODLASTYEAR', 'TOTALYTD', 'DATESYTD',
        'VAR', 'RETURN', 'FORMAT', 'SELECTEDVALUE'
    ]
    
    def __init__(self, measures: List[Measure]):
        """
        Initialize the measure analyzer
        
        Args:
            measures: List of Measure objects
        """
        self.measures = measures
        self.analyses: List[MeasureAnalysis] = []
        self.statistics: Optional[MeasureStatistics] = None
        self.measure_names: Set[str] = set()
    
    def analyze(self) -> List[MeasureAnalysis]:
        """
        Analyze all measures
        
        Returns:
            List of MeasureAnalysis objects
        """
        self.analyses = []
        
        # First pass: collect all measure names
        for measure in self.measures:
            self.measure_names.add(measure.name)
        
        # Second pass: analyze each measure
        for measure in self.measures:
            analysis = self._analyze_measure(measure)
            self.analyses.append(analysis)
        
        # Calculate statistics
        self._calculate_statistics()
        
        return self.analyses
    
    def _analyze_measure(self, measure: Measure) -> MeasureAnalysis:
        """
        Analyze a single measure
        
        Args:
            measure: Measure object to analyze
        
        Returns:
            MeasureAnalysis object
        """
        expression = measure.expression or ""
        is_placeholder = measure.is_placeholder
        
        # If it's a placeholder, set complexity to 0
        if is_placeholder:
            complexity = 0.0
            dax_functions = []
            referenced_measures = []
            referenced_tables = []
            nesting = 0
        else:
            # Find DAX functions used
            dax_functions = self._extract_dax_functions(expression)
            
            # Find referenced measures
            referenced_measures = self._extract_referenced_measures(expression)
            
            # Find referenced tables
            referenced_tables = self._extract_referenced_tables(expression)
            
            # Calculate complexity
            complexity = self._calculate_complexity(
                expression, 
                dax_functions, 
                referenced_measures
            )
            
            # Calculate nesting level
            nesting = self._calculate_nesting_level(expression)
        
        return MeasureAnalysis(
            name=measure.name,
            table=measure.table,
            expression=expression,
            expression_length=len(expression),
            is_hidden=measure.is_hidden,
            format_string=measure.format_string,
            display_folder=measure.display_folder,
            complexity_score=complexity,
            dax_functions=dax_functions,
            referenced_measures=referenced_measures,
            referenced_tables=referenced_tables,
            nesting_level=nesting,
            is_placeholder=is_placeholder
        )
    
    def _extract_dax_functions(self, expression: str) -> List[str]:
        """Extract DAX functions from expression"""
        functions = []
        expr_upper = expression.upper()
        
        for func in self.DAX_FUNCTIONS:
            if func in expr_upper:
                # Check if it's actually a function call (followed by parenthesis)
                pattern = rf'\b{func}\s*\('
                if re.search(pattern, expr_upper):
                    functions.append(func)
        
        return functions
    
    def _extract_referenced_measures(self, expression: str) -> List[str]:
        """Extract referenced measures from expression"""
        referenced = []
        
        # Pattern: [MeasureName]
        pattern = r'\[([^\]]+)\]'
        matches = re.findall(pattern, expression)
        
        for match in matches:
            if match in self.measure_names:
                referenced.append(match)
        
        return list(set(referenced))  # Remove duplicates
    
    def _extract_referenced_tables(self, expression: str) -> List[str]:
        """Extract referenced tables from expression"""
        tables = []
        
        # Pattern: 'TableName'[Column] or TableName[Column]
        pattern = r"(?:'([^']+)'|\b([A-Za-z_][A-Za-z0-9_]*))(?=\[)"
        matches = re.findall(pattern, expression)
        
        for match in matches:
            table_name = match[0] or match[1]
            if table_name and not table_name.upper() in self.DAX_FUNCTIONS:
                tables.append(table_name)
        
        return list(set(tables))  # Remove duplicates
    
    def _calculate_complexity(self, expression: str, functions: List[str], 
                             referenced_measures: List[str]) -> float:
        """
        Calculate complexity score for a measure
        
        Factors:
        - Expression length
        - Number of functions
        - Number of referenced measures (dependencies)
        - Nesting level
        """
        score = 0.0
        
        # Length factor (normalize to 0-10)
        length_score = min(len(expression) / 100, 10)
        score += length_score
        
        # Function count (2 points per function)
        score += len(functions) * 2
        
        # Referenced measures (3 points per dependency)
        score += len(referenced_measures) * 3
        
        # Nested functions (count nested parentheses)
        max_depth = 0
        current_depth = 0
        for char in expression:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1
        score += max_depth * 2
        
        return round(score, 2)
    
    def _calculate_nesting_level(self, expression: str) -> int:
        """Calculate maximum nesting level of parentheses"""
        max_depth = 0
        current_depth = 0
        
        for char in expression:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1
        
        return max_depth
    
    def _calculate_statistics(self):
        """Calculate statistics about measures"""
        if not self.analyses:
            return
        
        # Function usage
        all_functions = []
        for analysis in self.analyses:
            all_functions.extend(analysis.dax_functions)
        function_counts = Counter(all_functions)
        most_common = function_counts.most_common(10)
        
        # Folders
        folders = Counter(
            a.display_folder for a in self.analyses 
            if a.display_folder
        )
        
        # Per table
        tables = Counter(a.table for a in self.analyses)
        
        # Lengths
        lengths = [a.expression_length for a in self.analyses]
        
        self.statistics = MeasureStatistics(
            total_measures=len(self.analyses),
            hidden_measures=sum(1 for a in self.analyses if a.is_hidden),
            avg_expression_length=round(sum(lengths) / len(lengths), 2) if lengths else 0,
            max_expression_length=max(lengths) if lengths else 0,
            min_expression_length=min(lengths) if lengths else 0,
            most_common_functions=most_common,
            avg_complexity=round(
                sum(a.complexity_score for a in self.analyses) / len(self.analyses), 2
            ) if self.analyses else 0,
            measures_by_folder=dict(folders),
            measures_per_table=dict(tables)
        )
    
    def get_measures_by_table(self, table_name: str) -> List[MeasureAnalysis]:
        """Get all measures for a specific table"""
        return [a for a in self.analyses if a.table == table_name]
    
    def get_most_complex_measures(self, limit: int = 10) -> List[MeasureAnalysis]:
        """Get the most complex measures"""
        return sorted(
            self.analyses, 
            key=lambda x: x.complexity_score, 
            reverse=True
        )[:limit]
    
    def get_measures_with_dependencies(self) -> List[MeasureAnalysis]:
        """Get measures that reference other measures"""
        return [a for a in self.analyses if a.referenced_measures]
    
    def get_statistics(self) -> Optional[MeasureStatistics]:
        """Get measure statistics"""
        return self.statistics
    
    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build a dependency graph of measures"""
        graph = {}
        for analysis in self.analyses:
            graph[analysis.name] = analysis.referenced_measures
        return graph
    
    def __repr__(self) -> str:
        """String representation"""
        return f"MeasureAnalyzer(measures={len(self.analyses)})"
