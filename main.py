#!/usr/bin/env python3
"""
Master orchestrator for Power BI PBIP analysis and documentation.

Usage:
    python main.py path/to/OnlineBaseline.pbip
    python main.py ../RecursosFuente/OnlineBaseline.pbip
    python main.py ../RecursosFuente/   (process all projects found)
"""

from __future__ import annotations

import argparse
from pathlib import Path

# Import parsers
from parsers.parse_tables import parse_tables
from parsers.parse_relationships import parse_relationships
from parsers.parse_measures import parse_measures
from parsers.parse_pages import parse_pages
from parsers.parse_datasources import parse_datasources
from parsers.parse_analysis import parse_analysis

# Import documentation generator (separated module)
from scripts.documentation_generator import DocumentationGenerator

# Import visualizers (optional)
try:
    from visualizers.relationship_graph import create_relationship_graph
    from visualizers.measure_dependency import create_measure_dependency_dag
    from visualizers.complexity_heatmap import create_complexity_heatmap
    from visualizers.schema_distribution import create_schema_distribution
    from visualizers.datatype_distribution import create_datatype_distribution

    VISUALIZERS_AVAILABLE = True
except ImportError as e:
    try:
        print(f"[WARN] Visualizers not available: {e}")
    except Exception:
        print("[WARN] Visualizers not available")
    VISUALIZERS_AVAILABLE = False


# -----------------------------
# Helpers (project discovery)
# -----------------------------
def find_semantic_model_dir(project_path: Path) -> Path | None:
    """
    Finds the SemanticModel/definition directory.

    Handles:
    - Direct path to .SemanticModel folder
    - Path to parent containing .SemanticModel folders
    - Path to .pbip folder (extracted) that contains *.SemanticModel/*
    """
    # Case 1: Direct .SemanticModel folder
    if project_path.is_dir() and project_path.name.endswith(".SemanticModel"):
        definition_dir = project_path / "definition"
        if definition_dir.exists():
            return definition_dir

    # Case 2: Parent folder containing .SemanticModel folders
    if project_path.is_dir():
        for item in project_path.iterdir():
            if item.is_dir() and item.name.endswith(".SemanticModel"):
                definition_dir = item / "definition"
                if definition_dir.exists():
                    return definition_dir

    # Case 3: Fallback - any folder/definition with TMDL files
    if project_path.is_dir():
        for item in project_path.iterdir():
            if item.is_dir():
                definition_dir = item / "definition"
                if definition_dir.exists() and any(definition_dir.glob("*.tmdl")):
                    return definition_dir

    return None


def get_pbip_projects(source_path: Path) -> list[Path]:
    """
    Get list of projects to process.

    Handles structures:
    1) RecursosFuente/
       ├── Project1.SemanticModel/
       ├── Project1.Report/
       ├── Project2.SemanticModel/
       └── Project2.Report/

    2) Project.pbip/ (folder - extracted)
       ├── Project.SemanticModel/
       └── Project.Report/

    3) Direct path to a .SemanticModel folder
    """
    projects: list[Path] = []

    if not source_path.exists():
        return projects

    # If a direct .SemanticModel folder is provided, process it
    if source_path.is_dir() and source_path.name.endswith(".SemanticModel"):
        return [source_path]

    # If a directory is provided, scan for *.SemanticModel folders
    if source_path.is_dir():
        for item in source_path.iterdir():
            if item.is_dir() and item.name.endswith(".SemanticModel"):
                projects.append(item)

        # If none found, scan for extracted .pbip folders
        if not projects:
            for item in source_path.iterdir():
                if item.is_dir() and item.name.endswith(".pbip"):
                    projects.append(item)

        # If the source itself is an extracted .pbip folder
        if source_path.name.endswith(".pbip"):
            projects.append(source_path)

    return projects


def clean_project_name(path: Path) -> str:
    """Normalize project name for output folder."""
    return path.name.replace(".pbip", "").replace(".SemanticModel", "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Power BI PBIP projects (.pbip/.SemanticModel) and generate JSON + documentation."
    )
    parser.add_argument(
        "source",
        type=str,
        help="Path to a .pbip folder, a .SemanticModel folder, or a parent folder containing projects",
    )
    return parser.parse_args()


# -----------------------------
# Main pipeline
# -----------------------------
def main() -> None:
    args = parse_args()
    source_path = Path(args.source).resolve()

    if not source_path.exists():
        print(f"[ERROR] Path not found: {source_path}")
        raise SystemExit(1)

    pbip_projects = get_pbip_projects(source_path)

    if not pbip_projects:
        print(f"[ERROR] No projects found in: {source_path}")
        print("")
        print("Expected folder structure (example):")
        print("  RecursosFuente/")
        print("  ├── MyProject.SemanticModel/")
        print("  │   └── definition/  (TMDL files) ← Required")
        print("  ├── MyProject.Report/")
        print("  ├── AnotherProject.SemanticModel/")
        print("  └── AnotherProject.Report/")
        print("")
        print("Or extracted folder:")
        print("  Project.pbip/ containing *.SemanticModel/ and *.Report/")
        raise SystemExit(1)

    print(f"Found {len(pbip_projects)} project(s) to process\n")

    output_base_dir = Path.cwd() / "powerbi-project"
    output_base_dir.mkdir(exist_ok=True)

    total_processed = 0
    total_skipped = 0

    for idx, project_root in enumerate(pbip_projects, 1):
        project_name = clean_project_name(project_root)

        print("=" * 80)
        print(f"[{idx}/{len(pbip_projects)}] Processing: {project_root.name}")
        print("=" * 80)

        # Identify semantic model TMDL directory
        tmdl_dir = find_semantic_model_dir(project_root)
        if tmdl_dir is None:
            print(f"[WARN] No semantic model found in {project_root.name}")
            print("       Skipping this project...\n")
            total_skipped += 1
            continue

        tmdl_files = list(Path(tmdl_dir).glob("*.tmdl"))
        if not tmdl_files:
            print(f"[WARN] No TMDL files found in {tmdl_dir}")
            print("       Skipping this project...\n")
            total_skipped += 1
            continue

        print(f"[OK] Found semantic model with {len(tmdl_files)} TMDL files")
        print(f"     Location: {tmdl_dir}\n")

        # Output directories per project
        output_dir = output_base_dir / project_name
        data_dir = output_dir / "data"
        reports_dir = output_dir / "reports"
        graphs_dir = output_dir / "graphs"

        data_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(exist_ok=True)
        graphs_dir.mkdir(exist_ok=True)

        # -------------------------
        # STEP 1: Parsers
        # -------------------------
        print("[STEP 1/3] Running parsers...")

        print("  • Parsing tables...", end=" ", flush=True)
        tables = parse_tables(str(tmdl_dir), str(data_dir / "tables.json"))
        print(f"[OK] {len(tables)} tables")

        print("  • Parsing relationships...", end=" ", flush=True)
        relationships = parse_relationships(str(tmdl_dir), str(data_dir / "relationships.json"))
        print(f"[OK] {len(relationships)} relationships")

        print("  • Parsing measures...", end=" ", flush=True)
        measures = parse_measures(str(tmdl_dir), str(data_dir / "measures.json"))
        print(f"[OK] {len(measures)} measures")

        # Pages parsing root depends on how the project was provided
        # - If given *.SemanticModel, its parent should contain *.Report
        # - If given extracted *.pbip folder, the folder itself should contain *.Report
        if project_root.name.endswith(".SemanticModel"):
            pages_root = project_root.parent
        else:
            pages_root = project_root

        print("  • Parsing pages...", end=" ", flush=True)
        pages = parse_pages(str(pages_root), str(data_dir / "pages.json"), project_name)
        print(f"[OK] {len(pages)} pages")

        print("  • Parsing datasources...", end=" ", flush=True)
        datasources = parse_datasources(str(tmdl_dir), str(data_dir / "datasources.json"))
        print(f"[OK] {len(datasources)} datasources")

        print("  • Running analysis...", end=" ", flush=True)
        parse_analysis(str(tmdl_dir), str(data_dir / "analysis.json"))
        print("[OK]")

        # -------------------------
        # STEP 2: Documentation
        # -------------------------
        print("\n[STEP 2/3] Generating documentation...")

        doc_gen = DocumentationGenerator(output_dir=output_dir, pbip_name=project_name)
        doc_gen.generate_all()
        print("  • Markdown documentation generated [OK]")

        # -------------------------
        # STEP 3: Visualizations
        # -------------------------
        if VISUALIZERS_AVAILABLE:
            print("\n[STEP 3/3] Generating visualizations...")

            # 1. Relationship Graph
            try:
                print("  • Generating relationship graph...", end=" ", flush=True)
                create_relationship_graph(
                    str(data_dir / "tables.json"),
                    str(data_dir / "relationships.json"),
                    str(graphs_dir / "relationship_graph.png"),
                    str(graphs_dir / "relationship_graph.html"),
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:80]})")

            # 2. Measure Dependency DAG
            try:
                print("  • Generating measure dependency DAG...", end=" ", flush=True)
                create_measure_dependency_dag(
                    str(data_dir / "measures.json"),
                    str(graphs_dir / "measure_dependency.png"),
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:80]})")

            # 3. Complexity Heatmap
            try:
                print("  • Generating complexity heatmap...", end=" ", flush=True)
                create_complexity_heatmap(
                    str(data_dir / "tables.json"),
                    str(data_dir / "measures.json"),
                    str(data_dir / "analysis.json"),
                    str(graphs_dir / "complexity_heatmap.png"),
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:80]})")

            # 4. Schema Distribution
            try:
                print("  • Generating schema distribution chart...", end=" ", flush=True)
                create_schema_distribution(
                    str(data_dir / "analysis.json"),
                    str(graphs_dir / "schema_type_donut.png"),
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:80]})")

            # 5. Datatype Distribution
            try:
                print("  • Generating datatype distribution chart...", end=" ", flush=True)
                create_datatype_distribution(
                    str(data_dir / "tables.json"),
                    str(graphs_dir / "datatype_distribution.png"),
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:80]})")

        print("\n[DONE]", project_name)
        print(f"   Output: {output_dir}\n")

        total_processed += 1

    # -------------------------
    # Final summary
    # -------------------------
    print("\n" + "=" * 80)
    print("[BATCH PROCESSING SUMMARY]")
    print("=" * 80)
    print(f"Total processed: {total_processed}")
    print(f"Total skipped: {total_skipped}")
    print(f"Output base directory: {output_base_dir}\n")

    if total_processed > 0:
        print("Generated files per project:")
        print("  [DIR] data/")
        print("     ├── tables.json")
        print("     ├── relationships.json")
        print("     ├── measures.json")
        print("     ├── pages.json")
        print("     ├── datasources.json")
        print("     └── analysis.json\n")
        print("  [DIR] reports/")
        print("     ├── TECHNICAL_DOCUMENTATION.md")
        print("     └── powerbi_analysis_*.md\n")
        if VISUALIZERS_AVAILABLE:
            print("  [DIR] graphs/")
            print("     ├── relationship_graph.png + .html")
            print("     ├── measure_dependency.png")
            print("     ├── complexity_heatmap.png")
            print("     ├── schema_type_donut.png")
            print("     └── datatype_distribution.png\n")
    print("=" * 80)


if __name__ == "__main__":
    main()