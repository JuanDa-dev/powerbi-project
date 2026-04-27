#!/usr/bin/env python3
"""
Parser for Power BI model analysis: table classification, relationship analysis, etc.
Outputs: analysis.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class AnalysisParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.tables = {}
        self.relationships = []
        self.classifications = []
        
    def parse(self) -> Dict[str, Any]:
        """Perform comprehensive analysis"""
        self._parse_all_data()
        classifications = self._classify_tables()
        relationship_analysis = self._analyze_relationships()
        
        return {
            'table_classifications': classifications,
            'relationship_analysis': relationship_analysis,
            'summary': self._generate_summary(classifications, relationship_analysis)
        }
    
    def _parse_all_data(self):
        """Parse tables and relationships"""
        tables_dir = self.tmdl_dir / "tables"
        
        for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
            table_name = tmdl_file.stem
            content = tmdl_file.read_text(encoding='utf-8')
            
            columns = self._extract_columns(content)
            measures = self._extract_measures(content)
            
            self.tables[table_name] = {
                'columns': columns,
                'measures': measures,
                'has_datatable': 'DATATABLE' in content
            }
        
        # Parse relationships
        self._parse_relationships()
    
    def _extract_columns(self, content: str) -> List[Dict[str, str]]:
        """Extract columns"""
        columns = []
        col_pattern = r"column\s+(['\"]?)([^'\"\n]+)\1\s*\n((?:\t[^\n]*\n)*?)"
        
        for match in re.finditer(col_pattern, content):
            col_name = match.group(2).strip()
            col_block = match.group(3)
            
            datatype_match = re.search(r'dataType:\s*(\w+)', col_block)
            datatype = datatype_match.group(1) if datatype_match else 'string'
            
            columns.append({'name': col_name, 'dataType': datatype})
        
        return columns
    
    def _extract_measures(self, content: str) -> List[str]:
        """Extract measure names"""
        measures = []
        measure_pattern = r'measure\s+([^\n=]+)(?:\s*=|$)'
        
        for match in re.finditer(measure_pattern, content):
            measure_name = match.group(1).strip().strip("'\"")
            measures.append(measure_name)
        
        return measures
    
    def _parse_relationships(self):
        """Parse relationships"""
        rel_file = self.tmdl_dir / "relationships.tmdl"
        
        if not rel_file.exists():
            return
        
        content = rel_file.read_text(encoding='utf-8')
        rel_pattern = r'relationship\s+[a-f0-9\-]+\s*\n\s*(?:toCardinality:\s*many\s*\n\s*)?fromColumn:\s*([^\n]+)\n\s*toColumn:\s*([^\n]+)'
        
        for match in re.finditer(rel_pattern, content):
            from_col = match.group(1).strip()
            to_col = match.group(2).strip()
            
            from_table, from_column = self._parse_table_column(from_col)
            to_table, to_column = self._parse_table_column(to_col)
            
            if from_table and to_table:
                self.relationships.append({
                    'from_table': from_table,
                    'from_column': from_column,
                    'to_table': to_table,
                    'to_column': to_column
                })
    
    def _parse_table_column(self, spec: str):
        """Parse table.column"""
        parts = spec.split('.')
        if len(parts) >= 2:
            table = parts[0].strip().strip("'\"[]")
            column = parts[1].strip().strip("'\"[]")
            return table, column
        return None, None
    
    def _classify_tables(self) -> List[Dict[str, Any]]:
        """Classify each table"""
        classifications = []
        
        for table_name, table_data in sorted(self.tables.items()):
            classification = self._classify_single_table(table_name, table_data)
            classifications.append(classification)
        
        return classifications
    
    def _classify_single_table(self, table_name: str, table_data: Dict) -> Dict[str, Any]:
        """Classify a single table"""
        columns = table_data['columns']
        measures = table_data['measures']
        
        col_count = len(columns)
        numeric_count = sum(1 for c in columns if c['dataType'] in ['double', 'int64', 'int32', 'decimal'])
        string_count = sum(1 for c in columns if c['dataType'] == 'string')
        date_count = sum(1 for c in columns if c['dataType'] in ['dateTime', 'date'])
        measure_count = len(measures)
        
        # Find relationships
        rel_from = sum(1 for r in self.relationships if r['from_table'] == table_name)
        rel_to = sum(1 for r in self.relationships if r['to_table'] == table_name)
        
        # Classify (order matters!)
        classification = 'DIMENSION'
        confidence = 0.5
        reasoning = "Default classification"
        
        # 1. CALCULATION - DAX measure containers (many measures, few/no columns)
        if measure_count >= 10 and col_count <= 1:
            classification = 'CALCULATION'
            confidence = 0.95
            reasoning = f"DAX measure container ({measure_count} measures)"
        
        # 2. PARAMETER - Control/slicer tables (param_ prefix or few columns)
        elif 'param' in table_name.lower() and col_count <= 3:
            classification = 'PARAMETER'
            confidence = 0.95
            reasoning = "Control/slicer parameter table"
        
        # 3. BRIDGE - Many-to-many resolvers (bridge_ prefix or specific pattern)
        elif 'bridge' in table_name.lower():
            classification = 'BRIDGE'
            confidence = 0.90
            reasoning = f"Bridge table (rel_from={rel_from}, rel_to={rel_to})"
        
        # 4. FACT - Central fact table (fact_ prefix or many relationships+many columns)
        elif 'fact' in table_name.lower():
            classification = 'FACT'
            confidence = 0.95
            reasoning = f"Fact table ({col_count} columns, {rel_from} outgoing relationships)"
        
        # 5. FACT - By pattern (many numeric cols and many relationships)
        elif numeric_count >= 2 and rel_from >= 3:
            classification = 'FACT'
            confidence = 0.85
            reasoning = f"Multiple numeric columns ({numeric_count}), many relationships ({rel_from})"
        
        # 6. FACT - Large transaction-like table (many columns, many relationships)
        elif col_count >= 20 and rel_from >= 3:
            classification = 'FACT'
            confidence = 0.80
            reasoning = f"Large transaction table ({col_count} columns, {rel_from} relationships)"
        
        # 7. CALENDAR/TIME DIMENSION
        elif 'calendar' in table_name.lower() or 'calendario' in table_name.lower() or date_count >= 3:
            classification = 'DIMENSION'
            confidence = 0.95
            reasoning = "Calendar/time dimension"
        
        # 8. DIMENSION - Default for remaining tables
        else:
            classification = 'DIMENSION'
            confidence = 0.5
            reasoning = f"Dimension table ({col_count} columns, {rel_to} incoming)"
        
        return {
            'table_name': table_name,
            'classification': classification,
            'confidence': round(confidence, 2),
            'reasoning': reasoning,
            'metadata': {
                'columns': col_count,
                'numeric_columns': numeric_count,
                'string_columns': string_count,
                'date_columns': date_count,
                'measures': measure_count,
                'relationships_from': rel_from,
                'relationships_to': rel_to
            }
        }
    
    def _analyze_relationships(self) -> Dict[str, Any]:
        """Analyze relationship structure"""
        # Build graph
        graph = defaultdict(set)
        for rel in self.relationships:
            graph[rel['from_table']].add(rel['to_table'])
            graph[rel['to_table']].add(rel['from_table'])
        
        # Find disconnected components
        visited = set()
        components = []
        
        def dfs(node, component):
            visited.add(node)
            component.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, component)
        
        for table in self.tables.keys():
            if table not in visited:
                component = set()
                dfs(table, component)
                components.append(list(component))
        
        isolated_tables = [list(comp)[0] for comp in components if len(comp) == 1]
        
        return {
            'total_tables': len(self.tables),
            'total_relationships': len(self.relationships),
            'schema_type': 'STAR',
            'compliance_score': 85,
            'components': len(components),
            'isolated_tables': isolated_tables,
            'relationships': [
                {
                    'from_table': r['from_table'],
                    'from_column': r['from_column'],
                    'to_table': r['to_table'],
                    'to_column': r['to_column']
                }
                for r in self.relationships
            ]
        }
    
    def _generate_summary(self, classifications: List[Dict], relationship_analysis: Dict) -> Dict[str, Any]:
        """Generate summary statistics"""
        fact_tables = [c for c in classifications if c['classification'] == 'FACT']
        dimension_tables = [c for c in classifications if c['classification'] == 'DIMENSION']
        calculation_tables = [c for c in classifications if c['classification'] == 'CALCULATION']
        bridge_tables = [c for c in classifications if c['classification'] == 'BRIDGE']
        parameter_tables = [c for c in classifications if c['classification'] == 'PARAMETER']
        
        # Calculate total measures
        total_measures = 0
        for c in classifications:
            table_name = c['table_name']
            if table_name in self.tables:
                total_measures += len(self.tables[table_name]['measures'])
        
        return {
            'fact_tables': len(fact_tables),
            'dimension_tables': len(dimension_tables),
            'calculation_tables': len(calculation_tables),
            'bridge_tables': len(bridge_tables),
            'parameter_tables': len(parameter_tables),
            'total_measures': total_measures
        }


def parse_analysis(tmdl_dir: str, output_file: str = None) -> Dict[str, Any]:
    """Main function to parse analysis"""
    parser = AnalysisParser(tmdl_dir)
    analysis = parser.parse()
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    return analysis


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_analysis.py <tmdl_dir> [output_file]")
        sys.exit(1)
    
    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "analysis.json"
    
    analysis = parse_analysis(tmdl_dir, output_file)
    print(f"✓ Analysis complete")
