#!/usr/bin/env python3
"""
Power BI Documentation Generator using local Ollama.

Reads pre-extracted JSON files produced by the parsers and generates
a formal 5-section Markdown document — section by section to stay
within the context window of small CPU-only models.

Usage:
    python ollama_generator.py
    python ollama_generator.py <data_dir> <output_dir>

Examples:
    # Auto-detect first project in powerbi-project/powerbi-project/
    python ollama_generator.py
    
    # Specific project data
    python ollama_generator.py powerbi-project/powerbi-project/AmericasConsolidatedBalanceSheet/data
    
    # Custom output location
    python ollama_generator.py powerbi-project/powerbi-project/OnlineBaseline/data powerbi-project/output_ollama
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    from ollama_client import generate_with_retry, check_connection, DEFAULT_MODEL
except ImportError:
    print("❌  ollama_client.py not found in the same directory.")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_DOC = """You are a technical documentation specialist for Power BI / PBIP projects.
Generate formal, enterprise-grade documentation for internal BI developer wikis.

Rules:
- Output ONLY valid Markdown for the requested section. Nothing else.
- Never invent data. If a value is missing, write N/A.
- Use pipe tables for all structured data.
- Stub or empty DAX expressions must be marked as [Not implemented].
- Do not add sections beyond what is requested."""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# JSON LOADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _load(path: Path):
    """Load a JSON file. Returns empty list if not found."""
    if not path.exists():
        print(f"  [WARN] {path.name} not found — skipping.")
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all(data_dir: str) -> Dict:
    """Load all parser JSON outputs from data_dir."""
    base = Path(data_dir)
    print(f"\n[1/3] Loading JSON files from: {base.resolve()}\n")

    data = {
        "tables":        _load(base / "tables.json"),
        "relationships": _load(base / "relationships.json"),
        "measures":      _load(base / "measures.json"),
        "pages":         _load(base / "pages.json"),
        "datasources":   _load(base / "datasources.json"),
        "analysis":      _load(base / "analysis.json"),
    }

    for key, value in data.items():
        count = len(value) if isinstance(value, list) else "loaded"
        print(f"  {key:<16} {count} items" if count != "loaded"
              else f"  {key:<16} {count}")

    return data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION GENERATORS
# One LLM call per section — small prompt, fast on CPU
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _call(prompt: str, model: str) -> str:
    """Single LLM call with retry. Shared by all section generators."""
    return generate_with_retry(
        prompt=prompt,
        system=SYSTEM_DOC,
        model=model,
        temperature=0.1,
        json_mode=False
    )


def section_1_general(meta: Dict, model: str) -> str:
    """Section 1 — General Description."""
    print("\n  [1/5] General Description...")

    prompt = f"""Write ONLY the following Markdown section for a Power BI technical document.
Do not add any other section or heading outside of what is shown below.

## 1. General Description

| Property       | Value |
|----------------|-------|
| Report Name    | {meta.get('project_name', 'N/A')} |
| Report Title   | {meta.get('report_title', 'N/A')} |
| Purpose        | {meta.get('purpose', 'N/A')} |
| Created By     | {meta.get('created_by', 'N/A')} |
| Creation Date  | {meta.get('creation_date', 'N/A')} |

Fill each cell with the value shown. If a value is None or null, write N/A.
Output ONLY the Markdown table above, nothing else."""

    return _call(prompt, model)


def section_2_dataset(datasources: list, model: str) -> str:
    """Section 2 — Data Set."""
    print("  [2/5] Data Set...")

    prompt = f"""Write ONLY the following Markdown section for a Power BI technical document.

## 2. Data Set

Create a table with these exact columns:
| Origin | Database | Endpoint | Catalog | Schema |

Use this JSON data to fill the rows:
{json.dumps(datasources, indent=2, ensure_ascii=False)}

If the list is empty or all values are null, add one row with N/A in every cell.
Output ONLY the Markdown section heading and table, nothing else."""

    return _call(prompt, model)


def section_3_datamodel(relationships: list, model: str) -> str:
    """Section 3 — Data Model."""
    print("  [3/5] Data Model...")

    prompt = f"""Write ONLY the following Markdown section for a Power BI technical document.

## 3. Data Model

Create a table with these exact columns:
| From Table | From Column | To Table | To Column |

Use this JSON data to fill the rows:
{json.dumps(relationships, indent=2, ensure_ascii=False)}

Each object in the list is one row. Map the JSON fields to the table columns.
Output ONLY the Markdown section heading and table, nothing else."""

    return _call(prompt, model)


MEASURES_BATCH_SIZE = 8  # max measures per LLM call — keeps prompts small on CPU


def _measures_to_markdown(table_name: str, measures: list, model: str) -> str:
    """
    Generate the Measures subsection for a table.
    Splits into batches of MEASURES_BATCH_SIZE to avoid large prompts.
    """
    if not measures:
        return ""

    batches = [
        measures[i: i + MEASURES_BATCH_SIZE]
        for i in range(0, len(measures), MEASURES_BATCH_SIZE)
    ]

    parts = []
    for b_idx, batch in enumerate(batches, 1):
        label = (f" (part {b_idx}/{len(batches)})" if len(batches) > 1 else "")
        print(f"      ↳ measures batch {b_idx}/{len(batches)}...")

        prompt = f"""Write ONLY a Markdown table for these DAX measures from the '{table_name}' table{label}.

Table columns: Name | Formula | Description

Rules:
- Formula column: copy the DAX expression as inline code using backticks.
- If the expression is empty, null, or shorter than 5 characters → write [Not implemented].
- Description column: one short sentence describing what the measure calculates.
- Output ONLY the Markdown table rows. No heading, no explanation.

Data:
{json.dumps(batch, indent=2, ensure_ascii=False)}"""

        result = _call(prompt, model)
        parts.append(result)

    # Combine all batch results under one heading
    header = "#### Measures and Calculated Columns\n\n| Name | Formula | Description |\n|------|---------|-------------|"
    rows   = "\n".join(parts)
    return f"{header}\n{rows}"


def section_4_tables(tables: list, measures: list, model: str) -> str:
    """
    Section 4 — Tables and Composition.
    One LLM call per table for columns.
    Measures split into batches of MEASURES_BATCH_SIZE — safe for CPU + large measure tables.
    """
    print("  [4/5] Tables and Composition...")

    # Build measures lookup: table_name → [measures]
    measures_by_table: Dict[str, list] = {}
    for m in measures:
        tbl = m.get("table", "")
        measures_by_table.setdefault(tbl, []).append(m)

    section_parts = ["## 4. Tables and Composition\n"]

    for i, table in enumerate(tables, 1):
        name         = table.get("name", "unknown")
        tbl_measures = measures_by_table.get(name, [])
        n_measures   = len(tbl_measures)

        print(f"    ({i}/{len(tables)}) {name}"
              + (f" — {n_measures} measures in "
                 f"{-(-n_measures // MEASURES_BATCH_SIZE)} batch(es)" if n_measures else "")
              + "...")

        # ── Columns section — one call per table ──────────────────────────────
        col_prompt = f"""Write ONLY the Markdown subsection for this single Power BI table.
Use ### as the heading. Do not add any other section or heading.

### {name}

| Property | Value |
|----------|-------|
| Type     | {table.get('type', 'N/A')} |
| Catalog  | {table.get('catalog', 'N/A')} |
| Schema   | {table.get('schema', 'N/A')} |

#### Columns

Create a table with columns: Column Name | Data Type | Observations

Use this data:
{json.dumps(table.get('columns', []), indent=2, ensure_ascii=False)}

If the columns list is empty, write "No columns defined."
Output ONLY the Markdown for this subsection. Nothing else."""

        col_part = _call(col_prompt, model)
        print(f"    ↳ columns done.")

        # ── Measures — batched separately ─────────────────────────────────────
        measures_part = _measures_to_markdown(name, tbl_measures, model)

        section_parts.append(col_part)
        if measures_part:
            section_parts.append(measures_part)

    return "\n\n".join(section_parts)


def section_5_pages(pages: list, model: str) -> str:
    """Section 5 — Structure Pages and Visuals."""
    print("  [5/5] Pages and Visuals...")

    if not pages:
        return (
            "## 5. Structure Pages and Visuals\n\n"
            "Visual metadata not available in current export."
        )

    prompt = f"""Write ONLY the following Markdown section for a Power BI technical document.

## 5. Structure Pages and Visuals

For each page in the data below:
- Use ### as the heading with the page name
- Create a table with columns: Visual Type | Fields Used
- If a page has no visuals, write "No visuals documented."

Use this JSON data:
{json.dumps(pages, indent=2, ensure_ascii=False)}

Output ONLY the Markdown section heading and page subsections, nothing else."""

    return _call(prompt, model)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ORCHESTRATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_documentation(
    data_dir: str,
    output_dir: str,
    metadata: Optional[Dict] = None,
    model: str = DEFAULT_MODEL
) -> Path:
    """
    Full pipeline:
      1. Load the 6 parser JSON files
      2. Generate each of the 5 sections via separate Ollama calls
      3. Assemble and save DOCUMENTATION.md

    Each section is a small, focused prompt — safe for CPU-only machines.
    Streaming in the client ensures no timeout regardless of generation time.
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    meta = metadata or {}

    # 1. Load
    data = load_all(data_dir)

    # 2. Generate sections
    print("\n[2/3] Generating sections with Ollama (streaming)...")
    print("      One call per section — no timeouts.\n")

    s1 = section_1_general(meta, model)
    s2 = section_2_dataset(data["datasources"], model)
    s3 = section_3_datamodel(data["relationships"], model)
    s4 = section_4_tables(data["tables"], data["measures"], model)
    s5 = section_5_pages(data["pages"], model)

    # 3. Assemble
    title   = meta.get("project_name", "Power BI Model")
    divider = "\n\n---\n\n"

    document = "\n\n".join([
        f"# {title} — Technical Documentation",
        s1, s2, s3, s4, s5
    ])

    # 4. Save
    doc_path = output_path / "DOCUMENTATION.md"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(document)

    return doc_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":

    print("=" * 70)
    print("  Power BI Documentation Generator (with Ollama)")
    print("=" * 70)

    if not check_connection(DEFAULT_MODEL):
        print(f"\n❌  Fix the errors above, then:")
        print(f"    ollama serve")
        print(f"    ollama pull {DEFAULT_MODEL}")
        sys.exit(1)

    print(f"[OK] Ollama connected — model: {DEFAULT_MODEL}")

    # Paths - Updated for multi-project structure
    if len(sys.argv) > 1:
        # User provided data_dir explicitly
        data_dir = sys.argv[1]
    else:
        # Default: look for data in the multi-project output structure
        # Searches: powerbi-project/powerbi-project/*/data/
        project_root = Path("powerbi-project/powerbi-project")
        if project_root.exists():
            projects = [p for p in project_root.iterdir() if p.is_dir()]
            if projects:
                # Use the first project found
                data_dir = str(projects[0] / "data")
                print(f"\n  Found projects: {', '.join(p.name for p in projects)}")
                print(f"  Using: {projects[0].name}/data")
            else:
                data_dir = "powerbi-project/powerbi-project/data"
        else:
            data_dir = "powerbi-project/data"
    
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "powerbi-project/output"

    print(f"  Data dir:   {Path(data_dir).resolve()}")
    print(f"  Output dir: {Path(output_dir).resolve()}")

    # Project metadata — edit here or load from a metadata.json
    metadata = {
        "project_name":        "Power BI Model",
        "report_title":        None,
        "purpose":             None,
        "created_by":          None,
        "creation_date":       None,
        "culture":             "en-US",
        "compatibility_level": 1200,
    }

    try:
        doc_path = generate_documentation(
            data_dir=data_dir,
            output_dir=output_dir,
            metadata=metadata,
            model=DEFAULT_MODEL
        )

        print("\n[3/3] Saving document...")
        print(f"\n{'=' * 70}")
        print("  DONE")
        print(f"{'=' * 70}")
        print(f"\n  ✅  {doc_path.resolve()}")

    except FileNotFoundError as e:
        print(f"\n❌  File not found: {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"\n❌  Ollama error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌  Unexpected error: {e}")
        raise