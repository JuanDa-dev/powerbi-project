#!/usr/bin/env python3
"""
Parser for Power BI measures and calculations from TMDL definition.
Outputs: 
  - measures.json (all measures with metadata)
  - unused_measures.json (measures with no dependencies or references)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DAX FUNCTION CATALOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DAX_FUNCTIONS: Dict[str, int] = {
    # Aggregations
    "SUM": 1, "COUNT": 1, "AVERAGE": 1, "MIN": 1, "MAX": 1,
    "COUNTA": 1, "COUNTBLANK": 1, "DISTINCTCOUNT": 2,
    # Iterators
    "SUMX": 3, "AVERAGEX": 3, "COUNTX": 3, "MAXX": 3, "MINX": 3,
    "RANKX": 4, "PERCENTILEX.INC": 4, "PERCENTILEX.EXC": 4,
    # Filter context
    "CALCULATE": 3, "CALCULATETABLE": 3,
    "ALL": 2, "ALLEXCEPT": 2, "ALLSELECTED": 2, "KEEPFILTERS": 2,
    "FILTER": 3, "REMOVEFILTERS": 2,
    # Relationships
    "RELATED": 2, "RELATEDTABLE": 2, "USERELATIONSHIP": 3,
    "CROSSFILTER": 3, "TREATAS": 3,
    # Time intelligence
    "TOTALYTD": 3, "TOTALQTD": 3, "TOTALMTD": 3,
    "SAMEPERIODLASTYEAR": 3, "PREVIOUSYEAR": 3, "PREVIOUSMONTH": 3,
    "PARALLELPERIOD": 4, "DATEADD": 3, "DATESYTD": 3,
    # Table functions
    "VALUES": 2, "DISTINCT": 2, "TOPN": 3, "SAMPLE": 3,
    "ADDCOLUMNS": 4, "SELECTCOLUMNS": 3, "SUMMARIZE": 4,
    # Logical
    "IF": 2, "IFERROR": 2, "SWITCH": 3,
    "AND": 1, "OR": 1, "NOT": 1,
    # Divide
    "DIVIDE": 1,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MEASURE PARSER CLASS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
                    
                    # Extract dependencies: [MeasureName] references
                    dependencies = self._extract_dependencies(full_expression, measure_name)
                    
                    # Detect functions used
                    functions_used = self._detect_functions(full_expression)
                    
                    # Calculate complexity (no arbitrary cap)
                    complexity_score = self._calculate_complexity(full_expression, functions_used)
                    
                    # Detect if stub (empty/incomplete)
                    is_stub = self._is_stub(full_expression)
                    
                    # Store measure
                    self.measures.append({
                        'name': measure_name,
                        'table': table_name,
                        'expression': full_expression,
                        'complexity_score': complexity_score,
                        'functions_used': functions_used,
                        'dependencies': dependencies,
                        'is_stub': is_stub,
                        'expression_length': len(full_expression),
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
        
        # Don't truncate — keep full expression for analysis
        return expr
    
    def _detect_functions(self, expression: str) -> List[str]:
        """Detect DAX functions used in expression"""
        found = set()
        expr_upper = expression.upper()
        
        for fn in DAX_FUNCTIONS:
            # Match function name followed by '(' to avoid partial matches
            if re.search(r'\b' + fn.replace('.', r'\.') + r'\s*\(', expr_upper):
                found.add(fn)
        
        return sorted(found)
    
    def _extract_dependencies(self, expression: str, own_name: str) -> List[str]:
        """
        Extract [MeasureName] references from DAX expression.
        Excludes column references and the measure itself.
        """
        # Match [something] NOT preceded by a word char (table name)
        candidates = re.findall(r'(?<!\w)\[([^\]]+)\]', expression)
        deps = set()
        
        for c in candidates:
            # Skip if it's the measure itself
            if c != own_name:
                deps.add(c)
        
        return sorted(deps)
    
    def _calculate_complexity(self, expression: str, functions_used: List[str]) -> float:
        """
        Dynamic complexity score with no arbitrary cap.
        
        Components:
          - Function weights × occurrences
          - Nesting depth
          - VAR declarations
          - Expression length (log-scaled)
        """
        if not expression or expression == "[Expression not fully captured]":
            return 0.0
        
        expr_upper = expression.upper()
        
        # 1. Function weights
        func_score = 0.0
        for fn in functions_used:
            weight = DAX_FUNCTIONS.get(fn, 1)
            occurrences = len(re.findall(r'\b' + fn.replace('.', r'\.') + r'\s*\(', expr_upper))
            func_score += weight * occurrences
        
        # 2. Nesting depth
        max_depth = 0
        depth = 0
        for ch in expression:
            if ch == "(":
                depth += 1
                max_depth = max(max_depth, depth)
            elif ch == ")":
                depth = max(0, depth - 1)
        nesting_score = max_depth * 0.5
        
        # 3. VAR declarations
        var_count = len(re.findall(r'\bVAR\b', expr_upper))
        var_score = var_count * 1.5
        
        # 4. Expression length (log-scaled, capped at 3)
        import math
        length_score = min(math.log10(max(len(expression), 1)), 3)
        
        total = round(func_score + nesting_score + var_score + length_score, 2)
        return total
    
    def _is_stub(self, expression: str) -> bool:
        """True if expression is empty, placeholder, or trivially short"""
        if not expression or expression == "[Expression not fully captured]":
            return True
        clean = expression.replace("[Expression not fully captured]", "").strip()
        clean = clean.replace("`", "").strip()
        return len(clean) < 5


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNUSED MEASURES ANALYZER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze_unused_measures(
    measures: List[Dict[str, Any]],
    pages: Optional[List[Dict]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Analyze which measures are unused.
    
    A measure is considered "used" if:
    1. Another measure depends on it
    2. It's used in a page/visual
    
    Returns:
      - List of unused measures
      - Analysis summary
    """
    
    # Build measure name set for quick lookup
    all_measure_names = {m['name'] for m in measures}
    
    # Track which measures are referenced
    referenced = set()
    
    # 1. Check cross-measure dependencies
    for m in measures:
        for dep in m.get('dependencies', []):
            if dep in all_measure_names:
                referenced.add(dep)
    
    # 2. Check pages/visuals (if provided)
    if pages:
        for page in pages:
            for visual in page.get('visuals', []):
                for field in visual.get('fields', []):
                    field_ref = field.get('ref', '')
                    # Simple heuristic: if field matches measure name
                    if field_ref in all_measure_names:
                        referenced.add(field_ref)
    
    # 3. Identify unused measures
    unused = [m for m in measures if m['name'] not in referenced]
    
    # 4. Build analysis summary
    summary = {
        "total_measures": len(measures),
        "used_measures": len(referenced),
        "unused_measures": len(unused),
        "unused_percentage": round(len(unused) / len(measures) * 100, 1) if measures else 0,
        "cleanup_candidates": [
            {
                "name": m['name'],
                "table": m['table'],
                "complexity": m['complexity_score'],
                "is_stub": m.get('is_stub', False),
                "reason": "Stub/incomplete measure" if m.get('is_stub') else "Not referenced by any measure or visual"
            }
            for m in unused
        ]
    }
    
    return unused, summary


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_measures(
    tmdl_dir: str,
    output_file: str = None,
    pages: Optional[List[Dict]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Main function to parse measures and detect unused ones.
    
    Returns:
      - All measures
      - Unused measures
      - Analysis summary
    """
    parser = MeasureParser(tmdl_dir)
    measures = parser.parse()
    
    # Resolve cross-measure dependencies
    measures = _resolve_dependencies(measures)
    
    # Analyze unused measures
    unused, analysis = analyze_unused_measures(measures, pages)
    
    # Save all measures
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # All measures
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(measures, f, indent=2, ensure_ascii=False)
        
        # Unused measures report
        unused_path = output_path.parent / "unused_measures.json"
        with open(unused_path, 'w', encoding='utf-8') as f:
            json.dump({
                "analysis": analysis,
                "unused_measures": unused
            }, f, indent=2, ensure_ascii=False)
    
    return measures, unused, analysis


def _resolve_dependencies(measures: List[Dict]) -> List[Dict]:
    """
    Cross-reference [MeasureName] dependencies against actual measure names.
    Filters out column references.
    """
    known_names = {m["name"] for m in measures}
    
    for m in measures:
        confirmed = [d for d in m.get("dependencies", []) if d in known_names]
        m["dependencies"] = confirmed
    
    return measures


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_measures.py <tmdl_dir> [output_file]")
        sys.exit(1)
    
    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "measures.json"
    
    measures, unused, analysis = parse_measures(tmdl_dir, output_file)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"  Measures Analysis")
    print(f"{'='*60}\n")
    print(f"  Total measures:       {analysis['total_measures']}")
    print(f"  Used measures:        {analysis['used_measures']}")
    print(f"  Unused measures:      {analysis['unused_measures']}")
    print(f"  Unused percentage:    {analysis['unused_percentage']}%\n")
    
    if unused:
        print(f"  Cleanup Candidates (unused measures):\n")
        for m in analysis['cleanup_candidates'][:10]:
            reason_label = "STUB" if m['is_stub'] else "UNREFERENCED"
            print(f"    • {m['name']} [{reason_label}]")
            print(f"      Table: {m['table']}, Complexity: {m['complexity']}")
            print(f"      Reason: {m['reason']}\n")
        
        if len(analysis['cleanup_candidates']) > 10:
            print(f"    ... and {len(analysis['cleanup_candidates']) - 10} more")
    
    print(f"\n  Output files:")
    print(f"    • measures.json")
    print(f"    • unused_measures.json")
    print(f"\n{'='*60}\n")