#!/usr/bin/env python3
"""
Parser for Power BI relationships from TMDL definition.

Purpose:
- Extract semantic model relationships from relationships.tmdl.
- Preserve compatibility with the original relationships.json list contract.
- Capture cardinality, filter direction, active state and useful metadata.
- Add lightweight quality flags for downstream documentation/analysis.

Outputs:
- relationships.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


class RelationshipParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.relationships: List[Dict[str, Any]] = []
        self.issues: List[str] = []

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse relationships from TMDL.

        Keeps backward-compatible output:
        [
            {
                "id": "...",
                "from_table": "...",
                "from_column": "...",
                "to_table": "...",
                "to_column": "...",
                "cardinality": "...",
                "cross_filter_direction": "..."
            }
        ]
        """
        rel_file = self.tmdl_dir / "relationships.tmdl"

        if not rel_file.exists():
            return []

        content = self._safe_read(rel_file)
        if not content.strip():
            return []

        self._extract_relationships(content)

        return self.relationships

    # -------------------------------------------------------------------------
    # File handling
    # -------------------------------------------------------------------------

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
    # Relationship extraction
    # -------------------------------------------------------------------------

    def _extract_relationships(self, content: str) -> None:
        """
        Extract all relationship blocks from relationships.tmdl.

        This is intentionally block-based because TMDL property order can vary.
        """
        blocks = self._split_relationship_blocks(content)

        for block in blocks:
            relationship = self._parse_relationship_block(block)

            if relationship:
                self.relationships.append(relationship)

    def _split_relationship_blocks(self, content: str) -> List[str]:
        """
        Split relationships.tmdl into relationship blocks.

        Handles blocks that start with:
        relationship <id>
        """
        pattern = re.compile(
            r"(^|\n)\s*relationship\s+([^\n]+)\n",
            re.IGNORECASE
        )

        matches = list(pattern.finditer(content))
        blocks = []

        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            blocks.append(content[start:end].strip())

        return blocks

    def _parse_relationship_block(self, block: str) -> Optional[Dict[str, Any]]:
        """
        Parse one relationship block.
        """
        header_match = re.search(
            r"relationship\s+(?P<id>[^\n]+)",
            block,
            re.IGNORECASE
        )

        if not header_match:
            return None

        rel_id = header_match.group("id").strip().strip("'\"")

        properties = self._extract_properties(block)

        from_col_spec = properties.get("fromColumn")
        to_col_spec = properties.get("toColumn")

        if not from_col_spec or not to_col_spec:
            self.issues.append(f"Relationship {rel_id} skipped because fromColumn or toColumn is missing.")
            return None

        from_table, from_column = self._parse_table_column(from_col_spec)
        to_table, to_column = self._parse_table_column(to_col_spec)

        if not from_table or not to_table:
            self.issues.append(f"Relationship {rel_id} skipped because table/column parsing failed.")
            return None

        from_cardinality = self._normalize_cardinality(
            properties.get("fromCardinality"),
            default="many"
        )
        to_cardinality = self._normalize_cardinality(
            properties.get("toCardinality"),
            default="one"
        )

        cardinality = self._format_cardinality(from_cardinality, to_cardinality)

        cross_filter_behavior = properties.get("crossFilteringBehavior")
        cross_filter_direction = self._normalize_cross_filter_direction(cross_filter_behavior)

        is_active = self._parse_bool(properties.get("isActive"), default=True)
        rely_on_referential_integrity = self._parse_bool(
            properties.get("relyOnReferentialIntegrity"),
            default=False
        )

        security_filtering_behavior = properties.get("securityFilteringBehavior")
        lineage_tag = properties.get("lineageTag")

        quality_flags = self._build_quality_flags(
            from_cardinality=from_cardinality,
            to_cardinality=to_cardinality,
            cross_filter_direction=cross_filter_direction,
            is_active=is_active
        )

        return {
            "id": rel_id,
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column,

            # Backward-compatible fields
            "cardinality": cardinality,
            "cross_filter_direction": cross_filter_direction,

            # More detailed metadata for analysis/documentation
            "from_cardinality": from_cardinality,
            "to_cardinality": to_cardinality,
            "cross_filtering_behavior": cross_filter_behavior or "singleDirection",
            "security_filtering_behavior": security_filtering_behavior,
            "is_active": is_active,
            "rely_on_referential_integrity": rely_on_referential_integrity,
            "lineage_tag": lineage_tag,
            "quality_flags": quality_flags,
            "raw": {
                "fromColumn": from_col_spec,
                "toColumn": to_col_spec
            }
        }

    def _extract_properties(self, block: str) -> Dict[str, str]:
        """
        Extract key: value properties from a relationship block.
        """
        properties: Dict[str, str] = {}

        property_pattern = re.compile(
            r"^\s*(?P<key>[A-Za-z][A-Za-z0-9_]*):\s*(?P<value>.+?)\s*$",
            re.MULTILINE
        )

        for match in property_pattern.finditer(block):
            key = match.group("key").strip()
            value = match.group("value").strip().strip("'\"")
            properties[key] = value

        return properties

    # -------------------------------------------------------------------------
    # Table/column parsing
    # -------------------------------------------------------------------------

    def _parse_table_column(self, spec: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse table-column references from TMDL.

        Supports:
        - Table.Column
        - 'Table Name'.'Column Name'
        - Table[Column]
        - 'Table Name'[Column Name]
        - [Table].[Column] style partially
        """
        if not spec:
            return None, None

        spec = spec.strip().strip("'\"")

        # Pattern: 'Table Name'[Column Name] or Table[Column]
        bracket_match = re.match(
            r"^(?P<table>'[^']+'|\"[^\"]+\"|[^\[]+)\[(?P<column>[^\]]+)\]$",
            spec
        )
        if bracket_match:
            table = self._clean_identifier(bracket_match.group("table"))
            column = self._clean_identifier(bracket_match.group("column"))
            return table, column

        # Pattern: 'Table Name'.'Column Name'
        quoted_dot_match = re.match(
            r"^(?P<table>'[^']+'|\"[^\"]+\"|\[[^\]]+\])\s*\.\s*(?P<column>'[^']+'|\"[^\"]+\"|\[[^\]]+\])$",
            spec
        )
        if quoted_dot_match:
            table = self._clean_identifier(quoted_dot_match.group("table"))
            column = self._clean_identifier(quoted_dot_match.group("column"))
            return table, column

        # Generic dot split.
        # Use the last dot as separator to support table names that may contain dots.
        if "." in spec:
            table_part, column_part = spec.rsplit(".", 1)
            table = self._clean_identifier(table_part)
            column = self._clean_identifier(column_part)
            return table, column

        return None, None

    @staticmethod
    def _clean_identifier(value: str) -> str:
        """
        Clean TMDL table/column identifiers.
        """
        if value is None:
            return ""

        value = value.strip()

        # Remove brackets and quotes around the entire identifier.
        value = value.strip("'\"")
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]

        return value.strip()

    # -------------------------------------------------------------------------
    # Normalization
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize_cardinality(value: Optional[str], default: str) -> str:
        """
        Normalize cardinality values.
        """
        if not value:
            return default

        value = value.strip().lower()

        mapping = {
            "one": "one",
            "many": "many",
            "1": "one",
            "*": "many"
        }

        return mapping.get(value, value)

    @staticmethod
    def _format_cardinality(from_cardinality: str, to_cardinality: str) -> str:
        """
        Convert from/to cardinalities into readable relationship cardinality.
        """
        left = "Many" if from_cardinality == "many" else "One"
        right = "Many" if to_cardinality == "many" else "One"

        return f"{left}-to-{right}"

    @staticmethod
    def _normalize_cross_filter_direction(value: Optional[str]) -> str:
        """
        Normalize cross filtering behavior into documentation-friendly direction.
        """
        if not value:
            return "Single"

        normalized = value.strip().lower()

        if normalized in {"bothdirections", "both", "bidirectional"}:
            return "Both"

        if normalized in {"onedirection", "single", "singledirection"}:
            return "Single"

        return value

    @staticmethod
    def _parse_bool(value: Optional[str], default: bool = False) -> bool:
        """
        Parse boolean-like values.
        """
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        return str(value).strip().lower() == "true"

    # -------------------------------------------------------------------------
    # Quality flags
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_quality_flags(
        from_cardinality: str,
        to_cardinality: str,
        cross_filter_direction: str,
        is_active: bool
    ) -> List[str]:
        """
        Generate lightweight quality flags for downstream analysis.
        """
        flags = []

        if from_cardinality == "many" and to_cardinality == "many":
            flags.append("MANY_TO_MANY")

        if cross_filter_direction == "Both":
            flags.append("BIDIRECTIONAL_FILTERING")

        if not is_active:
            flags.append("INACTIVE_RELATIONSHIP")

        if from_cardinality == "one" and to_cardinality == "one":
            flags.append("ONE_TO_ONE")

        return flags


def parse_relationships(tmdl_dir: str, output_file: str = None) -> List[Dict[str, Any]]:
    """
    Main function to parse relationships.

    Keeps backward-compatible output as a list.
    """
    parser = RelationshipParser(tmdl_dir)
    relationships = parser.parse()

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(relationships, f, indent=2, ensure_ascii=False)

    return relationships


def get_relationship_list(result: Any) -> List[Dict[str, Any]]:
    """
    Compatibility helper.

    Supports:
    - Old/current contract: [...]
    - Potential future contract: {"relationships": [...]}
    """
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]

    if isinstance(result, dict):
        relationships = result.get("relationships", [])
        if isinstance(relationships, list):
            return [item for item in relationships if isinstance(item, dict)]

    return []


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_relationships.py <tmdl_dir> [output_file]")
        sys.exit(1)

    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "relationships.json"

    relationships = parse_relationships(tmdl_dir, output_file)

    print(f"✓ Parsed {len(relationships)} relationships")

    inactive_count = sum(1 for r in relationships if not r.get("is_active", True))
    many_to_many_count = sum(1 for r in relationships if "MANY_TO_MANY" in r.get("quality_flags", []))
    bidirectional_count = sum(1 for r in relationships if "BIDIRECTIONAL_FILTERING" in r.get("quality_flags", []))

    if inactive_count:
        print(f"  ⚠ Inactive relationships: {inactive_count}")

    if many_to_many_count:
        print(f"  ⚠ Many-to-many relationships: {many_to_many_count}")

    if bidirectional_count:
        print(f"  ⚠ Bidirectional relationships: {bidirectional_count}")