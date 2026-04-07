"""
Hierarchy Analyzer
Analyzes hierarchies in the data model
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import Counter
from parsers.model_bim_parser import Hierarchy, ModelBIM


@dataclass
class HierarchyAnalysis:
    """Analysis results for a single hierarchy"""
    name: str
    table: str
    level_count: int
    levels: List[Dict[str, str]]
    is_hidden: bool = False


@dataclass
class HierarchyStatistics:
    """Statistics about hierarchies in the model"""
    total_hierarchies: int
    hidden_hierarchies: int
    avg_levels_per_hierarchy: float
    max_levels: int
    min_levels: int
    hierarchies_per_table: Dict[str, int]
    tables_with_hierarchies: int


class HierarchyAnalyzer:
    """
    Analyzes hierarchies in a Power BI model
    """
    
    def __init__(self, model: ModelBIM):
        """
        Initialize the hierarchy analyzer
        
        Args:
            model: Parsed ModelBIM object
        """
        self.model = model
        self.analyses: List[HierarchyAnalysis] = []
        self.statistics: Optional[HierarchyStatistics] = None
    
    def analyze(self) -> List[HierarchyAnalysis]:
        """
        Analyze all hierarchies in the model
        
        Returns:
            List of HierarchyAnalysis objects
        """
        self.analyses = []
        
        for table in self.model.tables:
            for hierarchy in table.hierarchies:
                analysis = self._analyze_hierarchy(hierarchy)
                self.analyses.append(analysis)
        
        # Calculate statistics
        self._calculate_statistics()
        
        return self.analyses
    
    def _analyze_hierarchy(self, hierarchy: Hierarchy) -> HierarchyAnalysis:
        """
        Analyze a single hierarchy
        
        Args:
            hierarchy: Hierarchy object to analyze
        
        Returns:
            HierarchyAnalysis object
        """
        return HierarchyAnalysis(
            name=hierarchy.name,
            table=hierarchy.table,
            level_count=len(hierarchy.levels),
            levels=hierarchy.levels,
            is_hidden=hierarchy.is_hidden
        )
    
    def _calculate_statistics(self):
        """Calculate statistics about hierarchies"""
        if not self.analyses:
            self.statistics = HierarchyStatistics(
                total_hierarchies=0,
                hidden_hierarchies=0,
                avg_levels_per_hierarchy=0,
                max_levels=0,
                min_levels=0,
                hierarchies_per_table={},
                tables_with_hierarchies=0
            )
            return
        
        # Levels statistics
        level_counts = [a.level_count for a in self.analyses]
        
        # Per table
        tables = Counter(a.table for a in self.analyses)
        
        self.statistics = HierarchyStatistics(
            total_hierarchies=len(self.analyses),
            hidden_hierarchies=sum(1 for a in self.analyses if a.is_hidden),
            avg_levels_per_hierarchy=round(
                sum(level_counts) / len(level_counts), 2
            ) if level_counts else 0,
            max_levels=max(level_counts) if level_counts else 0,
            min_levels=min(level_counts) if level_counts else 0,
            hierarchies_per_table=dict(tables),
            tables_with_hierarchies=len(tables)
        )
    
    def get_hierarchies_by_table(self, table_name: str) -> List[HierarchyAnalysis]:
        """Get all hierarchies for a specific table"""
        return [a for a in self.analyses if a.table == table_name]
    
    def get_visible_hierarchies(self) -> List[HierarchyAnalysis]:
        """Get all visible hierarchies"""
        return [a for a in self.analyses if not a.is_hidden]
    
    def get_statistics(self) -> Optional[HierarchyStatistics]:
        """Get hierarchy statistics"""
        return self.statistics
    
    def __repr__(self) -> str:
        """String representation"""
        return f"HierarchyAnalyzer(hierarchies={len(self.analyses)})"
