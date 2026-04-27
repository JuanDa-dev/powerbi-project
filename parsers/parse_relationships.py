#!/usr/bin/env python3
"""
Parser for Power BI relationships from TMDL definition.
Outputs: relationships.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple


class RelationshipParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.relationships = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse relationships from TMDL"""
        rel_file = self.tmdl_dir / "relationships.tmdl"
        
        if not rel_file.exists():
            return []
        
        content = rel_file.read_text(encoding='utf-8')
        self._extract_relationships(content)
        
        return self.relationships
    
    def _extract_relationships(self, content: str):
        """Extract all relationships from content"""
        rel_pattern = r'relationship\s+([a-f0-9\-]+)\s*\n\s*(?:toCardinality:\s*many\s*\n\s*)?fromColumn:\s*([^\n]+)\n\s*toColumn:\s*([^\n]+)'
        
        for match in re.finditer(rel_pattern, content):
            rel_id = match.group(1).strip()
            from_col = match.group(2).strip()
            to_col = match.group(3).strip()
            
            from_table, from_column = self._parse_table_column(from_col)
            to_table, to_column = self._parse_table_column(to_col)
            
            if from_table and to_table:
                # Many-to-One by default unless specified
                self.relationships.append({
                    'id': rel_id,
                    'from_table': from_table,
                    'from_column': from_column,
                    'to_table': to_table,
                    'to_column': to_column,
                    'cardinality': 'Many-to-One',
                    'cross_filter_direction': 'Both'
                })
    
    def _parse_table_column(self, spec: str) -> Tuple[str, str]:
        """Parse 'table.column' format"""
        parts = spec.split('.')
        if len(parts) >= 2:
            table = parts[0].strip().strip("'\"[]")
            column = parts[1].strip().strip("'\"[]")
            return table, column
        return None, None


def parse_relationships(tmdl_dir: str, output_file: str = None) -> List[Dict[str, Any]]:
    """Main function to parse relationships"""
    parser = RelationshipParser(tmdl_dir)
    relationships = parser.parse()
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(relationships, f, indent=2, ensure_ascii=False)
    
    return relationships


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_relationships.py <tmdl_dir> [output_file]")
        sys.exit(1)
    
    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "relationships.json"
    
    relationships = parse_relationships(tmdl_dir, output_file)
    print(f"✓ Parsed {len(relationships)} relationships")
