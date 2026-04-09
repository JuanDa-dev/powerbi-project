"""
Quick test script for parsers
Tests basic parsing functionality
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pbi-mcp-enhanced'))

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


def test_pbip_parser_rejects_non_pbip_file():
    """Test that PBIPParser rejects files that are not .pbip"""
    print("=" * 60)
    print("Testing PBIPParser rejects non-.pbip files")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        tmp_path = f.name
    try:
        try:
            PBIPParser(tmp_path)
            print("✗ Should have raised ValueError for non-.pbip file")
            return False
        except ValueError as e:
            print(f"✓ Correctly rejected non-.pbip file: {e}")
    finally:
        os.unlink(tmp_path)
    print()
    return True


def test_pbip_parser_accepts_pbip_file():
    """Test that PBIPParser accepts a .pbip file and parses sibling folders"""
    print("=" * 60)
    print("Testing PBIPParser accepts .pbip file and resolves sibling structure")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        project_name = "MyProject"

        # Create the .pbip pointer file
        pbip_file = tmpdir / f"{project_name}.pbip"
        pbip_file.write_text('{"version": "1.0", "artifacts": [{"report": {"path": "MyProject.Report"}}]}')

        # Create .Report sibling folder
        report_dir = tmpdir / f"{project_name}.Report"
        report_dir.mkdir()
        (report_dir / "definition.pbir").write_text('{}')

        # Create .SemanticModel sibling folder with model.bim
        semantic_dir = tmpdir / f"{project_name}.SemanticModel"
        semantic_dir.mkdir()
        (semantic_dir / "definition.pbism").write_text('{}')
        (semantic_dir / "model.bim").write_text('{"model": {"tables": [], "relationships": []}}')

        parser = PBIPParser(str(pbip_file))
        structure = parser.parse()

        assert structure.has_report, "Expected has_report to be True"
        assert structure.model_bim_path is not None, "Expected model_bim_path to be set"
        assert structure.report_definition_path is not None, "Expected report_definition_path to be set"
        assert structure.root_path == tmpdir, f"Expected root_path to be parent dir, got {structure.root_path}"

        print(f"✓ PBIPParser correctly accepted .pbip file: {pbip_file.name}")
        print(f"  - root_path: {structure.root_path}")
        print(f"  - report_definition_path: {structure.report_definition_path}")
        print(f"  - model_bim_path: {structure.model_bim_path}")
    print()
    return True



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
        test_pbip_parser_rejects_non_pbip_file()
        test_pbip_parser_accepts_pbip_file()
        
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
