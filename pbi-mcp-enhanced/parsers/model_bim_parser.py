"""
Model.bim Parser
Parses Power BI Tabular Model (JSON format)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Column:
    """Represents a column in a table"""
    name: str
    data_type: str
    source_column: Optional[str] = None
    is_hidden: bool = False
    is_key: bool = False
    lineage_tag: Optional[str] = None
    expression: Optional[str] = None  # For calculated columns
    format_string: Optional[str] = None
    data_category: Optional[str] = None


@dataclass
class Measure:
    """Represents a DAX measure"""
    name: str
    expression: str
    table: str
    format_string: Optional[str] = None
    description: Optional[str] = None
    is_hidden: bool = False
    lineage_tag: Optional[str] = None
    display_folder: Optional[str] = None


@dataclass
class Hierarchy:
    """Represents a hierarchy"""
    name: str
    table: str
    levels: List[Dict[str, str]] = field(default_factory=list)
    is_hidden: bool = False


@dataclass
class Relationship:
    """Represents a relationship between tables"""
    name: Optional[str]
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cross_filtering_behavior: str = "oneDirection"
    is_active: bool = True
    cardinality: Optional[str] = None
    lineage_tag: Optional[str] = None


@dataclass
class Table:
    """Represents a table in the model"""
    name: str
    columns: List[Column] = field(default_factory=list)
    measures: List[Measure] = field(default_factory=list)
    hierarchies: List[Hierarchy] = field(default_factory=list)
    is_hidden: bool = False
    lineage_tag: Optional[str] = None
    source: Optional[str] = None
    partitions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Role:
    """Represents a security role (RLS)"""
    name: str
    description: Optional[str] = None
    table_permissions: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ModelBIM:
    """Represents the complete Power BI Tabular Model"""
    name: str
    tables: List[Table]
    relationships: List[Relationship]
    hierarchies: List['Hierarchy'] = field(default_factory=list)
    roles: List[Role] = field(default_factory=list)
    culture: str = "en-US"
    compatibility_level: int = 1500
    data_sources: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def measures(self) -> List[Measure]:
        """Extract all measures from all tables"""
        all_measures = []
        for table in self.tables:
            # Check if table has measures attribute
            if hasattr(table, 'measures') and table.measures:
                all_measures.extend(table.measures)
        # Also check for _all_measures attribute (TMDL parser)
        if hasattr(self, '_all_measures'):
            all_measures.extend(self._all_measures)
        return all_measures


class ModelBIMParser:
    """Parser for model.bim files"""
    
    def __init__(self, model_bim_path: str):
        """
        Initialize the model.bim parser
        
        Args:
            model_bim_path: Path to the model.bim file
        """
        self.model_path = Path(model_bim_path)
        self.raw_data: Optional[Dict] = None
        self.model: Optional[ModelBIM] = None
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"model.bim not found: {model_bim_path}")
    
    def parse(self) -> ModelBIM:
        """
        Parse the model.bim file
        
        Returns:
            ModelBIM object with complete model structure
        """
        # Load JSON
        with open(self.model_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        
        # Extract model data
        model_data = self.raw_data.get('model', {})
        
        # Parse tables
        tables = self._parse_tables(model_data.get('tables', []))
        
        # Parse relationships
        relationships = self._parse_relationships(model_data.get('relationships', []))
        
        # Parse roles
        roles = self._parse_roles(model_data.get('roles', []))
        
        # Create model object
        self.model = ModelBIM(
            name=self.raw_data.get('name', 'Unknown'),
            tables=tables,
            relationships=relationships,
            roles=roles,
            culture=model_data.get('culture', 'en-US'),
            compatibility_level=self.raw_data.get('compatibilityLevel', 1500),
            data_sources=model_data.get('dataSources', [])
        )
        
        return self.model
    
    def _parse_tables(self, tables_data: List[Dict]) -> List[Table]:
        """Parse tables from raw data"""
        tables = []
        
        for table_data in tables_data:
            table_name = table_data.get('name', 'Unknown')
            
            # Parse columns
            columns = []
            for col_data in table_data.get('columns', []):
                column = Column(
                    name=col_data.get('name', 'Unknown'),
                    data_type=col_data.get('dataType', 'string'),
                    source_column=col_data.get('sourceColumn'),
                    is_hidden=col_data.get('isHidden', False),
                    is_key=col_data.get('isKey', False),
                    lineage_tag=col_data.get('lineageTag'),
                    expression=col_data.get('expression'),
                    format_string=col_data.get('formatString'),
                    data_category=col_data.get('dataCategory')
                )
                columns.append(column)
            
            # Parse measures
            measures = []
            for measure_data in table_data.get('measures', []):
                measure = Measure(
                    name=measure_data.get('name', 'Unknown'),
                    expression=measure_data.get('expression', ''),
                    table=table_name,
                    format_string=measure_data.get('formatString'),
                    description=measure_data.get('description'),
                    is_hidden=measure_data.get('isHidden', False),
                    lineage_tag=measure_data.get('lineageTag'),
                    display_folder=measure_data.get('displayFolder')
                )
                measures.append(measure)
            
            # Parse hierarchies
            hierarchies = []
            for hier_data in table_data.get('hierarchies', []):
                hierarchy = Hierarchy(
                    name=hier_data.get('name', 'Unknown'),
                    table=table_name,
                    levels=[{
                        'name': level.get('name', ''),
                        'column': level.get('column', '')
                    } for level in hier_data.get('levels', [])],
                    is_hidden=hier_data.get('isHidden', False)
                )
                hierarchies.append(hierarchy)
            
            # Create table
            table = Table(
                name=table_name,
                columns=columns,
                measures=measures,
                hierarchies=hierarchies,
                is_hidden=table_data.get('isHidden', False),
                lineage_tag=table_data.get('lineageTag'),
                source=table_data.get('source'),
                partitions=table_data.get('partitions', [])
            )
            tables.append(table)
        
        return tables
    
    def _parse_relationships(self, rel_data: List[Dict]) -> List[Relationship]:
        """Parse relationships from raw data"""
        relationships = []
        
        for rel in rel_data:
            relationship = Relationship(
                name=rel.get('name'),
                from_table=rel.get('fromTable', 'Unknown'),
                from_column=rel.get('fromColumn', 'Unknown'),
                to_table=rel.get('toTable', 'Unknown'),
                to_column=rel.get('toColumn', 'Unknown'),
                cross_filtering_behavior=rel.get('crossFilteringBehavior', 'oneDirection'),
                is_active=rel.get('isActive', True),
                cardinality=rel.get('fromCardinality'),
                lineage_tag=rel.get('lineageTag')
            )
            relationships.append(relationship)
        
        return relationships
    
    def _parse_roles(self, roles_data: List[Dict]) -> List[Role]:
        """Parse security roles from raw data"""
        roles = []
        
        for role_data in roles_data:
            role = Role(
                name=role_data.get('name', 'Unknown'),
                description=role_data.get('description'),
                table_permissions=role_data.get('tablePermissions', [])
            )
            roles.append(role)
        
        return roles
    
    def get_model(self) -> ModelBIM:
        """
        Get the parsed model (must call parse() first)
        
        Returns:
            ModelBIM object
        """
        if self.model is None:
            raise RuntimeError("Must call parse() before get_model()")
        return self.model
    
    def get_table(self, table_name: str) -> Optional[Table]:
        """
        Get a specific table by name
        
        Args:
            table_name: Name of the table
        
        Returns:
            Table object or None if not found
        """
        if self.model is None:
            return None
        
        for table in self.model.tables:
            if table.name == table_name:
                return table
        return None
    
    def get_all_measures(self) -> List[Measure]:
        """
        Get all measures from all tables
        
        Returns:
            List of all measures
        """
        if self.model is None:
            return []
        
        all_measures = []
        for table in self.model.tables:
            all_measures.extend(table.measures)
        return all_measures
    
    def get_all_columns(self) -> List[tuple[str, Column]]:
        """
        Get all columns from all tables
        
        Returns:
            List of (table_name, column) tuples
        """
        if self.model is None:
            return []
        
        all_columns = []
        for table in self.model.tables:
            for column in table.columns:
                all_columns.append((table.name, column))
        return all_columns
    
    def __repr__(self) -> str:
        """String representation of the parser"""
        return f"ModelBIMParser(path={self.model_path}, parsed={self.model is not None})"
