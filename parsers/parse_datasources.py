#!/usr/bin/env python3
"""
Parser for Power BI data sources and connections.
Outputs: datasources.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


class DataSourceParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.datasources = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse data sources from TMDL definition"""
        # Try to extract from database.tmdl or model.tmdl
        self._extract_from_model_files()
        
        return self.datasources
    
    def _extract_from_model_files(self):
        """Extract data source info from model definition files"""
        model_file = self.tmdl_dir / "model.tmdl"
        
        if model_file.exists():
            content = model_file.read_text(encoding='utf-8')
            
            # Look for source definitions
            source_pattern = r'source\s*=\s*([^\n]+)'
            for match in re.finditer(source_pattern, content):
                source_def = match.group(1).strip()
                
                # Parse source type
                source_type = self._extract_source_type(source_def)
                
                if source_type:
                    self.datasources.append({
                        'type': source_type,
                        'definition': source_def[:100] + "..." if len(source_def) > 100 else source_def
                    })
        
        # Also check expressions.tmdl for M queries
        expr_file = self.tmdl_dir / "expressions.tmdl"
        if expr_file.exists():
            content = expr_file.read_text(encoding='utf-8')
            
            # Count let/in expressions (Power Query)
            if 'let' in content.lower() and 'in' in content.lower():
                self.datasources.append({
                    'type': 'Power Query (M)',
                    'definition': 'Power Query transformations found'
                })
    
    def _extract_source_type(self, source_def: str) -> str:
        """Identify source type from definition"""
        lower_def = source_def.lower()
        
        if 'sql' in lower_def:
            return 'SQL Server'
        elif 'csv' in lower_def or 'text' in lower_def:
            return 'CSV/Text'
        elif 'excel' in lower_def or 'xlsx' in lower_def:
            return 'Excel'
        elif 'sharepoint' in lower_def or 'list' in lower_def:
            return 'SharePoint List'
        elif 'odata' in lower_def:
            return 'OData Feed'
        elif 'web' in lower_def or 'http' in lower_def:
            return 'Web Source'
        elif 'database' in lower_def:
            return 'Database'
        else:
            return 'Other'


def parse_datasources(tmdl_dir: str, output_file: str = None) -> List[Dict[str, Any]]:
    """Main function to parse data sources"""
    parser = DataSourceParser(tmdl_dir)
    datasources = parser.parse()
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(datasources, f, indent=2, ensure_ascii=False)
    
    return datasources


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_datasources.py <tmdl_dir> [output_file]")
        sys.exit(1)
    
    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "datasources.json"
    
    datasources = parse_datasources(tmdl_dir, output_file)
    print(f"✓ Parsed {len(datasources)} data sources")
