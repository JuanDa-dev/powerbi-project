"""
Parser for Power BI report pages and visualizations.
Outputs: pages.json
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class PageParser:
    def __init__(self, pbip_root: str, project_name: str = None):
        self.pbip_root = Path(pbip_root)
        self.project_name = project_name  # e.g., "AmericasConsolidatedBalanceSheet" or "OnlineBaseline"
        # Auto-detect the .Report folder (flexible for any project name)
        self.report_dir = self._find_report_dir()
        self.pages = []
    
    def _find_report_dir(self) -> Path:
        """Auto-detect the Report directory for the specific project"""
        # First, check if pbip_root itself is a .Report folder
        if self.pbip_root.name.endswith(".Report"):
            return self.pbip_root / "definition"
        
        # If pbip_root is a parent, look for matching .Report folder
        if self.project_name:
            # Look for .Report folder that matches the project name
            matching_report = self.pbip_root / f"{self.project_name}.Report"
            if matching_report.is_dir():
                return matching_report / "definition"
        
        # Fallback: search all .Report folders (but now with proper matching attempt first)
        for item in self.pbip_root.iterdir():
            if item.is_dir() and item.name.endswith(".Report"):
                # If project_name is provided, prioritize exact matches
                if self.project_name:
                    if item.name == f"{self.project_name}.Report":
                        return item / "definition"
                else:
                    # No project name provided, return first .Report found
                    return item / "definition"
        
        # Fallback: return default path but it won't exist
        return self.pbip_root / "Report" / "definition"
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse all report pages"""
        if not self.report_dir.exists():
            return []
        
        pages_dir = self.report_dir / "pages"
        
        if not pages_dir.exists():
            return []
        
        # Read pages metadata
        page_order = self._get_page_order(pages_dir)
        
        if not page_order:
            return []
        
        # Parse each page
        for page_id in page_order:
            page_data = self._parse_page(pages_dir, page_id)
            if page_data:
                self.pages.append(page_data)
        
        return self.pages
    
    def _get_page_order(self, pages_dir: Path) -> List[str]:
        """Get page order from pages.json"""
        page_order = []
        pages_metadata_file = pages_dir / "pages.json"
        
        if pages_metadata_file.exists():
            try:
                metadata = json.loads(pages_metadata_file.read_text(encoding='utf-8'))
                
                # Try to get pageOrder from metadata
                if isinstance(metadata, dict) and 'pageOrder' in metadata:
                    page_order = metadata.get('pageOrder', [])
                # If metadata is a list, use it directly
                elif isinstance(metadata, list):
                    page_order = [item.get('id') or item.get('name') for item in metadata if isinstance(item, dict)]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        # Fallback: scan directories for page folders (exclude pages.json)
        if not page_order:
            page_order = [
                d.name for d in pages_dir.iterdir() 
                if d.is_dir() and d.name not in ['pages', 'bookmarks']
            ]
        
        return sorted(page_order)  # Sort for consistency
    
    def _parse_page(self, pages_dir: Path, page_id: str) -> Dict[str, Any]:
        """Parse a single page"""
        page_dir = pages_dir / page_id
        
        if not page_dir.is_dir():
            return None
        
        # Get page metadata
        display_name = page_id
        page_metadata = {}
        
        # Try to read page.json for display name
        page_file = page_dir / "page.json"
        if page_file.exists():
            try:
                page_data = json.loads(page_file.read_text(encoding='utf-8'))
                display_name = page_data.get('displayName', page_id)
                page_metadata = page_data
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Parse visualizations
        visuals_dir = page_dir / "visuals"
        visuals_count = 0
        visual_ids = []
        visuals = []
        charts = []
        
        if visuals_dir.exists():
            for visual_dir in visuals_dir.iterdir():
                if visual_dir.is_dir() and visual_dir.name != "visuals":
                    visuals_count += 1
                    visual_ids.append(visual_dir.name)
                    
                    # Parse detailed visual info
                    visual_info = self._parse_visual(visual_dir)
                    if visual_info:
                        visuals.append(visual_info)
                        
                        # Collect charts separately
                        if visual_info.get('category') == 'CHART':
                            charts.append(visual_info)
        
        return {
            'page_id': page_id,
            'display_name': display_name,
            'visuals_count': visuals_count,
            'visual_ids': visual_ids,
            'visuals': visuals,
            'charts': charts,
            'chart_count': len(charts)
        }
    
    def _parse_visual(self, visual_dir: Path) -> Dict[str, Any]:
        """Parse a single visual and extract type, category, and info"""
        visual_file = visual_dir / "visual.json"
        
        if not visual_file.exists():
            return None
        
        try:
            visual_data = json.loads(visual_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, KeyError):
            return None
        
        visual_id = visual_dir.name
        visual_type = visual_data.get('visual', {}).get('visualType', 'unknown')
        
        # Categorize visual
        category = self._categorize_visual(visual_type)
        
        # Extract descriptive info
        visual_info = {
            'visual_id': visual_id,
            'visual_type': visual_type,
            'category': category,
        }
        
        # Extract fields/measures for descriptive name
        if category == 'CHART':
            fields = self._extract_chart_fields(visual_data)
            visual_info['fields'] = fields
            visual_info['display_name'] = self._generate_visual_name(visual_type, fields)
        elif category == 'TABLE':
            fields = self._extract_table_fields(visual_data)
            visual_info['fields'] = fields
            visual_info['display_name'] = f"{visual_type.title()} of {fields[0] if fields else 'Data'}"
        else:
            visual_info['display_name'] = visual_type.title()
        
        return visual_info
    
    def _categorize_visual(self, visual_type: str) -> str:
        """Categorize visual by type"""
        chart_types = [
            'columnChart', 'lineChart', 'areaChart', 'barChart', 
            'scatterChart', 'bubbleChart', 'donutChart', 'pieChart',
            'waterfallChart', 'ribbonChart', 'gaugeChart', 'KPI',
            'lineClusteredColumnComboChart', 'lineStackedColumnComboChart',
            'columnClusteredLineChart', 'columnStackedLineChart',
            'comboChart', 'clusteredBarChart', 'stackedBarChart',
            'clusteredColumnChart', 'stackedColumnChart', 'stackedAreaChart',
            'clusteredAreaChart', 'funnelChart', 'treemapChart',
            'radialGaugeChart', 'smallMultiple'
        ]
        
        table_types = ['table', 'pivotTable', 'matrix']
        slicer_types = ['slicer', 'ChicletSlicer1448559807354', 'timeSlicer']
        button_types = ['actionButton', 'button']
        text_types = ['textbox', 'shape']
        card_types = ['cardVisual', 'card', 'multiRowCard', 'KPI']
        
        if visual_type in chart_types:
            return 'CHART'
        elif visual_type in table_types:
            return 'TABLE'
        elif visual_type in slicer_types:
            return 'SLICER'
        elif visual_type in button_types:
            return 'BUTTON'
        elif visual_type in text_types:
            return 'TEXT'
        elif visual_type in card_types:
            return 'CARD'
        else:
            return 'OTHER'
    
    def _extract_chart_fields(self, visual_data: Dict) -> List[str]:
        """Extract measure/dimension names from chart"""
        fields = []
        try:
            query = visual_data.get('visual', {}).get('query', {})
            query_state = query.get('queryState', {})
            
            # Get values (measures)
            for item in query_state.get('Values', {}).get('projections', []):
                nq_ref = item.get('nativeQueryRef', '')
                if nq_ref:
                    fields.append(nq_ref)
            
            # Get categories (dimensions)
            for section in ['Rows', 'Columns']:
                for item in query_state.get(section, {}).get('projections', []):
                    nq_ref = item.get('nativeQueryRef', '')
                    if nq_ref and nq_ref not in fields:
                        fields.append(nq_ref)
        except (KeyError, TypeError):
            pass
        
        return fields[:3]  # Limit to 3 fields for display
    
    def _extract_table_fields(self, visual_data: Dict) -> List[str]:
        """Extract field names from table"""
        fields = []
        try:
            query = visual_data.get('visual', {}).get('query', {})
            query_state = query.get('queryState', {})
            
            for section in ['Rows', 'Columns', 'Values']:
                for item in query_state.get(section, {}).get('projections', []):
                    nq_ref = item.get('nativeQueryRef', '')
                    if nq_ref and nq_ref not in fields:
                        fields.append(nq_ref)
        except (KeyError, TypeError):
            pass
        
        return fields[:3]
    
    def _generate_visual_name(self, visual_type: str, fields: List[str]) -> str:
        """Generate descriptive name for visual"""
        type_labels = {
            'columnChart': 'Column Chart',
            'lineChart': 'Line Chart',
            'areaChart': 'Area Chart',
            'barChart': 'Bar Chart',
            'waterfallChart': 'Waterfall Chart',
            'scatterChart': 'Scatter Plot',
            'bubbleChart': 'Bubble Chart',
            'pieChart': 'Pie Chart',
            'donutChart': 'Donut Chart',
            'ribbonChart': 'Ribbon Chart',
            'gaugeChart': 'Gauge'
        }
        
        base_name = type_labels.get(visual_type, visual_type.title())
        
        if fields:
            field_str = ', '.join(fields[:2])
            return f"{base_name}: {field_str}"
        
        return base_name


def parse_pages(pbip_root: str, output_file: str = None, project_name: str = None) -> List[Dict[str, Any]]:
    """Main function to parse pages"""
    parser = PageParser(pbip_root, project_name)
    
    # Debug: show report directory detection
    if not parser.report_dir.exists():
        print(f"  [WARN] Report directory not found: {parser.report_dir}")
        return []
    
    pages = parser.parse()
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pages, f, indent=2, ensure_ascii=False)
    
    return pages


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_pages.py <pbip_root> [output_file]")
        sys.exit(1)
    
    pbip_root = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "pages.json"
    
    pages = parse_pages(pbip_root, output_file)
    print(f"✓ Parsed {len(pages)} pages")