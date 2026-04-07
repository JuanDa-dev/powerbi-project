"""
Test report generators
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'pbi-mcp-enhanced'))

def test_imports():
    """Test that all report generators can be imported"""
    from report import (
        ReportHeaderGenerator,
        ExecutiveSummaryGenerator,
        TablesSectionGenerator,
        MeasuresSectionGenerator,
        RelationshipsSectionGenerator,
        RecommendationsGenerator,
        ReportExporter
    )
    
    print("✅ All report generators imported successfully")
    print(f"  - ReportHeaderGenerator: {ReportHeaderGenerator}")
    print(f"  - ExecutiveSummaryGenerator: {ExecutiveSummaryGenerator}")
    print(f"  - TablesSectionGenerator: {TablesSectionGenerator}")
    print(f"  - MeasuresSectionGenerator: {MeasuresSectionGenerator}")
    print(f"  - RelationshipsSectionGenerator: {RelationshipsSectionGenerator}")
    print(f"  - RecommendationsGenerator: {RecommendationsGenerator}")
    print(f"  - ReportExporter: {ReportExporter}")

if __name__ == "__main__":
    test_imports()
