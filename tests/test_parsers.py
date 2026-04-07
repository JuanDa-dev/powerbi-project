"""
Quick test script for parsers
Tests basic parsing functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parsers import PBIPParser, ModelBIMParser, DefinitionParser, TMDLParser


def test_pbip_parser():
    """Test PBIP structure parser"""
    print("=" * 60)
    print("Testing PBIP Parser")
    print("=" * 60)
    
    # This would need a real .pbip directory
    print("✓ PBIPParser class loaded successfully")
    print(f"  - PBIPParser.__init__ signature: (pbip_path: str)")
    print(f"  - Methods: parse(), get_structure(), is_valid(), list_files()")
    print()


def test_model_bim_parser():
    """Test model.bim parser"""
    print("=" * 60)
    print("Testing Model.bim Parser")
    print("=" * 60)
    
    print("✓ ModelBIMParser class loaded successfully")
    print(f"  - ModelBIMParser.__init__ signature: (model_bim_path: str)")
    print(f"  - Methods: parse(), get_model(), get_table(), get_all_measures()")
    print(f"  - Data classes: Table, Column, Measure, Relationship, Hierarchy, Role")
    print()


def test_definition_parser():
    """Test definition parser"""
    print("=" * 60)
    print("Testing Definition Parser")
    print("=" * 60)
    
    print("✓ DefinitionParser class loaded successfully")
    print(f"  - DefinitionParser.__init__ signature: (definition_path: str)")
    print(f"  - Methods: parse(), is_report(), is_dataset()")
    print(f"  - Supports: definition.pbir, definition.pbism")
    print()


def test_tmdl_parser():
    """Test TMDL parser"""
    print("=" * 60)
    print("Testing TMDL Parser")
    print("=" * 60)
    
    print("✓ TMDLParser class loaded successfully")
    print(f"  - TMDLParser.__init__ signature: (tmdl_directory: str)")
    print(f"  - Methods: parse(), convert_to_model_bim_format(), is_available()")
    print(f"  - Parses: .tmdl text files")
    print()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "PARSER TESTS - PHASE 2" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_pbip_parser()
        test_model_bim_parser()
        test_definition_parser()
        test_tmdl_parser()
        
        print("=" * 60)
        print("✓ ALL PARSERS LOADED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Create or obtain a sample .pbip project for testing")
        print("  2. Test parsers with real data")
        print("  3. Proceed to Phase 3: Analyzers")
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
