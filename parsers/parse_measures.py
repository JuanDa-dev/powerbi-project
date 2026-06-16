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
        # Load column metadata to distinguish columns from measures
        self.columns_by_table = self._load_column_metadata()
        self.all_column_names = set()
        for cols in self.columns_by_table.values():
            self.all_column_names.update(cols)
        
    def _load_column_metadata(self) -> Dict[str, Set[str]]:
        """
        Load column names from all tables to distinguish columns from measures.
        
        Returns: Dict mapping table_name -> set of column names
        """
        columns = {}
        tables_dir = self.tmdl_dir / "tables"
        
        if not tables_dir.exists():
            return columns
        
        for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
            table_name = tmdl_file.stem
            content = tmdl_file.read_text(encoding='utf-8')
            
            # Extract column names from table definition
            col_names = self._extract_column_names(content)
            columns[table_name] = col_names
        
        return columns
    
    def _extract_column_names(self, content: str) -> Set[str]:
        """Extract column names from TMDL table definition."""
        col_names = set()
        
        # Match: column ColumnName = ...
        for match in re.finditer(r'^\s*column\s+([^\s=]+)', content, re.MULTILINE):
            col_name = match.group(1).strip().strip("'\"")
            col_names.add(col_name)
        
        return col_names
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse all measures from TMDL tables"""
        tables_dir = self.tmdl_dir / "tables"
        
        if not tables_dir.exists():
            return []
        
        for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
            table_name = tmdl_file.stem
            content = tmdl_file.read_text(encoding='utf-8')
            self._extract_measures(content, table_name)
        
        # Enrich measures with dependency graph and architectural metrics
        self.measures = self._build_dependency_graph()
        
        return self.measures
    
    def _extract_measures(self, content: str, table_name: str):
        """Extract measures from a table using robust block-based parsing"""
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a measure definition
            if re.match(r'\s*measure\s+', line):
                # Extract measure name - handles both quoted and unquoted names
                # Pattern: measure 'Full Name With Spaces' = ... 
                #      or: measure SimpleName = ...
                name_match = re.match(r"\s*measure\s+(?:'([^']*)'|([^\s=]+))\s*(?:=\s*(.*))?", line)
                
                if name_match:
                    # Group 1: name in quotes, Group 2: name without quotes
                    measure_name = name_match.group(1) if name_match.group(1) else name_match.group(2)
                    measure_name = measure_name.strip().strip("'\"")
                    measure_indent = len(line) - len(line.lstrip())
                    
                    # Extract the full measure block (header + expression + metadata)
                    measure_block = self._extract_measure_block(lines, i, measure_indent)
                    
                    # Parse metadata (description, format, display folder, etc.)
                    metadata = self._parse_measure_metadata(measure_block, measure_name)
                    
                    # Parse DAX expression (new indent-based approach)
                    full_expression = self._parse_dax_expression_new(measure_block)
                    
                    # Extract column dependencies from expression
                    column_dependencies = self._extract_column_dependencies(full_expression)
                    
                    # Extract dependencies: [MeasureName] references
                    measure_dependencies = self._extract_dependencies(full_expression, measure_name)
                    
                    # Detect functions used
                    functions_used = self._detect_functions(full_expression)
                    
                    # Calculate complexity (no arbitrary cap)
                    complexity_score = self._calculate_complexity(full_expression, functions_used)
                    
                    # Detect if stub (empty/incomplete)
                    is_stub = self._is_stub(full_expression)
                    
                    # Detect DAX antipatterns
                    antipatterns = self._detect_antipatterns(full_expression)
                    
                    # Store measure with enriched metadata
                    self.measures.append({
                        'name': measure_name,
                        'table': table_name,
                        'expression': full_expression,
                        'description': metadata.get('description', ''),
                        'display_folder': metadata.get('display_folder', ''),
                        'format_string': metadata.get('format_string', ''),
                        'is_hidden': metadata.get('is_hidden', False),
                        'has_description': bool(metadata.get('description')),
                        'has_format': bool(metadata.get('format_string')),
                        'complexity_score': complexity_score,
                        'functions_used': functions_used,
                        'dependencies': measure_dependencies,
                        'column_dependencies': column_dependencies,
                        'is_stub': is_stub,
                        'expression_length': len(full_expression),
                        # Antipatterns grouped under antipattern_analysis
                        'antipattern_analysis': {
                            'has_antipatterns': antipatterns['has_antipatterns'],
                            'antipattern_count': antipatterns['antipattern_count'],
                            'antipatterns': antipatterns['antipatterns'],
                            'highest_severity': antipatterns['highest_severity'],
                        },
                    })
                    
                    # Skip to end of measure block
                    i += len(measure_block.split('\n'))
                else:
                    i += 1
            else:
                i += 1
    
    def _extract_measure_block(self, lines: List[str], start_idx: int, base_indent: int) -> str:
        """
        Extract complete measure block (from 'measure' keyword to next same-level element).
        
        Returns the raw block text including metadata.
        """
        block = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            line_indent = len(line) - len(line.lstrip())
            line_stripped = line.lstrip()
            
            # For the first line (the measure definition itself), always include it
            if i == start_idx:
                block.append(line)
                i += 1
                continue
            
            # Stop if we hit another top-level keyword at base indentation
            if (line_stripped and line_indent <= base_indent and 
                (line_stripped.startswith(('measure ', 'table ', 'column ', 'partition ')))):
                # Don't include this line
                break
            
            block.append(line)
            i += 1
        
        return '\n'.join(block)
    
    def _parse_dax_expression(self, block: str) -> str:
        """
        DEPRECATED: Use _parse_dax_expression_new instead.
        This method remains for backward compatibility.
        
        TMDL files use indentation, not backticks. Forwarding to new implementation.
        """
        return self._parse_dax_expression_new(block)
    
    def _clean_expression(self, expr: str) -> str:
        """Clean up DAX expression - robust version that preserves actual content"""
        if not expr:
            return "[Expression not fully captured]"
        
        # Remove backticks and backtick markers
        expr = expr.replace('```', ' ').strip()
        expr = expr.replace('[MULTILINE]', '').strip()
        
        # Normalize whitespace
        expr = ' '.join(expr.split())
        
        # If completely empty after cleanup, mark as incomplete
        if not expr or expr.isspace():
            return "[Expression not fully captured]"
        
        # Keep full expression - no truncation
        return expr
    
    def _parse_measure_metadata(self, block: str, measure_name: str) -> Dict[str, Any]:
        """
        Extract measure metadata: description, format, display folder, hidden status.
        
        TMDL format:
            measure 'MeasureName' = <expression>
                displayFolder: "Path/To/Folder"
                formatString: "#,##0"
                description: "Some text"
                hidden: true
        """
        metadata = {
            'description': '',
            'display_folder': '',
            'format_string': '',
            'is_hidden': False,
        }
        
        # Extract description (between quotes after description =)
        desc_match = re.search(r'description:\s*"([^"]*)"', block)
        if desc_match:
            metadata['description'] = desc_match.group(1)
        
        # Extract display folder
        folder_match = re.search(r'displayFolder:\s*"([^"]*)"', block)
        if folder_match:
            metadata['display_folder'] = folder_match.group(1)
        
        # Extract format string
        fmt_match = re.search(r'formatString:\s*"([^"]*)"', block)
        if fmt_match:
            metadata['format_string'] = fmt_match.group(1)
        
        # Check if hidden
        if re.search(r'hidden:\s*true', block, re.IGNORECASE):
            metadata['is_hidden'] = True
        
        return metadata
    
    def _parse_dax_expression_new(self, block: str) -> str:
        """
        Parse DAX expression from measure block handling THREE formats:
        
        Format 1 - INLINE:
            measure 'Name' = [expression]
            
        Format 2 - INDENTED MULTILINE:
            measure 'Name' = 
                VAR x = ...
                RETURN ...
                
        Format 3 - BACKTICKS:
            measure 'Name' = ```
                VAR x = ...
                RETURN ...
            ```
        """
        lines = block.split('\n')
        
        # Find the measure = line
        measure_line_idx = None
        for idx, line in enumerate(lines):
            if re.match(r'\s*measure\s+', line):
                measure_line_idx = idx
                break
        
        if measure_line_idx is None:
            return "[Expression not found]"
        
        measure_line = lines[measure_line_idx]
        
        # Extract what comes after "measure 'Name' ="
        match = re.match(r"\s*measure\s+'?([^'=]+)'?\s*=\s*(.*)", measure_line)
        if not match:
            return "[Expression parse error]"
        
        inline_part = match.group(2).strip() if match.group(2) else ""
        base_indent = len(measure_line) - len(measure_line.lstrip())
        
        # FORMAT 1: Full inline expression (doesn't start with backticks or newline)
        # If we have content after "=" that's not backticks and not empty, it's a complete inline expression
        if inline_part and not inline_part.startswith('```'):
            # This is an inline expression on the same line as "measure ... ="
            # It's complete if it ends naturally (newline) or is the only expression
            return self._clean_expression(inline_part)
        
        # FORMAT 3: Backtick format
        if inline_part.startswith('```'):
            expr_lines = []
            # Look for content between backticks
            found_open = False
            for idx in range(measure_line_idx, len(lines)):
                line = lines[idx]
                backtick_count = line.count('```')
                
                if backtick_count >= 2:
                    # Both open and close on same line (rare)
                    parts = line.split('```')
                    if len(parts) > 2:
                        expr_lines.append(parts[1].strip())
                    break
                elif backtick_count == 1:
                    if not found_open:
                        found_open = True
                        # Get content after opening backticks
                        after_open = line.split('```')[1].strip()
                        if after_open:
                            expr_lines.append(after_open)
                    else:
                        # This is closing backtick
                        before_close = line.split('```')[0].strip()
                        if before_close:
                            expr_lines.append(before_close)
                        break
                elif found_open:
                    # Content between backticks
                    expr_lines.append(line.strip())
            
            full_expr = ' '.join(expr_lines)
            return self._clean_expression(full_expr)
        
        # FORMAT 2: Indented multiline (most common in this PBIP)
        expr_lines = []
        
        # Collect subsequent indented lines (expression continuation)
        for idx in range(measure_line_idx + 1, len(lines)):
            line = lines[idx]
            
            # Skip empty lines
            if not line.strip():
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # Stop if we hit metadata at measure level (description, format, etc.)
            if line_indent <= base_indent:
                if any(kw in line for kw in ['description:', 'displayFolder:', 'formatString:', 'hidden:', 'lineageTag:', 'annotation', 'measure ']):
                    break
            
            # Stop if we hit another measure
            if line_indent <= base_indent and re.match(r'\s*measure\s+', line):
                break
            
            # If indented, it's part of DAX
            if line_indent > base_indent:
                expr_lines.append(line.strip())
        
        if expr_lines:
            full_expr = ' '.join(expr_lines)
            return self._clean_expression(full_expr)
        
        # No expression found
        return "[Expression not found]"
    
    def _extract_column_dependencies(self, expression: str) -> List[str]:
        """
        Extract column references used in measure expression.
        
        Detects patterns:
        - Table[Column]
        - 'Table'[Column]
        - [Column] (unqualified, assumes current context)
        
        Returns sorted list of unique column names (without table qualifiers).
        """
        columns = set()
        
        # Pattern 1: Qualified refs 'Table'[Column] or "Table"[Column]
        qualified = re.findall(r"['\"]?([A-Za-z_][A-Za-z0-9_\s]*)['\"]?\s*\[\s*([^\]]+)\s*\]", expression)
        for table_name, col_name in qualified:
            columns.add(col_name.strip())
        
        # Pattern 2: Unqualified [Column] references
        unqualified = re.findall(r'(?<!\w)\[([^\]]+)\]', expression)
        for ref in unqualified:
            # Filter out function names and measure references
            # Columns typically have simple names or underscores
            if not ref.startswith('[') and ref.lower() not in DAX_FUNCTIONS:
                columns.add(ref.strip())
        
        return sorted(columns)
    
    def _detect_functions(self, expression: str) -> List[str]:
        """Detect DAX functions used in expression (case-insensitive)"""
        found = set()
        expr_upper = expression.upper()
        
        # Create uppercase version of DAX_FUNCTIONS for case-insensitive lookup
        dax_funcs_upper = {fn.upper(): fn for fn in DAX_FUNCTIONS.keys()}
        
        for fn_upper, fn_original in dax_funcs_upper.items():
            # Match function name followed by '(' to avoid partial matches
            if re.search(r'\b' + fn_upper.replace('.', r'\.') + r'\s*\(', expr_upper):
                found.add(fn_original)
        
        return sorted(found)
    
    def _extract_dependencies(self, expression: str, own_name: str) -> List[str]:
        """
        Extract measure dependencies from DAX expression.
        
        Smart filtering:
        1. Detects qualified refs: 'Table'[Column] or "Table"[Column] → filters out (column)
        2. Detects unqualified refs: [Something] → checks if it's a known column → filters if true
        3. Keeps only references that could be measures (cross-table references)
        
        Args:
            expression: DAX expression to parse
            own_name: Name of current measure (to exclude self-references)
        
        Returns:
            List of measure dependencies (deduplicated, sorted)
        """
        deps = set()
        
        # Pattern 1: Qualified column references 'Table'[Column] or "Table"[Column]
        # These are ALWAYS columns, never measures → skip them
        qualified_cols = re.findall(r"['\"]([^'\"]+)['\"]\s*\[\s*([^\]]+)\s*\]", expression)
        qualified_col_set = {col_name for table, col_name in qualified_cols}
        
        # Pattern 2: Unqualified bracketed references [Something]
        # Could be column or measure - need to distinguish
        all_refs = re.findall(r'(?<!\w)\[([^\]]+)\]', expression)
        
        for ref in all_refs:
            # Skip self-references
            if ref == own_name:
                continue
            
            # Skip qualified column references (already parsed in Pattern 1)
            if ref in qualified_col_set:
                continue
            
            # Skip if this is a known column name from any table
            # (in DAX, [ColumnName] without qualification refers to table context)
            if ref in self.all_column_names:
                continue
            
            # If we reach here, it's likely a measure reference
            deps.add(ref)
        
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
    
    def _build_dependency_graph(self) -> List[Dict[str, Any]]:
        """
        Build complete dependency graph with architectural impact metrics.
        
        Enriches each measure with:
        - dependency_depth: How derived (0=base, 1+=composed)
        - dependents_count: How many measures depend on this
        - dependents: List of dependent measures
        - is_base_measure: True if has no dependencies
        - is_leaf_measure: True if no one depends on it
        - architectural_role: FOUNDATION/BASE/INTERMEDIATE/LEAF
        - architectural_complexity: Internal complexity + impact weight
        """
        if not self.measures:
            return self.measures
        
        measure_names = {m["name"] for m in self.measures}
        
        # Direct dependencies (already in each measure)
        depends_on = {m["name"]: set(m.get("dependencies", [])) for m in self.measures}
        
        # Inverse dependencies: who depends on each measure
        depended_by = defaultdict(set)
        for measure_name, deps in depends_on.items():
            for dep in deps:
                if dep in measure_names:  # Only if dep is a known measure
                    depended_by[dep].add(measure_name)
        
        # Calculate depth in dependency tree
        def get_depth(name: str, visited: Optional[Set[str]] = None) -> int:
            """Recursively calculate depth (0=base, 1+=derived)"""
            if visited is None:
                visited = set()
            if name in visited:
                return 0  # Cycle detected
            visited.add(name)
            
            deps = depends_on.get(name, set())
            if not deps:
                return 0  # Base measure
            
            # Depth = 1 + max depth of dependencies
            return 1 + max((get_depth(d, visited.copy()) for d in deps), default=0)
        
        # Enrich each measure with graph metrics
        for m in self.measures:
            name = m["name"]
            
            # Dependency metrics
            m["dependency_depth"] = get_depth(name)
            m["dependents_count"] = len(depended_by.get(name, set()))
            m["dependents"] = sorted(depended_by.get(name, set()))
            
            # Classification
            m["is_base_measure"] = len(depends_on.get(name, set())) == 0
            m["is_leaf_measure"] = len(depended_by.get(name, set())) == 0
            
            # Architectural role
            if m["is_base_measure"] and m["dependents_count"] >= 3:
                m["architectural_role"] = "FOUNDATION"  # Base measure used by many
            elif m["is_base_measure"]:
                m["architectural_role"] = "BASE"        # Base measure (low usage)
            elif m["is_leaf_measure"]:
                m["architectural_role"] = "LEAF"        # Derived, unused downstream
            else:
                m["architectural_role"] = "INTERMEDIATE"  # Middle layer
            
            # Architectural complexity score
            # Combines internal complexity with dependency impact
            internal_complexity = m.get("complexity_score", 0.0)
            
            # Impact weight: measures that many depend on add architectural complexity
            impact_weight = m["dependents_count"] * 0.3
            
            # Derivation weight: deeply nested measures are more fragile
            derivation_weight = m["dependency_depth"] * 0.2
            
            # Total architectural complexity
            m["architectural_complexity"] = round(
                internal_complexity + impact_weight + derivation_weight, 2
            )
        
        return self.measures
    
    def _is_stub(self, expression: str) -> bool:
        """True if expression is empty, placeholder, or trivially short"""
        if not expression or expression == "[Expression not fully captured]":
            return True
        clean = expression.replace("[Expression not fully captured]", "").strip()
        clean = clean.replace("`", "").strip()
        return len(clean) < 5
    
    def _detect_antipatterns(self, expression: str) -> Dict[str, Any]:
        """
        Detect DAX antipatterns that negatively impact performance.
        High-impact patterns that should be refactored.
        
        Returns dict with:
        - has_antipatterns: bool
        - antipattern_count: int
        - antipatterns: list of detected issues
        - highest_severity: str (HIGH, MEDIUM, LOW, NONE)
        """
        expr_upper = expression.upper()
        antipatterns = []
        
        # 1. FILTER over full table — critical performance issue
        # Pattern: FILTER(TableName, condition) instead of FILTER(VALUES(...))
        filter_full_table = re.findall(
            r"FILTER\s*\(\s*'?[A-Za-z_][A-Za-z0-9_\s]*'?\s*,",
            expression, re.IGNORECASE
        )
        if filter_full_table:
            antipatterns.append({
                "code": "DAX001",
                "name": "FILTER over full table",
                "severity": "HIGH",
                "occurrences": len(filter_full_table),
                "fix": "Use CALCULATETABLE or filter on specific column: FILTER(VALUES(Table[Col]), ...)"
            })
        
        # 2. Nested iterators — SUMX inside SUMX, etc.
        iterator_fns = ["SUMX", "AVERAGEX", "MAXX", "MINX", "COUNTX", "PRODUCTX"]
        for fn in iterator_fns:
            # Look for nested pattern: fn(...fn(...)...)
            pattern = rf"{fn}\s*\([^()]*{fn}\s*\("
            if re.search(pattern, expr_upper):
                antipatterns.append({
                    "code": "DAX002",
                    "name": f"Nested iterator: {fn} inside iterator",
                    "severity": "HIGH",
                    "occurrences": 1,
                    "fix": "Refactor using VAR to pre-calculate inner iterator result"
                })
                break  # Report once, not per function
        
        # 3. Complex measure without VAR — readability and performance
        has_var = bool(re.search(r"\bVAR\b", expr_upper))
        is_complex = len(expression) > 200 or expression.count("(") > 5
        if is_complex and not has_var:
            antipatterns.append({
                "code": "DAX003",
                "name": "Complex measure without VAR",
                "severity": "MEDIUM",
                "occurrences": 1,
                "fix": "Introduce VAR declarations to improve readability and avoid repeated sub-expression evaluation"
            })
        
        # 4. Deep IF nesting — refactor to SWITCH
        nested_if_count = len(re.findall(r"\bIF\s*\(", expr_upper))
        if nested_if_count >= 3:
            antipatterns.append({
                "code": "DAX004",
                "name": f"Deep IF nesting ({nested_if_count} levels)",
                "severity": "MEDIUM",
                "occurrences": nested_if_count,
                "fix": "Replace nested IF with SWITCH(TRUE(), ...) for better readability and performance"
            })
        
        # 5. Hard-coded division without DIVIDE — potential division by zero
        hard_divide = re.findall(r"[^/<>=]\s*/\s*[^/<>=]", expression)
        if hard_divide and "DIVIDE" not in expr_upper:
            antipatterns.append({
                "code": "DAX005",
                "name": "Division without DIVIDE() function",
                "severity": "LOW",
                "occurrences": len(hard_divide),
                "fix": "Use DIVIDE(numerator, denominator, [alternate_result]) to handle division by zero safely"
            })
        
        return {
            "has_antipatterns": len(antipatterns) > 0,
            "antipattern_count": len(antipatterns),
            "antipatterns": antipatterns,
            "highest_severity": (
                "HIGH" if any(a["severity"] == "HIGH" for a in antipatterns)
                else "MEDIUM" if any(a["severity"] == "MEDIUM" for a in antipatterns)
                else "LOW" if antipatterns else "NONE"
            )
        }
    

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNUSED MEASURES ANALYZER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _collect_visual_fields(pages: List[Dict]) -> Set[str]:
    """
    Extract all field references from report visuals.
    
    Handles multiple formats:
    1. String direct: "Actual"
    2. Object with ref: {"ref": "Actual"}
    3. Object with name: {"name": "Actual"}
    4. Qualified ref: "Table[Measure]" → extracts "Measure"
    
    Returns:
        Set of field names referenced in visuals
    """
    referenced = set()
    
    for page in pages:
        for visual in page.get('visuals', []):
            for field in visual.get('fields', []):
                
                # Case 1: Field is a string directly (most common in pages.json)
                if isinstance(field, str):
                    field_name = field.strip()
                    
                    # Handle qualified references: "Table[Measure]" → "Measure"
                    if "[" in field_name and "]" in field_name:
                        match = re.search(r'\[([^\]]+)\]', field_name)
                        if match:
                            referenced.add(match.group(1))
                    else:
                        referenced.add(field_name)
                
                # Case 2: Field is a dictionary (complex format)
                elif isinstance(field, dict):
                    # Try multiple keys: ref, name, column, measure
                    field_name = (
                        field.get('ref') 
                        or field.get('name') 
                        or field.get('column')
                        or field.get('measure')
                    )
                    
                    if field_name:
                        field_name = str(field_name).strip()
                        
                        # Handle qualified references in dict format
                        if "[" in field_name and "]" in field_name:
                            match = re.search(r'\[([^\]]+)\]', field_name)
                            if match:
                                referenced.add(match.group(1))
                        else:
                            referenced.add(field_name)
    
    return referenced


def _classify_cleanup_risk(measure: Dict[str, Any]) -> str:
    """
    Classify cleanup risk for unused measures.
    
    Determines if a measure is safe to delete or requires investigation.
    
    Returns:
        SAFE_DELETE: Empty stub or zero complexity
        REVIEW_SUGGESTED: Simple measure, likely redundant
        DO_NOT_DELETE: Base measure (even if not in reports)
        INVESTIGATE: Complex measure with no references (possible bug)
    """
    # Stubs and empty measures are always safe to delete
    if measure.get("is_stub", False):
        return "SAFE_DELETE"
    
    complexity = measure.get("complexity_score", 0.0)
    
    # Zero complexity means no real logic
    if complexity == 0.0:
        return "SAFE_DELETE"
    
    # Base measures should be preserved (might be used elsewhere)
    if measure.get("is_base_measure", False):
        return "DO_NOT_DELETE"
    
    # Very complex measure with no references is suspicious
    if complexity > 10:
        return "INVESTIGATE"
    
    # Simple measures are usually redundant
    if complexity < 3:
        return "REVIEW_SUGGESTED"
    
    # Default: moderate complexity requires review
    return "REVIEW_SUGGESTED"


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
    pages_analyzed = bool(pages)
    
    # 1. Check cross-measure dependencies
    for m in measures:
        for dep in m.get('dependencies', []):
            if dep in all_measure_names:
                referenced.add(dep)
    
    # 2. Check pages/visuals using robust field extraction
    if pages:
        visual_fields = _collect_visual_fields(pages)
        # Only add fields that are known measures
        referenced.update(visual_fields & all_measure_names)
    
    # 3. Identify unused measures
    unused = [m for m in measures if m['name'] not in referenced]
    
    # 4. Build analysis summary with cleanup risk classification
    cleanup_candidates = []
    for m in unused:
        cleanup_risk = _classify_cleanup_risk(m)
        cleanup_candidates.append({
            "name": m['name'],
            "table": m['table'],
            "complexity": m['complexity_score'],
            "is_stub": m.get('is_stub', False),
            "architectural_role": m.get('architectural_role', 'UNKNOWN'),
            "dependency_depth": m.get('dependency_depth', 0),
            "cleanup_risk": cleanup_risk,
            "reason": {
                "SAFE_DELETE": "Stub/incomplete or zero complexity measure — safe to delete",
                "REVIEW_SUGGESTED": "Simple measure likely redundant — review before deleting",
                "DO_NOT_DELETE": "Base measure — preserve even if not in reports (may be used by other measures)",
                "INVESTIGATE": "Complex measure with no references — investigate for broken dependencies"
            }.get(cleanup_risk, "Review before deletion")
        })
    
    summary = {
        "total_measures": len(measures),
        "used_measures": len(referenced),
        "unused_measures": len(unused),
        "unused_percentage": round(len(unused) / len(measures) * 100, 1) if measures else 0,
        "analysis_coverage": {
            "measure_dependencies": True,
            "visual_fields": pages_analyzed,
            "tooltip_fields": False,
            "conditional_formatting": False,
            "rls_expressions": False,
            "dynamic_dax_patterns": False,
            "calculated_tables": False,
        },
        "analysis_scope_note": "Deterministic for measure-to-measure dependencies and report visual fields only.",
        "analysis_limitations": [
            "Tooltip fields",
            "Conditional formatting expressions",
            "Row Level Security expressions",
            "Dynamic DAX patterns (NAMEOF or string-based references)",
            "Calculated tables and table expressions",
        ],
        "cleanup_by_risk": {
            "safe_delete": len([c for c in cleanup_candidates if c["cleanup_risk"] == "SAFE_DELETE"]),
            "review_suggested": len([c for c in cleanup_candidates if c["cleanup_risk"] == "REVIEW_SUGGESTED"]),
            "investigate": len([c for c in cleanup_candidates if c["cleanup_risk"] == "INVESTIGATE"]),
            "do_not_delete": len([c for c in cleanup_candidates if c["cleanup_risk"] == "DO_NOT_DELETE"]),
        },
        "cleanup_candidates": cleanup_candidates
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

    if pages is None:
        pages = _load_pages_context(Path(tmdl_dir))
    
    # Resolve cross-measure dependencies with column context
    measures = _resolve_dependencies(measures, parser.columns_by_table)
    
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


def _load_pages_context(tmdl_dir: Path) -> Optional[List[Dict[str, Any]]]:
    """Try to load pages.json from the sibling report folder when the parser is run directly."""
    semantic_model_dir = tmdl_dir.parent if tmdl_dir.name == "definition" else tmdl_dir
    if semantic_model_dir.name.endswith(".SemanticModel"):
        project_root = semantic_model_dir.parent
        project_name = semantic_model_dir.name.replace(".SemanticModel", "")
        pages_path = project_root / f"{project_name}.Report" / "definition" / "pages" / "pages.json"
        if pages_path.exists():
            try:
                pages_data = json.loads(pages_path.read_text(encoding="utf-8"))
                if isinstance(pages_data, list):
                    return [p for p in pages_data if isinstance(p, dict)]
            except (json.JSONDecodeError, OSError):
                pass
    return None


def _resolve_dependencies(measures: List[Dict], columns_by_table: Dict[str, Set[str]] = None) -> List[Dict]:
    """
    Cross-reference dependencies against actual measure names.
    Filters out column references and validates measure-to-measure links.
    
    Args:
        measures: List of parsed measures
        columns_by_table: Optional dict of table->columns for additional filtering
    
    Returns:
        Measures with validated dependencies
    """
    known_measure_names = {m["name"] for m in measures}
    
    # Build all known column names if provided
    all_column_names = set()
    if columns_by_table:
        for cols in columns_by_table.values():
            all_column_names.update(cols)
    
    for m in measures:
        confirmed_deps = []
        
        for dep in m.get("dependencies", []):
            # Check 1: Is it a known measure name?
            if dep in known_measure_names:
                # Check 2: Is it NOT a known column name? (extra safety)
                if dep not in all_column_names:
                    confirmed_deps.append(dep)
        
        m["dependencies"] = confirmed_deps
    
    return measures


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse Power BI measures and detect unused candidates.")
    parser.add_argument("tmdl_dir", help="Path to the TMDL definition directory")
    parser.add_argument("output_file", nargs="?", default="measures.json", help="Where to write measures.json")
    parser.add_argument("--pages", dest="pages_file", default=None, help="Optional pages.json file for visual-field analysis")
    args = parser.parse_args()

    pages = None
    if args.pages_file:
        pages_path = Path(args.pages_file)
        if pages_path.exists():
            try:
                pages_data = json.loads(pages_path.read_text(encoding="utf-8"))
                if isinstance(pages_data, list):
                    pages = [p for p in pages_data if isinstance(p, dict)]
            except (json.JSONDecodeError, OSError):
                pages = None

    measures, unused, analysis = parse_measures(args.tmdl_dir, args.output_file, pages=pages)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"  Measures Analysis")
    print(f"{'='*60}\n")
    print(f"  Total measures:       {analysis['total_measures']}")
    print(f"  Used measures:        {analysis['used_measures']}")
    print(f"  Unused measures:      {analysis['unused_measures']}")
    print(f"  Unused percentage:    {analysis['unused_percentage']}%\n")

    coverage = analysis.get("analysis_coverage", {})
    limitations = analysis.get("analysis_limitations", [])
    print("  Coverage:")
    print(f"    • Measure dependencies: {'yes' if coverage.get('measure_dependencies') else 'no'}")
    print(f"    • Visual fields:        {'yes' if coverage.get('visual_fields') else 'no'}")
    print("  Not analyzed:")
    for item in limitations[:5]:
        print(f"    • {item}")
    print()
    
    if unused:
        print(f"  Potentially unused measures (manual verification recommended):\n")
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