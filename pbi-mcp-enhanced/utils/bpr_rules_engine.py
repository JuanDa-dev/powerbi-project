"""
Best Practice Rules (BPR) Framework
Implements standardized rules for Power BI semantic model analysis

Based on: https://github.com/TabularEditor/BestPracticeRules
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
import re


class RuleCategory(Enum):
    """Best Practice Rule categories"""
    DAX_EXPRESSIONS = "DAX Expressions"
    FORMATTING = "Formatting"
    METADATA = "Metadata"
    MODEL_LAYOUT = "Model Layout"
    NAMING_CONVENTIONS = "Naming Conventions"
    PERFORMANCE = "Performance"


class RuleSeverity(Enum):
    """Severity levels for rule violations"""
    COSMETIC = 1
    MINOR = 2
    IMPORTANT = 3
    VERY_IMPORTANT = 4
    CRITICAL = 5
    
    @property
    def label(self) -> str:
        labels = {
            1: "Cosmetic",
            2: "Minor",
            3: "Important",
            4: "Very Important",
            5: "Critical"
        }
        return labels.get(self.value, "Unknown")


class ObjectScope(Enum):
    """Scope of objects that a rule applies to"""
    TABLE = "Table"
    COLUMN = "Column"
    MEASURE = "Measure"
    RELATIONSHIP = "Relationship"
    HIERARCHY = "Hierarchy"
    PARTITION = "Partition"
    MODEL = "Model"


@dataclass
class BestPracticeRule:
    """Represents a single Best Practice Rule"""
    
    id: str
    name: str
    category: RuleCategory
    description: str
    severity: RuleSeverity
    scope: List[ObjectScope]
    evaluator: Callable[[Any], bool]
    recommendation: str
    remarks: Optional[str] = None
    source: str = "custom"
    
    def evaluate(self, obj: Any) -> bool:
        """
        Evaluate if an object violates this rule
        
        Args:
            obj: Object to evaluate (Table, Column, Measure, etc.)
            
        Returns:
            True if object violates the rule, False otherwise
        """
        try:
            return self.evaluator(obj)
        except Exception as e:
            # Silently handle evaluation errors
            return False


@dataclass
class ViolationResult:
    """Result of a rule violation"""
    
    rule_id: str
    rule_name: str
    rule_severity: RuleSeverity
    object_type: str
    object_name: str
    table_name: Optional[str] = None
    recommendation: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def location(self) -> str:
        """Full location of the violation"""
        if self.table_name:
            return f"{self.table_name}.{self.object_name}"
        return self.object_name


@dataclass
class BPRScoreResult:
    """Complete BPR scoring result"""
    
    total_violations: int
    critical_violations: int
    important_violations: int
    minor_violations: int
    cosmetic_violations: int
    
    by_category: Dict[str, Dict[str, int]] = field(default_factory=dict)
    violations_by_severity: Dict[str, int] = field(default_factory=dict)
    compliance_score: float = 0.0  # 0-100
    
    @property
    def overall_violations(self) -> int:
        """Total number of violations"""
        return (self.critical_violations + 
                self.important_violations + 
                self.minor_violations + 
                self.cosmetic_violations)
    
    @property
    def critical_issues_count(self) -> int:
        """Count of critical issues"""
        return self.critical_violations
    
    @property
    def needs_attention(self) -> bool:
        """Whether model needs attention"""
        return self.critical_violations > 0 or self.important_violations > 5


class RulesEngine:
    """
    Engine for evaluating Best Practice Rules against Power BI models
    """
    
    def __init__(self):
        """Initialize the rules engine"""
        self.rules: Dict[str, BestPracticeRule] = {}
        self._violations: List[ViolationResult] = []
    
    def register_rule(self, rule: BestPracticeRule) -> None:
        """
        Register a new rule
        
        Args:
            rule: BestPracticeRule to register
        """
        self.rules[rule.id] = rule
    
    def register_rules(self, rules: List[BestPracticeRule]) -> None:
        """
        Register multiple rules at once
        
        Args:
            rules: List of BestPracticeRule objects
        """
        for rule in rules:
            self.register_rule(rule)
    
    def get_rule(self, rule_id: str) -> Optional[BestPracticeRule]:
        """Get a rule by ID"""
        return self.rules.get(rule_id)
    
    def get_rules_by_category(self, category: RuleCategory) -> List[BestPracticeRule]:
        """Get all rules in a category"""
        return [r for r in self.rules.values() if r.category == category]
    
    def get_rules_by_severity(self, severity: RuleSeverity) -> List[BestPracticeRule]:
        """Get all rules with a specific severity"""
        return [r for r in self.rules.values() if r.severity == severity]
    
    def evaluate_object(self, obj: Any, obj_type: str, table_name: Optional[str] = None) -> List[ViolationResult]:
        """
        Evaluate an object against all applicable rules
        
        Args:
            obj: Object to evaluate
            obj_type: Type of object (Table, Column, Measure, etc.)
            table_name: Parent table name (if applicable)
            
        Returns:
            List of ViolationResult objects
        """
        violations = []
        
        try:
            obj_name = getattr(obj, 'name', str(obj))
        except:
            obj_name = "Unknown"
        
        # Find applicable rules for this object type
        for rule in self.rules.values():
            # Check if rule applies to this object type
            try:
                scope_match = any(
                    scope.value.lower() == obj_type.lower()
                    for scope in rule.scope
                )
                
                if not scope_match:
                    continue
                
                # Evaluate the rule
                if rule.evaluate(obj):
                    violation = ViolationResult(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        rule_severity=rule.severity,
                        object_type=obj_type,
                        object_name=obj_name,
                        table_name=table_name,
                        recommendation=rule.recommendation
                    )
                    violations.append(violation)
            except Exception as e:
                # Skip rules that error
                continue
        
        return violations
    
    def evaluate_objects(self, objects: List[Any], obj_type: str, table_name: Optional[str] = None) -> List[ViolationResult]:
        """
        Evaluate multiple objects
        
        Args:
            objects: List of objects to evaluate
            obj_type: Type of objects
            table_name: Parent table name (if applicable)
            
        Returns:
            List of ViolationResult objects
        """
        all_violations = []
        for obj in objects:
            violations = self.evaluate_object(obj, obj_type, table_name)
            all_violations.extend(violations)
        return all_violations
    
    def calculate_score(self, violations: List[ViolationResult], total_items: int) -> BPRScoreResult:
        """
        Calculate BPR score from violations
        
        Args:
            violations: List of ViolationResult objects
            total_items: Total number of items evaluated
            
        Returns:
            BPRScoreResult with comprehensive scoring
        """
        # Count violations by severity
        severity_counts = {
            RuleSeverity.CRITICAL: 0,
            RuleSeverity.VERY_IMPORTANT: 0,
            RuleSeverity.IMPORTANT: 0,
            RuleSeverity.MINOR: 0,
            RuleSeverity.COSMETIC: 0,
        }
        
        category_violations = {}
        
        for violation in violations:
            severity_counts[violation.rule_severity] += 1
            
            category = violation.rule_id.split('_')[0]
            if category not in category_violations:
                category_violations[category] = 0
            category_violations[category] += 1
        
        # Calculate compliance score
        # Weight: Critical=5, Very Important=4, Important=3, Minor=2, Cosmetic=1
        total_weight = (
            severity_counts[RuleSeverity.CRITICAL] * 5 +
            severity_counts[RuleSeverity.VERY_IMPORTANT] * 4 +
            severity_counts[RuleSeverity.IMPORTANT] * 3 +
            severity_counts[RuleSeverity.MINOR] * 2 +
            severity_counts[RuleSeverity.COSMETIC] * 1
        )
        
        # Normalize: max score would be if all items had highest severity
        max_weight = max(1, total_items * 5)
        compliance_score = max(0, 100 - (total_weight / max_weight * 100))
        
        return BPRScoreResult(
            total_violations=len(violations),
            critical_violations=severity_counts[RuleSeverity.CRITICAL],
            important_violations=severity_counts[RuleSeverity.VERY_IMPORTANT],
            minor_violations=severity_counts[RuleSeverity.IMPORTANT],
            cosmetic_violations=severity_counts[RuleSeverity.MINOR] + severity_counts[RuleSeverity.COSMETIC],
            by_category=category_violations,
            violations_by_severity={
                "critical": severity_counts[RuleSeverity.CRITICAL],
                "very_important": severity_counts[RuleSeverity.VERY_IMPORTANT],
                "important": severity_counts[RuleSeverity.IMPORTANT],
                "minor": severity_counts[RuleSeverity.MINOR],
                "cosmetic": severity_counts[RuleSeverity.COSMETIC],
            },
            compliance_score=round(compliance_score, 2)
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of registered rules"""
        categories = {}
        for rule in self.rules.values():
            cat_name = rule.category.value
            if cat_name not in categories:
                categories[cat_name] = []
            categories[cat_name].append({
                "id": rule.id,
                "name": rule.name,
                "severity": rule.severity.value,
                "source": rule.source
            })
        
        return {
            "total_rules": len(self.rules),
            "by_category": categories,
            "by_severity": {
                "critical": len(self.get_rules_by_severity(RuleSeverity.CRITICAL)),
                "very_important": len(self.get_rules_by_severity(RuleSeverity.VERY_IMPORTANT)),
                "important": len(self.get_rules_by_severity(RuleSeverity.IMPORTANT)),
                "minor": len(self.get_rules_by_severity(RuleSeverity.MINOR)),
                "cosmetic": len(self.get_rules_by_severity(RuleSeverity.COSMETIC)),
            }
        }
