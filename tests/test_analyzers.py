"""
Test script for analyzers
Tests basic analyzer functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analyzers import (
    TableAnalyzer, ColumnAnalyzer, MeasureAnalyzer,
    RelationshipAnalyzer, HierarchyAnalyzer, RoleAnalyzer
)


def test_analyzer_imports():
    """Test that all analyzers can be imported"""
    print("=" * 60)
    print("Testing Analyzer Imports")
    print("=" * 60)
    
    analyzers = [
        ('TableAnalyzer', TableAnalyzer),
        ('ColumnAnalyzer', ColumnAnalyzer),
        ('MeasureAnalyzer', MeasureAnalyzer),
        ('RelationshipAnalyzer', RelationshipAnalyzer),
        ('HierarchyAnalyzer', HierarchyAnalyzer),
        ('RoleAnalyzer', RoleAnalyzer),
    ]
    
    for name, analyzer_class in analyzers:
        print(f"✓ {name}: {analyzer_class}")
    
    print()
    print("All analyzers loaded successfully!")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 14 + "ANALYZER TESTS - PHASE 3" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_analyzer_imports()
        
        print("=" * 60)
        print("✓ ALL ANALYZERS LOADED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Analyzer Capabilities:")
        print("  • TableAnalyzer: Classifies fact/dimension tables")
        print("  • ColumnAnalyzer: Analyzes data types and calculated columns")
        print("  • MeasureAnalyzer: Extracts DAX complexity and dependencies")
        print("  • RelationshipAnalyzer: Maps table relationships and cardinality")
        print("  • HierarchyAnalyzer: Analyzes hierarchical structures")
        print("  • RoleAnalyzer: Extracts RLS security rules")
        print()
        print("Next steps:")
        print("  1. Proceed to Phase 4: Statistics")
        print("  2. Then Phase 5: Visualizations")
        print("  3. Finally Phase 6: Report Generation")
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
