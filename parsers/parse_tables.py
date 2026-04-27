#!/usr/bin/env python3
"""
Parser for Power BI tables from TMDL definition.
Outputs: tables.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


class TableParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.tables = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse all TMDL table files"""
        tables_dir = self.tmdl_dir / "tables"
        
        if not tables_dir.exists():
            return []
        
        for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
            table_name = tmdl_file.stem
            table_data = self._parse_table_file(tmdl_file, table_name)
            if table_data:
                self.tables.append(table_data)
        
        return self.tables
    
    def _parse_table_file(self, file_path: Path, table_name: str) -> Dict[str, Any]:
        """Parse a single TMDL table file"""
        content = file_path.read_text(encoding='utf-8')
        
        columns = self._extract_columns(content)
        measures = self._extract_measures(content)
        
        return {
            'name': table_name,
            'columns': columns,
            'measures': measures,
            'column_count': len(columns),
            'measure_count': len(measures),
            'is_calculation': len(columns) == 0 and len(measures) > 0,
            'is_parameter': 'DATATABLE' in content,
            'file': str(file_path)
        }
    
    def _extract_columns(self, content: str) -> List[Dict[str, str]]:
        """Extract columns from TMDL content"""
        columns = []
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for column definition at indent level 1 (single tab)
            if line.strip().startswith('column '):
                col_def = line.strip()
                col_name = col_def.replace('column ', '').strip()
                
                # Initialize column data
                datatype = 'string'
                
                # Look ahead for column properties (indented with at least 2 tabs)
                j = i + 1
                while j < len(lines):
                    prop_line = lines[j]
                    if not prop_line.strip():
                        # Skip blank lines
                        j += 1
                        continue
                    # Stop if we hit a property at lower indent level (new column)
                    if prop_line and not prop_line.startswith('\t\t'):
                        break
                    # Extract dataType
                    if 'dataType:' in prop_line:
                        datatype_match = re.search(r'dataType\s*:\s*(\S+)', prop_line)
                        if datatype_match:
                            datatype = datatype_match.group(1)
                    j += 1
                
                # Detect if it's a calculated column
                is_calculated = ' = ' in col_name
                
                columns.append({
                    'name': col_name,
                    'dataType': datatype,
                    'is_calculated': is_calculated
                })
                i = j if j > i + 1 else i + 1
            else:
                i += 1
        
        return columns
    
    def _extract_measures(self, content: str) -> List[Dict[str, str]]:
        """Extract measures from TMDL content"""
        measures = []
        measure_pattern = r'measure\s+([^\n=]+)(?:\s*=|$)'
        
        for match in re.finditer(measure_pattern, content):
            measure_name = match.group(1).strip().strip("'\"")
            measures.append({
                'name': measure_name
            })
        
        return measures


def parse_tables(tmdl_dir: str, output_file: str = None) -> List[Dict[str, Any]]:
    """Main function to parse tables"""
    parser = TableParser(tmdl_dir)
    tables = parser.parse()
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=2, ensure_ascii=False)
    
    return tables


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_tables.py <tmdl_dir> [output_file]")
        sys.exit(1)
    
    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "tables.json"
    
    tables = parse_tables(tmdl_dir, output_file)
    print(f"✓ Parsed {len(tables)} tables")
