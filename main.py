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
from pathlib import Path
from datetime import datetime

# Import parsers
from parsers.parse_tables import parse_tables
from parsers.parse_relationships import parse_relationships
from parsers.parse_measures import parse_measures
from parsers.parse_pages import parse_pages
from parsers.parse_datasources import parse_datasources
from parsers.parse_analysis import parse_analysis


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
        """Generate TECHNICAL_DOCUMENTATION.md"""
        doc = []
        
        # Header
        doc.append("# Power BI Technical Documentation")
        doc.append("")
        doc.append(f"**Project:** {self.pbip_name}")
        doc.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("")
        
        # 1. General Description
        doc.append("## 1. General Description")
        doc.append("")
        doc.append(f"Power BI project: **{self.pbip_name}**")
        doc.append("")
        
        # 2. Data Model Summary
        doc.append("## 2. Data Model Summary")
        doc.append("")
        
        if self.analysis_data:
            summary = self.analysis_data.get('summary', {})
            doc.append(f"- **Fact Tables:** {summary.get('fact_tables', 0)}")
            doc.append(f"- **Dimension Tables:** {summary.get('dimension_tables', 0)}")
            doc.append(f"- **Calculation Tables:** {summary.get('calculation_tables', 0)}")
            doc.append(f"- **Bridge Tables:** {summary.get('bridge_tables', 0)}")
            doc.append(f"- **Parameter Tables:** {summary.get('parameter_tables', 0)}")
            doc.append(f"- **Total Measures:** {summary.get('total_measures', 0)}")
            doc.append("")
        
        # 3. Tables
        doc.append("## 3. Tables and Composition")
        doc.append("")
        
        for table in self.tables_data:
            doc.append(f"### {table['name']}")
            doc.append(f"**Columns:** {table['column_count']} | **Measures:** {table['measure_count']}")
            if table['column_count'] > 0:
                doc.append(f"- Data Types: {', '.join(set(c['dataType'] for c in table['columns']))}")
            doc.append("")
        
        # 4. Relationships
        doc.append("## 4. Relationships")
        doc.append("")
        
        if self.relationships_data:
            doc.append(f"**Total Relationships:** {len(self.relationships_data)}")
            doc.append("")
            doc.append("| From Table | From Column | To Table | To Column | Cardinality |")
            doc.append("|------------|------------|----------|-----------|-------------|")
            for rel in self.relationships_data:
                doc.append(f"| {rel['from_table']} | {rel['from_column']} | {rel['to_table']} | {rel['to_column']} | {rel['cardinality']} |")
            doc.append("")
        
        # 5. Measures
        doc.append("## 5. Measures")
        doc.append("")
        
        if self.measures_data:
            doc.append(f"**Total Measures:** {len(self.measures_data)}")
            doc.append("")
            for measure in self.measures_data[:20]:  # Show first 20
                doc.append(f"- **{measure['name']}** ({measure['table']})")
            if len(self.measures_data) > 20:
                doc.append(f"- ... and {len(self.measures_data) - 20} more measures")
            doc.append("")
        
        # 6. Report Pages
        doc.append("## 6. Report Pages and Visualizations")
        doc.append("")
        
        if self.pages_data:
            total_visuals = sum(p['visuals_count'] for p in self.pages_data)
            doc.append(f"**Total Pages:** {len(self.pages_data)}")
            doc.append(f"**Total Visualizations:** {total_visuals}")
            doc.append("")
            doc.append("| Page | Display Name | Visualizations |")
            doc.append("|------|--------------|-----------------|")
            for page in self.pages_data:
                doc.append(f"| {page['page_id']} | {page['display_name']} | {page['visuals_count']} |")
            doc.append("")
        
        return "\n".join(doc)
    
    def generate_extended_documentation(self) -> str:
        """Generate powerbi_analysis_fecha_code.md"""
        doc = []
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Header
        doc.append(f"# Power BI Detailed Analysis Report")
        doc.append(f"**Generated:** {timestamp}")
        doc.append(f"**Project:** {self.pbip_name}")
        doc.append("")
        
        # Executive Summary
        doc.append("## Executive Summary")
        doc.append("")
        
        if self.analysis_data:
            rel_analysis = self.analysis_data.get('relationship_analysis', {})
            doc.append(f"- **Total Tables:** {rel_analysis.get('total_tables', 0)}")
            doc.append(f"- **Total Relationships:** {rel_analysis.get('total_relationships', 0)}")
            doc.append(f"- **Schema Type:** {rel_analysis.get('schema_type', 'N/A')}")
            doc.append(f"- **Compliance Score:** {rel_analysis.get('compliance_score', 0)}/100")
            doc.append("")
        
        # Detailed Table Classifications
        doc.append("## Table Classifications")
        doc.append("")
        
        if self.analysis_data:
            classifications = self.analysis_data.get('table_classifications', [])
            
            # Group by classification
            grouped = {}
            for cls in classifications:
                classification = cls['classification']
                if classification not in grouped:
                    grouped[classification] = []
                grouped[classification].append(cls)
            
            for classification in ['FACT', 'DIMENSION', 'BRIDGE', 'CALCULATION', 'PARAMETER']:
                if classification in grouped:
                    doc.append(f"### {classification} Tables ({len(grouped[classification])})")
                    doc.append("")
                    for table in grouped[classification]:
                        doc.append(f"**{table['table_name']}**")
                        doc.append(f"- Classification: {table['classification']} (Confidence: {table['confidence']})")
                        doc.append(f"- Reasoning: {table['reasoning']}")
                        metadata = table.get('metadata', {})
                        doc.append(f"- Columns: {metadata.get('columns', 0)}")
                        doc.append(f"- Measures: {metadata.get('measures', 0)}")
                        doc.append("")
        
        # Detailed Relationship Analysis
        doc.append("## Relationship Details")
        doc.append("")
        
        if self.relationships_data:
            doc.append(f"**Total Relationships:** {len(self.relationships_data)}")
            doc.append("")
            for rel in self.relationships_data:
                doc.append(f"- `{rel['from_table']}.{rel['from_column']}` → `{rel['to_table']}.{rel['to_column']}`")
            doc.append("")
        
        # Data Sources
        doc.append("## Data Sources")
        doc.append("")
        
        if self.datasources_data:
            for ds in self.datasources_data:
                doc.append(f"- **{ds['type']}**: {ds['definition']}")
            doc.append("")
        else:
            doc.append("- No data sources explicitly defined\n")
        
        # Pages & Visuals Detail
        doc.append("## Pages and Visualizations Detail")
        doc.append("")
        
        if self.pages_data:
            for page in self.pages_data:
                doc.append(f"### {page['display_name']}")
                doc.append(f"- Page ID: {page['page_id']}")
                doc.append(f"- Visualizations: {page['visuals_count']}")
                doc.append("")
        
        return "\n".join(doc)


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py path/to/OnlineBaseline.pbip")
        print("Example: python main.py ../RecursosFuente/OnlineBaseline.pbip")
        sys.exit(1)
    
    pbip_path = Path(sys.argv[1]).resolve()
    
    if not pbip_path.exists():
        print(f"❌ Error: PBIP path not found: {pbip_path}")
        sys.exit(1)
    
    # Determine paths
    if pbip_path.is_dir():
        pbip_root = pbip_path
    else:
        pbip_root = pbip_path.parent
    
    tmdl_dir = pbip_root / "OnlineBaseline.SemanticModel" / "definition"
    
    if not tmdl_dir.exists():
        print(f"❌ Error: TMDL directory not found: {tmdl_dir}")
        sys.exit(1)
    
    # Output directory
    output_dir = Path.cwd() / "powerbi-project"
    output_dir.mkdir(exist_ok=True)
    
    # Create subdirectories for organized output
    data_dir = output_dir / "data"
    reports_dir = output_dir / "reports"
    data_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    
    pbip_name = pbip_root.name
    
    print("=" * 80)
    print("POWER BI PBIP ANALYSIS PIPELINE")
    print("=" * 80)
    print(f"PBIP Root: {pbip_root}")
    print(f"Output Dir: {output_dir}")
    print("")
    
    # ========== STEP 1: RUN ALL PARSERS ==========
    print("📊 [1/2] Running parsers...")
    
    # Parse tables
    print("  • Parsing tables...", end=" ", flush=True)
    tables = parse_tables(str(tmdl_dir), str(data_dir / "tables.json"))
    print(f"✓ {len(tables)} tables")
    
    # Parse relationships
    print("  • Parsing relationships...", end=" ", flush=True)
    relationships = parse_relationships(str(tmdl_dir), str(data_dir / "relationships.json"))
    print(f"✓ {len(relationships)} relationships")
    
    # Parse measures
    print("  • Parsing measures...", end=" ", flush=True)
    measures = parse_measures(str(tmdl_dir), str(data_dir / "measures.json"))
    print(f"✓ {len(measures)} measures")
    
    # Parse pages
    print("  • Parsing pages...", end=" ", flush=True)
    pages = parse_pages(str(pbip_root), str(data_dir / "pages.json"))
    print(f"✓ {len(pages)} pages")
    
    # Parse datasources
    print("  • Parsing datasources...", end=" ", flush=True)
    datasources = parse_datasources(str(tmdl_dir), str(data_dir / "datasources.json"))
    print(f"✓ {len(datasources)} datasources")
    
    # Parse analysis
    print("  • Running analysis...", end=" ", flush=True)
    analysis = parse_analysis(str(tmdl_dir), str(data_dir / "analysis.json"))
    print("✓")
    
    # ========== STEP 2: GENERATE DOCUMENTATION ==========
    print("")
    print("📝 [2/2] Generating documentation...")
    
    doc_gen = DocumentationGenerator(output_dir, pbip_name)
    doc_gen.load_all_data(data_dir)
    
    # Technical Documentation
    print("  • Generating TECHNICAL_DOCUMENTATION.md...", end=" ", flush=True)
    tech_doc = doc_gen.generate_technical_documentation()
    tech_file = reports_dir / "TECHNICAL_DOCUMENTATION.md"
    tech_file.write_text(tech_doc, encoding='utf-8')
    print("✓")
    
    # Extended Documentation
    print("  • Generating extended analysis...", end=" ", flush=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extended_doc = doc_gen.generate_extended_documentation()
    extended_file = reports_dir / f"powerbi_analysis_{timestamp}.md"
    extended_file.write_text(extended_doc, encoding='utf-8')
    print("✓")
    
    # ========== SUMMARY ==========
    print("")
    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print("")
    print("📊 Data Files (powerbi-project/data/):")
    print(f"  • tables.json")
    print(f"  • relationships.json")
    print(f"  • measures.json")
    print(f"  • pages.json")
    print(f"  • datasources.json")
    print(f"  • analysis.json")
    print("")
    print("📝 Documentation Files (powerbi-project/reports/):")
    print(f"  • TECHNICAL_DOCUMENTATION.md")
    print(f"  • powerbi_analysis_{timestamp}.md")
    print("")
    print(f"All files saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
