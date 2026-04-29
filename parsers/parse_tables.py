#!/usr/bin/env python3
"""
Parser for Power BI tables from TMDL definition.

Purpose:
- Extract table, column, measure and partition metadata from TMDL table files.
- Preserve compatibility with the original tables.json list contract.
- Provide richer metadata for documentation, analysis and visualizations.

Outputs:
- tables.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter


class TableParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.tables: List[Dict[str, Any]] = []

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse all TMDL table files.

        Keeps backward-compatible output as a list:
        [
            {
                "name": "...",
                "columns": [...],
                "measures": [...],
                "column_count": 0,
                "measure_count": 0
            }
        ]
        """
        tables_dir = self.tmdl_dir / "tables"

        if not tables_dir.exists():
            return []

        for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
            table_name = tmdl_file.stem
            table_data = self._parse_table_file(tmdl_file, table_name)

            if table_data:
                self.tables.append(table_data)

        return self.tables

    # -------------------------------------------------------------------------
    # File parsing
    # -------------------------------------------------------------------------

    def _parse_table_file(self, file_path: Path, table_name: str) -> Dict[str, Any]:
        """
        Parse a single TMDL table file.
        """
        content = self._safe_read(file_path)

        columns = self._extract_columns(content)
        measures = self._extract_measures(content)
        partitions = self._extract_partitions(content)
        annotations = self._extract_annotations(content)

        column_type_distribution = Counter(
            col.get("dataType", "Unknown") for col in columns
        )

        hidden_columns = sum(1 for col in columns if col.get("is_hidden", False))
        calculated_columns = sum(1 for col in columns if col.get("is_calculated", False))
        key_like_columns = sum(1 for col in columns if col.get("is_key", False))

        has_datatable = "DATATABLE" in content.upper()
        has_calculated_table_expression = self._has_calculated_table_expression(content)
        is_hidden_table = self._extract_bool_property(content, "isHidden", default=False)

        table_kind = self._infer_table_kind(
            table_name=table_name,
            columns=columns,
            measures=measures,
            partitions=partitions,
            has_datatable=has_datatable,
            has_calculated_table_expression=has_calculated_table_expression
        )

        return {
            "name": table_name,
            "columns": columns,
            "measures": measures,
            "partitions": partitions,

            # Backward-compatible fields
            "column_count": len(columns),
            "measure_count": len(measures),
            "is_calculation": table_kind == "CALCULATION",
            "is_parameter": table_kind == "PARAMETER",
            "file": str(file_path),

            # Extended metadata
            "table_kind": table_kind,
            "is_hidden": is_hidden_table,
            "has_datatable": has_datatable,
            "has_calculated_table_expression": has_calculated_table_expression,
            "partition_count": len(partitions),
            "hidden_column_count": hidden_columns,
            "calculated_column_count": calculated_columns,
            "key_like_column_count": key_like_columns,
            "data_type_distribution": dict(column_type_distribution),
            "annotations": annotations,
            "source": {
                "file": self._relative_path(file_path),
                "raw_size_chars": len(content)
            }
        }

    @staticmethod
    def _safe_read(file_path: Path) -> str:
        """
        Safely read a TMDL file.
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Column extraction
    # -------------------------------------------------------------------------

    def _extract_columns(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract columns from TMDL content using block-based parsing.
        """
        columns = []
        blocks = self._extract_object_blocks(content, object_keyword="column")

        for name, block, line_number in blocks:
            column_data = self._parse_column_block(name, block, line_number)
            columns.append(column_data)

        return columns

    def _parse_column_block(self, raw_name: str, block: str, line_number: int) -> Dict[str, Any]:
        """
        Parse a single column block.
        """
        column_name, inline_expression = self._split_name_and_expression(raw_name)

        data_type = self._extract_property(block, "dataType") or "string"
        source_column = self._extract_property(block, "sourceColumn")
        format_string = self._extract_property(block, "formatString")
        summarize_by = self._extract_property(block, "summarizeBy")
        data_category = self._extract_property(block, "dataCategory")
        description = self._extract_property(block, "description")
        lineage_tag = self._extract_property(block, "lineageTag")
        source_lineage_tag = self._extract_property(block, "sourceLineageTag")
        is_hidden = self._extract_bool_property(block, "isHidden", default=False)

        expression = self._extract_column_expression(inline_expression, block)
        is_calculated = bool(expression)

        is_key = self._infer_key_column(column_name, source_column)
        semantic_role = self._infer_column_semantic_role(
            column_name=column_name,
            data_type=data_type,
            is_key=is_key,
            data_category=data_category
        )

        return {
            "name": column_name,
            "dataType": data_type,

            # Backward-compatible field
            "is_calculated": is_calculated,

            # Extended metadata
            "expression": expression,
            "sourceColumn": source_column,
            "formatString": format_string,
            "summarizeBy": summarize_by,
            "dataCategory": data_category,
            "description": description,
            "lineageTag": lineage_tag,
            "sourceLineageTag": source_lineage_tag,
            "is_hidden": is_hidden,
            "is_key": is_key,
            "semantic_role": semantic_role,
            "annotations": self._extract_annotations(block),
            "source": {
                "line": line_number
            }
        }

    @staticmethod
    def _split_name_and_expression(raw_name: str) -> Tuple[str, str]:
        """
        Split column header into name and optional inline expression.

        Supports:
        - column CustomerKey
        - column 'Customer Key'
        - column FullName = [First] & " " & [Last]
        """
        raw_name = raw_name.strip()

        if "=" not in raw_name:
            return raw_name.strip().strip("'\""), ""

        name_part, expr_part = raw_name.split("=", 1)
        return name_part.strip().strip("'\""), expr_part.strip()

    def _extract_column_expression(self, inline_expression: str, block: str) -> str:
        """
        Extract calculated column expression if present.
        """
        if inline_expression:
            return self._clean_expression(inline_expression)

        fenced = self._extract_fenced_expression(block)
        if fenced:
            return self._clean_expression(fenced)

        # Some calculated columns may have expression-like lines in the block.
        # Keep this conservative to avoid capturing metadata as expressions.
        expression_property = self._extract_property(block, "expression")
        if expression_property:
            return self._clean_expression(expression_property)

        return ""

    # -------------------------------------------------------------------------
    # Measure extraction, lightweight
    # -------------------------------------------------------------------------

    def _extract_measures(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract measure names and lightweight metadata.

        Full DAX analysis should remain in parse_measures.py.
        This parser only provides table-level measure inventory.
        """
        measures = []
        blocks = self._extract_object_blocks(content, object_keyword="measure")

        for name, block, line_number in blocks:
            measure_name, inline_expression = self._split_name_and_expression(name)

            measures.append({
                "name": measure_name,
                "expression_preview": self._expression_preview(
                    inline_expression or self._extract_fenced_expression(block)
                ),
                "formatString": self._extract_property(block, "formatString"),
                "displayFolder": self._extract_property(block, "displayFolder"),
                "description": self._extract_property(block, "description"),
                "is_hidden": self._extract_bool_property(block, "isHidden", default=False),
                "lineageTag": self._extract_property(block, "lineageTag"),
                "source": {
                    "line": line_number
                }
            })

        return measures

    # -------------------------------------------------------------------------
    # Partition extraction
    # -------------------------------------------------------------------------

    def _extract_partitions(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract partition metadata from table TMDL.
        """
        partitions = []
        blocks = self._extract_object_blocks(content, object_keyword="partition")

        for name, block, line_number in blocks:
            mode = self._extract_property(block, "mode")
            source_type = self._infer_partition_source_type(block)

            partitions.append({
                "name": name.strip().strip("'\""),
                "mode": mode,
                "source_type": source_type,
                "has_m_expression": "let" in block.lower() and "in" in block.lower(),
                "has_datatable": "DATATABLE" in block.upper(),
                "source_preview": self._expression_preview(self._extract_fenced_expression(block) or block),
                "source": {
                    "line": line_number
                }
            })

        return partitions

    @staticmethod
    def _infer_partition_source_type(block: str) -> str:
        """
        Infer partition source type from partition content.
        """
        upper_block = block.upper()
        lower_block = block.lower()

        if "DATATABLE" in upper_block:
            return "DATATABLE"
        if "SQL.DATABASE" in upper_block or "SQL" in upper_block:
            return "SQL"
        if "EXCEL.WORKBOOK" in upper_block or ".xlsx" in lower_block or ".xls" in lower_block:
            return "Excel"
        if "CSV.DOCUMENT" in upper_block or ".csv" in lower_block:
            return "CSV/Text"
        if "SHAREPOINT" in upper_block:
            return "SharePoint"
        if "WEB.CONTENTS" in upper_block or "https://" in lower_block or "http://" in lower_block:
            return "Web"
        if "let" in lower_block and "in" in lower_block:
            return "Power Query"
        return "Unknown"

    # -------------------------------------------------------------------------
    # Generic object block extraction
    # -------------------------------------------------------------------------

    def _extract_object_blocks(self, content: str, object_keyword: str) -> List[Tuple[str, str, int]]:
        """
        Extract TMDL object blocks.

        Returns:
        [
            (object_name_or_header, block_content, line_number)
        ]

        This parser is tolerant of spaces/tabs and does not require exact
        indentation rules.
        """
        lines = content.splitlines()
        blocks: List[Tuple[str, str, int]] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped.startswith(f"{object_keyword} "):
                i += 1
                continue

            start_indent = self._indent_level(line)
            start_line_number = i + 1

            header = stripped[len(object_keyword):].strip()

            i += 1
            block_lines = []

            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                next_indent = self._indent_level(next_line)

                if not next_stripped:
                    block_lines.append(next_line)
                    i += 1
                    continue

                if next_indent <= start_indent and self._is_tmdl_object_start(next_stripped):
                    break

                block_lines.append(next_line)
                i += 1

            blocks.append((header, "\n".join(block_lines), start_line_number))

        return blocks

    @staticmethod
    def _is_tmdl_object_start(stripped_line: str) -> bool:
        """
        Identify start of a new TMDL object.
        """
        prefixes = (
            "table ",
            "column ",
            "measure ",
            "hierarchy ",
            "level ",
            "partition ",
            "annotation ",
            "relationship ",
            "calculationGroup ",
            "calculationItem "
        )
        return stripped_line.startswith(prefixes)

    @staticmethod
    def _indent_level(line: str) -> int:
        """
        Count indentation treating tabs as 4 spaces.
        """
        expanded = line.replace("\t", "    ")
        return len(expanded) - len(expanded.lstrip(" "))

    # -------------------------------------------------------------------------
    # Metadata extraction
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_property(block: str, key: str) -> Optional[str]:
        """
        Extract a scalar key: value property.
        """
        pattern = re.compile(
            rf"^\s*{re.escape(key)}:\s*(?P<value>.+?)\s*$",
            re.MULTILINE
        )

        match = pattern.search(block)
        if not match:
            return None

        value = match.group("value").strip().strip("'\"")
        return value if value else None

    @staticmethod
    def _extract_bool_property(block: str, key: str, default: bool = False) -> bool:
        """
        Extract boolean key: value property.
        """
        pattern = re.compile(
            rf"^\s*{re.escape(key)}:\s*(?P<value>true|false)\s*$",
            re.MULTILINE | re.IGNORECASE
        )

        match = pattern.search(block)
        if not match:
            return default

        return match.group("value").lower() == "true"

    @staticmethod
    def _extract_annotations(block: str) -> List[Dict[str, str]]:
        """
        Extract lightweight annotation metadata.
        """
        annotations = []

        annotation_pattern = re.compile(
            r"^\s*annotation\s+(?P<name>[^\n=]+)(?:\s*=\s*(?P<value>.+))?$",
            re.MULTILINE
        )

        for match in annotation_pattern.finditer(block):
            name = match.group("name").strip().strip("'\"")
            value = (match.group("value") or "").strip().strip("'\"")
            annotations.append({
                "name": name,
                "value": value
            })

        return annotations

    @staticmethod
    def _extract_fenced_expression(block: str) -> str:
        """
        Extract expression inside triple backticks.
        """
        match = re.search(r"```(?P<body>.*?)```", block, re.DOTALL)
        if match:
            return match.group("body").strip()
        return ""

    @staticmethod
    def _clean_expression(expression: str) -> str:
        """
        Clean expression while preserving useful DAX/M readability.
        """
        if not expression:
            return ""

        expression = expression.replace("```", "").strip()
        lines = [line.rstrip() for line in expression.splitlines()]

        cleaned_lines = []
        previous_blank = False

        for line in lines:
            if not line.strip():
                if not previous_blank:
                    cleaned_lines.append("")
                previous_blank = True
            else:
                cleaned_lines.append(line.strip())
                previous_blank = False

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def _expression_preview(expression: str, max_length: int = 300) -> str:
        """
        Compact expression preview for documentation tables.
        """
        compact = re.sub(r"\s+", " ", expression or "").strip()
        return compact[:max_length] + "..." if len(compact) > max_length else compact

    # -------------------------------------------------------------------------
    # Inference helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _infer_key_column(column_name: str, source_column: Optional[str]) -> bool:
        """
        Infer whether a column looks like a key.
        """
        candidates = [column_name or "", source_column or ""]
        text = " ".join(candidates).lower()

        key_patterns = [
            "_id",
            " id",
            "id_",
            "key",
            "code",
            "codigo",
            "código",
            "sk_",
            "bk_"
        ]

        return any(pattern in text for pattern in key_patterns)

    @staticmethod
    def _infer_column_semantic_role(
        column_name: str,
        data_type: str,
        is_key: bool,
        data_category: Optional[str]
    ) -> str:
        """
        Infer a lightweight semantic role for documentation.
        """
        name = (column_name or "").lower()
        dtype = (data_type or "").lower()
        category = (data_category or "").lower()

        if is_key:
            return "KEY"
        if dtype in {"datetime", "date"} or "date" in name or "fecha" in name:
            return "DATE"
        if dtype in {"double", "decimal", "int64", "int32", "currency"}:
            return "NUMERIC"
        if category in {"city", "country", "stateorprovince", "postalcode", "latitude", "longitude"}:
            return "GEOGRAPHY"
        if "name" in name or "nombre" in name or "description" in name or "descripcion" in name or "descripción" in name:
            return "ATTRIBUTE"
        if dtype == "boolean":
            return "FLAG"
        return "ATTRIBUTE"

    @staticmethod
    def _has_calculated_table_expression(content: str) -> bool:
        """
        Detect whether a table appears to be calculated.
        """
        upper_content = content.upper()

        calculated_signals = [
            "DATATABLE",
            "SUMMARIZE",
            "SUMMARIZECOLUMNS",
            "ADDCOLUMNS",
            "SELECTCOLUMNS",
            "GENERATESERIES",
            "CALENDAR",
            "CALENDARAUTO",
            "UNION",
            "FILTER("
        ]

        return any(signal in upper_content for signal in calculated_signals)

    @staticmethod
    def _infer_table_kind(
        table_name: str,
        columns: List[Dict[str, Any]],
        measures: List[Dict[str, Any]],
        partitions: List[Dict[str, Any]],
        has_datatable: bool,
        has_calculated_table_expression: bool
    ) -> str:
        """
        Infer a lightweight table kind.

        This does not replace parse_analysis.py classification.
        It only provides table-level technical hints.
        """
        name = table_name.lower()

        if measures and len(columns) <= 1:
            return "CALCULATION"

        if "measure" in name or "calculation" in name or "kpi" in name:
            if measures:
                return "CALCULATION"

        if has_datatable and len(columns) <= 5:
            return "PARAMETER"

        if "param" in name or "parameter" in name or "slicer" in name:
            return "PARAMETER"

        if has_calculated_table_expression:
            return "CALCULATED_TABLE"

        if partitions:
            return "MODEL_TABLE"

        return "UNKNOWN"

    def _relative_path(self, file_path: Path) -> str:
        """
        Return path relative to TMDL directory when possible.
        """
        try:
            return str(file_path.relative_to(self.tmdl_dir))
        except ValueError:
            return str(file_path)


def parse_tables(tmdl_dir: str, output_file: str = None) -> List[Dict[str, Any]]:
    """
    Main function to parse tables.

    Keeps backward-compatible output as a list.
    """
    parser = TableParser(tmdl_dir)
    tables = parser.parse()

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tables, f, indent=2, ensure_ascii=False)

    return tables


def get_table_list(result: Any) -> List[Dict[str, Any]]:
    """
    Compatibility helper.

    Supports:
    - Current contract: [...]
    - Potential future contract: {"tables": [...]}
    """
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]

    if isinstance(result, dict):
        tables = result.get("tables", [])
        if isinstance(tables, list):
            return [item for item in tables if isinstance(item, dict)]

    return []


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_tables.py <tmdl_dir> [output_file]")
        sys.exit(1)

    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "tables.json"

    tables = parse_tables(tmdl_dir, output_file)

    print(f"✓ Parsed {len(tables)} tables")

    total_columns = sum(t.get("column_count", 0) for t in tables)
    total_measures = sum(t.get("measure_count", 0) for t in tables)

    print(f"  Columns: {total_columns}")
    print(f"  Measures: {total_measures}")