#!/usr/bin/env python3
"""
Parser for Power BI measures and calculations from TMDL definition.
Outputs: measures.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


class MeasureParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.measures = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse all measures from TMDL tables"""
        tables_dir = self.tmdl_dir / "tables"
        
        if not tables_dir.exists():
            return []
        
        for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
            table_name = tmdl_file.stem
            content = tmdl_file.read_text(encoding='utf-8')
            self._extract_measures(content, table_name)
        
        return self.measures
    
    def _extract_measures(self, content: str, table_name: str):
        """Extract measures from a table"""
        measure_pattern = r'measure\s+([^\n=]+)(?:\s*=\s*((?:[^\n]|\n(?!\t))+)|$)'
        
        for match in re.finditer(measure_pattern, content, re.MULTILINE):
            measure_name = match.group(1).strip().strip("'\"")
            measure_expression = match.group(2).strip() if match.group(2) else ""
            
            # Count DAX complexity
            complexity_score = self._calculate_complexity(measure_expression)
            
            self.measures.append({
                'name': measure_name,
                'table': table_name,
                'expression': measure_expression[:200] + "..." if len(measure_expression) > 200 else measure_expression,
                'complexity_score': complexity_score
            })
    
    def _calculate_complexity(self, expression: str) -> int:
        """Simple complexity score based on DAX functions"""
        score = 1
        
        # Count common DAX functions
        functions = [
            'CALCULATE', 'FILTER', 'ALL', 'RELATED', 'RELATEDTABLE',
            'SUMX', 'MAXX', 'MINX', 'AVERAGEX', 'COUNTX',
            'IF', 'AND', 'OR', 'NOT',
            'VALUES', 'DISTINCT', 'TOPN'
        ]
        
        for func in functions:
            score += expression.count(func) * 2
        
        # Count aggregations
        score += expression.count('SUM') + expression.count('COUNT') + expression.count('AVERAGE')
        
        return min(score, 10)  # Cap at 10


def parse_measures(tmdl_dir: str, output_file: str = None) -> List[Dict[str, Any]]:
    """Main function to parse measures"""
    parser = MeasureParser(tmdl_dir)
    measures = parser.parse()
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(measures, f, indent=2, ensure_ascii=False)
    
    return measures


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_measures.py <tmdl_dir> [output_file]")
        sys.exit(1)
    
    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "measures.json"
    
    measures = parse_measures(tmdl_dir, output_file)
    print(f"✓ Parsed {len(measures)} measures")
