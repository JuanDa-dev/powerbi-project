"""
Role Analyzer
Analyzes security roles and RLS (Row Level Security) rules
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import Counter
from parsers.model_bim_parser import Role, ModelBIM


@dataclass
class RoleAnalysis:
    """Analysis results for a single security role"""
    name: str
    description: Optional[str]
    table_permission_count: int
    table_permissions: List[Dict[str, str]]
    has_filters: bool = False
    tables_with_rls: List[str] = field(default_factory=list)


@dataclass
class RoleStatistics:
    """Statistics about security roles in the model"""
    total_roles: int
    roles_with_rls: int
    avg_permissions_per_role: float
    tables_with_rls: int
    most_restricted_tables: List[tuple[str, int]]


class RoleAnalyzer:
    """
    Analyzes security roles and RLS in a Power BI model
    """
    
    def __init__(self, model: ModelBIM):
        """
        Initialize the role analyzer
        
        Args:
            model: Parsed ModelBIM object
        """
        self.model = model
        self.analyses: List[RoleAnalysis] = []
        self.statistics: Optional[RoleStatistics] = None
    
    def analyze(self) -> List[RoleAnalysis]:
        """
        Analyze all security roles in the model
        
        Returns:
            List of RoleAnalysis objects
        """
        self.analyses = []
        
        for role in self.model.roles:
            analysis = self._analyze_role(role)
            self.analyses.append(analysis)
        
        # Calculate statistics
        self._calculate_statistics()
        
        return self.analyses
    
    def _analyze_role(self, role: Role) -> RoleAnalysis:
        """
        Analyze a single security role
        
        Args:
            role: Role object to analyze
        
        Returns:
            RoleAnalysis object
        """
        table_permissions = role.table_permissions or []
        
        # Extract tables with RLS
        tables_with_rls = [
            perm.get('name', '') 
            for perm in table_permissions 
            if perm.get('filterExpression')
        ]
        
        # Check if any filters exist
        has_filters = any(
            perm.get('filterExpression') 
            for perm in table_permissions
        )
        
        return RoleAnalysis(
            name=role.name,
            description=role.description,
            table_permission_count=len(table_permissions),
            table_permissions=table_permissions,
            has_filters=has_filters,
            tables_with_rls=tables_with_rls
        )
    
    def _calculate_statistics(self):
        """Calculate statistics about roles"""
        if not self.analyses:
            self.statistics = RoleStatistics(
                total_roles=0,
                roles_with_rls=0,
                avg_permissions_per_role=0,
                tables_with_rls=0,
                most_restricted_tables=[]
            )
            return
        
        # Count roles with RLS
        roles_with_rls = sum(1 for a in self.analyses if a.has_filters)
        
        # Average permissions
        total_permissions = sum(a.table_permission_count for a in self.analyses)
        avg_permissions = total_permissions / len(self.analyses) if self.analyses else 0
        
        # Count tables with RLS
        all_rls_tables = []
        for analysis in self.analyses:
            all_rls_tables.extend(analysis.tables_with_rls)
        
        table_counts = Counter(all_rls_tables)
        most_restricted = table_counts.most_common(10)
        
        self.statistics = RoleStatistics(
            total_roles=len(self.analyses),
            roles_with_rls=roles_with_rls,
            avg_permissions_per_role=round(avg_permissions, 2),
            tables_with_rls=len(set(all_rls_tables)),
            most_restricted_tables=most_restricted
        )
    
    def get_roles_with_rls(self) -> List[RoleAnalysis]:
        """Get all roles that have RLS filters"""
        return [a for a in self.analyses if a.has_filters]
    
    def get_tables_with_rls(self) -> List[str]:
        """Get all tables that have RLS applied"""
        tables = set()
        for analysis in self.analyses:
            tables.update(analysis.tables_with_rls)
        return list(tables)
    
    def get_rls_for_table(self, table_name: str) -> List[RoleAnalysis]:
        """Get all roles that apply RLS to a specific table"""
        return [
            a for a in self.analyses 
            if table_name in a.tables_with_rls
        ]
    
    def get_statistics(self) -> Optional[RoleStatistics]:
        """Get role statistics"""
        return self.statistics
    
    def has_security(self) -> bool:
        """Check if the model has any security roles defined"""
        return len(self.analyses) > 0
    
    def __repr__(self) -> str:
        """String representation"""
        return f"RoleAnalyzer(roles={len(self.analyses)})"
