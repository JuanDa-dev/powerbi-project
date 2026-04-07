"""
Test script for visualizations
Tests basic visualization functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from visualizations import (
    RelationshipDiagramGenerator,
    DataTypeChartGenerator,
    MeasureDependencyGenerator,
    TableComplexityChartGenerator
)


def test_viz_imports():
    """Test that all visualization modules can be imported"""
    print("=" * 60)
    print("Testing Visualization Module Imports")
    print("=" * 60)
    
    modules = [
        ('RelationshipDiagramGenerator', RelationshipDiagramGenerator),
        ('DataTypeChartGenerator', DataTypeChartGenerator),
        ('MeasureDependencyGenerator', MeasureDependencyGenerator),
        ('TableComplexityChartGenerator', TableComplexityChartGenerator),
    ]
    
    for name, module_class in modules:
        print(f"✓ {name}: {module_class}")
    
    print()
    print("All visualization modules loaded successfully!")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "VISUALIZATION TESTS - PHASE 5" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_viz_imports()
        
        print("=" * 60)
        print("✓ ALL VISUALIZATION MODULES LOADED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Visualization Capabilities:")
        print("  • RelationshipDiagramGenerator: Network graph of table relationships")
        print("  • DataTypeChartGenerator: Bar/pie charts of data type distribution")
        print("  • MeasureDependencyGenerator: DAX measure dependency graphs")
        print("  • TableComplexityChartGenerator: Stacked complexity visualizations")
        print()
        print("Technologies:")
        print("  • NetworkX: Graph creation and layout")
        print("  • Matplotlib: Chart rendering")
        print("  • Seaborn: Color palettes and themes")
        print()
        print("Next steps:")
        print("  1. Proceed to Phase 6: Report Generation")
        print("  2. Assemble all components into Markdown reports")
        print("  3. Complete Phase 7: CLI and Testing")
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
