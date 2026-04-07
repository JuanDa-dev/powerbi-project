"""
TMDL Parser
Parses Tabular Model Definition Language format and converts to ModelBIM format
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import re
from .model_bim_parser import ModelBIM, Table, Column, Measure, Relationship


class TMDLParser:
    """
    Parser for TMDL format files
    
    TMDL is a text-based format that's more Git-friendly than model.bim.
    Each table, measure, etc. is in a separate .tmdl file.
    """
    
    def __init__(self, tmdl_directory: str):
        """
        Initialize the TMDL parser
        
        Args:
            tmdl_directory: Path to the TMDL definition directory
        """
        self.tmdl_dir = Path(tmdl_directory)
        
        if not self.tmdl_dir.exists():
            raise FileNotFoundError(f"TMDL directory not found: {tmdl_directory}")
        
        if not self.tmdl_dir.is_dir():
            raise ValueError(f"TMDL path must be a directory: {tmdl_directory}")
    
    def parse(self) -> ModelBIM:
        """
        Parse TMDL files and return ModelBIM object
        
        Returns:
            ModelBIM object compatible with the rest of the pipeline
        """
        tables = []
        relationships = []
        all_measures = []
        
        # Parse model.tmdl for metadata
        model_tmdl = self.tmdl_dir / 'model.tmdl'
        model_name = "TMDL Model"
        if model_tmdl.exists():
            content = model_tmdl.read_text(encoding='utf-8')
            name_match = re.search(r'model\s+(\w+)', content)
            if name_match:
                model_name = name_match.group(1)
        
        # Parse tables directory
        tables_dir = self.tmdl_dir / 'tables'
        if tables_dir.exists():
            for table_file in tables_dir.glob('*.tmdl'):
                table_data = self._parse_table_file(table_file)
                if table_data:
                    tables.append(table_data['table'])
                    all_measures.extend(table_data['measures'])
        
        # Parse relationships
        relationships_file = self.tmdl_dir / 'relationships.tmdl'
        if relationships_file.exists():
            relationships = self._parse_relationships_file(relationships_file)
        
        # Create ModelBIM object
        # Store measures in a special attribute that will be picked up by the measures property
        model = ModelBIM(
            name=model_name,
            compatibility_level=1200,
            culture="en-US",
            tables=tables,
            relationships=relationships,
            hierarchies=[],
            roles=[],
            data_sources=[]
        )
        
        # Add measures as a custom attribute
        model._all_measures = all_measures
        
        return model
    
    def _parse_table_file(self, file_path: Path) -> Optional[Dict]:
        """Parse a table TMDL file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract table name
            table_match = re.search(r'table\s+(.+)', content)
            if not table_match:
                return None
            
            table_name = table_match.group(1).strip()
            if table_name.startswith("'") and table_name.endswith("'"):
                table_name = table_name[1:-1]
            
            # Parse columns
            columns = []
            column_pattern = r'column\s+(.+?)\n\s+dataType:\s*(.+?)(?=\n\s*(?:column|measure|partition|$))'
            for match in re.finditer(column_pattern, content, re.MULTILINE | re.DOTALL):
                col_name = match.group(1).strip()
                if col_name.startswith("'") and col_name.endswith("'"):
                    col_name = col_name[1:-1]
                data_type = match.group(2).strip()
                
                columns.append(Column(
                    name=col_name,
                    data_type=data_type,
                    source_column=col_name,
                    is_hidden=False,
                    expression=None
                ))
            
            # Parse measures
            measures = []
            measure_pattern = r'measure\s+(.+?)\s*=\s*(.+?)(?=\n\s*(?:measure|column|partition|annotation|$))'
            for match in re.finditer(measure_pattern, content, re.MULTILINE | re.DOTALL):
                measure_name = match.group(1).strip()
                if measure_name.startswith("'") and measure_name.endswith("'"):
                    measure_name = measure_name[1:-1]
                expression = match.group(2).strip()
                
                measures.append(Measure(
                    name=measure_name,
                    table=table_name,
                    expression=expression,
                    is_hidden=False
                ))
            
            # Create table object
            table = Table(
                name=table_name,
                columns=columns,
                is_hidden=False
            )
            
            return {
                'table': table,
                'measures': measures
            }
            
        except Exception as e:
            print(f"Warning: Failed to parse table {file_path.name}: {e}")
            return None
    
    def _parse_relationships_file(self, file_path: Path) -> List[Relationship]:
        """Parse relationships TMDL file"""
        relationships = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Split by relationship blocks
            rel_blocks = re.split(r'\nrelationship\s+', content)
            
            for block in rel_blocks[1:]:  # Skip first empty block
                # Extract relationship properties from format: fromColumn: Table.Column
                from_column_match = re.search(r'fromColumn:\s*(.+?)\.(.+)', block)
                to_column_match = re.search(r'toColumn:\s*(.+?)\.(.+)', block)
                
                if from_column_match and to_column_match:
                    from_table = from_column_match.group(1).strip()
                    from_column = from_column_match.group(2).strip()
                    to_table = to_column_match.group(1).strip()
                    to_column = to_column_match.group(2).strip()
                    
                    # Clean quotes
                    from_table = from_table.strip("'\"")
                    from_column = from_column.strip("'\"")
                    to_table = to_table.strip("'\"")
                    to_column = to_column.strip("'\"")
                    
                    # Generate a name for the relationship
                    rel_name = f"{from_table}_{from_column}_to_{to_table}_{to_column}"
                    
                    relationships.append(Relationship(
                        name=rel_name,
                        from_table=from_table,
                        from_column=from_column,
                        to_table=to_table,
                        to_column=to_column,
                        cardinality="many_to_one",
                        is_active=True
                    ))
        
        except Exception as e:
            print(f"Warning: Failed to parse relationships: {e}")
        
        return relationships
    
    def __repr__(self) -> str:
        """String representation of the parser"""
        return f"TMDLParser(path={self.tmdl_dir})"
