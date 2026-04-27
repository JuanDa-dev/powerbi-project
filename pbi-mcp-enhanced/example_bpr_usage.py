"""
Example: Integrating BPR into the Analysis Pipeline

This script demonstrates how to:
1. Load and parse a .pbip project
2. Evaluate against Best Practice Rules
3. Generate compliance report
4. Integrate with existing analysis
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import PBIPParser, ModelBIMParser
from utils.bpr_evaluator import BPRScoreCalculator
from utils.bpr_standard_rules import create_standard_rules
from utils.bpr_report_generator import BPRReportGenerator


def analyze_with_bpr(pbip_path: str) -> dict:
    """
    Complete analysis pipeline with BPR integration
    
    Args:
        pbip_path: Path to .pbip file or project directory
        
    Returns:
        Dictionary with analysis results and BPR report
    """
    
    print(f"📊 Analyzing: {pbip_path}")
    print("=" * 70)
    
    # Step 1: Parse PBIP
    print("\n1️⃣ Parsing PBIP structure...")
    pbip_parser = PBIPParser(str(pbip_path))
    structure = pbip_parser.parse()
    
    if not structure.has_semantic_model:
        print("❌ No semantic model found!")
        return None
    
    print("   ✅ PBIP parsed successfully")
    
    # Step 2: Parse Model
    print("\n2️⃣ Parsing semantic model...")
    if structure.model_bim_path and structure.model_bim_path.exists():
        model_bim_parser = ModelBIMParser(str(structure.model_bim_path))
        model = model_bim_parser.parse()
        print("   ✅ Model loaded (BIM format)")
    else:
        print("❌ Model format not supported in this example")
        return None
    
    if not model.tables:
        print("❌ No tables found!")
        return None
    
    print(f"   ✅ Found {len(model.tables)} tables, {len(model.measures)} measures")
    
    # Step 3: Load BPR Rules
    print("\n3️⃣ Loading Best Practice Rules...")
    engine = create_standard_rules()
    print(f"   ✅ Loaded {len(engine.rules)} rules")
    
    # Step 4: Evaluate Model
    print("\n4️⃣ Evaluating model against BPR...")
    calculator = BPRScoreCalculator(engine)
    bpr_report = calculator.evaluate_model(model)
    
    print(f"   ✅ Evaluation complete")
    print(f"   • Objects evaluated: {bpr_report.total_objects_evaluated}")
    print(f"   • Violations found: {bpr_report.total_violations}")
    print(f"   • Compliance score: {bpr_report.compliance_percentage:.1f}%")
    
    # Step 5: Evaluate Tables Individually
    print("\n5️⃣ Analyzing tables individually...")
    table_reports = calculator.evaluate_tables(model.tables)
    
    print(f"   ✅ Analyzed {len(table_reports)} tables")
    
    worst_table = min(
        table_reports.items(),
        key=lambda x: x[1].compliance_percentage
    )
    print(f"   ⚠️  Table with lowest compliance: {worst_table[0]} ({worst_table[1].compliance_percentage:.1f}%)")
    
    # Step 6: Generate Report
    print("\n6️⃣ Generating report...")
    generator = BPRReportGenerator()
    markdown_report = generator.generate(bpr_report)
    
    print("   ✅ Report generated")
    
    # Step 7: Get Action Items
    print("\n7️⃣ Extracting action items...")
    action_items = calculator.get_action_items(bpr_report)
    
    print(f"   ✅ Found {len(action_items)} action items")
    print("\n   Top 5 Priority Issues:")
    for i, item in enumerate(action_items[:5], 1):
        print(f"   {i}. [{item['priority']}] {item['rule']}")
        print(f"      📍 {item['object']}")
        print(f"      💡 {item['recommendation']}\n")
    
    # Return Results
    return {
        'model': model,
        'bpr_report': bpr_report,
        'bpr_markdown': markdown_report,
        'table_reports': table_reports,
        'action_items': action_items[:10],  # Top 10
        'engine': engine
    }


def print_summary(results: dict) -> None:
    """Print analysis summary"""
    if not results:
        return
    
    report = results['bpr_report']
    score = report.score_result
    
    print("\n" + "=" * 70)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\n✨ Overall Compliance Score: {report.compliance_percentage:.1f}%")
    
    print(f"\nViolations by Severity:")
    print(f"  • 🔴 Critical:         {score.critical_violations}")
    print(f"  • 🟠 Very Important:   {score.important_violations}")
    print(f"  • 🟡 Important:        {score.minor_violations}")
    print(f"  • 🔵 Minor/Cosmetic:   {score.cosmetic_violations}")
    print(f"  {'─' * 35}")
    print(f"  • Total:               {report.total_violations}")
    
    print(f"\nTable Compliance:")
    table_reports = results['table_reports']
    sorted_tables = sorted(
        table_reports.items(),
        key=lambda x: x[1].compliance_percentage
    )
    
    for table_name, table_report in sorted_tables[:5]:
        emoji = "✅" if table_report.compliance_percentage >= 80 else "⚠️ "
        print(f"  {emoji} {table_name}: {table_report.compliance_percentage:.1f}%")
    
    if len(sorted_tables) > 5:
        print(f"  ... and {len(sorted_tables) - 5} more tables")
    
    print(f"\nNext Steps:")
    print(f"  1. Review the generated Markdown report")
    print(f"  2. Address critical issues first")
    print(f"  3. Follow recommendations for each violation")
    print(f"  4. Re-run analysis to verify improvements")


def export_report(results: dict, output_path: str) -> str:
    """
    Export BPR report to file
    
    Args:
        results: Analysis results dictionary
        output_path: Path where to save report
        
    Returns:
        Path to saved report
    """
    from datetime import datetime
    
    output_path = Path(output_path)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_path / f"bpr_analysis_{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(results['bpr_markdown'])
    
    print(f"\n✅ Report saved to: {report_path}")
    return str(report_path)


if __name__ == "__main__":
    # Example usage
    pbip_path = "../RecursosFuente/CorporateSpend.pbip"
    
    try:
        # Run analysis
        results = analyze_with_bpr(pbip_path)
        
        if results:
            # Print summary
            print_summary(results)
            
            # Export report
            export_report(results, "output")
            
            print("\n" + "=" * 70)
            print("✅ Analysis complete!")
            print("=" * 70)
        else:
            print("\n❌ Analysis failed")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
