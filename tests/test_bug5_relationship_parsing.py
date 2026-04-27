#!/usr/bin/env python3
"""
Unit tests for Bug #5: Bridge table relationship detection
"""

import unittest
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent / "pbi-mcp-enhanced"))

from parsers import TMDLParser
from analyzers import TableAnalyzer


class TestBug5BridgeTableRelationships(unittest.TestCase):
    """Test that bridge_addressable_table relationships are correctly detected"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixture"""
        # Find TMDL directory
        tmdl_dir = Path(__file__).parent.parent.parent / "RecursosFuente" / "ManualBaseline.SemanticModel" / "definition"
        
        if not tmdl_dir.exists():
            raise FileNotFoundError(f"TMDL directory not found: {tmdl_dir}")
        
        # Parse TMDL
        parser = TMDLParser(str(tmdl_dir))
        cls.model = parser.parse()
        
        # Analyze
        cls.table_analyzer = TableAnalyzer(cls.model.tables, cls.model.relationships)
        cls.table_analyzer.analyze()
    
    def test_relationships_parsed(self):
        """Verify that relationships are parsed"""
        self.assertGreater(len(self.model.relationships), 0, "No relationships found in model")
    
    def test_bridge_table_exists(self):
        """Verify that bridge_addressable_table exists"""
        bridge_tables = [t for t in self.model.tables if 'bridge' in t.name.lower()]
        self.assertGreater(len(bridge_tables), 0, "bridge_addressable_table not found")
        self.assertEqual(bridge_tables[0].name, 'bridge_addressable_table')
    
    def test_bridge_table_has_relationships(self):
        """Verify that bridge_addressable_table has relationships"""
        bridge_rels = [
            r for r in self.model.relationships 
            if r.from_table == 'bridge_addressable_table' or r.to_table == 'bridge_addressable_table'
        ]
        
        self.assertGreater(
            len(bridge_rels), 0, 
            "bridge_addressable_table has no relationships! Found relationships: " + 
            ", ".join([f"{r.from_table}→{r.to_table}" for r in self.model.relationships])
        )
    
    def test_bridge_table_analyzer_relationship_count(self):
        """Verify that table analyzer correctly counts bridge table relationships"""
        bridge_analysis = self.table_analyzer.analyses.get('bridge_addressable_table')
        
        self.assertIsNotNone(bridge_analysis, "bridge_addressable_table analysis not found")
        self.assertGreater(
            bridge_analysis.relationship_count, 0,
            f"bridge_addressable_table shows {bridge_analysis.relationship_count} relationships but should have > 0"
        )
    
    def test_fact_spend_transactions_bridge_connection(self):
        """Verify that fact_spend_transactions connects to bridge_addressable_table"""
        rels_with_bridge = [
            r for r in self.model.relationships 
            if (r.from_table == 'fact_spend_transactions' and r.to_table == 'bridge_addressable_table') or
               (r.from_table == 'bridge_addressable_table' and r.to_table == 'fact_spend_transactions')
        ]
        
        self.assertGreater(
            len(rels_with_bridge), 0,
            "No relationship found between fact_spend_transactions and bridge_addressable_table"
        )
    
    def test_all_relationships_have_tables(self):
        """Verify that all relationships reference tables that exist in model"""
        model_table_names = {t.name for t in self.model.tables}
        
        for rel in self.model.relationships:
            self.assertIn(
                rel.from_table, model_table_names,
                f"Relationship references non-existent table: {rel.from_table}"
            )
            self.assertIn(
                rel.to_table, model_table_names,
                f"Relationship references non-existent table: {rel.to_table}"
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
