"""
Test script for statistics utilities
Tests basic statistics functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import (
    ModelSummaryGenerator, DAXComplexityAnalyzer,
    DataTypeAnalyzer, RelationshipGraphAnalyzer
)


def test_stats_imports():
    """Test that all statistics modules can be imported"""
    print("=" * 60)
    print("Testing Statistics Module Imports")
    print("=" * 60)
    
    modules = [
        ('ModelSummaryGenerator', ModelSummaryGenerator),
        ('DAXComplexityAnalyzer', DAXComplexityAnalyzer),
        ('DataTypeAnalyzer', DataTypeAnalyzer),
        ('RelationshipGraphAnalyzer', RelationshipGraphAnalyzer),
    ]
    
    for name, module_class in modules:
        print(f"✓ {name}: {module_class}")
    
    print()
    print("All statistics modules loaded successfully!")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 13 + "STATISTICS TESTS - PHASE 4" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_stats_imports()
        
        print("=" * 60)
        print("✓ ALL STATISTICS MODULES LOADED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Statistics Capabilities:")
        print("  • ModelSummaryGenerator: Comprehensive model overview")
        print("  • DAXComplexityAnalyzer: Measure complexity patterns")
        print("  • DataTypeAnalyzer: Column type distribution")
        print("  • RelationshipGraphAnalyzer: Graph structure metrics")
        print()
        print("Next steps:")
        print("  1. Proceed to Phase 5: Visualizations")
        print("  2. Generate charts and diagrams")
        print("  3. Then Phase 6: Report Generation")
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
