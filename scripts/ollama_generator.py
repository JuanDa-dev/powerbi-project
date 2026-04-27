#!/usr/bin/env python3
"""
AI-Enriched documentation generator using local Ollama.

Enriches Power BI model metadata with AI-generated classifications and descriptions.
Requires local Ollama instance running with llama3.1 model.

Usage:
    python ollama_generator.py ../powerbi-project/data/tables.json output/
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Import local Ollama client
try:
    from ollama_client import generate, check_connection
except ImportError:
    print("❌ Error: ollama_client.py not found in same directory")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM PROMPTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_CLASSIFIER = """You are a Power BI semantic model analyzer.
Classify tables based on structural evidence (column names, count, relationships, measures).

RULES:
- FACT: Many numeric columns, multiple measures, foreign keys
- DIMENSION: Mostly text/key columns, few measures, referenced by facts
- BRIDGE: Connects many-to-many relationships, both FKs
- CALCULATION: No sourceColumn (all expressions/DAX)
- PARAMETER: Single value or date range, usually small

Return ONLY valid JSON. No markdown, no explanations."""

SYSTEM_DAX = """You are a DAX expert explaining measures to BI developers.
Classify measure patterns concisely and accurately.

RULES:
- SUM: Simple aggregation of numeric column
- COUNT: Counts rows
- RATIO: Division of two measures
- TIME_INTELLIGENCE: TOTALYTD, PARALLELPERIOD, SAMEPERIODLASTYEAR
- DYNAMIC: Uses CALCULATE with slicers, filters
- CONDITIONAL: IF statements, DAX logic
- FILTER: FILTER, SUMX, aggregation on filtered set

Return ONLY valid JSON. No markdown, no explanations."""

SYSTEM_DOC = """You are a technical documentation specialist for Power BI.
Generate formal, enterprise-grade documentation from JSON metadata.

RULES:
- Never invent information. If missing, write N/A.
- Output ONLY valid Markdown.
- Use tables for structured data.
- All data types, calculated columns, measures must be documented.
- Brief descriptions for each table type.
- Link relationships clearly."""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENRICHMENT FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def enrich_table_classification(table: Dict[str, Any]) -> Dict[str, Any]:
    """Use Ollama to classify table by structure."""
    
    # Gather structural evidence
    col_count = table.get("column_count", 0)
    measure_count = table.get("measure_count", 0)
    
    # Count column types
    text_cols = 0
    numeric_cols = 0
    date_cols = 0
    
    for col in table.get("columns", []):
        dt = col.get("dataType", "string")
        if dt in ["int64", "double"]:
            numeric_cols += 1
        elif dt in ["dateTime", "date"]:
            date_cols += 1
        else:
            text_cols += 1
    
    # Sample column names
    col_names = [c["name"] for c in table.get("columns", [])[:8]]
    
    prompt = f"""Classify this Power BI table:

Name: {table['name']}
Total columns: {col_count}
Text columns: {text_cols}
Numeric columns: {numeric_cols}
Date columns: {date_cols}
Measures defined: {measure_count}
Column samples: {', '.join(col_names)}

Respond with JSON only:
{{
  "classification": "FACT|DIMENSION|BRIDGE|CALCULATION|PARAMETER",
  "confidence": 0.0,
  "reasoning": "one sentence explanation"
}}"""
    
    try:
        raw = generate(prompt, system=SYSTEM_CLASSIFIER, temperature=0.1)
        result = json.loads(raw)
        
        table["ai_classification"] = result.get("classification", "UNKNOWN")
        table["ai_confidence"] = result.get("confidence", 0.0)
        table["ai_reasoning"] = result.get("reasoning", "")
        
        print(f"✅ {table['name']}: {table['ai_classification']} (confidence: {table['ai_confidence']})")
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  {table['name']}: Classification failed ({e})")
        table["ai_classification"] = "UNKNOWN"
        table["ai_confidence"] = 0.0
        table["ai_reasoning"] = "Failed to classify"
    
    return table


def enrich_measure_description(table_name: str, measure: Dict[str, Any]) -> Dict[str, Any]:
    """Use Ollama to classify and describe measure."""
    
    expr = measure.get("expression", "").strip() or "[empty]"
    if len(expr) > 300:
        expr = expr[:300] + "..."  # Truncate long expressions
    
    deps = measure.get("dependencies", [])
    
    prompt = f"""Classify this DAX measure:

Table: {table_name}
Name: {measure['name']}
Expression: {expr}
Dependencies: {', '.join(deps) if deps else 'none'}

Respond with JSON only:
{{
  "description": "1-2 sentences describing what this measure calculates",
  "aggregation_type": "SUM|COUNT|RATIO|TIME_INTELLIGENCE|DYNAMIC|CONDITIONAL|FILTER|UNKNOWN",
  "is_stub": true
}}"""
    
    try:
        raw = generate(prompt, system=SYSTEM_DAX, temperature=0.1)
        result = json.loads(raw)
        
        measure["ai_description"] = result.get("description", "")
        measure["ai_aggregation_type"] = result.get("aggregation_type", "UNKNOWN")
        measure["ai_is_stub"] = result.get("is_stub", False)
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  {measure['name']}: Description failed ({e})")
        measure["ai_description"] = "Description unavailable"
        measure["ai_aggregation_type"] = "UNKNOWN"
        measure["ai_is_stub"] = False
    
    return measure


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN GENERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_enriched_documentation(
    tables_json: str,
    relationships_json: str,
    pages_json: str,
    output_dir: str
):
    """Generate AI-enriched documentation."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\n📂 Loading data...")
    with open(tables_json) as f:
        tables = json.load(f)
    
    with open(relationships_json) as f:
        relationships = json.load(f)
    
    with open(pages_json) as f:
        pages = json.load(f)
    
    # 1. Enrich table classifications
    print("\n🤖 Enriching table classifications...")
    tables = [enrich_table_classification(t) for t in tables]
    
    # 2. Enrich measure descriptions
    print("\n🤖 Enriching measure descriptions...")
    for table in tables:
        if "measures" in table:
            table["measures"] = [
                enrich_measure_description(table["name"], m)
                for m in table["measures"]
            ]
    
    # 3. Save enriched JSON
    enriched_tables_path = output_path / "tables_enriched.json"
    with open(enriched_tables_path, "w", encoding="utf-8") as f:
        json.dump(tables, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Enriched tables → {enriched_tables_path}")
    
    # 4. Generate documentation
    print("\n📝 Generating AI documentation...")
    
    doc_prompt = _build_documentation_prompt(tables, relationships, pages)
    documentation = generate(doc_prompt, system=SYSTEM_DOC, temperature=0.1)
    
    doc_path = output_path / "AI_DOCUMENTATION.md"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(documentation)
    print(f"✅ Documentation → {doc_path}")
    
    print("\n" + "="*70)
    print("✅ AI-ENRICHED DOCUMENTATION COMPLETE")
    print("="*70)
    return enriched_tables_path, doc_path


def _build_documentation_prompt(
    tables: List[Dict],
    relationships: List[Dict],
    pages: List[Dict]
) -> str:
    """Build documentation generation prompt."""
    
    # Summary statistics
    fact_tables = [t for t in tables if t.get("ai_classification") == "FACT"]
    dim_tables = [t for t in tables if t.get("ai_classification") == "DIMENSION"]
    
    total_measures = sum(len(t.get("measures", [])) for t in tables)
    total_relationships = len(relationships)
    total_pages = len(pages)
    
    # Build table summary
    tables_md = "| Table | Type | Columns | Measures |\n"
    tables_md += "|-------|------|---------|----------|\n"
    for t in tables:
        tables_md += f"| {t['name']} | {t.get('ai_classification', 'UNKNOWN')} | {t.get('column_count', 0)} | {t.get('measure_count', 0)} |\n"
    
    prompt = f"""Generate technical documentation for this Power BI semantic model.

## MODEL SUMMARY
- Total tables: {len(tables)}
- Fact tables: {len(fact_tables)}
- Dimension tables: {len(dim_tables)}
- Total measures: {total_measures}
- Relationships: {total_relationships}
- Report pages: {total_pages}

## TABLES STRUCTURE
{tables_md}

## RELATIONSHIPS
{json.dumps(relationships[:5], indent=2)}

## SAMPLE MEASURES
{json.dumps([m for t in tables[:2] for m in t.get('measures', [])[:2]], indent=2)}

Generate documentation with these sections:
1. Executive Summary
2. Data Model Overview
3. Table Specifications (with AI classifications)
4. Measure Dictionary
5. Key Relationships
6. Data Quality Notes"""
    
    return prompt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    
    # Check Ollama connection
    if not check_connection():
        print("\n❌ Cannot proceed without Ollama. Start it with: ollama serve")
        sys.exit(1)
    
    # Default paths
    tables_json = "powerbi-project/data/tables.json"
    relationships_json = "powerbi-project/data/relationships.json"
    pages_json = "powerbi-project/data/pages.json"
    output_dir = "powerbi-project/output_ai"
    
    # Allow CLI arguments
    if len(sys.argv) > 1:
        tables_json = sys.argv[1]
    if len(sys.argv) > 2:
        relationships_json = sys.argv[2]
    if len(sys.argv) > 3:
        pages_json = sys.argv[3]
    if len(sys.argv) > 4:
        output_dir = sys.argv[4]
    
    # Generate
    try:
        generate_enriched_documentation(
            tables_json=tables_json,
            relationships_json=relationships_json,
            pages_json=pages_json,
            output_dir=output_dir
        )
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
