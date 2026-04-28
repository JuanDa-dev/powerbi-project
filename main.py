#!/usr/bin/env python3
"""
Master orchestrator for Power BI PBIP analysis and documentation.
Orchestrates modular parsers and generates comprehensive documentation.

Usage:
    python main.py path/to/OnlineBaseline.pbip
    python main.py ../RecursosFuente/OnlineBaseline.pbip
"""

import sys
import json
import base64
from pathlib import Path
from datetime import datetime

# Import parsers
from parsers.parse_tables import parse_tables
from parsers.parse_relationships import parse_relationships
from parsers.parse_measures import parse_measures
from parsers.parse_pages import parse_pages
from parsers.parse_datasources import parse_datasources
from parsers.parse_analysis import parse_analysis

# Import visualizers
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
    except:
        print(f"[WARNING] Visualizers not available")
    VISUALIZERS_AVAILABLE = False


class DocumentationGenerator:
    """Generates documentation from parsed JSON files"""
    
    def __init__(self, output_dir: Path, pbip_name: str):
        self.output_dir = output_dir
        self.data_dir = output_dir / "data"
        self.reports_dir = output_dir / "reports"
        self.pbip_name = pbip_name
        self.tables_data = []
        self.relationships_data = []
        self.measures_data = []
        self.pages_data = []
        self.datasources_data = []
        self.analysis_data = {}
        
        # Create subdirectories
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def load_all_data(self, json_dir: Path):
        """Load all generated JSON files from data directory"""
        if (json_dir / "tables.json").exists():
            self.tables_data = json.loads((json_dir / "tables.json").read_text(encoding='utf-8'))
        if (json_dir / "relationships.json").exists():
            self.relationships_data = json.loads((json_dir / "relationships.json").read_text(encoding='utf-8'))
        if (json_dir / "measures.json").exists():
            self.measures_data = json.loads((json_dir / "measures.json").read_text(encoding='utf-8'))
        if (json_dir / "pages.json").exists():
            self.pages_data = json.loads((json_dir / "pages.json").read_text(encoding='utf-8'))
        if (json_dir / "datasources.json").exists():
            self.datasources_data = json.loads((json_dir / "datasources.json").read_text(encoding='utf-8'))
        if (json_dir / "analysis.json").exists():
            self.analysis_data = json.loads((json_dir / "analysis.json").read_text(encoding='utf-8'))
    
    def generate_technical_documentation(self) -> str:
        """Generate concise TECHNICAL_DOCUMENTATION.md - ready to copy/paste"""
        doc = []
        
        # Header
        doc.append("# Power BI Semantic Model Documentation")
        doc.append("")
        doc.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("")
        
        # 1. General Description
        doc.append("## General Description")
        doc.append("")
        doc.append(f"**Semantic Model:** {self.pbip_name}")
        
        # Get summary from analysis
        if self.analysis_data:
            summary = self.analysis_data.get('summary', {})
            total_tables = summary.get('total_tables', len(self.tables_data))
            total_measures = summary.get('total_measures', 0)
            doc.append(f"**Tables:** {total_tables} | **Measures:** {total_measures}")
        doc.append("")
        
        # 2. Dataset: Endpoint
        doc.append("## Dataset: Endpoint")
        doc.append("")
        
        if self.datasources_data:
            for ds in self.datasources_data:
                doc.append(f"- **{ds.get('type', 'Unknown')}**: {ds.get('definition', 'N/A')}")
        else:
            doc.append("- No explicit data sources defined")
        doc.append("")
        
        # 3. Table Mapping (Semantic Model)
        doc.append("## Table Mapping (Semantic Model)")
        doc.append("")
        
        if self.analysis_data and 'table_classifications' in self.analysis_data:
            classifications = self.analysis_data['table_classifications']
            
            # Group tables by type
            grouped = {}
            for cls in classifications:
                classification = cls['classification']
                if classification not in grouped:
                    grouped[classification] = []
                grouped[classification].append(cls)
            
            # Display in order: FACT, DIMENSION, BRIDGE, CALCULATION, PARAMETER
            for table_type in ['FACT', 'DIMENSION', 'BRIDGE', 'CALCULATION', 'PARAMETER']:
                if table_type in grouped:
                    table_list = grouped[table_type]
                    doc.append(f"**{table_type} Tables** ({len(table_list)})")
                    for table in table_list:
                        doc.append(f"- {table['table_name']}")
                    doc.append("")
        
        # 4. Tables and Composition
        doc.append("## Tables and Composition")
        doc.append("")
        
        doc.append("| Table Name | Type | Columns | Measures | Description |")
        doc.append("|------------|------|---------|----------|-------------|")
        
        if self.analysis_data and 'table_classifications' in self.analysis_data:
            classifications = self.analysis_data['table_classifications']
            
            for cls in sorted(classifications, key=lambda x: x['table_name']):
                table_name = cls['table_name']
                table_type = cls['classification']
                metadata = cls.get('metadata', {})
                columns = metadata.get('columns', 0)
                measures = metadata.get('measures', 0)
                reasoning = cls.get('reasoning', '')
                
                doc.append(f"| {table_name} | {table_type} | {columns} | {measures} | {reasoning} |")
        
        doc.append("")
        
        # 5. Relationships
        if self.relationships_data:
            doc.append("## Relationships")
            doc.append("")
            doc.append(f"**Total Relationships:** {len(self.relationships_data)}")
            doc.append("")
            doc.append("| From Table | From Column | To Table | To Column | Cardinality |")
            doc.append("|------------|------------|----------|-----------|-------------|")
            
            for rel in self.relationships_data:
                doc.append(
                    f"| {rel['from_table']} | {rel['from_column']} | "
                    f"{rel['to_table']} | {rel['to_column']} | {rel['cardinality']} |"
                )
            doc.append("")
        
        # 6. Report Pages
        if self.pages_data:
            doc.append("## Pages")
            doc.append("")
            doc.append(f"**Total Pages:** {len(self.pages_data)}")
            doc.append("")
            doc.append("| Page Name | Visualizations |")
            doc.append("|-----------|-----------------|")
            
            for page in self.pages_data:
                doc.append(f"| {page['display_name']} | {page['visuals_count']} |")
            doc.append("")
        
        return "\n".join(doc)
    
    def generate_extended_documentation(self) -> str:
        """Generate comprehensive powerbi_analysis_fecha_code.md with charts and details"""
        doc = []
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Header
        doc.append("# Power BI Semantic Model - Comprehensive Analysis")
        doc.append(f"**Project:** {self.pbip_name}")
        doc.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("")
        doc.append("---")
        doc.append("")
        
        # TABLE OF CONTENTS
        doc.append("## Table of Contents")
        doc.append("1. [Executive Overview](#executive-overview)")
        doc.append("2. [Model Complexity Analysis](#model-complexity-analysis)")
        doc.append("3. [Tables Summary](#tables-summary)")
        doc.append("4. [Detailed Table Classifications](#detailed-table-classifications)")
        doc.append("5. [Relationships Analysis](#relationships-analysis)")
        doc.append("6. [Measures Overview](#measures-overview)")
        doc.append("7. [Columns Details](#columns-details)")
        doc.append("8. [Report Pages](#report-pages)")
        doc.append("9. [Data Quality](#data-quality)")
        doc.append("")
        
        # ===== 1. EXECUTIVE OVERVIEW =====
        doc.append("---")
        doc.append("## Executive Overview")
        doc.append("")
        
        if self.analysis_data:
            summary = self.analysis_data.get('summary', {})
            rel_analysis = self.analysis_data.get('relationship_analysis', {})
            
            doc.append("### Model Statistics")
            doc.append("")
            doc.append(f"- **Total Tables:** {summary.get('total_tables', len(self.tables_data))}")
            doc.append(f"- **Total Relationships:** {len(self.relationships_data)}")
            doc.append(f"- **Total Measures:** {summary.get('total_measures', len(self.measures_data))}")
            doc.append(f"- **Schema Type:** {rel_analysis.get('schema_type', 'N/A')}")
            doc.append(f"- **Compliance Score:** {rel_analysis.get('compliance_score', 0)}/100")
            doc.append(f"- **Report Pages:** {len(self.pages_data)}")
            doc.append("")
            
            # Table Type Distribution
            doc.append("### Table Distribution")
            doc.append("")
            doc.append(f"- **Fact Tables:** {summary.get('fact_tables', 0)}")
            doc.append(f"- **Dimension Tables:** {summary.get('dimension_tables', 0)}")
            doc.append(f"- **Bridge Tables:** {summary.get('bridge_tables', 0)}")
            doc.append(f"- **Calculation Tables:** {summary.get('calculation_tables', 0)}")
            doc.append(f"- **Parameter Tables:** {summary.get('parameter_tables', 0)}")
            doc.append("")
        
        # ===== 2. MODEL COMPLEXITY ANALYSIS =====
        doc.append("---")
        doc.append("## Model Complexity Analysis")
        doc.append("")
        
        doc.append("### Visual Representations")
        doc.append("")
        
        # Embed charts if they exist
        graph_dir = Path(self.output_dir) / "graphs"
        
        charts = [
            ("relationship_graph.png", "Relationship Diagram"),
            ("schema_type_donut.png", "Table Type Distribution"),
            ("complexity_heatmap.png", "Model Complexity Heatmap"),
            ("datatype_distribution.png", "Data Type Distribution"),
            ("measure_dependency.png", "Measure Dependencies"),
        ]
        
        for chart_file, chart_title in charts:
            chart_path = graph_dir / chart_file
            if chart_path.exists():
                doc.append(f"#### {chart_title}")
                doc.append(f"![{chart_title}]({chart_path.name})")
                doc.append("")
        
        # ===== 3. TABLES SUMMARY =====
        doc.append("---")
        doc.append("## Tables Summary")
        doc.append("")
        
        if self.tables_data:
            doc.append("| Table | Columns | Measures | Data Types |")
            doc.append("|-------|---------|----------|------------|")
            
            for table in sorted(self.tables_data, key=lambda x: x['name']):
                data_types = set()
                for col in table.get('columns', []):
                    if not col.get('is_calculated', False):
                        data_types.add(col.get('dataType', 'Unknown'))
                
                data_types_str = ', '.join(sorted(data_types)) if data_types else 'N/A'
                doc.append(
                    f"| {table['name']} | {table['column_count']} | "
                    f"{table['measure_count']} | {data_types_str} |"
                )
            doc.append("")
        
        # ===== 4. DETAILED TABLE CLASSIFICATIONS =====
        doc.append("---")
        doc.append("## Detailed Table Classifications")
        doc.append("")
        
        if self.analysis_data and 'table_classifications' in self.analysis_data:
            classifications = self.analysis_data['table_classifications']
            
            # Group by classification
            grouped = {}
            for cls in classifications:
                classification = cls['classification']
                if classification not in grouped:
                    grouped[classification] = []
                grouped[classification].append(cls)
            
            for table_type in ['FACT', 'DIMENSION', 'BRIDGE', 'CALCULATION', 'PARAMETER']:
                if table_type in grouped:
                    tables_of_type = grouped[table_type]
                    doc.append(f"### {table_type} Tables ({len(tables_of_type)})")
                    doc.append("")
                    
                    for table in tables_of_type:
                        doc.append(f"#### {table['table_name']}")
                        doc.append(f"- **Classification:** {table['classification']}")
                        doc.append(f"- **Confidence:** {table['confidence']}")
                        doc.append(f"- **Reasoning:** {table['reasoning']}")
                        
                        metadata = table.get('metadata', {})
                        doc.append(f"- **Columns:** {metadata.get('columns', 0)}")
                        doc.append(f"- **Numeric Columns:** {metadata.get('numeric_columns', 0)}")
                        doc.append(f"- **String Columns:** {metadata.get('string_columns', 0)}")
                        doc.append(f"- **Date Columns:** {metadata.get('date_columns', 0)}")
                        doc.append(f"- **Measures:** {metadata.get('measures', 0)}")
                        doc.append("")
        
        # ===== 5. RELATIONSHIPS ANALYSIS =====
        doc.append("---")
        doc.append("## Relationships Analysis")
        doc.append("")
        
        if self.relationships_data:
            doc.append(f"**Total Relationships:** {len(self.relationships_data)}")
            doc.append("")
            doc.append("| From Table | From Column | To Table | To Column | Cardinality |")
            doc.append("|------------|------------|----------|-----------|-------------|")
            
            for rel in self.relationships_data:
                doc.append(
                    f"| {rel['from_table']} | {rel['from_column']} | "
                    f"{rel['to_table']} | {rel['to_column']} | {rel['cardinality']} |"
                )
            doc.append("")
        else:
            doc.append("No relationships defined in the model.")
            doc.append("")
        
        # ===== 6. MEASURES OVERVIEW =====
        doc.append("---")
        doc.append("## Measures Overview")
        doc.append("")
        
        if self.measures_data:
            doc.append(f"**Total Measures:** {len(self.measures_data)}")
            doc.append("")
            doc.append("| Table | Measure Name | Complexity | DAX Snippet |")
            doc.append("|-------|--------------|-----------|------------|")
            
            for measure in self.measures_data:
                table_name = measure.get('table', 'Unknown')
                measure_name = measure.get('name', 'Unknown')
                complexity = measure.get('complexity', 0)
                dax = measure.get('expression', '').replace('|', '\\|')[:50]
                
                doc.append(f"| {table_name} | {measure_name} | {complexity}/10 | {dax}... |")
            doc.append("")
        else:
            doc.append("No measures defined in the model.")
            doc.append("")
        
        # ===== 7. COLUMNS DETAILS =====
        doc.append("---")
        doc.append("## Columns Details")
        doc.append("")
        
        if self.tables_data:
            for table in sorted(self.tables_data, key=lambda x: x['name']):
                if table.get('columns'):
                    doc.append(f"### {table['name']}")
                    doc.append("")
                    doc.append("| Column Name | Data Type | Calculated | Key |")
                    doc.append("|------------|-----------|-----------|-----|")
                    
                    for col in table['columns']:
                        col_name = col.get('name', 'Unknown')
                        data_type = col.get('dataType', 'Unknown')
                        is_calc = "✓" if col.get('is_calculated', False) else ""
                        is_key = "✓" if col.get('is_key', False) else ""
                        
                        doc.append(f"| {col_name} | {data_type} | {is_calc} | {is_key} |")
                    doc.append("")
        
        # ===== 8. REPORT PAGES =====
        doc.append("---")
        doc.append("## Report Pages")
        doc.append("")
        
        if self.pages_data:
            doc.append(f"**Total Pages:** {len(self.pages_data)}")
            doc.append("")
            doc.append("| Page Name | Visualizations |")
            doc.append("|-----------|-----------------|")
            
            for page in self.pages_data:
                doc.append(f"| {page['display_name']} | {page['visuals_count']} |")
            doc.append("")
        else:
            doc.append("No report pages found.")
            doc.append("")
        
        # ===== 9. DATA QUALITY =====
        doc.append("---")
        doc.append("## Data Quality")
        doc.append("")
        
        if self.analysis_data:
            rel_analysis = self.analysis_data.get('relationship_analysis', {})
            doc.append(f"- **Schema Compliance Score:** {rel_analysis.get('compliance_score', 0)}/100")
            doc.append(f"- **Schema Type:** {rel_analysis.get('schema_type', 'N/A')}")
            doc.append(f"- **Orphaned Tables:** {rel_analysis.get('orphaned_tables', 0)}")
        
        doc.append("")
        doc.append("---")
        doc.append("*End of Report*")
        
        return "\n".join(doc)


def find_semantic_model_dir(project_path: Path) -> Path:
    """
    Finds the SemanticModel/definition directory.
    
    Handles:
    - Direct path to .SemanticModel folder
    - Path to parent containing .SemanticModel folders
    - Path to .pbip folder
    """
    # Case 1: Direct .SemanticModel folder
    if project_path.name.endswith(".SemanticModel"):
        definition_dir = project_path / "definition"
        if definition_dir.exists():
            return definition_dir
    
    # Case 2: Parent folder containing .SemanticModel folders
    for item in project_path.iterdir():
        if item.is_dir() and item.name.endswith(".SemanticModel"):
            definition_dir = item / "definition"
            if definition_dir.exists():
                return definition_dir
    
    # Case 3: Fallback - look for any definition with TMDL files
    for item in project_path.iterdir():
        if item.is_dir():
            definition_dir = item / "definition"
            if definition_dir.exists() and any(definition_dir.glob("*.tmdl")):
                return definition_dir
    
    return None


def get_pbip_files(source_path: Path) -> list:
    """
    Get list of projects to process.
    
    Handles structures:
    1. RecursosFuente/
       ├── Project1.SemanticModel/  ← Returns this
       ├── Project1.Report/
       ├── Project2.SemanticModel/  ← Returns this
       └── Project2.Report/
    
    2. Project.pbip/  (folder - already extracted)
       └── Returns the folder itself
    """
    pbip_projects = []
    
    if not source_path.is_dir():
        return pbip_projects
    
    # Strategy 1: Look for *.SemanticModel folders
    for item in source_path.iterdir():
        if item.is_dir() and item.name.endswith(".SemanticModel"):
            pbip_projects.append(item)
    
    # Strategy 2: If no SemanticModel folders, look for .pbip folders
    if not pbip_projects:
        for item in source_path.iterdir():
            if item.is_dir() and item.name.endswith(".pbip"):
                pbip_projects.append(item)
    
    # Strategy 3: If source is itself a .pbip or .SemanticModel folder
    if source_path.name.endswith(".pbip") or source_path.name.endswith(".SemanticModel"):
        if pbip_projects:
            return pbip_projects  # Already found items, return them
        pbip_projects.append(source_path)
    
    return pbip_projects


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py path/to/file.pbip")
        print("   or: python main.py path/to/folder/  (will find all .pbip files)")
        print("")
        print("Examples:")
        print("  python main.py ../RecursosFuente/OnlineBaseline.pbip")
        print("  python main.py ../RecursosFuente/  (processes all .pbip files)")
        print("  python main.py .  (find .pbip in current directory)")
        sys.exit(1)
    
    source_path = Path(sys.argv[1]).resolve()
    
    if not source_path.exists():
        print(f"[ERROR] Path not found: {source_path}")
        sys.exit(1)
    
    # Get list of PBIP files to process
    pbip_files = get_pbip_files(source_path)
    
    if not pbip_files:
        print(f"[ERROR] No projects found in: {source_path}")
        print("")
        print("Expected folder structure:")
        print("  RecursosFuente/")
        print("  ├── MyProject.pbip (file)")
        print("  ├── MyProject.SemanticModel/")
        print("  │   └── definition/  (TMDL files) ← Required")
        print("  ├── MyProject.Report/")
        print("  ├── AnotherProject.pbip (file)")
        print("  ├── AnotherProject.SemanticModel/")
        print("  └── AnotherProject.Report/")
        print("")
        print("Or: Project.pbip/ (folder with extracted contents)")
        sys.exit(1)
    
    print(f"Found {len(pbip_files)} .pbip file(s) to process")
    print("")
    
    # Output base directory
    output_base_dir = Path.cwd() / "powerbi-project"
    output_base_dir.mkdir(exist_ok=True)
    
    # Summary statistics
    total_processed = 0
    total_skipped = 0
    
    # Process each PBIP file
    for pbip_index, pbip_root in enumerate(pbip_files, 1):
        print(f"{'='*80}")
        print(f"[{pbip_index}/{len(pbip_files)}] Processing: {pbip_root.name}")
        print(f"{'='*80}")
        
        # Find the semantic model directory
        tmdl_dir = find_semantic_model_dir(pbip_root)
        
        if tmdl_dir is None:
            print(f"[WARN] No semantic model found in {pbip_root.name}")
            print(f"   Skipping this project...")
            total_skipped += 1
            print("")
            continue
        
        # Verify TMDL files exist
        tmdl_files = list(tmdl_dir.glob("*.tmdl"))
        if not tmdl_files:
            print(f"[WARN] No TMDL files found in {tmdl_dir}")
            print(f"   Skipping this project...")
            total_skipped += 1
            print("")
            continue
        
        print(f"[OK] Found semantic model with {len(tmdl_files)} TMDL files")
        print(f"  Location: {tmdl_dir}")
        print("")
        
        # Create output directory per project (remove .pbip and .SemanticModel extensions)
        pbip_name_clean = pbip_root.name.replace(".pbip", "").replace(".SemanticModel", "")
        output_dir = output_base_dir / pbip_name_clean
        data_dir = output_dir / "data"
        reports_dir = output_dir / "reports"
        graphs_dir = output_dir / "graphs"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(exist_ok=True)
        graphs_dir.mkdir(exist_ok=True)
        
        print("[STEP 1/3] Running parsers...")
        
        # Parse tables
        print("  • Parsing tables...", end=" ", flush=True)
        tables = parse_tables(str(tmdl_dir), str(data_dir / "tables.json"))
        print(f"[OK] {len(tables)} tables")
        
        # Parse relationships
        print("  • Parsing relationships...", end=" ", flush=True)
        relationships = parse_relationships(str(tmdl_dir), str(data_dir / "relationships.json"))
        print(f"[OK] {len(relationships)} relationships")
        
        # Parse measures
        print("  • Parsing measures...", end=" ", flush=True)
        measures = parse_measures(str(tmdl_dir), str(data_dir / "measures.json"))
        print(f"[OK] {len(measures)} measures")
        
        # Parse pages (pbip_root's parent contains both .SemanticModel and .Report)
        print("  • Parsing pages...", end=" ", flush=True)
        project_name = pbip_root.name.replace(".SemanticModel", "").replace(".pbip", "")
        pages = parse_pages(str(pbip_root.parent), str(data_dir / "pages.json"), project_name)
        print(f"[OK] {len(pages)} pages")
        
        # Parse datasources
        print("  • Parsing datasources...", end=" ", flush=True)
        datasources = parse_datasources(str(tmdl_dir), str(data_dir / "datasources.json"))
        print(f"[OK] {len(datasources)} datasources")
        
        # Parse analysis
        print("  • Running analysis...", end=" ", flush=True)
        analysis = parse_analysis(str(tmdl_dir), str(data_dir / "analysis.json"))
        print("[OK]")
        
        # ========== STEP 2: GENERATE DOCUMENTATION ==========
        print("")
        print("[STEP 2/3] Generating documentation...")
        
        doc_gen = DocumentationGenerator(output_dir, pbip_name_clean)
        doc_gen.load_all_data(data_dir)
        
        # Technical Documentation
        print("  • Generating TECHNICAL_DOCUMENTATION.md...", end=" ", flush=True)
        tech_doc = doc_gen.generate_technical_documentation()
        tech_file = reports_dir / "TECHNICAL_DOCUMENTATION.md"
        tech_file.write_text(tech_doc, encoding='utf-8')
        print("[OK]")
        
        # Extended Documentation
        print("  • Generating extended analysis...", end=" ", flush=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extended_doc = doc_gen.generate_extended_documentation()
        extended_file = reports_dir / f"powerbi_analysis_{timestamp}.md"
        extended_file.write_text(extended_doc, encoding='utf-8')
        print("[OK]")
        
        # ========== STEP 3: GENERATE VISUALIZATIONS ==========
        if VISUALIZERS_AVAILABLE:
            print("")
            print("[STEP 3/3] Generating visualizations...")
            
            graphs_dir.mkdir(exist_ok=True)
            
            # 1. Relationship Graph
            try:
                print("  • Generating relationship graph...", end=" ", flush=True)
                rel_result = create_relationship_graph(
                    str(data_dir / "tables.json"),
                    str(data_dir / "relationships.json"),
                    str(graphs_dir / "relationship_graph.png"),
                    str(graphs_dir / "relationship_graph.html")
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:40]})")
            
            # 2. Measure Dependency DAG
            try:
                print("  • Generating measure dependency DAG...", end=" ", flush=True)
                dep_result = create_measure_dependency_dag(
                    str(data_dir / "measures.json"),
                    str(graphs_dir / "measure_dependency.png")
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:40]})")
            
            # 3. Complexity Heatmap
            try:
                print("  • Generating complexity heatmap...", end=" ", flush=True)
                heat_result = create_complexity_heatmap(
                    str(data_dir / "tables.json"),
                    str(data_dir / "measures.json"),
                    str(data_dir / "analysis.json"),
                    str(graphs_dir / "complexity_heatmap.png")
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:40]})")
            
            # 4. Schema Distribution
            try:
                print("  • Generating schema distribution chart...", end=" ", flush=True)
                schema_result = create_schema_distribution(
                    str(data_dir / "analysis.json"),
                    str(graphs_dir / "schema_type_donut.png")
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:40]})")
            
            # 5. Datatype Distribution
            try:
                print("  • Generating datatype distribution chart...", end=" ", flush=True)
                dtype_result = create_datatype_distribution(
                    str(data_dir / "tables.json"),
                    str(graphs_dir / "datatype_distribution.png")
                )
                print("[OK]")
            except Exception as e:
                print(f"[FAIL] ({str(e)[:40]})")
        
        # Summary for this PBIP
        print("")
        print(f"[DONE] {pbip_name_clean}")
        print(f"   Output: {output_dir}")
        print("")
        
        total_processed += 1
    
    # ========== FINAL SUMMARY ==========
    print("")
    print("=" * 80)
    print("[BATCH PROCESSING SUMMARY]")
    print("=" * 80)
    print(f"Total processed: {total_processed}")
    print(f"Total skipped: {total_skipped}")
    print(f"Output base directory: {output_base_dir}")
    print("")
    
    if total_processed > 0:
        print("Generated files per project:")
        print("  [DIR] data/")
        print("     ├── tables.json")
        print("     ├── relationships.json")
        print("     ├── measures.json")
        print("     ├── pages.json")
        print("     ├── datasources.json")
        print("     └── analysis.json")
        print("")
        print("  [DIR] reports/")
        print("     ├── TECHNICAL_DOCUMENTATION.md")
        print("     └── powerbi_analysis_*.md")
        print("")
        if VISUALIZERS_AVAILABLE:
            print("  [DIR] graphs/")
            print("     ├── relationship_graph.png + .html")
            print("     ├── measure_dependency.png")
            print("     ├── complexity_heatmap.png")
            print("     ├── schema_type_donut.png")
            print("     └── datatype_distribution.png")
            print("")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
