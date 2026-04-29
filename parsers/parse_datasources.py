#!/usr/bin/env python3
"""
Parser for Power BI data sources and connections.

Purpose:
- Extract Power Query / M data source references from TMDL files.
- Classify source types with confidence scoring.
- Normalize and deduplicate data source definitions.
- Generate documentation-ready metadata, issues and recommendations.

Outputs:
- datasources.json
"""

import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict


class DataSourceParser:
    """
    Parses data source definitions from a Power BI TMDL directory.

    Typical files inspected:
    - model.tmdl
    - expressions.tmdl
    - tables/*.tmdl

    The parser focuses on common Power Query/M connectors such as:
    - Sql.Database
    - Excel.Workbook
    - Csv.Document
    - SharePoint.Files
    - SharePoint.Contents
    - OData.Feed
    - Web.Contents
    - Folder.Files
    - File.Contents
    """

    CONNECTOR_PATTERNS = {
        "SQL Server": [
            r"Sql\.Database\s*\(",
            r"AnalysisServices\.Database\s*\(",
        ],
        "Excel": [
            r"Excel\.Workbook\s*\(",
        ],
        "CSV/Text": [
            r"Csv\.Document\s*\(",
            r"Lines\.FromBinary\s*\(",
        ],
        "SharePoint": [
            r"SharePoint\.Files\s*\(",
            r"SharePoint\.Contents\s*\(",
            r"SharePoint\.Tables\s*\(",
        ],
        "OData Feed": [
            r"OData\.Feed\s*\(",
        ],
        "Web Source": [
            r"Web\.Contents\s*\(",
            r"Web\.Page\s*\(",
        ],
        "Folder": [
            r"Folder\.Files\s*\(",
            r"Folder\.Contents\s*\(",
        ],
        "File": [
            r"File\.Contents\s*\(",
        ],
        "Dataverse": [
            r"CommonDataService\.Database\s*\(",
            r"Dataverse\.Contents\s*\(",
        ],
        "Power BI Dataflow": [
            r"PowerPlatform\.Dataflows\s*\(",
            r"PowerBI\.Dataflows\s*\(",
        ],
        "Azure": [
            r"AzureStorage\.BlobContents\s*\(",
            r"AzureStorage\.DataLake\s*\(",
            r"AzureDataExplorer\.Contents\s*\(",
        ],
        "Oracle": [
            r"Oracle\.Database\s*\(",
        ],
        "PostgreSQL": [
            r"PostgreSQL\.Database\s*\(",
        ],
        "MySQL": [
            r"MySQL\.Database\s*\(",
        ],
    }

    M_CONNECTOR_REGEX = re.compile(
        r"(?P<connector>[A-Za-z0-9_]+\.[A-Za-z0-9_]+)\s*\((?P<args>.*?)\)",
        re.DOTALL
    )

    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.datasources: List[Dict[str, Any]] = []
        self.issues: List[str] = []
        self.recommendations: List[str] = []

    def parse(self) -> Dict[str, Any]:
        """
        Parse and analyze data sources from the TMDL directory.
        """
        files = self._get_candidate_files()

        if not files:
            self.issues.append("No TMDL files were found for data source analysis.")
            self.recommendations.append("Validate that the provided path points to the SemanticModel/definition directory.")
            return self._build_result([])

        raw_sources = []

        for file_path in files:
            content = self._safe_read(file_path)
            if not content:
                continue

            raw_sources.extend(self._extract_from_content(content, file_path))

        datasources = self._deduplicate_sources(raw_sources)
        datasources = self._sort_sources(datasources)

        self._analyze_datasource_quality(datasources)

        return self._build_result(datasources)

    # -------------------------------------------------------------------------
    # File discovery
    # -------------------------------------------------------------------------

    def _get_candidate_files(self) -> List[Path]:
        """
        Return TMDL files likely to contain data source or M expression metadata.
        """
        candidates = []

        direct_files = [
            self.tmdl_dir / "model.tmdl",
            self.tmdl_dir / "expressions.tmdl",
            self.tmdl_dir / "database.tmdl",
        ]

        for file_path in direct_files:
            if file_path.exists():
                candidates.append(file_path)

        tables_dir = self.tmdl_dir / "tables"
        if tables_dir.exists():
            candidates.extend(sorted(tables_dir.glob("*.tmdl")))

        return sorted(set(candidates))

    @staticmethod
    def _safe_read(file_path: Path) -> str:
        """
        Safely read a file as UTF-8.
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Extraction
    # -------------------------------------------------------------------------

    def _extract_from_content(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract data source references from a TMDL file content.
        """
        sources = []

        expression_blocks = self._extract_expression_blocks(content)

        if expression_blocks:
            for expression_name, expression_content in expression_blocks:
                sources.extend(
                    self._extract_m_connectors(
                        expression_content,
                        source_file=file_path,
                        expression_name=expression_name
                    )
                )
        else:
            sources.extend(
                self._extract_m_connectors(
                    content,
                    source_file=file_path,
                    expression_name=None
                )
            )

        # Fallback: detect generic source assignments.
        sources.extend(self._extract_source_assignments(content, file_path))

        return sources

    def _extract_expression_blocks(self, content: str) -> List[Tuple[str, str]]:
        """
        Extract expression blocks from TMDL content.

        This is intentionally tolerant because TMDL indentation and expression
        formatting can vary between exported models.
        """
        blocks = []

        expression_pattern = re.compile(
            r"(?:^|\n)\s*expression\s+(['\"]?)(?P<name>[^'\"\n]+)\1\s*=\s*(?P<body>.*?)(?=\n\s*expression\s+|$)",
            re.DOTALL
        )

        for match in expression_pattern.finditer(content):
            name = match.group("name").strip()
            body = match.group("body").strip()
            blocks.append((name, body))

        return blocks

    def _extract_m_connectors(
        self,
        content: str,
        source_file: Path,
        expression_name: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract known M connector calls from content.
        """
        sources = []

        for match in self.M_CONNECTOR_REGEX.finditer(content):
            connector = match.group("connector")
            args = self._clean_text(match.group("args"))

            source_type, confidence, detection_reason = self._classify_connector(connector, args)

            if source_type == "Other":
                continue

            attributes = self._extract_attributes(connector, args)

            source = {
                "id": self._make_source_id(connector, args, str(source_file), expression_name),
                "type": source_type,
                "connector": connector,
                "confidence": confidence,
                "detection_reason": detection_reason,
                "source_file": self._relative_path(source_file),
                "expression_name": expression_name,
                "attributes": attributes,
                "definition": self._truncate_definition(f"{connector}({args})"),
                "privacy_note": self._privacy_note(source_type, attributes),
            }

            sources.append(source)

        return sources

    def _extract_source_assignments(self, content: str, source_file: Path) -> List[Dict[str, Any]]:
        """
        Fallback extraction for simple 'source =' assignments.
        """
        sources = []

        source_pattern = re.compile(r"(?:^|\n)\s*source\s*=\s*(?P<source>[^\n]+)", re.IGNORECASE)

        for match in source_pattern.finditer(content):
            source_def = self._clean_text(match.group("source"))
            source_type, confidence, reason = self._classify_source_text(source_def)

            if source_type == "Other":
                continue

            source = {
                "id": self._make_source_id("source_assignment", source_def, str(source_file), None),
                "type": source_type,
                "connector": "source_assignment",
                "confidence": confidence,
                "detection_reason": reason,
                "source_file": self._relative_path(source_file),
                "expression_name": None,
                "attributes": self._extract_attributes("source_assignment", source_def),
                "definition": self._truncate_definition(source_def),
                "privacy_note": self._privacy_note(source_type, {}),
            }

            sources.append(source)

        return sources

    # -------------------------------------------------------------------------
    # Classification
    # -------------------------------------------------------------------------

    def _classify_connector(self, connector: str, args: str) -> Tuple[str, float, str]:
        """
        Classify a connector using known M connector names and argument signals.
        """
        connector_text = connector.strip()
        combined_text = f"{connector_text} {args}".lower()

        for source_type, patterns in self.CONNECTOR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, connector_text, re.IGNORECASE):
                    return source_type, 0.95, f"Detected M connector: {connector_text}"

        return self._classify_source_text(combined_text)

    def _classify_source_text(self, text: str) -> Tuple[str, float, str]:
        """
        Classify source using generic keyword detection.
        """
        lower_text = text.lower()

        keyword_map = [
            ("SQL Server", ["sql.database", "sql server", "sqlserver", "database.windows.net"]),
            ("Excel", ["excel.workbook", ".xlsx", ".xlsm", ".xls"]),
            ("CSV/Text", ["csv.document", ".csv", ".txt", "text/csv"]),
            ("SharePoint", ["sharepoint.files", "sharepoint.contents", "sharepoint.com"]),
            ("OData Feed", ["odata.feed", "odata"]),
            ("Web Source", ["web.contents", "https://", "http://"]),
            ("Folder", ["folder.files", "folder.contents"]),
            ("File", ["file.contents"]),
            ("Dataverse", ["commondataservice.database", "dataverse"]),
            ("Power BI Dataflow", ["powerplatform.dataflows", "powerbi.dataflows", "dataflows"]),
            ("Azure", ["azurestorage", "azuredatalake", "azuredataexplorer"]),
            ("Oracle", ["oracle.database"]),
            ("PostgreSQL", ["postgresql.database"]),
            ("MySQL", ["mysql.database"]),
        ]

        for source_type, keywords in keyword_map:
            if any(keyword in lower_text for keyword in keywords):
                return source_type, 0.70, f"Detected by keyword match for {source_type}"

        if "database" in lower_text:
            return "Database", 0.55, "Generic database keyword detected"

        return "Other", 0.30, "No reliable data source pattern detected"

    # -------------------------------------------------------------------------
    # Attribute extraction
    # -------------------------------------------------------------------------

    def _extract_attributes(self, connector: str, args: str) -> Dict[str, Any]:
        """
        Extract common attributes from M connector arguments.
        """
        attributes: Dict[str, Any] = {}

        quoted_values = self._extract_quoted_values(args)
        connector_lower = connector.lower()

        if connector_lower == "sql.database":
            if len(quoted_values) >= 1:
                attributes["server"] = quoted_values[0]
            if len(quoted_values) >= 2:
                attributes["database"] = quoted_values[1]

        elif connector_lower in {
            "analysisservices.database",
            "oracle.database",
            "postgresql.database",
            "mysql.database",
            "commondataservice.database"
        }:
            if len(quoted_values) >= 1:
                attributes["server"] = quoted_values[0]
            if len(quoted_values) >= 2:
                attributes["database"] = quoted_values[1]

        elif connector_lower in {
            "web.contents",
            "web.page",
            "odata.feed",
            "sharepoint.files",
            "sharepoint.contents",
            "sharepoint.tables"
        }:
            if quoted_values:
                attributes["url"] = quoted_values[0]
                attributes["domain"] = self._extract_domain(quoted_values[0])

        elif connector_lower in {
            "file.contents",
            "excel.workbook",
            "csv.document",
            "folder.files",
            "folder.contents"
        }:
            if quoted_values:
                attributes["path"] = quoted_values[0]
                attributes["file_extension"] = self._extract_file_extension(quoted_values[0])

        else:
            if quoted_values:
                attributes["first_argument"] = quoted_values[0]

        attributes["argument_count"] = len(quoted_values)

        return attributes

    @staticmethod
    def _extract_quoted_values(text: str) -> List[str]:
        """
        Extract quoted string values from connector arguments.
        """
        values = []

        # Handles normal M strings: "value"
        for match in re.finditer(r'"([^"]*)"', text):
            values.append(match.group(1))

        # Handles single quoted values if present.
        for match in re.finditer(r"'([^']*)'", text):
            values.append(match.group(1))

        return values

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        match = re.search(r"https?://([^/]+)", url, re.IGNORECASE)
        return match.group(1).lower() if match else None

    @staticmethod
    def _extract_file_extension(path: str) -> Optional[str]:
        suffix = Path(path).suffix.lower()
        return suffix if suffix else None

    # -------------------------------------------------------------------------
    # Deduplication and quality analysis
    # -------------------------------------------------------------------------

    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate sources using type, connector and main attributes.
        """
        grouped = {}

        for source in sources:
            key = self._dedupe_key(source)

            if key not in grouped:
                grouped[key] = source
                grouped[key]["occurrences"] = 1
                grouped[key]["references"] = [{
                    "source_file": source.get("source_file"),
                    "expression_name": source.get("expression_name")
                }]
            else:
                grouped[key]["occurrences"] += 1
                grouped[key]["references"].append({
                    "source_file": source.get("source_file"),
                    "expression_name": source.get("expression_name")
                })

                grouped[key]["confidence"] = max(
                    grouped[key].get("confidence", 0),
                    source.get("confidence", 0)
                )

        return list(grouped.values())

    @staticmethod
    def _dedupe_key(source: Dict[str, Any]) -> str:
        attrs = source.get("attributes", {})

        key_parts = [
            source.get("type", ""),
            source.get("connector", ""),
            attrs.get("server", ""),
            attrs.get("database", ""),
            attrs.get("url", ""),
            attrs.get("domain", ""),
            attrs.get("path", ""),
        ]

        raw_key = "|".join(str(part).lower() for part in key_parts if part is not None)
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _sort_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            sources,
            key=lambda x: (
                x.get("type", ""),
                x.get("connector", ""),
                x.get("attributes", {}).get("server", ""),
                x.get("attributes", {}).get("url", ""),
                x.get("attributes", {}).get("path", "")
            )
        )

    def _analyze_datasource_quality(self, datasources: List[Dict[str, Any]]) -> None:
        """
        Generate issues and recommendations based on detected data sources.
        """
        if not datasources:
            self.issues.append("No explicit data sources were detected.")
            self.recommendations.append("Review expressions.tmdl and table partitions to confirm whether source definitions are stored elsewhere.")
            return

        source_types = Counter(ds["type"] for ds in datasources)

        if len(source_types) > 3:
            self.issues.append(f"Multiple data source types detected: {', '.join(sorted(source_types.keys()))}.")
            self.recommendations.append("Validate gateway, privacy levels and refresh configuration for mixed-source models.")

        file_based_sources = [
            ds for ds in datasources
            if ds["type"] in {"Excel", "CSV/Text", "File", "Folder"}
        ]

        if file_based_sources:
            self.recommendations.append("For file-based sources, confirm that paths are stable and accessible from the refresh environment.")

        web_sources = [
            ds for ds in datasources
            if ds["type"] in {"Web Source", "OData Feed", "SharePoint"}
        ]

        if web_sources:
            self.recommendations.append("For web or cloud sources, confirm authentication method, privacy level and scheduled refresh behavior.")

        low_confidence = [ds for ds in datasources if ds.get("confidence", 0) < 0.7]
        if low_confidence:
            self.issues.append(f"{len(low_confidence)} data source(s) were detected with low confidence.")
            self.recommendations.append("Review low-confidence source detections manually in the original TMDL/M expressions.")

    # -------------------------------------------------------------------------
    # Output
    # -------------------------------------------------------------------------

    def _build_result(self, datasources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build final output contract.
        """
        source_type_counts = Counter(ds["type"] for ds in datasources)
        connector_counts = Counter(ds["connector"] for ds in datasources)

        return {
            "datasources": datasources,
            "summary": {
                "total_datasources": len(datasources),
                "source_type_distribution": dict(source_type_counts),
                "connector_distribution": dict(connector_counts),
                "has_m_queries": any(ds.get("connector") not in {None, "source_assignment"} for ds in datasources),
                "has_file_based_sources": any(ds["type"] in {"Excel", "CSV/Text", "File", "Folder"} for ds in datasources),
                "has_cloud_sources": any(ds["type"] in {"SharePoint", "OData Feed", "Web Source", "Dataverse", "Power BI Dataflow", "Azure"} for ds in datasources),
                "has_database_sources": any(ds["type"] in {"SQL Server", "Database", "Oracle", "PostgreSQL", "MySQL"} for ds in datasources),
            },
            "issues": self._unique_list(self.issues),
            "recommendations": self._unique_list(self.recommendations)
        }

    @staticmethod
    def _truncate_definition(definition: str, max_length: int = 300) -> str:
        definition = DataSourceParser._clean_text(definition)
        return definition[:max_length] + "..." if len(definition) > max_length else definition

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def _relative_path(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.tmdl_dir))
        except ValueError:
            return str(file_path)

    @staticmethod
    def _make_source_id(
        connector: str,
        args: str,
        file_path: str,
        expression_name: Optional[str]
    ) -> str:
        raw = f"{connector}|{args}|{file_path}|{expression_name or ''}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _privacy_note(source_type: str, attributes: Dict[str, Any]) -> Optional[str]:
        """
        Adds lightweight documentation notes without exposing credentials.
        """
        if source_type in {"Web Source", "OData Feed", "SharePoint"}:
            return "Cloud/web source detected; validate authentication and privacy level."
        if source_type in {"Excel", "CSV/Text", "File", "Folder"}:
            return "File-based source detected; validate path availability for refresh."
        if source_type in {"SQL Server", "Database", "Oracle", "PostgreSQL", "MySQL"}:
            return "Database source detected; validate gateway and credential configuration."
        return None

    @staticmethod
    def _unique_list(items: List[str]) -> List[str]:
        seen = set()
        unique = []

        for item in items:
            if item not in seen:
                unique.append(item)
                seen.add(item)

        return unique


def parse_datasources(tmdl_dir: str, output_file: str = None) -> Dict[str, Any]:
    """
    Main function to parse Power BI data sources.
    """
    parser = DataSourceParser(tmdl_dir)
    result = parser.parse()

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_datasources.py <tmdl_dir> [output_file]")
        sys.exit(1)

    tmdl_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "datasources.json"

    result = parse_datasources(tmdl_dir, output_file)

    total = result.get("summary", {}).get("total_datasources", 0)
    print(f"✓ Parsed {total} data sources")

    if result.get("issues"):
        print(f"⚠ Issues detected: {len(result['issues'])}")