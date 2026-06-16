#!/usr/bin/env python3
"""
Parser for Power BI column usage analysis.

Purpose:
- Detect which columns are actually used in the semantic model
- Identify unused columns (like "measure killer" functionality)
- Calculate usage percentage per table
- Analyze usage in measures, relationships, calculated columns, and partitions

Outputs:
- column_usage.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict


class ColumnUsageParser:
    def __init__(self):
        self.tables: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []
        self.measures: List[Dict[str, Any]] = []
        self.pages: List[Dict[str, Any]] = []

    def parse(
        self,
        tables: List[Dict[str, Any]] = None,
        relationships: List[Dict[str, Any]] = None,
        measures: List[Dict[str, Any]] = None,
        pages: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze column usage across the semantic model.

        Returns:
        {
            "summary": {
                "total_columns": 413,
                "columns_used_in_measures": 276,
                "columns_used_in_pages": 0,
                "total_unique_columns_used": 276,
                "total_unused": 137
            },
            "unused_by_table": {
                "Calendar From": ["Month", "MonthName", ...],
                "Calendar To": [...],
                ...
            }
        }
        """
        self.tables = tables or []
        self.relationships = relationships or []
        self.measures = measures or []
        self.pages = pages or []

        # Collect columns used in measures
        columns_used_in_measures = set()
        for measure in self.measures:
            columns_used_in_measures.update(measure.get('column_dependencies', []))

        # Collect columns used in pages
        columns_used_in_pages = set()
        for page in self.pages:
            self._collect_page_fields(page, columns_used_in_pages)

        columns_used_total = columns_used_in_measures | columns_used_in_pages

        # Build column catalog from tables
        columns_by_table = defaultdict(set)
        table_usage = []
        for table in self.tables:
            table_name = table.get('name', 'Unknown')
            for col in table.get('columns', []):
                col_name = col.get('name', '')
                if col_name:
                    columns_by_table[table_name].add(col_name)

        # Build per-table usage stats
        for table in self.tables:
            table_name = table.get('name', 'Unknown')
            table_columns = columns_by_table.get(table_name, set())
            used_columns = sorted(table_columns & columns_used_total)
            unused_columns = sorted(table_columns - columns_used_total)
            total_columns = len(table_columns)
            used_count = len(used_columns)
            unused_count = len(unused_columns)
            usage_percentage = round(100 * used_count / total_columns) if total_columns else 0

            table_usage.append({
                "table_name": table_name,
                "total_columns": total_columns,
                "used_columns": used_count,
                "unused_columns": unused_count,
                "usage_percentage": usage_percentage,
                "used_column_names": used_columns,
                "unused_column_names": unused_columns,
                "has_measures": table.get("measure_count", 0) > 0,
                "has_calculated_columns": table.get("calculated_column_count", 0) > 0,
                "measure_count": table.get("measure_count", 0),
                "calculated_column_count": table.get("calculated_column_count", 0),
                "table_kind": table.get("table_kind", "UNKNOWN"),
            })

        # Find unused columns per table
        unused_by_table = {}
        for table_name, cols in columns_by_table.items():
            unused = cols - columns_used_total
            if unused:
                unused_by_table[table_name] = sorted(unused)

        return {
            "summary": {
                "total_columns": sum(len(c) for c in columns_by_table.values()),
                "columns_used_in_measures": len(columns_used_in_measures),
                "columns_used_in_pages": len(columns_used_in_pages),
                "total_unique_columns_used": len(columns_used_total),
                "total_unused": sum(len(c) for c in unused_by_table.values()),
                "tables_with_full_usage": len([row for row in table_usage if row["usage_percentage"] == 100 and row["total_columns"] > 0]),
                "average_table_usage_percentage": round(sum(row["usage_percentage"] for row in table_usage) / len(table_usage), 1) if table_usage else 0.0,
            },
            "table_usage": table_usage,
            "unused_by_table": unused_by_table,
        }

    @staticmethod
    def _collect_page_fields(obj: Any, columns_set: Set[str]) -> None:
        """Recursively collect [ColumnName] references from page objects."""
        if isinstance(obj, str):
            if '[' in obj and ']' in obj:
                matches = re.findall(r'\[([^\]]+)\]', obj)
                columns_set.update(matches)
        elif isinstance(obj, dict):
            for v in obj.values():
                ColumnUsageParser._collect_page_fields(v, columns_set)
        elif isinstance(obj, list):
            for item in obj:
                ColumnUsageParser._collect_page_fields(item, columns_set)


def parse_column_usage(
    tables: List[Dict[str, Any]] = None,
    relationships: List[Dict[str, Any]] = None,
    measures: List[Dict[str, Any]] = None,
    pages: List[Dict[str, Any]] = None,
    output_file: str = None
) -> Dict[str, Any]:
    """
    Main function to analyze column usage.

    Args:
        tables: List of tables from parse_tables
        relationships: List of relationships from parse_relationships
        measures: List of measures from parse_measures
        pages: List of pages from parse_pages
        output_file: Optional output file path

    Returns:
        Column usage analysis dict
    """
    parser = ColumnUsageParser()
    column_usage = parser.parse(
        tables=tables,
        relationships=relationships,
        measures=measures,
        pages=pages
    )

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(column_usage, f, indent=2, ensure_ascii=False)

    return column_usage


if __name__ == "__main__":
    print("parse_column_usage.py - Column usage analysis parser")
    print("")
    print("This parser is designed to be called from main.py with:")
    print("  - tables from parse_tables()")
    print("  - relationships from parse_relationships()")
    print("  - measures from parse_measures()")
    print("  - pages from parse_pages()")
    print("")
    print("Usage: python main.py <pbip_path>")
