#!/usr/bin/env python3
"""
Convenience script to discover and run PBIP analysis
Finds all .pbip files in the current directory and subdirectories
"""

import sys
import os
from pathlib import Path
from typing import List
import argparse

def find_pbip_files(start_path: Path = None, recursive: bool = True) -> List[Path]:
    """
    Find all .pbip files in the specified directory
    
    Args:
        start_path: Directory to search (default: current directory)
        recursive: Whether to search recursively in subdirectories
        
    Returns:
        List of Path objects pointing to .pbip files
    """
    if start_path is None:
        start_path = Path.cwd()
    
    start_path = Path(start_path)
    
    if not start_path.is_dir():
        print(f"ERROR: {start_path} is not a valid directory")
        return []
    
    pattern = "**/*.pbip" if recursive else "*.pbip"
    pbip_files = sorted(start_path.glob(pattern))
    
    return pbip_files


def display_pbip_files(pbip_files: List[Path]) -> None:
    """Display discovered PBIP files"""
    print("\n" + "="*70)
    print("🔍 PBIP Files Discovered:")
    print("="*70)
    
    if not pbip_files:
        print("No .pbip files found.")
        return
    
    for idx, pbip_file in enumerate(pbip_files, 1):
        print(f"{idx}. {pbip_file.name:<30} ({pbip_file.parent.name}/)")
    
    print("="*70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Discover and analyze Power BI .pbip projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find and list .pbip files in current directory
  python run.py
  
  # Analyze specific .pbip file
  python run.py ./CorporateSpend.pbip
  
  # Analyze all .pbip files with custom output
  python run.py --all -o ./all_reports
  
  # Find .pbip files in specific directory
  python run.py --search ./my-projects
  
  # Show help
  python run.py --help
        """
    )
    
    parser.add_argument('pbip_path', nargs='?', type=str, 
                       help='Optional: Path to specific .pbip file to analyze')
    parser.add_argument('--search', type=str, default=None,
                       help='Directory to search for .pbip files (default: current directory)')
    parser.add_argument('--all', action='store_true',
                       help='Analyze all discovered .pbip files')
    parser.add_argument('-o', '--output', type=str, default='output',
                       help='Output directory for reports (default: output/)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do not search subdirectories')
    
    args = parser.parse_args()
    
    # Determine search directory
    search_dir = Path(args.search) if args.search else Path.cwd()
    
    # Find PBIP files
    pbip_files = find_pbip_files(search_dir, recursive=not args.no_recursive)
    
    if not pbip_files:
        print(f"⚠️  No .pbip files found in {search_dir}")
        return 1
    
    display_pbip_files(pbip_files)
    
    # If specific file provided, use that
    if args.pbip_path:
        pbip_to_analyze = Path(args.pbip_path)
        if not pbip_to_analyze.exists():
            print(f"ERROR: File not found: {pbip_to_analyze}")
            return 1
        pbip_files = [pbip_to_analyze]
    
    # If --all flag, analyze all found files
    if args.all:
        print(f"📊 Analyzing {len(pbip_files)} .pbip file(s)...\n")
        
        # Import here to avoid issues if main.py is not available
        sys.path.insert(0, str(Path(__file__).parent))
        from main import PBIPAnalyzer
        
        for pbip_file in pbip_files:
            try:
                print(f"Processing: {pbip_file.name}")
                analyzer = PBIPAnalyzer(
                    pbip_path=str(pbip_file),
                    output_dir=args.output,
                    verbose=args.verbose
                )
                report_path = analyzer.analyze()
                print(f"✅ Report: {report_path}\n")
            except Exception as e:
                print(f"❌ Failed to analyze {pbip_file.name}: {e}\n")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
        
        return 0
    
    # If only one file found, offer to analyze it
    if len(pbip_files) == 1:
        pbip_file = pbip_files[0]
        response = input(f"Analyze '{pbip_file.name}'? (y/n): ").strip().lower()
        
        if response == 'y':
            sys.path.insert(0, str(Path(__file__).parent))
            from main import PBIPAnalyzer
            
            try:
                analyzer = PBIPAnalyzer(
                    pbip_path=str(pbip_file),
                    output_dir=args.output,
                    verbose=args.verbose
                )
                report_path = analyzer.analyze()
                print(f"\n✅ Report generated: {report_path}\n")
                return 0
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                return 1
    
    # Multiple files found, ask which one to analyze
    if len(pbip_files) > 1:
        print("Multiple .pbip files found. Choose which to analyze:\n")
        for idx, pbip_file in enumerate(pbip_files, 1):
            print(f"  {idx}. {pbip_file.name}")
        
        while True:
            try:
                choice = input("\nEnter number (or 'a' for all): ").strip().lower()
                
                if choice == 'a':
                    args.all = True
                    return main()  # Re-run with --all flag
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(pbip_files):
                    pbip_file = pbip_files[choice_idx]
                    break
                else:
                    print(f"Invalid choice. Please enter 1-{len(pbip_files)}")
            except ValueError:
                print("Invalid input. Please enter a number or 'a'.")
        
        # Analyze selected file
        sys.path.insert(0, str(Path(__file__).parent))
        from main import PBIPAnalyzer
        
        try:
            analyzer = PBIPAnalyzer(
                pbip_path=str(pbip_file),
                output_dir=args.output,
                verbose=args.verbose
            )
            report_path = analyzer.analyze()
            print(f"\n✅ Report generated: {report_path}\n")
            return 0
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
