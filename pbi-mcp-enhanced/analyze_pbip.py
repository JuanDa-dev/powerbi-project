#!/usr/bin/env python3
"""
Power BI Project Analyzer - Enhanced Entry Point
Automatically detects and analyzes Power BI projects
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import PBIPAnalyzer


def find_pbip_projects(search_dir: Path) -> List[tuple]:
    """
    Find all PBIP projects in a directory
    
    Args:
        search_dir: Directory to search for .pbip files
        
    Returns:
        List of tuples (pbip_file, project_name)
    """
    projects = []
    
    if not search_dir.exists():
        return projects
    
    # Find all .pbip files
    for pbip_file in search_dir.glob("*.pbip"):
        project_name = pbip_file.stem
        
        # Verify associated folders exist
        semantic_folder = search_dir / f"{project_name}.SemanticModel"
        report_folder = search_dir / f"{project_name}.Report"
        
        # At least one should exist
        if semantic_folder.exists() or report_folder.exists():
            projects.append((pbip_file, project_name))
    
    return projects


def analyze_single_project(pbip_file: Path, output_base: Path, verbose: bool = False) -> bool:
    """
    Analyze a single PBIP project
    
    Args:
        pbip_file: Path to .pbip file
        output_base: Base output directory
        verbose: Enable verbose logging
        
    Returns:
        True if successful, False otherwise
    """
    try:
        project_name = pbip_file.stem
        output_dir = output_base / project_name
        
        print(f"\n📊 Analyzing: {project_name}")
        print(f"   From: {pbip_file}")
        
        # Run analysis
        analyzer = PBIPAnalyzer(str(pbip_file), str(output_dir), verbose=verbose)
        report_file = analyzer.analyze()
        
        print(f"   ✅ Generated: {report_file}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Power BI Project Analyzer - Auto-detects and analyzes PBIP projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific project
  python analyze_pbip.py ../RecursosFuente/CorporateSpend.pbip

  # Analyze all projects in a directory
  python analyze_pbip.py ../RecursosFuente --all

  # Auto-detect and choose project
  python analyze_pbip.py ../RecursosFuente

  # Search in specific directory
  python analyze_pbip.py --search ../RecursosFuente --all

  # Generate verbose output
  python analyze_pbip.py ../RecursosFuente/CorporateSpend.pbip -v
        """
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to .pbip file, project directory, or parent directory containing .pbip files"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Analyze all PBIP projects found in the directory"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--search",
        help="Search directory for .pbip files (alternative to positional argument)"
    )
    
    args = parser.parse_args()
    
    # Determine search directory
    if args.search:
        search_dir = Path(args.search)
    elif args.path:
        search_dir = Path(args.path)
    else:
        parser.print_help()
        return 1
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # Handle .pbip file input
    if search_dir.is_file() and search_dir.suffix.lower() == '.pbip':
        print(f"🔍 Detected: PBIP file")
        success = analyze_single_project(search_dir, output_dir, args.verbose)
        return 0 if success else 1
    
    # Handle directory input
    if not search_dir.is_dir():
        print(f"❌ Error: Path not found: {search_dir}")
        return 1
    
    # Find all projects
    projects = find_pbip_projects(search_dir)
    
    if not projects:
        print(f"❌ No PBIP projects found in: {search_dir}")
        print(f"\nExpected structure:")
        print(f"  {search_dir}/")
        print(f"  ├── ProjectName.pbip")
        print(f"  ├── ProjectName.Report/")
        print(f"  └── ProjectName.SemanticModel/")
        return 1
    
    print(f"🔍 Found {len(projects)} PBIP project(s):")
    for i, (pbip_file, project_name) in enumerate(projects, 1):
        print(f"   {i}. {project_name}")
    
    # Analyze based on arguments
    if args.all:
        print(f"\n📊 Analyzing all {len(projects)} projects...")
        success_count = 0
        for pbip_file, _ in projects:
            if analyze_single_project(pbip_file, output_dir, args.verbose):
                success_count += 1
        
        print(f"\n✅ Completed: {success_count}/{len(projects)} projects analyzed")
        return 0 if success_count == len(projects) else 1
    
    else:
        # Interactive selection
        if len(projects) == 1:
            pbip_file, project_name = projects[0]
            print(f"\n📊 Analyzing: {project_name}")
        else:
            print(f"\nSelect project to analyze:")
            for i, (pbip_file, project_name) in enumerate(projects, 1):
                print(f"  {i}. {project_name}")
            
            while True:
                try:
                    choice = input(f"\nEnter number (1-{len(projects)}) or 'all' for all projects: ").strip()
                    
                    if choice.lower() == 'all':
                        args.all = True
                        return main()
                    
                    idx = int(choice) - 1
                    if 0 <= idx < len(projects):
                        pbip_file, project_name = projects[idx]
                        break
                    else:
                        print(f"Invalid selection. Please enter 1-{len(projects)}")
                except ValueError:
                    print(f"Invalid input. Please enter 1-{len(projects)} or 'all'")
        
        # Analyze selected project
        success = analyze_single_project(pbip_file, output_dir, args.verbose)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
