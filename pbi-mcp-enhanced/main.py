#!/usr/bin/env python3
"""
Power BI Project EDA Tool - Main Entry Point
Analyzes .pbip projects and generates comprehensive Markdown reports
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import logging

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parsers import PBIPParser, ModelBIMParser
from analyzers import (
    TableAnalyzer, ColumnAnalyzer, MeasureAnalyzer,
    RelationshipAnalyzer, HierarchyAnalyzer, RoleAnalyzer
)
from utils import (
    ModelSummaryGenerator, DAXComplexityAnalyzer,
    DataTypeAnalyzer, RelationshipGraphAnalyzer
)
from visualizations import (
    RelationshipDiagramGenerator, DataTypeChartGenerator,
    MeasureDependencyGenerator, TableComplexityChartGenerator
)
from report import (
    ReportHeaderGenerator, ExecutiveSummaryGenerator,
    TablesSectionGenerator, MeasuresSectionGenerator,
    RelationshipsSectionGenerator, RecommendationsGenerator,
    ReportExporter
)


class PBIPAnalyzer:
    """Main analyzer orchestrator"""
    
    def __init__(self, pbip_path: str, output_dir: str = "output", verbose: bool = False):
        """Initialize analyzer"""
        self.pbip_path = Path(pbip_path)
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Validate inputs
        self._validate_inputs()
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
    
    def _validate_inputs(self):
        """Validate input parameters"""
        if not self.pbip_path.exists():
            raise FileNotFoundError(f"PBIP path does not exist: {self.pbip_path}")
        
        if self.pbip_path.is_file():
            # Accept a .pbip pointer file directly
            if self.pbip_path.suffix.lower() != '.pbip':
                raise ValueError(f"File must have .pbip extension: {self.pbip_path}")
            return

        if not self.pbip_path.is_dir():
            raise ValueError(f"PBIP path must be a .pbip file or directory: {self.pbip_path}")
        
        # Check for required structure in a directory
        required_dirs = ['semantic-model', 'report']
        missing = [d for d in required_dirs if not (self.pbip_path / d).exists()]
        
        if missing:
            raise ValueError(
                f"Invalid .pbip structure. Missing directories: {', '.join(missing)}\n"
                f"Expected .pbip project directory with 'semantic-model' and 'report' folders."
            )
    
    def analyze(self) -> str:
        """Run complete analysis pipeline"""
        try:
            self.logger.info(f"Starting analysis of: {self.pbip_path.name}")
            
            # Phase 1: Parse PBIP structure
            self.logger.info("Phase 1/7: Parsing PBIP structure...")
            pbip_parser = PBIPParser(str(self.pbip_path))
            structure = pbip_parser.parse()
            
            # Phase 2: Parse model.bim or TMDL
            self.logger.info("Phase 2/7: Parsing semantic model...")
            
            # Try model.bim first
            if structure.model_bim_path and structure.model_bim_path.exists():
                model_bim_parser = ModelBIMParser(str(structure.model_bim_path))
                model = model_bim_parser.parse()
            elif structure.model_tmdl_path and structure.model_tmdl_path.exists():
                # Use TMDL parser
                from parsers import TMDLParser
                self.logger.info("  Using TMDL format...")
                tmdl_parser = TMDLParser(str(structure.model_tmdl_path))
                model = tmdl_parser.parse()
            else:
                raise ValueError(
                    "No model found. Expected model.bim or TMDL definition folder.\n"
                    f"Checked paths:\n"
                    f"  - model.bim: {structure.model_bim_path}\n"
                    f"  - TMDL: {structure.model_tmdl_path}"
                )
            
            if not model.tables:
                raise ValueError("No tables found in model. The semantic model may be empty or corrupted.")
            
            self.logger.info(f"  Found: {len(model.tables)} tables, {len(model.measures)} measures, {len(model.relationships)} relationships")
            
            # Phase 3: Analyze tables
            self.logger.info("Phase 3/7: Analyzing tables and measures...")
            table_analyzer = TableAnalyzer(model.tables, model.relationships)
            table_analyzer.analyze()
            
            measure_analyzer = MeasureAnalyzer(model.measures)
            measure_analyzer.analyze()
            
            relationship_analyzer = RelationshipAnalyzer(model.relationships, model.tables)
            relationship_analyzer.analyze()
            
            # Phase 4: Generate statistics
            self.logger.info("Phase 4/7: Generating statistics...")
            summary_gen = ModelSummaryGenerator(
                table_analyzer, measure_analyzer, relationship_analyzer
            )
            summary = summary_gen.generate()
            
            dax_analyzer = DAXComplexityAnalyzer(measure_analyzer)
            dax_stats = dax_analyzer.analyze()
            
            data_type_analyzer = DataTypeAnalyzer(model.tables)
            data_type_stats = data_type_analyzer.analyze()
            
            graph_analyzer = RelationshipGraphAnalyzer(relationship_analyzer)
            graph_metrics = graph_analyzer.analyze()
            
            # Phase 5: Generate visualizations
            self.logger.info("Phase 5/7: Creating visualizations...")
            image_paths = {}
            
            # Relationship diagram
            rel_diagram = RelationshipDiagramGenerator(relationship_analyzer, table_analyzer)
            rel_path = self.images_dir / "relationship_diagram.png"
            rel_diagram.generate(str(rel_path))
            image_paths['relationship_diagram'] = f"images/{rel_path.name}"
            self.logger.debug(f"  Generated: {rel_path.name}")
            
            # Data type chart
            dtype_chart = DataTypeChartGenerator(data_type_stats)
            dtype_path = self.images_dir / "data_type_distribution.png"
            dtype_chart.generate(str(dtype_path))
            image_paths['data_type_chart'] = f"images/{dtype_path.name}"
            self.logger.debug(f"  Generated: {dtype_path.name}")
            
            # Measure dependencies (only if measures exist)
            if model.measures:
                measure_dep = MeasureDependencyGenerator(measure_analyzer)
                measure_path = self.images_dir / "measure_dependencies.png"
                measure_dep.generate(str(measure_path))
                image_paths['measure_dependencies'] = f"images/{measure_path.name}"
                self.logger.debug(f"  Generated: {measure_path.name}")
            
            # Table complexity
            table_complexity = TableComplexityChartGenerator(table_analyzer)
            table_path = self.images_dir / "table_complexity.png"
            table_complexity.generate(str(table_path))
            image_paths['table_complexity'] = f"images/{table_path.name}"
            self.logger.debug(f"  Generated: {table_path.name}")
            
            # Phase 6: Generate report sections
            self.logger.info("Phase 6/7: Assembling Markdown report...")
            
            header_gen = ReportHeaderGenerator(model, summary, str(self.pbip_path))
            summary_gen_report = ExecutiveSummaryGenerator(summary, dax_stats, data_type_stats, graph_metrics)
            tables_gen = TablesSectionGenerator(table_analyzer)
            measures_gen = MeasuresSectionGenerator(measure_analyzer, dax_stats)
            relationships_gen = RelationshipsSectionGenerator(relationship_analyzer, graph_metrics)
            recommendations_gen = RecommendationsGenerator(
                summary, graph_metrics, dax_stats, table_analyzer, relationship_analyzer
            )
            
            # Phase 7: Export report
            self.logger.info("Phase 7/7: Exporting report...")
            exporter = ReportExporter(str(self.output_dir))
            report_path = exporter.export(
                header_gen, summary_gen_report, tables_gen, measures_gen,
                relationships_gen, recommendations_gen, image_paths
            )
            
            self.logger.info("Analysis complete!")
            self.logger.info(f"Report generated: {report_path}")
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            raise


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Power BI Project EDA Tool - Analyze .pbip projects and generate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ./my-project.pbip
  python main.py ./my-project.pbip -o ./reports
  python main.py ./my-project.pbip --verbose

  # Also accepts a project directory (legacy):
  python main.py ./my-project.pbip/ -o ./reports

The tool will generate:
  - Markdown report with comprehensive analysis
  - PNG visualizations (relationship diagrams, charts)
  - All outputs saved to the specified output directory
        """
    )
    
    parser.add_argument('pbip_path', type=str, help='Path to .pbip project file or directory')
    parser.add_argument('-o', '--output', type=str, default='output',
                        help='Output directory for reports and charts (default: output/)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--version', action='version', version='Power BI EDA Tool v1.0.0')
    
    args = parser.parse_args()
    
    try:
        analyzer = PBIPAnalyzer(
            pbip_path=args.pbip_path,
            output_dir=args.output,
            verbose=args.verbose
        )
        
        report_path = analyzer.analyze()
        
        print(f"\n{'='*60}")
        print(f"SUCCESS: Report generated at:")
        print(f"  {report_path}")
        print(f"{'='*60}\n")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        print(f"Please verify the path exists and try again.\n", file=sys.stderr)
        return 1
        
    except ValueError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}", file=sys.stderr)
        print(f"Use --verbose flag for detailed error information.\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
