#!/usr/bin/env python3
"""
Parser for Power BI report pages and visualizations.
Outputs: pages.json
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class PageParser:
    def __init__(self, pbip_root: str):
        self.pbip_root = Path(pbip_root)
        self.report_dir = self.pbip_root / "OnlineBaseline.Report" / "definition"
        self.pages = []
        
    def parse(self) -> List[Dict[str, Any]]:
        """Parse all report pages"""
        pages_dir = self.report_dir / "pages"
        
        if not pages_dir.exists():
            return []
        
        # Read pages metadata
        page_order = self._get_page_order(pages_dir)
        
        # Parse each page
        for page_id in page_order:
            page_data = self._parse_page(pages_dir, page_id)
            if page_data:
                self.pages.append(page_data)
        
        return self.pages
    
    def _get_page_order(self, pages_dir: Path) -> List[str]:
        """Get page order from pages.json"""
        pages_metadata_file = pages_dir / "pages.json"
        page_order = []
        
        if pages_metadata_file.exists():
            try:
                metadata = json.loads(pages_metadata_file.read_text(encoding='utf-8'))
                page_order = metadata.get('pageOrder', [])
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Fallback: scan directories
        if not page_order:
            page_order = [d.name for d in pages_dir.iterdir() if d.is_dir() and d.name != 'pages']
        
        return page_order
    
    def _parse_page(self, pages_dir: Path, page_id: str) -> Dict[str, Any]:
        """Parse a single page"""
        page_dir = pages_dir / page_id
        
        if not page_dir.is_dir():
            return None
        
        # Get page metadata
        page_file = page_dir / "page.json"
        display_name = page_id
        
        if page_file.exists():
            try:
                page_data = json.loads(page_file.read_text(encoding='utf-8'))
                display_name = page_data.get('displayName', page_id)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Count visualizations
        visuals_dir = page_dir / "visuals"
        visuals_count = 0
        visual_ids = []
        
        if visuals_dir.exists():
            for visual_dir in visuals_dir.iterdir():
                if visual_dir.is_dir():
                    visuals_count += 1
                    visual_ids.append(visual_dir.name)
        
        return {
            'page_id': page_id,
            'display_name': display_name,
            'visuals_count': visuals_count,
            'visual_ids': visual_ids
        }


def parse_pages(pbip_root: str, output_file: str = None) -> List[Dict[str, Any]]:
    """Main function to parse pages"""
    parser = PageParser(pbip_root)
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
