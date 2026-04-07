"""
Report Exporter
Assembles all sections and exports final Markdown report
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from .header_generator import ReportHeaderGenerator
from .summary_generator import ExecutiveSummaryGenerator
from .tables_generator import TablesSectionGenerator
from .measures_generator import MeasuresSectionGenerator
from .relationships_generator import RelationshipsSectionGenerator
from .recommendations_generator import RecommendationsGenerator


class ReportExporter:
    """
    Assembles all report sections and exports to Markdown
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize exporter
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export(self,
               header_gen: ReportHeaderGenerator,
               summary_gen: ExecutiveSummaryGenerator,
               tables_gen: TablesSectionGenerator,
               measures_gen: MeasuresSectionGenerator,
               relationships_gen: RelationshipsSectionGenerator,
               recommendations_gen: Optional[RecommendationsGenerator] = None,
               image_paths: Optional[dict] = None) -> str:
        """
        Assemble and export report
        
        Args:
            header_gen: Header generator
            summary_gen: Summary generator
            tables_gen: Tables generator
            measures_gen: Measures generator
            relationships_gen: Relationships generator
            recommendations_gen: Recommendations generator (optional)
            image_paths: Dictionary of image paths for embedding
                - relationship_diagram: path to relationship diagram
                - data_type_chart: path to data type chart
                - measure_dependencies: path to measure dependency graph
                - table_complexity: path to table complexity chart
        
        Returns:
            Path to exported Markdown file
        """
        image_paths = image_paths or {}
        
        # Generate all sections
        sections = []
        
        # Header
        sections.append(header_gen.generate())
        
        # Executive Summary
        sections.append(summary_gen.generate())
        
        # Data Model Diagram (early in report)
        if image_paths.get('relationship_diagram'):
            sections.append("## Data Model Overview\n")
            sections.append(f"![Data Model Overview]({image_paths['relationship_diagram']})\n")
        
        # Tables Section
        sections.append(tables_gen.generate(
            image_path=image_paths.get('table_complexity')
        ))
        
        # Measures Section
        sections.append(measures_gen.generate(
            dependency_image_path=image_paths.get('measure_dependencies')
        ))
        
        # Relationships Section
        sections.append(relationships_gen.generate(
            diagram_path=image_paths.get('relationship_diagram')
        ))
        
        # Data Type Distribution
        if image_paths.get('data_type_chart'):
            sections.append("## Data Type Distribution\n")
            sections.append(f"![Data Types]({image_paths['data_type_chart']})\n")
        
        # Recommendations
        if recommendations_gen:
            sections.append(recommendations_gen.generate())
        
        # Footer
        sections.append(self._generate_footer())
        
        # Assemble full report
        full_report = "\n".join(sections)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"powerbi_analysis_{timestamp}.md"
        output_path = self.output_dir / filename
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        return str(output_path)
    
    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""
---

## About This Report

This report was generated automatically by the **Power BI Project EDA Tool**.

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Report Sections
- **Executive Summary**: High-level overview and key metrics
- **Data Model Overview**: Visual representation of table relationships
- **Tables Analysis**: Detailed breakdown of fact and dimension tables
- **Measures Analysis**: DAX complexity and dependency analysis
- **Relationships Analysis**: Graph structure and connectivity metrics
- **Data Type Distribution**: Column data type statistics
- **Recommendations**: Best practices and optimization suggestions

### Legend
- ✅ - Passed / Good practice
- ⚠️ - Warning / Needs attention
- 🔴 - Critical issue / Urgent action required
- 💡 - Suggestion / Enhancement opportunity

---

*For questions or issues, please refer to the tool documentation.*
"""
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ReportExporter(output_dir={self.output_dir})"
