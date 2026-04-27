#!/usr/bin/env python3
"""
Quick diagnostic script to test PBIP parser
Helps identify path issues when running analysis
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pbi_mcp_enhanced.parsers import PBIPParser


def test_pbip_path(pbip_input: str):
    """Test PBIP path resolution"""
    print(f"\n{'='*60}")
    print(f"Testing PBIP Path: {pbip_input}")
    print(f"{'='*60}\n")
    
    input_path = Path(pbip_input)
    
    # 1. Check if path exists
    print(f"1. Path exists: {input_path.exists()}")
    print(f"   Type: {'File' if input_path.is_file() else 'Directory' if input_path.is_dir() else 'Not found'}")
    
    # 2. If file, show parent and stem
    if input_path.is_file():
        print(f"\n2. File information:")
        print(f"   Name: {input_path.name}")
        print(f"   Stem: {input_path.stem}")
        print(f"   Suffix: {input_path.suffix}")
        print(f"   Parent: {input_path.parent}")
        
        # Show what the parser will look for
        project_name = input_path.stem
        parent = input_path.parent
        
        semantic_folder = parent / f"{project_name}.SemanticModel"
        report_folder = parent / f"{project_name}.Report"
        
        print(f"\n3. Associated folders (parser will look for):")
        print(f"   Semantic: {semantic_folder.name}")
        print(f"      Exists: {semantic_folder.exists()}")
        if semantic_folder.exists():
            print(f"      Contents: {list(semantic_folder.iterdir())[:3]}")
        
        print(f"   Report: {report_folder.name}")
        print(f"      Exists: {report_folder.exists()}")
    
    # 3. If directory, show contents
    elif input_path.is_dir():
        print(f"\n2. Directory information:")
        print(f"   Name: {input_path.name}")
        print(f"   Full path: {input_path}")
        
        # Look for .pbip files
        pbip_files = list(input_path.glob("*.pbip"))
        print(f"\n3. PBIP files in this directory:")
        if pbip_files:
            for pbip_file in pbip_files:
                project_name = pbip_file.stem
                semantic_folder = input_path / f"{project_name}.SemanticModel"
                report_folder = input_path / f"{project_name}.Report"
                
                print(f"   - {pbip_file.name}")
                print(f"     SemanticModel exists: {semantic_folder.exists()}")
                print(f"     Report exists: {report_folder.exists()}")
        else:
            print(f"   No .pbip files found!")
        
        # Show directory contents
        print(f"\n4. Directory contents:")
        for item in list(input_path.iterdir())[:10]:
            print(f"   - {item.name}")
    
    # 4. Try to parse
    print(f"\n5. Attempting to parse...")
    try:
        parser = PBIPParser(pbip_input)
        structure = parser.parse()
        
        print(f"   ✅ Parser succeeded!")
        print(f"   Has report: {structure.has_report}")
        print(f"   Has semantic model: {structure.has_semantic_model}")
        print(f"   Errors: {len(structure.errors)}")
        print(f"   Warnings: {len(structure.warnings)}")
        
        if structure.errors:
            print(f"   Error details:")
            for error in structure.errors:
                print(f"     - {error}")
        
        if structure.warnings:
            print(f"   Warnings:")
            for warning in structure.warnings:
                print(f"     - {warning}")
                
    except Exception as e:
        print(f"   ❌ Parser failed!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}\n")


def main():
    """Run diagnostics"""
    if len(sys.argv) < 2:
        print("Usage: python test_pbip.py <path_to_pbip_or_directory>")
        print("\nExamples:")
        print("  python test_pbip.py ../RecursosFuente/CorporateSpend.pbip")
        print("  python test_pbip.py ../RecursosFuente")
        return 1
    
    pbip_input = sys.argv[1]
    test_pbip_path(pbip_input)
    return 0


if __name__ == "__main__":
    sys.exit(main())
