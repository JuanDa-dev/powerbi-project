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
    table_type: str  # 'fact', 'dimension', 'bridge', 'parameter', 'calculation', 'calculated', 'unknown'
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
        
        # BUG FIX #5: Add logging to detect naming mismatches
        self._log_table_name_mismatch()
        
        # Build relationship map
        self._build_relationship_map()
    
    def _log_table_name_mismatch(self):
        """BUG FIX #5: Log tables in relationships vs model for debugging"""
        # Get all table names from model
        model_table_names = {t.name for t in self.tables}
        
        # Get all table names from relationships
        rel_table_names = set()
        for rel in self.relationships:
            rel_table_names.add(rel.from_table)
            rel_table_names.add(rel.to_table)
        
        # Log for debugging
        print("\n" + "=" * 70)
        print("DEBUG: Table Name Analysis")
        print("=" * 70)
        print(f"Tables in model: {sorted(model_table_names)}")
        print(f"Tables in relationships: {sorted(rel_table_names)}")
        
        # Check for mismatches
        missing_in_model = rel_table_names - model_table_names
        not_in_relationships = model_table_names - rel_table_names
        
        if missing_in_model:
            print(f"\n⚠️  WARNING: Tables in relationships but NOT in model:")
            for table_name in sorted(missing_in_model):
                print(f"   - {table_name} (POSSIBLE TYPO)")
        
        if not_in_relationships:
            print(f"\n✓ Tables in model with NO relationships (isolated):")
            for table_name in sorted(not_in_relationships):
                print(f"   - {table_name}")
        
        print("=" * 70 + "\n")
    
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
    
    def _count_table_relationships(self, table_name: str) -> int:
        """
        BUG FIX #5: Count relationships for a table with intelligent fallback
        
        Tries:
        1. Exact match in relationship_map
        2. Case-insensitive match (if no exact match found)
        3. Returns 0 if no match found
        """
        # Try exact match first
        if table_name in self.relationship_map:
            return len(self.relationship_map[table_name])
        
        # Try case-insensitive match
        table_name_lower = table_name.lower()
        for rel_table_name, connected_tables in self.relationship_map.items():
            if rel_table_name.lower() == table_name_lower:
                return len(connected_tables)
        
        # No match found
        return 0
    
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
        
        # BUG FIX #5: Use smarter relationship counting with fallback for case-insensitive match
        relationship_count = self._count_table_relationships(table.name)
        
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
        Classify table as fact, dimension, or other using priority-based heuristics
        
        Priority order (STRICT):
        0. SPECIAL TABLE TYPES (highest priority - checked FIRST):
           - table['name'] == "Calculations" or "_Measures", "_Calc", "Medidas" → Calculation
           - columns == 0 AND measures > 0 → Calculation
           - param_ prefix → Parameter
        
        1. Name PREFIXES:
           - fact_, fct_          → Fact
           - dim_                 → Dimension
           - bridge_              → Bridge (subtype of Dimension)
           - cal_, dim_calendario → Calendar (subtype of Dimension)
        
        2. Only if NO prefix match, evaluate heuristics:
           - >15 cols + numeric cols + ≥1 relationship → Fact
           - Column with amount/quantity keywords + (>10 cols OR >0 relationships) → Fact
           - Most connected table in graph (hub) → Fact candidate
        
        3. Fallback → Unknown
        
        Returns:
            Tuple of (type, confidence, reasons)
        """
        reasons = []
        
        # Calculated tables are usually special purpose
        if is_calculated:
            return ('calculated', 1.0, ['Table contains calculated columns'])
        
        name_lower = table.name.lower()
        
        # ========== PRIORITY 0: SPECIAL TABLE TYPES (HIGHEST PRIORITY) ==========
        # BUG FIX #3: Detect Calculation tables
        calculation_names = ['calculations', '_measures', '_calc', 'medidas']
        if name_lower in calculation_names or table.name.endswith(('_Measures', '_Calc')):
            confidence = 0.99
            reasons.append(f"Table name '{table.name}' is a calculation/measure container")
            return ('calculation', confidence, reasons)
        
        # BUG FIX #3: If 0 columns but has measures, it's a calculation table
        if column_count == 0 and measure_count > 0:
            confidence = 0.95
            reasons.append(f"Table has 0 columns but {measure_count} measures (calculation table)")
            return ('calculation', confidence, reasons)
        
        # BUG FIX #4: Parameter tables (param_ prefix)
        if name_lower.startswith('param_'):
            confidence = 0.95
            reasons.append(f"Table name '{table.name}' starts with 'param_' prefix (PARAMETER)")
            return ('parameter', confidence, reasons)
        
        # ========== PRIORITY 1: NAME PREFIXES ==========
        # BUG FIX #2: Prefixes must be checked FIRST and have absolute priority
        
        # Fact table prefixes
        fact_prefixes = ['fact_', 'fct_']
        if any(name_lower.startswith(prefix) for prefix in fact_prefixes):
            confidence = 0.95
            reasons.append(f"Table name '{table.name}' starts with fact table prefix")
            return ('fact', confidence, reasons)
        
        # ⭐ Dimension prefixes (MUST come before heuristics to fix dim_dict_americas_pl)
        if name_lower.startswith('dim_'):
            confidence = 0.95
            reasons.append(f"Table name '{table.name}' starts with 'dim_' prefix (DIMENSION)")
            return ('dimension', confidence, reasons)
        
        # Bridge table prefix
        if name_lower.startswith('bridge_'):
            confidence = 0.90
            reasons.append(f"Table name '{table.name}' starts with 'bridge_' prefix")
            return ('dimension', confidence, reasons)  # Bridge is a subtype of dimension
        
        # Parameter table prefix
        if name_lower.startswith('param_'):
            confidence = 0.90
            reasons.append(f"Table name '{table.name}' starts with 'param_' prefix (parameter table)")
            return ('dimension', confidence, reasons)  # Parameter is a subtype of dimension
        
        # Calendar table prefixes
        calendar_prefixes = ['cal_', 'dim_calendario', 'date_', 'calendar_']
        if any(name_lower.startswith(prefix) or name_lower == prefix.rstrip('_') 
               for prefix in calendar_prefixes):
            confidence = 0.90
            reasons.append(f"Table name '{table.name}' matches calendar table pattern")
            return ('dimension', confidence, reasons)  # Calendar is a subtype of dimension
        
        # ========== PRIORITY 2: HEURISTICS (only if no prefix matched) ==========
        numeric_column_types = {'int64', 'int', 'double', 'decimal', 'currency', 'float'}
        amount_keywords = ['amount', 'quantity', 'qty', 'value', 'price', 'cost', 'total', 
                          'sum', 'monto', 'valor', 'importe', 'gasto', 'spend']
        
        has_numeric_cols = any(
            (col.data_type or '').lower() in numeric_column_types 
            for col in table.columns
        )
        
        has_amount_cols = any(
            any(keyword in col.name.lower() for keyword in amount_keywords)
            for col in table.columns
        )
        
        # Heuristic: Large table with numeric columns and relationships
        if column_count > 15 and has_numeric_cols and relationship_count > 0:
            confidence = 0.90
            reasons.append(f"Has {column_count} columns with numeric types and {relationship_count} relationships (fact indicator)")
            return ('fact', confidence, reasons)
        
        # Heuristic: Amount/quantity columns with reasonable size
        if has_amount_cols and (column_count > 10 or relationship_count > 0):
            confidence = 0.80
            col_examples = [col.name for col in table.columns if any(kw in col.name.lower() for kw in amount_keywords)][:3]
            reasons.append(f"Contains amount/quantity columns: {', '.join(col_examples)} (fact indicator)")
            return ('fact', confidence, reasons)
        
        # Heuristic: Most connected table in graph (hub/center)
        max_degree_overall = max([len(self.relationship_map.get(t.name, [])) for t in self.tables], default=0)
        
        if max_degree_overall > 2 and relationship_count == max_degree_overall:
            confidence = 0.75
            reasons.append(f"Most connected table ({relationship_count} relationships) - typical fact table hub")
            return ('fact', confidence, reasons)
        
        # ========== PRIORITY 3: FALLBACK TO TRADITIONAL HEURISTICS ==========
        score_fact = 0
        score_dim = 0
        
        # Name-based heuristics
        if any(keyword in name_lower for keyword in ['sales', 'order']):
            score_fact += 2
            reasons.append(f"Table name '{table.name}' suggests fact table")
        
        if any(keyword in name_lower for keyword in ['dimension', 'customer', 'product']):
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
    
    def get_calculation_tables(self) -> List[TableAnalysis]:
        """BUG FIX #3: Get all calculation/measure container tables"""
        return [a for a in self.analyses.values() if a.table_type == 'calculation']
    
    def get_parameter_tables(self) -> List[TableAnalysis]:
        """BUG FIX #4: Get all parameter tables"""
        return [a for a in self.analyses.values() if a.table_type == 'parameter']
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics of table types"""
        summary = {
            'total': len(self.analyses),
            'fact': len([a for a in self.analyses.values() if a.table_type == 'fact']),
            'dimension': len([a for a in self.analyses.values() if a.table_type == 'dimension']),
            'calculation': len([a for a in self.analyses.values() if a.table_type == 'calculation']),
            'parameter': len([a for a in self.analyses.values() if a.table_type == 'parameter']),
            'calculated': len([a for a in self.analyses.values() if a.is_calculated]),
            'unknown': len([a for a in self.analyses.values() if a.table_type == 'unknown']),
            'hidden': len([a for a in self.analyses.values() if a.is_hidden])
        }
        return summary
    
    def __repr__(self) -> str:
        """String representation"""
        return f"TableAnalyzer(tables={len(self.analyses)})"
