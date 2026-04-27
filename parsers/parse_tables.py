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
        col_pattern = r"column\s+(['\"]?)([^'\"\n]+)\1\s*\n((?:\t[^\n]*\n)*?)"
        
        for match in re.finditer(col_pattern, content):
            col_name = match.group(2).strip()
            col_block = match.group(3)
            
            datatype_match = re.search(r'dataType:\s*(\w+)', col_block)
            datatype = datatype_match.group(1) if datatype_match else 'string'
            
            columns.append({
                'name': col_name,
                'dataType': datatype
            })
        
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
