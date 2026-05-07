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
from typing import Dict, List, Any, Set, Tuple


class ColumnUsageParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.tables: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []
        self.measures: List[Dict[str, Any]] = []

    def parse(
        self,
        tables: List[Dict[str, Any]] = None,
        relationships: List[Dict[str, Any]] = None,
        measures: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze column usage across the semantic model.

        Args:
            tables: List of tables from parse_tables (must include columns)
            relationships: List of relationships from parse_relationships
            measures: List of measures from parse_measures

        Returns:
        [
            {
                "table_name": "...",
                "total_columns": 25,
                "used_columns": 22,
                "unused_columns": 3,
                "usage_percentage": 88,
                "columns": [
                    {
                        "name": "column_name",
                        "is_used": true,
                        "used_in": ["relationship", "measure: MeasureName"],
                        "is_hidden": false,
                        "is_calculated": false,
                        "reason": ""
                    }
                ]
            }
        ]
        """
        self.tables = tables or []
        self.relationships = relationships or []
        self.measures = measures or []

        column_usage = []

        for table in self.tables:
            table_name = table.get("name", "Unknown")
            columns = table.get("columns", [])
            
            # Analyze each column in the table
            table_column_usage = {
                "table_name": table_name,
                "total_columns": len(columns),
                "used_columns": 0,
                "unused_columns": 0,
                "usage_percentage": 0,
                "columns": []
            }

            for column in columns:
                col_name = column.get("name", "")
                is_hidden = column.get("is_hidden", False)
                is_calculated = column.get("is_calculated", False)
                is_key = column.get("is_key", False)

                # Analyze where this column is used
                used_in = self._find_column_usage(table_name, col_name)
                is_used = self._is_column_used(
                    table_name=table_name,
                    column_name=col_name,
                    used_in=used_in,
                    is_hidden=is_hidden,
                    is_calculated=is_calculated,
                    is_key=is_key
                )

                reason = self._get_usage_reason(
                    is_used=is_used,
                    is_hidden=is_hidden,
                    is_calculated=is_calculated,
                    is_key=is_key,
                    used_in=used_in
                )

                col_usage = {
                    "name": col_name,
                    "is_used": is_used,
                    "used_in": used_in,
                    "is_hidden": is_hidden,
                    "is_calculated": is_calculated,
                    "is_key": is_key,
                    "reason": reason
                }

                table_column_usage["columns"].append(col_usage)

                if is_used:
                    table_column_usage["used_columns"] += 1
                else:
                    table_column_usage["unused_columns"] += 1

            # Calculate usage percentage
            if table_column_usage["total_columns"] > 0:
                table_column_usage["usage_percentage"] = round(
                    100 * table_column_usage["used_columns"] / table_column_usage["total_columns"]
                )

            column_usage.append(table_column_usage)

        return column_usage

    def _find_column_usage(self, table_name: str, column_name: str) -> List[str]:
        """
        Find all places where a column is used.

        Returns list of usage locations like:
        - "relationship: from_table.from_column"
        - "measure: MeasureName"
        - "calculated_column: ColumnName"
        - "partition: PartitionName"
        """
        usage = []

        # Check in relationships
        usage.extend(self._find_in_relationships(table_name, column_name))

        # Check in measures
        usage.extend(self._find_in_measures(table_name, column_name))

        # Check in other columns' expressions
        usage.extend(self._find_in_column_expressions(table_name, column_name))

        # Check in partitions
        usage.extend(self._find_in_partitions(table_name, column_name))

        return usage

    def _find_in_relationships(self, table_name: str, column_name: str) -> List[str]:
        """Find if column is used in relationships."""
        usage = []

        for rel in self.relationships:
            from_table = rel.get("from_table", "")
            from_column = rel.get("from_column", "")
            to_table = rel.get("to_table", "")
            to_column = rel.get("to_column", "")

            if from_table == table_name and from_column == column_name:
                usage.append(f"relationship: {from_table}.{from_column} -> {to_table}.{to_column}")

            if to_table == table_name and to_column == column_name:
                usage.append(f"relationship: {from_table}.{from_column} -> {to_table}.{to_column}")

        return usage

    def _find_in_measures(self, table_name: str, column_name: str) -> List[str]:
        """Find if column is used in measure expressions."""
        usage = []

        for measure in self.measures:
            measure_name = measure.get("name", "")
            table = measure.get("table", "")
            expression = measure.get("expression", "")

            # Only check measures in this table
            if table != table_name:
                continue

            # Look for column reference patterns in DAX
            if self._column_referenced_in_expression(column_name, expression):
                usage.append(f"measure: {measure_name}")

        return usage

    def _find_in_column_expressions(self, table_name: str, column_name: str) -> List[str]:
        """Find if column is used in other calculated column expressions."""
        usage = []

        for table in self.tables:
            if table.get("name", "") != table_name:
                continue

            for column in table.get("columns", []):
                if column.get("name", "") == column_name:
                    continue  # Skip self-reference

                expression = column.get("expression", "")
                if expression and self._column_referenced_in_expression(column_name, expression):
                    usage.append(f"calculated_column: {column.get('name', '')}")

        return usage

    def _find_in_partitions(self, table_name: str, column_name: str) -> List[str]:
        """Find if column is used in partition definitions."""
        usage = []

        for table in self.tables:
            if table.get("name", "") != table_name:
                continue

            for partition in table.get("partitions", []):
                source_preview = partition.get("source_preview", "")
                if source_preview and self._column_referenced_in_expression(column_name, source_preview):
                    usage.append(f"partition: {partition.get('name', '')}")

        return usage

    @staticmethod
    def _column_referenced_in_expression(column_name: str, expression: str) -> bool:
        """
        Check if a column is referenced in an expression.

        Looks for patterns like:
        - [ColumnName]
        - 'TableName'[ColumnName]
        - Spaces around column name
        """
        if not expression:
            return False

        # Pattern 1: [ColumnName]
        bracket_pattern = rf"\[{re.escape(column_name)}\]"
        if re.search(bracket_pattern, expression, re.IGNORECASE):
            return True

        # Pattern 2: 'TableName'[ColumnName]
        qualified_pattern = rf"\'\w+\'\[{re.escape(column_name)}\]"
        if re.search(qualified_pattern, expression, re.IGNORECASE):
            return True

        # Pattern 3: Column name as word (for unqualified DAX)
        # Only if surrounded by non-word characters
        word_pattern = rf"\b{re.escape(column_name)}\b"
        if re.search(word_pattern, expression, re.IGNORECASE):
            return True

        return False

    @staticmethod
    def _is_column_used(
        table_name: str,
        column_name: str,
        used_in: List[str],
        is_hidden: bool,
        is_calculated: bool,
        is_key: bool
    ) -> bool:
        """
        Determine if a column should be considered "used".

        Rules:
        1. If explicitly used somewhere (used_in is not empty) -> True
        2. If it's a key column -> True (likely used implicitly)
        3. If it's hidden -> True (intentional, not cleanup candidate)
        4. If it's calculated -> True (created for a purpose)
        5. Otherwise -> False
        """
        # Explicitly used
        if used_in:
            return True

        # Key columns are always "used" implicitly
        if is_key:
            return True

        # Hidden columns are intentional
        if is_hidden:
            return True

        # Calculated columns are created for a purpose
        if is_calculated:
            return True

        # Regular column with no usage = unused
        return False

    @staticmethod
    def _get_usage_reason(
        is_used: bool,
        is_hidden: bool,
        is_calculated: bool,
        is_key: bool,
        used_in: List[str]
    ) -> str:
        """Generate human-readable reason for column status."""
        if used_in:
            return ""  # Used columns need no reason

        if is_hidden:
            return "Hidden column (intentional)"

        if is_calculated:
            return "Calculated column (helper table)"

        if is_key:
            return "Key column (implicit usage)"

        return "Not referenced in model"


def parse_column_usage(
    tables: List[Dict[str, Any]] = None,
    relationships: List[Dict[str, Any]] = None,
    measures: List[Dict[str, Any]] = None,
    output_file: str = None
) -> List[Dict[str, Any]]:
    """
    Main function to analyze column usage.

    Args:
        tables: List of tables from parse_tables
        relationships: List of relationships from parse_relationships
        measures: List of measures from parse_measures
        output_file: Optional output file path

    Returns:
        List of table column usage analysis
    """
    parser = ColumnUsageParser("")
    column_usage = parser.parse(
        tables=tables,
        relationships=relationships,
        measures=measures
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
    print("")
    print("Usage: python main.py <pbip_path>")
