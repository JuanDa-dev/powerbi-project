"""
Standard Best Practice Rules for Power BI Models

Implements the most important rules from Tabular Editor Best Practice Analyzer
adapted for Python/Power BI analysis
"""

from typing import Any, List
from .bpr_rules_engine import (
    BestPracticeRule,
    RuleCategory,
    RuleSeverity,
    ObjectScope,
    RulesEngine
)


def create_standard_rules() -> RulesEngine:
    """Create and register all standard best practice rules"""
    
    engine = RulesEngine()
    
    # ============ DAX EXPRESSIONS ============
    
    # DAX_DIVISION_COLUMNS
    def dax_division_check(obj: Any) -> bool:
        """Check if measure/column uses division without DIVIDE()"""
        try:
            expr = getattr(obj, 'expression', '')
            if not expr:
                return False
            # Simple check for division operator without DIVIDE
            return '/' in expr and 'DIVIDE' not in expr.upper()
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="DAX_DIVISION_COLUMNS",
        name="Avoid division (use DIVIDE function instead)",
        category=RuleCategory.DAX_EXPRESSIONS,
        description="Calculated Columns, Measures or Calculated Tables should not use the division symbol (/) unless the denominator is a constant value. Use DIVIDE() function instead.",
        severity=RuleSeverity.IMPORTANT,
        scope=[ObjectScope.MEASURE, ObjectScope.COLUMN],
        evaluator=dax_division_check,
        recommendation="Replace '/' with DIVIDE() function to handle division by zero",
        source="standard"
    ))
    
    # DAX_TODO
    def dax_todo_check(obj: Any) -> bool:
        """Check if expression contains TODO"""
        try:
            expr = getattr(obj, 'expression', '')
            return 'TODO' in expr.upper() if expr else False
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="DAX_TODO",
        name="Revisit TODO expressions",
        category=RuleCategory.DAX_EXPRESSIONS,
        description="Objects with an expression containing 'TODO' should be revisited",
        severity=RuleSeverity.COSMETIC,
        scope=[ObjectScope.MEASURE, ObjectScope.COLUMN],
        evaluator=dax_todo_check,
        recommendation="Review and complete TODO items before deployment",
        source="standard"
    ))
    
    # ============ FORMATTING ============
    
    # APPLY_FORMAT_STRING_COLUMNS
    def format_string_columns_check(obj: Any) -> bool:
        """Check if numeric columns have format string"""
        try:
            # Check if visible, numeric, and missing format string
            is_visible = getattr(obj, 'is_hidden', True) == False
            data_type = getattr(obj, 'data_type', '').upper()
            is_numeric = data_type in ['INT64', 'DOUBLE', 'DECIMAL', 'DATETIME']
            has_format = bool(getattr(obj, 'format_string', ''))
            
            return is_visible and is_numeric and not has_format
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="APPLY_FORMAT_STRING_COLUMNS",
        name="Provide format string for visible numeric columns",
        category=RuleCategory.FORMATTING,
        description="Visible numeric columns should have their Format String property assigned",
        severity=RuleSeverity.MINOR,
        scope=[ObjectScope.COLUMN],
        evaluator=format_string_columns_check,
        recommendation="Assign appropriate format string (e.g., '#,##0.00' for decimals)",
        source="standard"
    ))
    
    # APPLY_FORMAT_STRING_MEASURES
    def format_string_measures_check(obj: Any) -> bool:
        """Check if numeric measures have format string"""
        try:
            is_visible = getattr(obj, 'is_hidden', True) == False
            data_type = getattr(obj, 'data_type', '').upper()
            is_numeric = data_type in ['INT64', 'DOUBLE', 'DECIMAL', 'DATETIME']
            has_format = bool(getattr(obj, 'format_string', ''))
            
            return is_visible and is_numeric and not has_format
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="APPLY_FORMAT_STRING_MEASURES",
        name="Provide format string for visible numeric measures",
        category=RuleCategory.FORMATTING,
        description="Visible measures should have their Format String property assigned",
        severity=RuleSeverity.MINOR,
        scope=[ObjectScope.MEASURE],
        evaluator=format_string_measures_check,
        recommendation="Assign appropriate format string for consistency",
        source="standard"
    ))
    
    # ============ METADATA ============
    
    # META_AVOID_FLOAT
    def avoid_float_check(obj: Any) -> bool:
        """Check if column uses floating point data type"""
        try:
            data_type = getattr(obj, 'data_type', '').upper()
            return data_type == 'DOUBLE'
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="META_AVOID_FLOAT",
        name="Do not use floating point data types",
        category=RuleCategory.METADATA,
        description="Floating point datatypes can cause unexpected results. Use Decimal instead.",
        severity=RuleSeverity.IMPORTANT,
        scope=[ObjectScope.COLUMN],
        evaluator=avoid_float_check,
        recommendation="Change data type from Double to Decimal for precision",
        source="standard"
    ))
    
    # META_SUMMARIZE_NONE
    def summarize_none_check(obj: Any) -> bool:
        """Check if numeric column should not be summarized"""
        try:
            is_visible = getattr(obj, 'is_hidden', True) == False
            data_type = getattr(obj, 'data_type', '').upper()
            is_numeric = data_type in ['INT64', 'DOUBLE', 'DECIMAL']
            summarize_by = getattr(obj, 'summarize_by', 'Sum').upper()
            
            return is_visible and is_numeric and summarize_by != 'NONE'
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="META_SUMMARIZE_NONE",
        name="Don't summarize numeric columns",
        category=RuleCategory.METADATA,
        description="Set SummarizeBy to 'None' for visible numeric columns to avoid unintentional summarization. Create measures for columns that should be summarized.",
        severity=RuleSeverity.COSMETIC,
        scope=[ObjectScope.COLUMN],
        evaluator=summarize_none_check,
        recommendation="Set SummarizeBy property to 'None' and create explicit measures",
        source="standard"
    ))
    
    # ============ MODEL LAYOUT ============
    
    # LAYOUT_HIDE_FK_COLUMNS
    def hide_fk_columns_check(obj: Any) -> bool:
        """Check if foreign key columns are hidden"""
        try:
            is_visible = getattr(obj, 'is_hidden', True) == False
            # Check if used in relationships
            is_fk = getattr(obj, 'is_key', False) == False
            has_relationship = getattr(obj, 'used_in_relationships', False)
            
            return is_visible and has_relationship and not is_fk
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="LAYOUT_HIDE_FK_COLUMNS",
        name="Hide foreign key columns",
        category=RuleCategory.MODEL_LAYOUT,
        description="Columns used in relationships should be hidden as the related dimension table is better for filtering.",
        severity=RuleSeverity.COSMETIC,
        scope=[ObjectScope.COLUMN],
        evaluator=hide_fk_columns_check,
        recommendation="Hide foreign key columns to simplify user experience",
        source="standard"
    ))
    
    # ============ NAMING CONVENTIONS ============
    
    # UPPERCASE_FIRST_LETTER
    def uppercase_first_letter_check(obj: Any) -> bool:
        """Check if object name starts with uppercase"""
        try:
            is_visible = getattr(obj, 'is_hidden', True) == False
            name = getattr(obj, 'name', '')
            
            if not name or not is_visible:
                return False
            
            return name[0].islower()
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="UPPERCASE_FIRST_LETTER",
        name="Object names must start with uppercase letter",
        category=RuleCategory.NAMING_CONVENTIONS,
        description="Avoid using lowercase starting letters. Use 'Sales' instead of 'sales' or 'mSales'.",
        severity=RuleSeverity.MINOR,
        scope=[ObjectScope.TABLE, ObjectScope.COLUMN, ObjectScope.MEASURE],
        evaluator=uppercase_first_letter_check,
        recommendation="Rename object to start with uppercase letter",
        source="standard"
    ))
    
    # NO_CAMELCASE
    def no_camelcase_check(obj: Any) -> bool:
        """Check if visible object uses inappropriate CamelCase"""
        try:
            is_visible = getattr(obj, 'is_hidden', True) == False
            name = getattr(obj, 'name', '')
            
            if not name or not is_visible or ' ' in name:
                return False
            
            # Check for camelCase pattern
            import re
            camel_pattern = r'[a-z]+[A-Z]+'
            return bool(re.search(camel_pattern, name))
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="NO_CAMELCASE",
        name="Avoid CamelCase in visible object names",
        category=RuleCategory.NAMING_CONVENTIONS,
        description="Visible objects should use proper case (e.g., 'First Name') not camelCase (e.g., 'firstName')",
        severity=RuleSeverity.MINOR,
        scope=[ObjectScope.COLUMN, ObjectScope.MEASURE, ObjectScope.TABLE],
        evaluator=no_camelcase_check,
        recommendation="Rename using proper case with spaces where appropriate",
        source="standard"
    ))
    
    # ============ PERFORMANCE ============
    
    # PERF_UNUSED_COLUMNS
    def unused_columns_check(obj: Any) -> bool:
        """Check if column is hidden and unused"""
        try:
            is_visible = getattr(obj, 'is_hidden', True) == False
            
            if is_visible:
                return False
            
            # Check if it has any dependencies or relationships
            has_refs = getattr(obj, 'referenced_by', 0) > 0
            has_rels = getattr(obj, 'used_in_relationships', False)
            has_hierarchies = getattr(obj, 'used_in_hierarchies', False)
            
            return not (has_refs or has_rels or has_hierarchies)
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="PERF_UNUSED_COLUMNS",
        name="Remove unused columns",
        category=RuleCategory.PERFORMANCE,
        description="Hidden columns with no dependencies should be removed to save space and improve processing time.",
        severity=RuleSeverity.MINOR,
        scope=[ObjectScope.COLUMN],
        evaluator=unused_columns_check,
        recommendation="Delete unused hidden columns from the model",
        source="standard"
    ))
    
    # PERF_UNUSED_MEASURES
    def unused_measures_check(obj: Any) -> bool:
        """Check if measure is hidden and unreferenced"""
        try:
            is_visible = getattr(obj, 'is_hidden', True) == False
            
            if is_visible:
                return False
            
            has_refs = getattr(obj, 'referenced_by', 0) > 0
            return not has_refs
        except:
            return False
    
    engine.register_rule(BestPracticeRule(
        id="PERF_UNUSED_MEASURES",
        name="Remove unused measures",
        category=RuleCategory.PERFORMANCE,
        description="Hidden measures that are not referenced should be removed.",
        severity=RuleSeverity.COSMETIC,
        scope=[ObjectScope.MEASURE],
        evaluator=unused_measures_check,
        recommendation="Delete unused hidden measures from the model",
        source="standard"
    ))
    
    return engine
