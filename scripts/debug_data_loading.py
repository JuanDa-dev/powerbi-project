#!/usr/bin/env python3
"""
Debug script to identify why JSON files are empty or missing.

Usage:
    python debug_data_loading.py ../RecursosFuente/
    python debug_data_loading.py powerbi-project/AmericasConsolidatedBalanceSheet/data/
"""

import sys
from pathlib import Path
import json

def debug_directory(data_dir: str):
    """Analyze data directory for missing/empty files."""
    
    base = Path(data_dir)
    
    if not base.exists():
        print(f"❌ Directory NOT FOUND: {base.resolve()}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"  Debugging Data Directory")
    print(f"  {base.resolve()}")
    print(f"{'='*70}\n")
    
    required_files = [
        "tables.json",
        "relationships.json", 
        "measures.json",
        "pages.json",
        "analysis.json",
    ]
    
    optional_files = [
        "column_usage.json",
        "unused_measures.json",
        "datasources.json",
    ]
    
    all_files = required_files + optional_files
    
    print("[REQUIRED FILES]")
    for filename in required_files:
        filepath = base / filename
        if not filepath.exists():
            print(f"  ❌ MISSING: {filename}")
        else:
            size = filepath.stat().st_size
            with open(filepath) as f:
                content = json.load(f)
            
            if isinstance(content, list):
                print(f"  ✅ {filename:<25} {len(content):4d} items ({size:,} bytes)")
            elif isinstance(content, dict):
                keys = len(content)
                print(f"  ✅ {filename:<25} dict {{{keys} keys}} ({size:,} bytes)")
            else:
                print(f"  ✅ {filename:<25} {type(content).__name__} ({size:,} bytes)")
    
    print("\n[OPTIONAL FILES]")
    for filename in optional_files:
        filepath = base / filename
        if not filepath.exists():
            print(f"  ⓘ  NOT FOUND: {filename}")
        else:
            size = filepath.stat().st_size
            with open(filepath) as f:
                content = json.load(f)
            
            if isinstance(content, list):
                print(f"  ✅ {filename:<25} {len(content):4d} items ({size:,} bytes)")
            elif isinstance(content, dict):
                keys = len(content)
                print(f"  ✅ {filename:<25} dict {{{keys} keys}} ({size:,} bytes)")
    
    print("\n[ANALYSIS]")
    
    # Check for empty files
    empty_files = []
    for filename in all_files:
        filepath = base / filename
        if filepath.exists():
            with open(filepath) as f:
                content = json.load(f)
                if (isinstance(content, list) and len(content) == 0) or \
                   (isinstance(content, dict) and len(content) == 0):
                    empty_files.append(filename)
    
    if empty_files:
        print(f"\n⚠️  EMPTY FILES: {', '.join(empty_files)}")
        print("\nPossible causes:")
        print("  1. Parsers haven't been run yet")
        print("  2. Data directory is wrong (check path)")
        print("  3. .pbip files weren't processed")
        print("\nFix:")
        print("  1. Run main.py first to generate JSON files:")
        print("       python main.py ../RecursosFuente/")
        print("  2. Verify .pbip files exist in RecursosFuente/")
    else:
        print("\n✅ All required files present and non-empty")
        print("\nYou can now run:")
        print("   python ollama_generator.py")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_data_loading.py <data_dir>")
        print("\nExamples:")
        print("  python debug_data_loading.py ../RecursosFuente/")
        print("  python debug_data_loading.py powerbi-project/AmericasConsolidatedBalanceSheet/data/")
        sys.exit(1)
    
    debug_directory(sys.argv[1])
