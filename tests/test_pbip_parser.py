#!/usr/bin/env python3
"""
Quick test script to verify PBIP parser works with .pbip files
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import PBIPParser

def test_pbip_file_input():
    """Test that parser accepts .pbip files"""
    
    # Test with .pbip JSON file
    pbip_file = Path("../RecursosFuente/CorporateSpend.pbip")
    
    if not pbip_file.exists():
        print(f"❌ Test file not found: {pbip_file}")
        return False
    
    print(f"Testing with: {pbip_file}")
    print(f"  Absolute path: {pbip_file.resolve()}")
    
    try:
        parser = PBIPParser(str(pbip_file))
        print(f"✅ Parser initialized successfully")
        print(f"  PBIP path: {parser.pbip_path}")
        
        structure = parser.parse()
        print(f"✅ Structure parsed successfully")
        print(f"  Has report: {structure.has_report}")
        print(f"  Has semantic model: {structure.has_semantic_model}")
        print(f"  Model BIM path: {structure.model_bim_path}")
        print(f"  Errors: {structure.errors}")
        print(f"  Warnings: {structure.warnings}")
        
        if structure.has_semantic_model and structure.model_bim_path:
            print(f"\n✅ SUCCESS: Parser can work with .pbip files!")
            print(f"  Found model: {structure.model_bim_path}")
            return True
        else:
            print(f"\n⚠️  WARNING: No semantic model found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pbip_file_input()
    sys.exit(0 if success else 1)
