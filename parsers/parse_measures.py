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
        """Extract measures from a table using improved parsing"""
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a measure definition
            if re.match(r'\s*measure\s+', line):
                # Extract measure name and check for inline expression
                match = re.match(r'\s*measure\s+([^\s=]+)\s*(?:=\s*(.*))?', line)
                
                if match:
                    measure_name = match.group(1).strip().strip("'\"")
                    inline_expr = match.group(2).strip() if match.group(2) else ""
                    
                    expr_lines = []
                    
                    # Check if inline expression is just backticks - if so, continue to next lines
                    if inline_expr and inline_expr != '```':
                        expr_lines.append(inline_expr)
                    elif inline_expr == '```':
                        # Multiline expression coming
                        expr_lines.append('[MULTILINE]')
                    
                    # Collect remaining expression lines
                    i += 1
                    measure_indent = len(line) - len(line.lstrip())
                    in_expression = (inline_expr == '```' or bool(inline_expr))
                    backtick_count = inline_expr.count('```')
                    
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.lstrip()
                        next_indent = len(next_line) - len(next_line.lstrip())
                        
                        # Stop if we hit another measure at same or lower indentation
                        if next_stripped.startswith('measure ') and next_indent <= measure_indent:
                            break
                        
                        # Stop if we hit table or other non-expression content
                        if next_stripped.startswith('table '):
                            break
                        
                        # Check for metadata lines that end the measure
                        if (next_stripped.startswith(('lineageTag:', 'formatString:', 'annotation ', 'dataCategory:')) 
                            and next_indent <= measure_indent + 8):
                            break
                        
                        # Track backticks to find end of multiline expression
                        backtick_count += next_line.count('```')
                        
                        # Add content lines
                        if next_stripped:
                            expr_lines.append(next_stripped)
                        
                        i += 1
                        
                        # Stop if we've closed all backticks
                        if backtick_count >= 2 and in_expression:
                            break
                    
                    # Join and clean expression
                    full_expression = ' '.join(expr_lines)
                    full_expression = self._clean_expression(full_expression)
                    
                    # Calculate complexity
                    complexity_score = self._calculate_complexity(full_expression)
                    
                    # Store measure
                    self.measures.append({
                        'name': measure_name,
                        'table': table_name,
                        'expression': full_expression,
                        'complexity_score': complexity_score
                    })
                else:
                    i += 1
            else:
                i += 1
    
    def _clean_expression(self, expr: str) -> str:
        """Clean up DAX expression"""
        # Remove backticks
        expr = expr.replace('```', ' ').strip()
        
        # Remove internal markers
        expr = expr.replace('[MULTILINE]', '').strip()
        
        # Remove extra whitespace
        expr = ' '.join(expr.split())
        
        # If expression is empty or just whitespace, mark as incomplete
        if not expr:
            return "[Expression not fully captured]"
        
        # Truncate very long expressions but keep first meaningful part
        if len(expr) > 300:
            expr = expr[:297] + "..."
        
        return expr
    
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
