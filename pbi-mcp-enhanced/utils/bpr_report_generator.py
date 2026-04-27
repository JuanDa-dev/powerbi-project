"""
Best Practice Rules Report Generator
Generates comprehensive BPR compliance reports in Markdown format
"""

from typing import Optional
from .bpr_evaluator import BPRComplianceReport, BPRScoreCalculator


class BPRReportGenerator:
    """Generates Markdown reports for BPR compliance"""
    
    def __init__(self):
        """Initialize report generator"""
        self.report = ""
    
    def generate(self, bpr_report: BPRComplianceReport) -> str:
        """
        Generate complete BPR compliance report
        
        Args:
            bpr_report: BPRComplianceReport object
            
        Returns:
            Markdown formatted report
        """
        self.report = ""
        
        # Header
        self._add_header(bpr_report)
        
        # Summary
        self._add_summary(bpr_report)
        
        # Scores
        self._add_scores(bpr_report)
        
        # Violations by severity
        self._add_violations_by_severity(bpr_report)
        
        # Violations by category
        self._add_violations_by_category(bpr_report)
        
        # Top recommendations
        self._add_recommendations(bpr_report)
        
        # Detailed violations
        self._add_detailed_violations(bpr_report)
        
        return self.report
    
    def _add_header(self, report: BPRComplianceReport) -> None:
        """Add header section"""
        compliance = report.compliance_percentage
        
        if compliance >= 90:
            status = "✅ Excellent"
            emoji = "🟢"
        elif compliance >= 75:
            status = "✅ Good"
            emoji = "🟡"
        elif compliance >= 60:
            status = "⚠️ Fair"
            emoji = "🟠"
        else:
            status = "❌ Poor"
            emoji = "🔴"
        
        self.report += f"""
## 📋 Best Practice Rules Compliance Analysis

**Overall Compliance Score: {compliance:.1f}/100** {emoji} {status}

**Objects Evaluated:** {report.total_objects_evaluated}
**Total Violations:** {report.total_violations}

"""
    
    def _add_summary(self, report: BPRComplianceReport) -> None:
        """Add summary statistics"""
        score = report.score_result
        
        self.report += f"""
### Compliance Summary

| Metric | Count |
|--------|-------|
| Critical Issues | {score.critical_violations} ❌ |
| Important Issues | {score.important_violations} ⚠️ |
| Minor Issues | {score.minor_violations} ℹ️ |
| Informational | {score.cosmetic_violations} 💡 |
| **Total** | **{report.total_violations}** |

"""
    
    def _add_scores(self, report: BPRComplianceReport) -> None:
        """Add scores by category"""
        score = report.score_result
        
        self.report += """
### Scores by Category

"""
        
        categories = {
            'DAX': 'DAX Expressions',
            'FORMAT': 'Formatting',
            'META': 'Metadata',
            'LAYOUT': 'Model Layout',
            'NAME': 'Naming Conventions',
            'PERF': 'Performance'
        }
        
        for prefix, category in categories.items():
            violations_in_cat = len([v for v in report.violations 
                                    if v.rule_id.startswith(prefix)])
            
            if violations_in_cat == 0:
                self.report += f"- **{category}**: ✅ All rules followed\n"
            else:
                self.report += f"- **{category}**: {violations_in_cat} violation(s)\n"
        
        self.report += "\n"
    
    def _add_violations_by_severity(self, report: BPRComplianceReport) -> None:
        """Add violations grouped by severity"""
        by_severity = report.violations_by_severity()
        
        self.report += """
### Violations by Severity

"""
        
        for severity in ['Critical', 'Very Important', 'Important', 'Minor', 'Cosmetic']:
            if severity in by_severity:
                violations = by_severity[severity]
                emoji_map = {
                    'Critical': '🔴',
                    'Very Important': '🟠',
                    'Important': '🟡',
                    'Minor': '🔵',
                    'Cosmetic': '⚪'
                }
                emoji = emoji_map.get(severity, '•')
                
                self.report += f"#### {emoji} {severity} ({len(violations)})\n\n"
                
                for v in violations[:5]:  # Show top 5
                    self.report += f"- **{v.rule_name}** (`{v.rule_id}`)\n"
                    self.report += f"  - Object: `{v.location}`\n"
                    self.report += f"  - Recommendation: {v.recommendation}\n\n"
                
                if len(violations) > 5:
                    self.report += f"- ... and {len(violations) - 5} more\n\n"
        
        self.report += "\n"
    
    def _add_violations_by_category(self, report: BPRComplianceReport) -> None:
        """Add violations grouped by category"""
        by_category = report.violations_by_category()
        
        self.report += """
### Violations by Category

"""
        
        for category in ['DAX', 'FORMAT', 'META', 'LAYOUT', 'NAME', 'PERF']:
            if category in by_category:
                violations = by_category[category]
                
                category_names = {
                    'DAX': 'DAX Expressions',
                    'FORMAT': 'Formatting',
                    'META': 'Metadata',
                    'LAYOUT': 'Model Layout',
                    'NAME': 'Naming Conventions',
                    'PERF': 'Performance'
                }
                
                self.report += f"#### {category_names.get(category, category)} ({len(violations)})\n\n"
                
                # Group by rule
                rules_map = {}
                for v in violations:
                    if v.rule_id not in rules_map:
                        rules_map[v.rule_id] = []
                    rules_map[v.rule_id].append(v)
                
                for rule_id, violations_list in rules_map.items():
                    if violations_list:
                        v = violations_list[0]
                        self.report += f"- **{v.rule_name}** ({len(violations_list)} occurrences)\n"
        
        self.report += "\n"
    
    def _add_recommendations(self, report: BPRComplianceReport) -> None:
        """Add top recommendations"""
        calc = BPRScoreCalculator()
        action_items = calc.get_action_items(report)
        
        if not action_items:
            return
        
        self.report += """
### Top Recommendations

"""
        
        for i, item in enumerate(action_items[:10], 1):
            priority_emoji = {
                'Critical': '🔴',
                'Very Important': '🟠',
                'Important': '🟡'
            }.get(item['priority'], '•')
            
            self.report += f"{i}. {priority_emoji} **{item['rule']}**\n"
            self.report += f"   - Object: `{item['object']}`\n"
            self.report += f"   - Action: {item['recommendation']}\n\n"
        
        if len(action_items) > 10:
            self.report += f"... and {len(action_items) - 10} more recommendations\n\n"
    
    def _add_detailed_violations(self, report: BPRComplianceReport) -> None:
        """Add detailed violations list"""
        if not report.violations:
            return
        
        self.report += """
### Detailed Violation List

| Rule | Object | Type | Severity | Recommendation |
|------|--------|------|----------|-----------------|
"""
        
        for v in report.violations[:50]:  # Show first 50
            severity_emoji = {
                'Critical': '🔴',
                'Very Important': '🟠',
                'Important': '🟡',
                'Minor': '🔵',
                'Cosmetic': '⚪'
            }.get(v.rule_severity.label, '•')
            
            rule = v.rule_name[:30] + ('...' if len(v.rule_name) > 30 else '')
            obj = v.location[:30] + ('...' if len(v.location) > 30 else '')
            rec = v.recommendation[:40] + ('...' if len(v.recommendation) > 40 else '')
            
            self.report += f"| `{rule}` | `{obj}` | {v.object_type} | {severity_emoji} {v.rule_severity.label} | {rec} |\n"
        
        if len(report.violations) > 50:
            self.report += f"\n*... and {len(report.violations) - 50} more violations (see detailed analysis)*\n"
        
        self.report += "\n"
    
    def generate_summary(self, bpr_report: BPRComplianceReport, 
                        show_critical_only: bool = False) -> str:
        """
        Generate brief summary report
        
        Args:
            bpr_report: BPRComplianceReport object
            show_critical_only: Only show critical violations
            
        Returns:
            Markdown formatted brief report
        """
        report = ""
        score = bpr_report.score_result
        compliance = bpr_report.compliance_percentage
        
        report += f"## Best Practice Compliance: {compliance:.1f}/100\n\n"
        
        if score.critical_violations > 0:
            report += f"⚠️ **{score.critical_violations} critical issue(s) found**\n\n"
        
        report += f"- Critical: {score.critical_violations}\n"
        report += f"- Important: {score.important_violations}\n"
        report += f"- Minor: {score.minor_violations}\n"
        report += f"- Informational: {score.cosmetic_violations}\n\n"
        
        if score.critical_violations > 0:
            report += "**Critical Issues to Fix:**\n\n"
            calc = BPRScoreCalculator()
            critical = calc.get_critical_violations(bpr_report)
            for v in critical[:5]:
                report += f"- {v.rule_name}: {v.location}\n"
        
        return report
