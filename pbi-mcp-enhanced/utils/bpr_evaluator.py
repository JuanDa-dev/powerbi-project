"""
Best Practice Rules Evaluator
Evaluates Power BI models against BPR standards and calculates compliance scores
"""

from typing import Any, List, Dict, Optional
from dataclasses import dataclass, field
from .bpr_rules_engine import RulesEngine, BPRScoreResult, ViolationResult


@dataclass
class BPRComplianceReport:
    """Comprehensive BPR compliance report"""
    
    total_objects_evaluated: int
    total_violations: int
    violations: List[ViolationResult] = field(default_factory=list)
    score_result: Optional[BPRScoreResult] = None
    
    @property
    def compliance_percentage(self) -> float:
        """Compliance percentage (0-100)"""
        return self.score_result.compliance_score if self.score_result else 100.0
    
    @property
    def critical_count(self) -> int:
        """Count of critical violations"""
        return self.score_result.critical_violations if self.score_result else 0
    
    @property
    def needs_review(self) -> bool:
        """Whether report needs review"""
        return self.critical_count > 0 or self.total_violations > 10
    
    def violations_by_category(self) -> Dict[str, List[ViolationResult]]:
        """Group violations by category"""
        by_cat = {}
        for v in self.violations:
            cat = v.rule_id.split('_')[0]
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(v)
        return by_cat
    
    def violations_by_severity(self) -> Dict[str, List[ViolationResult]]:
        """Group violations by severity"""
        by_sev = {}
        for v in self.violations:
            sev_label = v.rule_severity.label
            if sev_label not in by_sev:
                by_sev[sev_label] = []
            by_sev[sev_label].append(v)
        return by_sev


class BPRScoreCalculator:
    """
    Calculates Best Practice Rules compliance scores for Power BI models
    """
    
    def __init__(self, rules_engine: Optional[RulesEngine] = None):
        """
        Initialize calculator
        
        Args:
            rules_engine: RulesEngine instance. If None, standard rules will be loaded
        """
        self.engine = rules_engine
        self.violations: List[ViolationResult] = []
    
    def evaluate_model(self, model: Any) -> BPRComplianceReport:
        """
        Evaluate entire model against BPR
        
        Args:
            model: Power BI model object
            
        Returns:
            BPRComplianceReport with evaluation results
        """
        if not self.engine:
            from .bpr_standard_rules import create_standard_rules
            self.engine = create_standard_rules()
        
        violations = []
        object_count = 0
        
        # Evaluate tables
        try:
            tables = getattr(model, 'tables', [])
            for table in tables:
                object_count += 1
                table_violations = self.engine.evaluate_object(
                    table, 
                    "Table",
                    None
                )
                violations.extend(table_violations)
                
                # Evaluate columns in table
                columns = getattr(table, 'columns', [])
                for column in columns:
                    object_count += 1
                    col_violations = self.engine.evaluate_object(
                        column,
                        "Column",
                        getattr(table, 'name', 'Unknown')
                    )
                    violations.extend(col_violations)
                
                # Evaluate measures in table
                measures = getattr(table, 'measures', [])
                for measure in measures:
                    object_count += 1
                    meas_violations = self.engine.evaluate_object(
                        measure,
                        "Measure",
                        getattr(table, 'name', 'Unknown')
                    )
                    violations.extend(meas_violations)
                
                # Evaluate hierarchies in table
                hierarchies = getattr(table, 'hierarchies', [])
                for hierarchy in hierarchies:
                    object_count += 1
                    hier_violations = self.engine.evaluate_object(
                        hierarchy,
                        "Hierarchy",
                        getattr(table, 'name', 'Unknown')
                    )
                    violations.extend(hier_violations)
        except Exception as e:
            pass
        
        # Evaluate relationships
        try:
            relationships = getattr(model, 'relationships', [])
            for relationship in relationships:
                object_count += 1
                rel_violations = self.engine.evaluate_object(
                    relationship,
                    "Relationship",
                    None
                )
                violations.extend(rel_violations)
        except Exception as e:
            pass
        
        # Calculate score
        score_result = self.engine.calculate_score(violations, object_count)
        
        report = BPRComplianceReport(
            total_objects_evaluated=object_count,
            total_violations=len(violations),
            violations=violations,
            score_result=score_result
        )
        
        return report
    
    def evaluate_tables(self, tables: List[Any]) -> Dict[str, BPRComplianceReport]:
        """
        Evaluate individual tables
        
        Args:
            tables: List of table objects
            
        Returns:
            Dictionary of table_name -> BPRComplianceReport
        """
        if not self.engine:
            from .bpr_standard_rules import create_standard_rules
            self.engine = create_standard_rules()
        
        results = {}
        
        for table in tables:
            violations = []
            object_count = 1
            
            # Evaluate table itself
            table_violations = self.engine.evaluate_object(
                table,
                "Table",
                None
            )
            violations.extend(table_violations)
            
            # Evaluate columns
            try:
                columns = getattr(table, 'columns', [])
                for column in columns:
                    object_count += 1
                    col_violations = self.engine.evaluate_object(
                        column,
                        "Column",
                        getattr(table, 'name', 'Unknown')
                    )
                    violations.extend(col_violations)
            except:
                pass
            
            # Evaluate measures
            try:
                measures = getattr(table, 'measures', [])
                for measure in measures:
                    object_count += 1
                    meas_violations = self.engine.evaluate_object(
                        measure,
                        "Measure",
                        getattr(table, 'name', 'Unknown')
                    )
                    violations.extend(meas_violations)
            except:
                pass
            
            # Calculate score
            score_result = self.engine.calculate_score(violations, object_count)
            
            table_name = getattr(table, 'name', 'Unknown')
            results[table_name] = BPRComplianceReport(
                total_objects_evaluated=object_count,
                total_violations=len(violations),
                violations=violations,
                score_result=score_result
            )
        
        return results
    
    def get_critical_violations(self, report: BPRComplianceReport) -> List[ViolationResult]:
        """Get only critical violations"""
        return [v for v in report.violations 
                if v.rule_severity.value >= 4]
    
    def get_action_items(self, report: BPRComplianceReport) -> List[Dict[str, Any]]:
        """Get prioritized list of action items"""
        items = []
        
        # Group violations by severity
        by_severity = report.violations_by_severity()
        
        for severity in ['Critical', 'Very Important', 'Important']:
            if severity in by_severity:
                for violation in by_severity[severity]:
                    items.append({
                        'priority': severity,
                        'rule': violation.rule_name,
                        'object': violation.location,
                        'type': violation.object_type,
                        'recommendation': violation.recommendation
                    })
        
        return items
