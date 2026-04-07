"""
Model Summary Statistics
Generates high-level summary statistics for the entire model
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModelSummary:
    """Complete summary statistics for a Power BI model"""
    # Basic counts
    total_tables: int = 0
    fact_tables: int = 0
    dimension_tables: int = 0
    calculated_tables: int = 0
    hidden_tables: int = 0
    
    total_columns: int = 0
    calculated_columns: int = 0
    hidden_columns: int = 0
    key_columns: int = 0
    
    total_measures: int = 0
    hidden_measures: int = 0
    
    total_relationships: int = 0
    active_relationships: int = 0
    inactive_relationships: int = 0
    bidirectional_relationships: int = 0
    
    total_hierarchies: int = 0
    hidden_hierarchies: int = 0
    
    total_roles: int = 0
    roles_with_rls: int = 0
    
    # Derived metrics
    avg_columns_per_table: float = 0.0
    avg_measures_per_table: float = 0.0
    avg_relationships_per_table: float = 0.0
    
    # Model metadata
    model_name: str = ""
    compatibility_level: int = 0
    culture: str = ""
    data_sources_count: int = 0
    
    # Analysis timestamp
    analysis_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Additional insights
    has_security: bool = False
    has_hierarchies: bool = False
    has_calculated_tables: bool = False
    isolated_tables: int = 0


class ModelSummaryGenerator:
    """
    Generates comprehensive summary statistics for a Power BI model
    """
    
    def __init__(
        self,
        table_analyzer,
        measure_analyzer,
        relationship_analyzer
    ):
        """
        Initialize the summary generator
        
        Args:
            table_analyzer: TableAnalyzer instance
            measure_analyzer: MeasureAnalyzer instance
            relationship_analyzer: RelationshipAnalyzer instance
        """
        self.table_analyzer = table_analyzer
        self.measure_analyzer = measure_analyzer
        self.relationship_analyzer = relationship_analyzer
        self.summary: Optional[ModelSummary] = None
    
    def generate(self) -> ModelSummary:
        """
        Generate comprehensive model summary
        
        Returns:
            ModelSummary object with all statistics
        """
        # Count tables by classification
        fact_tables = sum(1 for a in self.table_analyzer.analyses.values() 
                         if a.table_type == 'fact')
        dim_tables = sum(1 for a in self.table_analyzer.analyses.values() 
                        if a.table_type == 'dimension')
        hidden_tables = sum(1 for t in self.table_analyzer.tables if t.is_hidden)
        
        # Count columns
        total_columns = sum(len(t.columns or []) for t in self.table_analyzer.tables)
        calculated_columns = sum(1 for t in self.table_analyzer.tables 
                                for c in (t.columns or []) 
                                if c.expression is not None)
        hidden_columns = sum(1 for t in self.table_analyzer.tables 
                            for c in (t.columns or []) 
                            if c.is_hidden)
        key_columns = sum(1 for t in self.table_analyzer.tables 
                         for c in (t.columns or []) 
                         if c.is_key)
        
        # Count measures
        total_measures = len(self.measure_analyzer.analyses)
        hidden_measures = sum(1 for m in self.measure_analyzer.analyses if m.is_hidden)
        
        # Count relationships
        total_relationships = len(self.relationship_analyzer.analyses)
        active_relationships = sum(1 for r in self.relationship_analyzer.analyses if r.is_active)
        inactive_relationships = total_relationships - active_relationships
        bidirectional_relationships = sum(1 for r in self.relationship_analyzer.analyses 
                                        if r.cross_filtering.lower() in ['both', 'bidirectional'])
        
        # Count hierarchies
        total_hierarchies = sum(len(t.hierarchies or []) for t in self.table_analyzer.tables)
        hidden_hierarchies = 0  # Not available in simple model
        
        # Roles
        total_roles = 0
        roles_with_rls = 0
        
        # Calculate averages
        total_tables = len(self.table_analyzer.tables)
        avg_columns = total_columns / total_tables if total_tables > 0 else 0
        avg_measures = total_measures / total_tables if total_tables > 0 else 0
        avg_relationships = total_relationships / total_tables if total_tables > 0 else 0
        
        # Find isolated tables
        connected_tables = set()
        for rel in self.relationship_analyzer.analyses:
            connected_tables.add(rel.from_table)
            connected_tables.add(rel.to_table)
        isolated_tables_count = len([t for t in self.table_analyzer.tables 
                                     if t.name not in connected_tables])
        
        # Build summary
        self.summary = ModelSummary(
            total_tables=total_tables,
            fact_tables=fact_tables,
            dimension_tables=dim_tables,
            calculated_tables=0,  # Not tracked
            hidden_tables=hidden_tables,
            total_columns=total_columns,
            calculated_columns=calculated_columns,
            hidden_columns=hidden_columns,
            key_columns=key_columns,
            total_measures=total_measures,
            hidden_measures=hidden_measures,
            total_relationships=total_relationships,
            active_relationships=active_relationships,
            inactive_relationships=inactive_relationships,
            bidirectional_relationships=bidirectional_relationships,
            total_hierarchies=total_hierarchies,
            hidden_hierarchies=hidden_hierarchies,
            total_roles=total_roles,
            roles_with_rls=roles_with_rls,
            avg_columns_per_table=round(avg_columns, 2),
            avg_measures_per_table=round(avg_measures, 2),
            avg_relationships_per_table=round(avg_relationships, 2),
            model_name="",  # Not available
            compatibility_level=0,  # Not available
            culture="",  # Not available
            data_sources_count=0,  # Not available
            has_security=total_roles > 0,
            has_hierarchies=total_hierarchies > 0,
            has_calculated_tables=False,
            isolated_tables=isolated_tables_count
        )
        
        return self.summary
