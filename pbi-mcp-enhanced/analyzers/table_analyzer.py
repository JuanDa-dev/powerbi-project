"""
Table Analyzer
Classifies tables as fact/dimension and analyzes table properties
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from parsers.model_bim_parser import Table, ModelBIM


@dataclass
class TableAnalysis:
    """Analysis results for a single table"""
    name: str
    table_type: str  # 'fact', 'dimension', 'bridge', 'calculated', 'unknown'
    column_count: int
    measure_count: int
    hierarchy_count: int
    relationship_count: int = 0
    is_hidden: bool = False
    is_calculated: bool = False
    has_partitions: bool = False
    partition_count: int = 0
    source_type: Optional[str] = None
    confidence: float = 1.0  # Confidence in classification (0-1)
    reasons: List[str] = field(default_factory=list)


class TableAnalyzer:
    """
    Analyzes tables in a Power BI model
    Classifies tables as fact or dimension tables
    """
    
    def __init__(self, tables: List[Table], relationships: List = None):
        """
        Initialize the table analyzer
        
        Args:
            tables: List of Table objects
            relationships: List of Relationship objects (optional)
        """
        self.tables = tables
        self.relationships = relationships or []
        self.analyses: Dict[str, TableAnalysis] = {}
        self.relationship_map: Dict[str, List[str]] = {}
        
        # Build relationship map
        self._build_relationship_map()
    
    def analyze(self) -> Dict[str, TableAnalysis]:
        """
        Analyze all tables in the model
        
        Returns:
            Dictionary mapping table names to analysis results
        """
        for table in self.tables:
            analysis = self._analyze_table(table)
            self.analyses[table.name] = analysis
        
        return self.analyses
    
    def _build_relationship_map(self):
        """Build a map of tables to their relationships"""
        for rel in self.relationships:
            # From table (many side typically)
            if rel.from_table not in self.relationship_map:
                self.relationship_map[rel.from_table] = []
            self.relationship_map[rel.from_table].append(rel.to_table)
            
            # To table (one side typically)
            if rel.to_table not in self.relationship_map:
                self.relationship_map[rel.to_table] = []
            self.relationship_map[rel.to_table].append(rel.from_table)
    
    def _analyze_table(self, table: Table) -> TableAnalysis:
        """
        Analyze a single table
        
        Args:
            table: Table object to analyze
        
        Returns:
            TableAnalysis object
        """
        # Basic counts
        column_count = len(table.columns)
        measure_count = len(table.measures)
        hierarchy_count = len(table.hierarchies)
        relationship_count = len(self.relationship_map.get(table.name, []))
        
        # Check if calculated
        is_calculated = any(col.expression for col in table.columns)
        
        # Check partitions
        has_partitions = len(table.partitions) > 0
        partition_count = len(table.partitions)
        
        # Classify table type
        table_type, confidence, reasons = self._classify_table(
            table, 
            column_count, 
            measure_count, 
            relationship_count,
            is_calculated
        )
        
        return TableAnalysis(
            name=table.name,
            table_type=table_type,
            column_count=column_count,
            measure_count=measure_count,
            hierarchy_count=hierarchy_count,
            relationship_count=relationship_count,
            is_hidden=table.is_hidden,
            is_calculated=is_calculated,
            has_partitions=has_partitions,
            partition_count=partition_count,
            source_type=self._detect_source_type(table),
            confidence=confidence,
            reasons=reasons
        )
    
    def _classify_table(self, table: Table, column_count: int, 
                       measure_count: int, relationship_count: int,
                       is_calculated: bool) -> tuple[str, float, List[str]]:
        """
        Classify table as fact, dimension, or other
        
        Returns:
            Tuple of (type, confidence, reasons)
        """
        reasons = []
        score_fact = 0
        score_dim = 0
        
        # Calculated tables are usually special purpose
        if is_calculated:
            return ('calculated', 1.0, ['Table contains calculated columns'])
        
        # Name-based heuristics
        name_lower = table.name.lower()
        if any(keyword in name_lower for keyword in ['fact', 'sales', 'transaction', 'order']):
            score_fact += 2
            reasons.append(f"Table name '{table.name}' suggests fact table")
        
        if any(keyword in name_lower for keyword in ['dim', 'dimension', 'calendar', 'date', 'customer', 'product']):
            score_dim += 2
            reasons.append(f"Table name '{table.name}' suggests dimension table")
        
        # Measure count (fact tables typically have measures)
        if measure_count > 3:
            score_fact += 2
            reasons.append(f"Has {measure_count} measures (typical for fact tables)")
        elif measure_count == 0:
            score_dim += 1
            reasons.append("No measures (typical for dimension tables)")
        
        # Hierarchy count (dimension tables often have hierarchies)
        if len(table.hierarchies) > 0:
            score_dim += 1
            reasons.append(f"Has {len(table.hierarchies)} hierarchies (typical for dimensions)")
        
        # Column count (dimensions typically have fewer columns than facts)
        if column_count > 20:
            score_fact += 1
            reasons.append(f"Large column count ({column_count}) suggests fact table")
        elif column_count <= 10:
            score_dim += 1
            reasons.append(f"Small column count ({column_count}) suggests dimension")
        
        # Relationship count (dimensions are typically on "one" side of many relationships)
        if relationship_count > 3:
            score_dim += 1
            reasons.append(f"Connected to {relationship_count} tables (typical for dimensions)")
        
        # Key indicators
        has_key = any(col.is_key for col in table.columns)
        if has_key:
            score_dim += 1
            reasons.append("Has key column (typical for dimensions)")
        
        # Make decision
        if score_fact > score_dim:
            confidence = min(score_fact / (score_fact + score_dim + 1), 1.0)
            return ('fact', confidence, reasons)
        elif score_dim > score_fact:
            confidence = min(score_dim / (score_fact + score_dim + 1), 1.0)
            return ('dimension', confidence, reasons)
        else:
            return ('unknown', 0.5, ['Could not confidently classify table'])
    
    def _detect_source_type(self, table: Table) -> Optional[str]:
        """Detect the source type of a table"""
        if not table.partitions:
            return None
        
        # Check first partition for source info
        first_partition = table.partitions[0]
        
        if 'mode' in first_partition:
            mode = first_partition['mode']
            if mode == 'import':
                return 'Import'
            elif mode == 'directQuery':
                return 'DirectQuery'
        
        return 'Unknown'
    
    def get_fact_tables(self) -> List[TableAnalysis]:
        """Get all tables classified as fact tables"""
        return [a for a in self.analyses.values() if a.table_type == 'fact']
    
    def get_dimension_tables(self) -> List[TableAnalysis]:
        """Get all tables classified as dimension tables"""
        return [a for a in self.analyses.values() if a.table_type == 'dimension']
    
    def get_calculated_tables(self) -> List[TableAnalysis]:
        """Get all calculated tables"""
        return [a for a in self.analyses.values() if a.is_calculated]
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics of table types"""
        summary = {
            'total': len(self.analyses),
            'fact': len([a for a in self.analyses.values() if a.table_type == 'fact']),
            'dimension': len([a for a in self.analyses.values() if a.table_type == 'dimension']),
            'calculated': len([a for a in self.analyses.values() if a.is_calculated]),
            'unknown': len([a for a in self.analyses.values() if a.table_type == 'unknown']),
            'hidden': len([a for a in self.analyses.values() if a.is_hidden])
        }
        return summary
    
    def __repr__(self) -> str:
        """String representation"""
        return f"TableAnalyzer(tables={len(self.analyses)})"
