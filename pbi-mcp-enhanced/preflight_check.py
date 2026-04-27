#!/usr/bin/env python3
"""
Pre-flight Check - Verify Everything is Ready
Antes de ejecutar el análisis, verifica que todo esté configurado
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verify Python version"""
    print("\n📌 Python Version Check")
    print("-" * 40)
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("   ❌ FAILED: Python 3.7+ required")
        return False
    else:
        print("   ✅ OK")
        return True

def check_dependencies():
    """Verify required packages"""
    print("\n📌 Dependencies Check")
    print("-" * 40)
    
    required = {
        'pandas': 'Data analysis',
        'pathlib': 'Path handling',
        'json': 'JSON parsing',
        'networkx': 'Graph analysis',
        'matplotlib': 'Visualizations',
        'tqdm': 'Progress bars'
    }
    
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package)
            print(f"   ✅ {package:15} - {description}")
        except ImportError:
            print(f"   ❌ {package:15} - {description} [MISSING]")
            missing.append(package)
    
    if missing:
        print(f"\n   Missing packages: {', '.join(missing)}")
        print(f"   Run: pip install -r requirements.txt")
        return False
    
    return True

def check_pbip_structure():
    """Verify .pbip files exist"""
    print("\n📌 .pbip Projects Structure Check")
    print("-" * 40)
    
    pbip_dir = Path("../../RecursosFuente")
    
    if not pbip_dir.exists():
        print(f"   ❌ Directory not found: {pbip_dir.absolute()}")
        return False
    
    pbip_files = list(pbip_dir.glob("*.pbip"))
    
    if not pbip_files:
        print(f"   ❌ No .pbip files found in: {pbip_dir}")
        return False
    
    print(f"   Found {len(pbip_files)} project(s):")
    
    all_valid = True
    for pbip_file in pbip_files:
        project_name = pbip_file.stem
        
        # Check associated folders
        semantic_folder = pbip_dir / f"{project_name}.SemanticModel"
        report_folder = pbip_dir / f"{project_name}.Report"
        
        semantic_ok = semantic_folder.exists()
        report_ok = report_folder.exists()
        
        status = "✅" if (semantic_ok or report_ok) else "❌"
        print(f"   {status} {project_name}")
        print(f"      - .SemanticModel: {'✓' if semantic_ok else '✗'}")
        print(f"      - .Report: {'✓' if report_ok else '✗'}")
        
        if not (semantic_ok or report_ok):
            all_valid = False
    
    return all_valid

def check_scripts():
    """Verify required scripts exist"""
    print("\n📌 Scripts Availability Check")
    print("-" * 40)
    
    scripts = [
        'main.py',
        'analyze_pbip.py',
        'run.py',
        'test_pbip.py',
        'quickstart.py'
    ]
    
    all_exist = True
    
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"   ✅ {script}")
        else:
            print(f"   ❌ {script} [NOT FOUND]")
            all_exist = False
    
    return all_exist

def check_parsers():
    """Verify parser module exists"""
    print("\n📌 Parser Module Check")
    print("-" * 40)
    
    try:
        from parsers import PBIPParser
        print("   ✅ PBIPParser imported successfully")
        return True
    except ImportError as e:
        print(f"   ❌ Failed to import PBIPParser: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("  ✨ PRE-FLIGHT CHECK - Power BI EDA Tool")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("PBIP Structure", check_pbip_structure),
        ("Scripts", check_scripts),
        ("Parsers", check_parsers),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error during {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("  📋 SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} checks passed\n")
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("  ✨ ALL CHECKS PASSED - Ready to analyze! ✨")
        print("="*60)
        print("\n🚀 Next steps:")
        print("\n   Option 1: Run specific project")
        print("   python main.py ../RecursosFuente/CorporateSpend.pbip")
        print("\n   Option 2: Interactive selection")
        print("   python analyze_pbip.py ../RecursosFuente")
        print("\n   Option 3: Run all projects")
        print("   python analyze_pbip.py ../RecursosFuente --all")
        print("\n   Option 4: See quick start guide")
        print("   python quickstart.py")
        return 0
    else:
        print("  ⚠️  SOME CHECKS FAILED - Please fix issues above")
        print("="*60)
        print("\n🔧 Troubleshooting:")
        
        if not results[1][1]:  # Dependencies
            print("\n   Missing dependencies? Run:")
            print("   pip install -r requirements.txt")
        
        if not results[2][1]:  # PBIP Structure
            print("\n   PBIP files not found? Check:")
            print("   - Correct directory path")
            print("   - .pbip files exist")
            print("   - Associated .SemanticModel folders exist")
        
        if not results[3][1]:  # Scripts
            print("\n   Scripts missing? Ensure you're in pbi-mcp-enhanced/")
            print("   cd pbi-mcp-enhanced")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
