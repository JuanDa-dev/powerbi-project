"""
DAX Complexity Statistics
Analyzes DAX measure complexity patterns
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter
from analyzers import MeasureAnalyzer, MeasureAnalysis


@dataclass
class DAXComplexityStats:
    """Statistics about DAX measure complexity"""
    # Expression length stats
    avg_expression_length: float = 0.0
    max_expression_length: int = 0
    min_expression_length: int = 0
    median_expression_length: float = 0.0
    
    # Complexity stats
    avg_complexity_score: float = 0.0
    max_complexity_score: float = 0.0
    min_complexity_score: float = 0.0
    
    # Function usage
    total_functions_used: int = 0
    unique_functions_count: int = 0
    most_common_functions: List[Tuple[str, int]] = field(default_factory=list)
    avg_functions_per_measure: float = 0.0
    
    # Nesting levels
    max_nesting_level: int = 0
    avg_nesting_level: float = 0.0
    
    # Dependencies
    measures_with_dependencies: int = 0
    avg_dependencies_per_measure: float = 0.0
    max_dependencies: int = 0
    
    # Most complex measures
    top_complex_measures: List[Dict[str, any]] = field(default_factory=list)
    
    # Categorization
    simple_measures: int = 0  # Complexity < 10
    moderate_measures: int = 0  # Complexity 10-30
    complex_measures: int = 0  # Complexity > 30
    
    # Function categories
    aggregation_functions: int = 0  # SUM, COUNT, AVERAGE, etc.
    filter_functions: int = 0  # FILTER, CALCULATE, ALL, etc.
    time_intelligence_functions: int = 0  # DATEADD, TOTALYTD, etc.
    logical_functions: int = 0  # IF, SWITCH, AND, OR, etc.


class DAXComplexityAnalyzer:
    """
    Analyzes DAX complexity patterns and statistics
    """
    
    # Function categories
    AGGREGATION_FUNCS = {'SUM', 'SUMX', 'AVERAGE', 'AVERAGEX', 'COUNT', 'COUNTROWS', 'COUNTA', 'MAX', 'MIN', 'MAXX', 'MINX'}
    FILTER_FUNCS = {'FILTER', 'CALCULATE', 'ALL', 'ALLEXCEPT', 'ALLSELECTED', 'VALUES', 'DISTINCT'}
    TIME_INTEL_FUNCS = {'DATEADD', 'SAMEPERIODLASTYEAR', 'TOTALYTD', 'DATESYTD', 'DATESBETWEEN'}
    LOGICAL_FUNCS = {'IF', 'SWITCH', 'AND', 'OR', 'NOT'}
    
    def __init__(self, measure_analyzer: MeasureAnalyzer):
        """
        Initialize DAX complexity analyzer
        
        Args:
            measure_analyzer: Analyzed measure data
        """
        self.measure_analyzer = measure_analyzer
        self.stats: Optional[DAXComplexityStats] = None
    
    def analyze(self) -> DAXComplexityStats:
        """
        Analyze DAX complexity patterns
        
        Returns:
            DAXComplexityStats object
        """
        analyses = self.measure_analyzer.analyses
        
        if not analyses:
            return DAXComplexityStats()
        
        # Expression lengths
        lengths = [a.expression_length for a in analyses]
        sorted_lengths = sorted(lengths)
        
        # Complexity scores
        complexity_scores = [a.complexity_score for a in analyses]
        
        # Nesting levels
        nesting_levels = [a.nesting_level for a in analyses]
        
        # Function analysis
        all_functions = []
        for analysis in analyses:
            all_functions.extend(analysis.dax_functions)
        
        function_counter = Counter(all_functions)
        most_common = function_counter.most_common(10)
        
        # Dependencies
        measures_with_deps = [a for a in analyses if a.referenced_measures]
        dependency_counts = [len(a.referenced_measures) for a in analyses]
        
        # Categorize complexity
        simple = sum(1 for s in complexity_scores if s < 10)
        moderate = sum(1 for s in complexity_scores if 10 <= s <= 30)
        complex_count = sum(1 for s in complexity_scores if s > 30)
        
        # Top complex measures
        top_complex = sorted(analyses, key=lambda x: x.complexity_score, reverse=True)[:10]
        top_complex_data = [
            {
                'name': m.name,
                'table': m.table,
                'complexity': m.complexity_score,
                'length': m.expression_length,
                'functions': len(m.dax_functions),
                'dependencies': len(m.referenced_measures)
            }
            for m in top_complex
        ]
        
        # Categorize functions
        agg_count = sum(count for func, count in function_counter.items() if func in self.AGGREGATION_FUNCS)
        filter_count = sum(count for func, count in function_counter.items() if func in self.FILTER_FUNCS)
        time_count = sum(count for func, count in function_counter.items() if func in self.TIME_INTEL_FUNCS)
        logical_count = sum(count for func, count in function_counter.items() if func in self.LOGICAL_FUNCS)
        
        # Build statistics
        self.stats = DAXComplexityStats(
            # Lengths
            avg_expression_length=round(sum(lengths) / len(lengths), 2),
            max_expression_length=max(lengths),
            min_expression_length=min(lengths),
            median_expression_length=sorted_lengths[len(sorted_lengths) // 2],
            
            # Complexity
            avg_complexity_score=round(sum(complexity_scores) / len(complexity_scores), 2),
            max_complexity_score=max(complexity_scores),
            min_complexity_score=min(complexity_scores),
            
            # Functions
            total_functions_used=len(all_functions),
            unique_functions_count=len(function_counter),
            most_common_functions=most_common,
            avg_functions_per_measure=round(len(all_functions) / len(analyses), 2),
            
            # Nesting
            max_nesting_level=max(nesting_levels),
            avg_nesting_level=round(sum(nesting_levels) / len(nesting_levels), 2),
            
            # Dependencies
            measures_with_dependencies=len(measures_with_deps),
            avg_dependencies_per_measure=round(sum(dependency_counts) / len(analyses), 2),
            max_dependencies=max(dependency_counts) if dependency_counts else 0,
            
            # Top complex
            top_complex_measures=top_complex_data,
            
            # Categorization
            simple_measures=simple,
            moderate_measures=moderate,
            complex_measures=complex_count,
            
            # Function categories
            aggregation_functions=agg_count,
            filter_functions=filter_count,
            time_intelligence_functions=time_count,
            logical_functions=logical_count
        )
        
        return self.stats
    
    def get_stats(self) -> Optional[DAXComplexityStats]:
        """Get the generated statistics"""
        return self.stats
    
    def get_complexity_distribution(self) -> Dict[str, int]:
        """Get distribution of complexity levels"""
        if not self.stats:
            return {}
        
        return {
            'simple': self.stats.simple_measures,
            'moderate': self.stats.moderate_measures,
            'complex': self.stats.complex_measures
        }
    
    def get_function_category_distribution(self) -> Dict[str, int]:
        """Get distribution of function categories"""
        if not self.stats:
            return {}
        
        return {
            'aggregation': self.stats.aggregation_functions,
            'filter': self.stats.filter_functions,
            'time_intelligence': self.stats.time_intelligence_functions,
            'logical': self.stats.logical_functions
        }
    
    def __repr__(self) -> str:
        """String representation"""
        if self.stats:
            return f"DAXComplexityAnalyzer(avg_complexity={self.stats.avg_complexity_score})"
        return "DAXComplexityAnalyzer(not analyzed)"
