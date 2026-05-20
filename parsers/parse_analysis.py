#!/usr/bin/env python3
"""
Parser for Power BI model analysis.

Purpose:
- Classify semantic model tables.
- Analyze relationship topology.
- Detect schema type dynamically.
- Calculate model compliance score.
- Generate issues and recommendations.

Outputs:
- analysis.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter, deque


NUMERIC_TYPES = {"double", "int64", "int32", "decimal", "currency"}
STRING_TYPES = {"string"}
DATE_TYPES = {"dateTime", "date"}
BOOLEAN_TYPES = {"boolean"}

TABLE_TYPES = {
    "FACT",
    "DIMENSION",
    "BRIDGE",
    "CALCULATION",
    "PARAMETER",
    "UNKNOWN"
}

# Foreign key detection patterns
FK_PATTERNS = [
    r".*[Ii]d$",              # EndsWith Id, id
    r".*[Ii]d[A-Z]",         # Contains Id followed by capital letter
    r".*_[Ii]d$",             # EndsWith _Id, _id
    r"^[Kk]ey_.*",           # StartsWith Key_, key_
    r".*[Kk]ey[A-Z]",        # Contains Key followed by capital
    r".*[Cc]ode$",            # EndsWith Code, code (common for dimension codes)
]

# Additive aggregation functions (for summarizeBy)
ADDITIVE_AGGREGATIONS = {"Sum", "sum", "SUM", "Count", "count", "COUNT"}


class AnalysisParser:
    def __init__(self, tmdl_dir: str):
        self.tmdl_dir = Path(tmdl_dir)
        self.tables: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        self.table_profiles: Dict[str, Dict[str, Any]] = {}

    def parse(self) -> Dict[str, Any]:
        """
        Perform comprehensive model analysis.
        """
        self._parse_all_data()

        self.table_profiles = self._build_table_profiles()
        classifications = self._classify_tables()
        relationship_analysis = self._analyze_relationships(classifications)
        model_metrics = self._generate_model_metrics(classifications, relationship_analysis)

        return {
            "table_classifications": classifications,
            "relationship_analysis": relationship_analysis,
            "model_metrics": model_metrics,
            "summary": self._generate_summary(classifications, relationship_analysis, model_metrics)
        }

    # -------------------------------------------------------------------------
    # Parsing
    # -------------------------------------------------------------------------

    def _parse_all_data(self) -> None:
        """
        Parse tables, columns, measures and relationships from TMDL directory.
        """
        tables_dir = self.tmdl_dir / "tables"

        if not tables_dir.exists():
            raise FileNotFoundError(f"Tables directory not found: {tables_dir}")

        for tmdl_file in sorted(tables_dir.glob("*.tmdl")):
            table_name = tmdl_file.stem
            content = tmdl_file.read_text(encoding="utf-8")

            columns = self._extract_columns(content)
            measures = self._extract_measures(content)

            self.tables[table_name] = {
                "columns": columns,
                "measures": measures,
                "has_datatable": "DATATABLE" in content.upper(),
                "raw_size_chars": len(content)
            }

        self._parse_relationships()

    def _extract_columns(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract columns and basic metadata from TMDL content.
        Detects:
        - Calculated columns (have inline expressions)
        - Concatenated columns (use CONCATENATE, CONCAT, or & operator)
        - Text key columns (concatenated string columns used in relationships)
        """
        columns = []

        col_pattern = r"column\s+(['\"]?)([^'\"\n]+)\1\s*\n((?:\t[^\n]*\n|\s{2,}[^\n]*\n)*?)"

        for match in re.finditer(col_pattern, content):
            col_name = match.group(2).strip()
            col_block = match.group(3)

            datatype_match = re.search(r"dataType:\s*(\w+)", col_block)
            datatype = datatype_match.group(1) if datatype_match else "string"

            is_hidden = bool(re.search(r"isHidden:\s*true", col_block, re.IGNORECASE))
            summarize_by_match = re.search(r"summarizeBy:\s*(\w+)", col_block)
            summarize_by = summarize_by_match.group(1) if summarize_by_match else None

            # Detect calculated columns
            # Calculated columns have an inline expression (= operator or expression: line)
            is_calculated = bool(
                re.search(r"^\s*column\s+['\"]?[^'\"]+['\"]?\s*=", content[match.start():match.end()], re.MULTILINE)
                or re.search(r"expression\s*=", col_block, re.IGNORECASE)
            )

            # Detect concatenated columns
            # Look for CONCATENATE, CONCAT functions or & operator in the column block
            is_concatenated = bool(
                re.search(r"CONCATENATE\s*\(", col_block, re.IGNORECASE)
                or re.search(r"CONCAT\s*\(", col_block, re.IGNORECASE)
                or re.search(r"[^=!<>]\s*&\s*[^=&]", col_block)  # & operator (not ==, !=, <=, >=, &&)
            )

            columns.append({
                "name": col_name,
                "dataType": datatype,
                "isHidden": is_hidden,
                "summarizeBy": summarize_by,
                "is_calculated": is_calculated,
                "is_concatenated": is_concatenated,
                "is_text_concatenated_key": is_concatenated and datatype in STRING_TYPES
            })

        return columns

    def _extract_measures(self, content: str) -> List[str]:
        """
        Extract measure names from TMDL content.
        """
        measures = []

        measure_pattern = r"measure\s+(['\"]?)([^'\"\n=]+)\1\s*(?:=|$)"

        for match in re.finditer(measure_pattern, content):
            measure_name = match.group(2).strip()
            if measure_name:
                measures.append(measure_name)

        return measures

    def _parse_relationships(self) -> None:
        """
        Parse model relationships from relationships.tmdl.
        """
        rel_file = self.tmdl_dir / "relationships.tmdl"

        if not rel_file.exists():
            return

        content = rel_file.read_text(encoding="utf-8")

        relationship_blocks = re.split(r"\n\s*relationship\s+", content)

        for block in relationship_blocks:
            if not block.strip():
                continue

            from_col_match = re.search(r"fromColumn:\s*([^\n]+)", block)
            to_col_match = re.search(r"toColumn:\s*([^\n]+)", block)
            from_card_match = re.search(r"fromCardinality:\s*(\w+)", block)
            to_card_match = re.search(r"toCardinality:\s*(\w+)", block)
            cross_filter_match = re.search(r"crossFilteringBehavior:\s*(\w+)", block)
            is_active_match = re.search(r"isActive:\s*(\w+)", block)

            if not from_col_match or not to_col_match:
                continue

            from_col = from_col_match.group(1).strip()
            to_col = to_col_match.group(1).strip()

            from_table, from_column = self._parse_table_column(from_col)
            to_table, to_column = self._parse_table_column(to_col)

            if from_table and to_table:
                self.relationships.append({
                    "from_table": from_table,
                    "from_column": from_column,
                    "to_table": to_table,
                    "to_column": to_column,
                    "from_cardinality": from_card_match.group(1) if from_card_match else "many",
                    "to_cardinality": to_card_match.group(1) if to_card_match else "one",
                    "cross_filtering_behavior": cross_filter_match.group(1) if cross_filter_match else "singleDirection",
                    "is_active": self._parse_bool(is_active_match.group(1)) if is_active_match else True
                })

    def _parse_table_column(self, spec: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a TMDL table/column reference.

        Supports patterns like:
        - Table.Column
        - 'Table Name'.'Column Name'
        - Table[Column]
        """
        spec = spec.strip()

        bracket_match = re.match(r"(.+)\[(.+)\]", spec)
        if bracket_match:
            table = bracket_match.group(1).strip().strip("'\"[]")
            column = bracket_match.group(2).strip().strip("'\"[]")
            return table, column

        parts = spec.split(".")
        if len(parts) >= 2:
            table = parts[0].strip().strip("'\"[]")
            column = ".".join(parts[1:]).strip().strip("'\"[]")
            return table, column

        return None, None

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return str(value).strip().lower() == "true"

    # -------------------------------------------------------------------------
    # Profiling
    # -------------------------------------------------------------------------

    def _build_table_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Build reusable table-level profile metrics.
        """
        profiles = {}

        for table_name, table_data in self.tables.items():
            columns = table_data["columns"]
            measures = table_data["measures"]

            col_count = len(columns)
            measure_count = len(measures)

            numeric_count = sum(1 for c in columns if c["dataType"] in NUMERIC_TYPES)
            string_count = sum(1 for c in columns if c["dataType"] in STRING_TYPES)
            date_count = sum(1 for c in columns if c["dataType"] in DATE_TYPES)
            boolean_count = sum(1 for c in columns if c["dataType"] in BOOLEAN_TYPES)

            # Count calculated and concatenated columns
            calculated_count = sum(1 for c in columns if c.get("is_calculated", False))
            concatenated_count = sum(1 for c in columns if c.get("is_concatenated", False))
            text_concat_key_count = sum(1 for c in columns if c.get("is_text_concatenated_key", False))

            rel_from = [r for r in self.relationships if r["from_table"] == table_name]
            rel_to = [r for r in self.relationships if r["to_table"] == table_name]

            outgoing_count = len(rel_from)
            incoming_count = len(rel_to)

            lower_name = table_name.lower()

            profiles[table_name] = {
                "columns": col_count,
                "measures": measure_count,
                "numeric_columns": numeric_count,
                "string_columns": string_count,
                "date_columns": date_count,
                "boolean_columns": boolean_count,
                "calculated_columns": calculated_count,
                "concatenated_columns": concatenated_count,
                "text_concatenated_keys": text_concat_key_count,
                "relationships_from": outgoing_count,
                "relationships_to": incoming_count,
                "total_relationships": outgoing_count + incoming_count,
                "has_datatable": table_data.get("has_datatable", False),
                "name_tokens": self._tokenize_name(lower_name),
                "is_isolated": outgoing_count + incoming_count == 0,
                "numeric_ratio": round(numeric_count / col_count, 4) if col_count else 0,
                "string_ratio": round(string_count / col_count, 4) if col_count else 0,
                "date_ratio": round(date_count / col_count, 4) if col_count else 0,
                "calculated_ratio": round(calculated_count / col_count, 4) if col_count else 0
            }

        return profiles

    @staticmethod
    def _tokenize_name(name: str) -> List[str]:
        tokens = re.split(r"[\s_\-\.]+", name.lower())
        return [t for t in tokens if t]

    # -------------------------------------------------------------------------
    # Table Classification
    # -------------------------------------------------------------------------

    def _classify_tables(self) -> List[Dict[str, Any]]:
        """
        Classify all tables using weighted scoring.
        """
        classifications = []

        for table_name in sorted(self.tables.keys()):
            classifications.append(self._classify_single_table(table_name))

        return classifications

    def _classify_single_table(self, table_name: str) -> Dict[str, Any]:
        """
        Classify a single table using multiple scoring signals.
        """
        profile = self.table_profiles[table_name]
        tokens = profile["name_tokens"]
        columns = self.tables[table_name]["columns"]

        scores = {
            "FACT": 0,
            "DIMENSION": 0,
            "BRIDGE": 0,
            "CALCULATION": 0,
            "PARAMETER": 0
        }

        evidence = defaultdict(list)

        # ---------------------------------------------------------------------
        # Name-based signals
        # ---------------------------------------------------------------------

        if any(t in tokens for t in ["fact", "facts", "transaction", "transactions", "sales", "spend", "ledger"]):
            scores["FACT"] += 35
            evidence["FACT"].append("Name suggests transactional/fact data")

        if any(t in tokens for t in ["dim", "dimension", "master", "catalog", "lookup"]):
            scores["DIMENSION"] += 30
            evidence["DIMENSION"].append("Name suggests dimension or lookup table")

        if any(t in tokens for t in ["bridge", "map", "mapping", "xref", "link"]):
            scores["BRIDGE"] += 35
            evidence["BRIDGE"].append("Name suggests bridge or mapping table")

        if any(t in tokens for t in ["calendar", "date", "time", "period", "fiscal"]):
            scores["DIMENSION"] += 35
            evidence["DIMENSION"].append("Name suggests calendar/time dimension")

        if any(t in tokens for t in ["parameter", "param", "selector", "slicer"]):
            scores["PARAMETER"] += 35
            evidence["PARAMETER"].append("Name suggests parameter or slicer table")

        if any(t in tokens for t in ["measure", "measures", "calculation", "calculations", "kpi", "metrics"]):
            scores["CALCULATION"] += 35
            evidence["CALCULATION"].append("Name suggests measure/calculation container")

        # ---------------------------------------------------------------------
        # Structure-based signals
        # ---------------------------------------------------------------------

        if profile["measures"] >= 10 and profile["columns"] <= 2:
            scores["CALCULATION"] += 50
            evidence["CALCULATION"].append("High measure count with very few columns")

        if profile["measures"] >= 5 and profile["columns"] <= 1:
            scores["CALCULATION"] += 35
            evidence["CALCULATION"].append("Likely dedicated measures table")

        if profile["has_datatable"] and profile["columns"] <= 5:
            scores["PARAMETER"] += 25
            evidence["PARAMETER"].append("Uses DATATABLE with low column count")

        if profile["columns"] <= 3 and profile["is_isolated"]:
            scores["PARAMETER"] += 20
            evidence["PARAMETER"].append("Small isolated table, likely control/parameter table")

        if profile["numeric_columns"] >= 2 and profile["relationships_from"] >= 2:
            scores["FACT"] += 25
            evidence["FACT"].append("Multiple numeric columns and outgoing relationships")

        if profile["relationships_from"] >= 3:
            scores["FACT"] += 20
            evidence["FACT"].append("High number of outgoing relationships")

        if profile["columns"] >= 20 and profile["relationships_from"] >= 2:
            scores["FACT"] += 15
            evidence["FACT"].append("Large table with multiple outgoing relationships")

        if profile["relationships_to"] >= 2 and profile["relationships_from"] == 0:
            scores["DIMENSION"] += 25
            evidence["DIMENSION"].append("Receives relationships from other tables")

        if profile["string_ratio"] >= 0.5 and profile["relationships_to"] >= 1:
            scores["DIMENSION"] += 15
            evidence["DIMENSION"].append("Attribute-heavy table with incoming relationships")

        if profile["date_columns"] >= 2:
            scores["DIMENSION"] += 25
            evidence["DIMENSION"].append("Multiple date columns suggest time dimension")

        if profile["relationships_from"] >= 1 and profile["relationships_to"] >= 1 and profile["columns"] <= 8:
            scores["BRIDGE"] += 25
            evidence["BRIDGE"].append("Connects tables with compact structure")

        if profile["relationships_from"] >= 2 and profile["relationships_to"] >= 2:
            scores["BRIDGE"] += 20
            evidence["BRIDGE"].append("Acts as connector between multiple related tables")

        # NEW: Penalize FACT tables with too many calculated columns
        if profile["calculated_columns"] >= 3 and profile["relationships_from"] >= 2:
            scores["FACT"] -= 15
            evidence["FACT"].append(f"Contains {profile['calculated_columns']} calculated columns (reduces fact table performance)")

        # NEW: Penalize concatenated string keys (weak key design)
        if profile["text_concatenated_keys"] > 0:
            scores["FACT"] -= 10
            scores["DIMENSION"] -= 8
            evidence["DIMENSION"].append(f"Uses {profile['text_concatenated_keys']} concatenated string key(s) instead of surrogate keys")

        # NEW: Bonus for clean design (no calculated/concatenated columns in facts)
        if profile["relationships_from"] >= 2 and profile["calculated_columns"] == 0 and profile["text_concatenated_keys"] == 0:
            scores["FACT"] += 10
            evidence["FACT"].append("Clean fact table structure with no concatenated keys")

        # NEW: Robust fact table detection via relationship cardinality and structure
        fact_score, fact_evidence = self._score_as_fact(table_name, profile, columns)
        if fact_score > 0:
            scores["FACT"] += fact_score
            evidence["FACT"].extend(fact_evidence)

        # ---------------------------------------------------------------------
        # Default fallback
        # ---------------------------------------------------------------------

        if max(scores.values()) == 0:
            scores["DIMENSION"] = 10
            evidence["DIMENSION"].append("Default fallback classification")

        classification = max(scores, key=scores.get)
        best_score = scores[classification]
        total_score = sum(scores.values())

        confidence = self._calculate_confidence(best_score, total_score)

        return {
            "table_name": table_name,
            "classification": classification,
            "confidence": confidence,
            "reasoning": "; ".join(evidence[classification]) or "No strong evidence found",
            "scores": scores,
            "metadata": profile
        }

    def _score_as_fact(self, table_name: str, profile: Dict[str, Any], columns: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        """
        Robust fact table detection using strict cardinality, isolation, and measure column signals.
        
        Core Principle: A fact table must satisfy at least ONE strong pillar:
        
        Pillar 1 (Strongest): Cardinality Pattern
        - 4+ active outgoing relationships
        - ALL relationships from "many" side (never "one")
        - Indicates pure transaction-level table
        
        Pillar 2 (Very Strong): Isolation + High Fanout
        - No incoming relationships (relationships_to = 0)
        - 3+ outgoing relationships (relationships_from >= 3)
        - Table only references, never referenced
        
        Pillar 3 (Strong): Numeric Measure Columns
        - 3+ numeric columns with summarizeBy != none
        - These are business metrics, not keys
        - Excludes columns with summarizeBy = none (FK columns)
        """
        score = 0
        evidence = []

        # =====================================================================
        # PILLAR 1: Strict Cardinality Pattern (Score +50)
        # =====================================================================
        outgoing_rels = [r for r in self.relationships if r["from_table"] == table_name]
        active_outgoing = [r for r in outgoing_rels if r.get("is_active", True)]
        
        if len(active_outgoing) >= 4:
            # All active outgoing relationships must be from "many" side
            all_many = all(r.get("from_cardinality", "many") == "many" for r in active_outgoing)
            if all_many:
                score += 50
                evidence.append(
                    f"STRONG: All {len(active_outgoing)} active outgoing relationships from 'many' side "
                    f"(4+ cardinality pattern - transaction-level table)"
                )

        # =====================================================================
        # PILLAR 2: Isolation + High Fanout (Score +45)
        # =====================================================================
        # Very strong: table is never filtered (relationships_to = 0) but filters many others
        if profile["relationships_to"] == 0 and profile["relationships_from"] >= 3:
            score += 45
            evidence.append(
                f"VERY STRONG: No incoming relationships + {profile['relationships_from']} outgoing "
                f"(pure fact source - never filtered)"
            )

        # =====================================================================
        # PILLAR 3: Numeric Measure Columns (Score +40)
        # =====================================================================
        # Measure columns: numeric + summarizeBy != none (Sum, Count, Average, etc)
        # Key columns: numeric + summarizeBy = none
        measure_cols = [
            c for c in columns
            if c["dataType"] in NUMERIC_TYPES
            and c.get("summarizeBy") is not None
            and str(c.get("summarizeBy", "")).lower() != "none"
        ]
        
        if len(measure_cols) >= 3:
            score += 40
            evidence.append(
                f"STRONG: {len(measure_cols)} numeric columns with additive summarizeBy "
                f"(business metrics, not keys)"
            )

        return score, evidence

    @staticmethod
    def _calculate_confidence(best_score: int, total_score: int) -> float:
        """
        Convert classification score into confidence between 0 and 1.
        """
        if total_score <= 0:
            return 0.3

        relative_confidence = best_score / total_score

        if best_score >= 70:
            base = 0.9
        elif best_score >= 50:
            base = 0.8
        elif best_score >= 30:
            base = 0.65
        elif best_score >= 15:
            base = 0.5
        else:
            base = 0.35

        confidence = (base + relative_confidence) / 2
        return round(min(max(confidence, 0.3), 0.98), 2)

    # -------------------------------------------------------------------------
    # Relationship Analysis
    # -------------------------------------------------------------------------

    def _analyze_relationships(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze relationship topology, schema type and model compliance.
        """
        graph = self._build_undirected_graph()
        components = self._find_components(graph)
        isolated_tables = [list(comp)[0] for comp in components if len(comp) == 1]

        classification_map = {
            c["table_name"]: c["classification"]
            for c in classifications
        }

        # Calculate average confidence for confidence bonus
        avg_confidence = round(
            sum(c["confidence"] for c in classifications) / len(classifications), 3
        ) if classifications else 0.5

        schema_type = self._detect_schema_type(classification_map, components)
        score_data = self._calculate_compliance_score(
            classification_map, components, isolated_tables, avg_confidence, schema_type
        )

        return {
            "total_tables": len(self.tables),
            "total_relationships": len(self.relationships),
            "active_relationships": sum(1 for r in self.relationships if r.get("is_active", True)),
            "inactive_relationships": sum(1 for r in self.relationships if not r.get("is_active", True)),
            "schema_type": schema_type,
            "compliance_score": score_data["score"],
            "score_breakdown": score_data["breakdown"],
            "average_classification_confidence": avg_confidence,
            "components": len(components),
            "component_details": [sorted(list(c)) for c in components],
            "isolated_tables": sorted(isolated_tables),
            "issues": score_data["issues"],
            "recommendations": score_data["recommendations"],
            "relationships": self.relationships
        }

    def _build_undirected_graph(self) -> Dict[str, set]:
        graph = defaultdict(set)

        for table in self.tables:
            graph[table] = set()

        for rel in self.relationships:
            from_table = rel["from_table"]
            to_table = rel["to_table"]

            graph[from_table].add(to_table)
            graph[to_table].add(from_table)

        return graph

    def _find_components(self, graph: Dict[str, set]) -> List[set]:
        visited = set()
        components = []

        for table in self.tables.keys():
            if table in visited:
                continue

            component = set()
            queue = deque([table])
            visited.add(table)

            while queue:
                node = queue.popleft()
                component.add(node)

                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            components.append(component)

        return components

    def _detect_schema_type(self, classification_map: Dict[str, str], components: List[set]) -> str:
        """
        Detect model schema type dynamically.

        Heuristics:
        - DISCONNECTED: no relationships or mostly isolated (excluding intentional tables).
        - FLAT: one or very few tables with no meaningful relationships.
        - STAR: one fact table connected mainly to dimensions.
        - GALAXY: multiple fact tables sharing dimensions.
        - SNOWFLAKE: dimensions connected to other dimensions.
        - UNKNOWN: fallback when topology is ambiguous.
        """
        total_tables = len(self.tables)
        total_relationships = len(self.relationships)

        if total_tables == 0:
            return "UNKNOWN"

        if total_relationships == 0:
            return "FLAT" if total_tables <= 2 else "DISCONNECTED"

        # Get isolated tables (components of size 1)
        isolated_tables = [list(comp)[0] for comp in components if len(comp) == 1]

        # Filter out intentional isolated tables (same logic as compliance scoring)
        calculation_tables = [t for t, c in classification_map.items() if c == "CALCULATION"]
        parameter_tables = [t for t, c in classification_map.items() if c == "PARAMETER"]
        
        intentional_isolated = set(calculation_tables + parameter_tables)
        intentional_isolated.update(t for t in isolated_tables if t.startswith(("_", "param", "Param")))
        
        real_isolated_tables = [t for t in isolated_tables if t not in intentional_isolated]

        # Check if remaining isolated tables are too many
        if real_isolated_tables and len(real_isolated_tables) / total_tables >= 0.5:
            return "DISCONNECTED"

        fact_tables = [t for t, c in classification_map.items() if c == "FACT"]
        dimension_tables = [t for t, c in classification_map.items() if c == "DIMENSION"]

        fact_count = len(fact_tables)

        dimension_to_dimension_rels = 0
        fact_to_dimension_rels = 0

        for rel in self.relationships:
            from_type = classification_map.get(rel["from_table"], "UNKNOWN")
            to_type = classification_map.get(rel["to_table"], "UNKNOWN")

            if from_type == "DIMENSION" and to_type == "DIMENSION":
                dimension_to_dimension_rels += 1

            if (
                from_type == "FACT" and to_type == "DIMENSION"
            ) or (
                from_type == "DIMENSION" and to_type == "FACT"
            ):
                fact_to_dimension_rels += 1

        if fact_count >= 2 and fact_to_dimension_rels >= fact_count:
            return "GALAXY"

        if dimension_to_dimension_rels > 0 and fact_count >= 1:
            return "SNOWFLAKE"

        if fact_count == 1 and fact_to_dimension_rels >= 2:
            return "STAR"

        if fact_count == 0 and total_relationships > 0:
            return "DIMENSIONAL"

        return "UNKNOWN"

    # -------------------------------------------------------------------------
    # Compliance Score
    # -------------------------------------------------------------------------

    def _calculate_compliance_score(
        self,
        classification_map: Dict[str, str],
        components: List[set],
        isolated_tables: List[str],
        avg_confidence: float = 0.5,
        schema_type: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        Calculate a schema compliance score from 0 to 100.
        
        Parameters:
        - avg_confidence: Average classification confidence (0.3-0.98)
        - schema_type: Detected schema type (affects score ceiling)
        """
        score = 100
        issues = []
        recommendations = []
        breakdown = {}

        total_tables = len(self.tables)
        total_relationships = len(self.relationships)

        fact_tables = [t for t, c in classification_map.items() if c == "FACT"]
        dimension_tables = [t for t, c in classification_map.items() if c == "DIMENSION"]
        bridge_tables = [t for t, c in classification_map.items() if c == "BRIDGE"]
        calculation_tables = [t for t, c in classification_map.items() if c == "CALCULATION"]
        parameter_tables = [t for t, c in classification_map.items() if c == "PARAMETER"]
        
        # Filter out intentional isolated tables (parameters, calculations)
        intentional_isolated = set(calculation_tables + parameter_tables)
        # Also check by naming convention
        intentional_isolated.update(t for t in isolated_tables if t.startswith(("_", "param", "Param")))
        
        real_isolated_tables = [t for t in isolated_tables if t not in intentional_isolated]

        # 1. Basic relationship coverage
        if total_tables > 1 and total_relationships == 0:
            penalty = 35
            score -= penalty
            issues.append("Model contains multiple tables but no relationships.")
            recommendations.append("Define relationships between fact and dimension tables where applicable.")
            breakdown["missing_relationships_penalty"] = -penalty

        # 2. Isolated tables (excluding intentional ones)
        if real_isolated_tables:
            isolated_ratio = len(real_isolated_tables) / total_tables
            penalty = min(25, round(isolated_ratio * 30))
            score -= penalty
            issues.append(f"{len(real_isolated_tables)} isolated table(s) detected (excluding {len(intentional_isolated)} intentional).")
            recommendations.append("Review isolated tables and define relationships where appropriate.")
            breakdown["isolated_tables_penalty"] = -penalty

        # 3. Fact table presence
        if total_relationships > 0 and not fact_tables:
            penalty = 20
            score -= penalty
            issues.append("No fact table was confidently identified.")
            recommendations.append("Review table naming, relationship direction and numeric transaction tables.")
            breakdown["missing_fact_table_penalty"] = -penalty

        # 4. Too many facts without shared dimensions
        if len(fact_tables) >= 2:
            shared_dims = self._count_shared_dimensions(fact_tables, classification_map)
            if shared_dims == 0:
                penalty = 10
                score -= penalty
                issues.append("Multiple fact tables detected without shared dimensions.")
                recommendations.append("Validate whether the model is intended to be a galaxy schema or separate subject areas.")
                breakdown["multiple_facts_no_shared_dimensions_penalty"] = -penalty

        # 5. Relationship cardinality
        many_to_many_count = sum(
            1 for r in self.relationships
            if r.get("from_cardinality") == "many" and r.get("to_cardinality") == "many"
        )

        if many_to_many_count:
            penalty = min(15, many_to_many_count * 5)
            score -= penalty
            issues.append(f"{many_to_many_count} many-to-many relationship(s) detected.")
            recommendations.append("Review many-to-many relationships and consider bridge tables where appropriate.")
            breakdown["many_to_many_penalty"] = -penalty

        # 6. Bidirectional relationships
        bidirectional_count = sum(
            1 for r in self.relationships
            if str(r.get("cross_filtering_behavior", "")).lower() in {"bothdirections", "both"}
        )

        if bidirectional_count:
            penalty = min(10, bidirectional_count * 3)
            score -= penalty
            issues.append(f"{bidirectional_count} bidirectional relationship(s) detected.")
            recommendations.append("Validate bidirectional filtering because it can increase ambiguity and model complexity.")
            breakdown["bidirectional_relationships_penalty"] = -penalty

        # 7. Inactive relationships
        inactive_count = sum(1 for r in self.relationships if not r.get("is_active", True))

        if inactive_count:
            penalty = min(8, inactive_count * 2)
            score -= penalty
            issues.append(f"{inactive_count} inactive relationship(s) detected.")
            recommendations.append("Document inactive relationships and related USERELATIONSHIP measures if used.")
            breakdown["inactive_relationships_penalty"] = -penalty

        # 8. NEW: Penalize concatenated string keys in relationships (weak key columns)
        text_concat_keys_total = sum(
            table.get("text_concatenated_keys", 0)
            for table in self.table_profiles.values()
        )

        if text_concat_keys_total > 0:
            penalty = min(12, text_concat_keys_total * 3)
            score -= penalty
            issues.append(f"{text_concat_keys_total} concatenated string key column(s) detected.")
            recommendations.append("Replace concatenated text keys with surrogate keys or proper composite keys. Concatenated keys reduce performance and maintainability.")
            breakdown["concatenated_text_keys_penalty"] = -penalty

        # 9. NEW: Penalize calculated columns in fact tables (performance issues)
        calculated_in_facts = 0
        for fact_table in fact_tables:
            if fact_table in self.table_profiles:
                calculated_in_facts += self.table_profiles[fact_table].get("calculated_columns", 0)

        if calculated_in_facts > 0:
            penalty = min(10, calculated_in_facts * 2)
            score -= penalty
            issues.append(f"{calculated_in_facts} calculated column(s) detected in fact table(s).")
            recommendations.append("Move calculations from fact tables to dimension tables or measures to improve query performance and reduce storage.")
            breakdown["calculated_columns_in_facts_penalty"] = -penalty

        # 10. Positive signals
        if fact_tables and dimension_tables and total_relationships > 0:
            bonus = 5
            score += bonus
            breakdown["dimensional_model_bonus"] = bonus

        if bridge_tables:
            bonus = min(5, len(bridge_tables) * 2)
            score += bonus
            breakdown["bridge_modeling_bonus"] = bonus

        # Apply confidence bonus (rewards models with clear classifications)
        confidence_bonus = round((avg_confidence - 0.3) * 10)  # Scale to 0-7 range
        if confidence_bonus > 0:
            score += confidence_bonus
            breakdown["classification_confidence_bonus"] = confidence_bonus
        
        # Determine schema-specific score ceiling
        # Complex schemas (SNOWFLAKE, GALAXY) have inherent structural complexity
        schema_ceilings = {
            "STAR": 100,
            "DIMENSIONAL": 95,
            "GALAXY": 90,
            "SNOWFLAKE": 88,
            "FLAT": 85,
            "DISCONNECTED": 70,
            "UNKNOWN": 95
        }
        
        schema_ceiling = schema_ceilings.get(schema_type, 95)
        score = max(0, min(schema_ceiling, round(score)))
        breakdown["schema_type_ceiling"] = schema_ceiling

        if not issues:
            recommendations.append("Model relationship structure appears consistent with dimensional modeling practices.")

        return {
            "score": score,
            "breakdown": breakdown,
            "issues": issues,
            "recommendations": recommendations
        }

    def _count_shared_dimensions(self, fact_tables: List[str], classification_map: Dict[str, str]) -> int:
        """
        Count dimensions connected to more than one fact table.
        """
        dim_usage = Counter()

        for rel in self.relationships:
            from_table = rel["from_table"]
            to_table = rel["to_table"]

            from_type = classification_map.get(from_table, "UNKNOWN")
            to_type = classification_map.get(to_table, "UNKNOWN")

            if from_table in fact_tables and to_type == "DIMENSION":
                dim_usage[to_table] += 1

            if to_table in fact_tables and from_type == "DIMENSION":
                dim_usage[from_table] += 1

        return sum(1 for _, count in dim_usage.items() if count >= 2)

    # -------------------------------------------------------------------------
    # Metrics and Summary
    # -------------------------------------------------------------------------

    def _generate_model_metrics(
        self,
        classifications: List[Dict[str, Any]],
        relationship_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate global model metrics.
        """
        total_columns = sum(c["metadata"]["columns"] for c in classifications)
        total_measures = sum(c["metadata"]["measures"] for c in classifications)

        avg_columns_per_table = round(total_columns / len(classifications), 2) if classifications else 0

        classification_counts = Counter(c["classification"] for c in classifications)

        return {
            "total_tables": len(classifications),
            "total_columns": total_columns,
            "total_measures": total_measures,
            "total_relationships": relationship_analysis["total_relationships"],
            "avg_columns_per_table": avg_columns_per_table,
            "classification_distribution": dict(classification_counts),
            "schema_type": relationship_analysis["schema_type"],
            "compliance_score": relationship_analysis["compliance_score"]
        }

    def _generate_summary(
        self,
        classifications: List[Dict[str, Any]],
        relationship_analysis: Dict[str, Any],
        model_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for documentation.
        """
        classification_counts = Counter(c["classification"] for c in classifications)

        return {
            "fact_tables": classification_counts.get("FACT", 0),
            "dimension_tables": classification_counts.get("DIMENSION", 0),
            "calculation_tables": classification_counts.get("CALCULATION", 0),
            "bridge_tables": classification_counts.get("BRIDGE", 0),
            "parameter_tables": classification_counts.get("PARAMETER", 0),
            "unknown_tables": classification_counts.get("UNKNOWN", 0),
            "total_measures": model_metrics["total_measures"],
            "total_columns": model_metrics["total_columns"],
            "schema_type": relationship_analysis["schema_type"],
            "compliance_score": relationship_analysis["compliance_score"],
            "issues_count": len(relationship_analysis["issues"])
        }


def parse_analysis(tmdl_dir: str, output_file: str = None) -> Dict[str, Any]:
    """
    Main function to parse Power BI semantic model analysis.
    """
    parser = AnalysisParser(tmdl_dir)
    analysis = parser.parse()

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
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

    print("✓ Analysis complete")
    print(f"Schema type: {analysis['relationship_analysis']['schema_type']}")
    print(f"Compliance score: {analysis['relationship_analysis']['compliance_score']}/100")