"""
Report Header Generator
Creates the header section of the Markdown report
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from parsers.model_bim_parser import ModelBIM
from utils import ModelSummary


class ReportHeaderGenerator:
    """
    Generates the header section of the analysis report
    """
    
    def __init__(self, model: ModelBIM, summary: ModelSummary, pbip_path: str):
        """
        Initialize header generator
        
        Args:
            model: Parsed ModelBIM object
            summary: Model summary statistics
            pbip_path: Path to the PBIP project
        """
        self.model = model
        self.summary = summary
        self.pbip_path = Path(pbip_path)
    
    def generate(self) -> str:
        """
        Generate the report header
        
        Returns:
            Markdown string for header
        """
        sections = []
        
        # Main title
        sections.append(self._generate_title())
        
        # Metadata section
        sections.append(self._generate_metadata())
        
        # Quick stats badges
        sections.append(self._generate_badges())
        
        # Separator
        sections.append("\n---\n")
        
        return "\n".join(sections)
    
    def _generate_title(self) -> str:
        """Generate main title"""
        return f"# Power BI Project Analysis Report\n\n## {self.model.name}\n"
    
    def _generate_metadata(self) -> str:
        """Generate metadata section"""
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        metadata = [
            "### Project Information\n",
            "| Property | Value |",
            "|----------|-------|",
            f"| **Project Name** | {self.model.name} |",
            f"| **Project Path** | `{self.pbip_path}` |",
            f"| **Analysis Date** | {analysis_date} |",
            f"| **Compatibility Level** | {self.model.compatibility_level} |",
            f"| **Culture** | {self.model.culture} |",
            f"| **Data Sources** | {len(self.model.data_sources)} |",
            ""
        ]
        
        return "\n".join(metadata)
    
    def _generate_badges(self) -> str:
        """Generate quick stats badges"""
        badges = [
            "### Quick Stats\n",
            f"![Tables](https://img.shields.io/badge/Tables-{self.summary.total_tables}-blue?style=for-the-badge)",
            f"![Measures](https://img.shields.io/badge/Measures-{self.summary.total_measures}-green?style=for-the-badge)",
            f"![Columns](https://img.shields.io/badge/Columns-{self.summary.total_columns}-orange?style=for-the-badge)",
            f"![Relationships](https://img.shields.io/badge/Relationships-{self.summary.total_relationships}-purple?style=for-the-badge)",
            ""
        ]
        
        return " ".join(badges)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ReportHeaderGenerator(model={self.model.name})"
