"""
Definition Parser
Parses definition.pbir (report metadata) and definition.pbism (dataset metadata)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ReportMetadata:
    """Represents report metadata from definition.pbir"""
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    visual_count: int = 0
    page_count: int = 0


@dataclass
class DatasetMetadata:
    """Represents dataset metadata from definition.pbism"""
    name: Optional[str] = None
    description: Optional[str] = None
    model_id: Optional[str] = None
    compatible_with_power_bi: bool = True


class DefinitionParser:
    """Parser for definition files (pbir and pbism)"""
    
    def __init__(self, definition_path: str):
        """
        Initialize the definition parser
        
        Args:
            definition_path: Path to definition.pbir or definition.pbism file
        """
        self.definition_path = Path(definition_path)
        self.raw_data: Optional[Dict] = None
        self.file_type: Optional[str] = None  # 'report' or 'dataset'
        
        if not self.definition_path.exists():
            raise FileNotFoundError(f"Definition file not found: {definition_path}")
        
        # Determine file type
        if self.definition_path.name == 'definition.pbir':
            self.file_type = 'report'
        elif self.definition_path.name in ['definition.pbism', 'definition.pbidataset']:
            self.file_type = 'dataset'
        else:
            raise ValueError(f"Unknown definition file type: {self.definition_path.name}")
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the definition file
        
        Returns:
            Parsed metadata (ReportMetadata or DatasetMetadata)
        """
        # Load JSON
        with open(self.definition_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        
        if self.file_type == 'report':
            return self._parse_report()
        else:
            return self._parse_dataset()
    
    def _parse_report(self) -> ReportMetadata:
        """Parse report definition (definition.pbir)"""
        if self.raw_data is None:
            raise RuntimeError("Must load data before parsing")
        
        # Count visuals and pages
        config = self.raw_data.get('config', {})
        visual_count = 0
        page_count = 0
        
        if isinstance(config, str):
            # Config might be a JSON string
            try:
                config = json.loads(config)
            except:
                config = {}
        
        sections = config.get('sections', [])
        if sections:
            page_count = len(sections)
            for section in sections:
                visual_containers = section.get('visualContainers', [])
                visual_count += len(visual_containers)
        
        metadata = ReportMetadata(
            name=self.raw_data.get('name'),
            version=self.raw_data.get('version'),
            description=self.raw_data.get('description'),
            config=config,
            resources=self.raw_data.get('resources', []),
            visual_count=visual_count,
            page_count=page_count
        )
        
        return metadata
    
    def _parse_dataset(self) -> DatasetMetadata:
        """Parse dataset definition (definition.pbism)"""
        if self.raw_data is None:
            raise RuntimeError("Must load data before parsing")
        
        metadata = DatasetMetadata(
            name=self.raw_data.get('name'),
            description=self.raw_data.get('description'),
            model_id=self.raw_data.get('modelId'),
            compatible_with_power_bi=self.raw_data.get('compatibleWithPowerBI', True)
        )
        
        return metadata
    
    def get_raw_data(self) -> Dict[str, Any]:
        """
        Get raw parsed JSON data
        
        Returns:
            Raw dictionary from JSON file
        """
        if self.raw_data is None:
            raise RuntimeError("Must call parse() first")
        return self.raw_data
    
    def is_report(self) -> bool:
        """Check if this is a report definition"""
        return self.file_type == 'report'
    
    def is_dataset(self) -> bool:
        """Check if this is a dataset definition"""
        return self.file_type == 'dataset'
    
    def __repr__(self) -> str:
        """String representation of the parser"""
        return f"DefinitionParser(path={self.definition_path}, type={self.file_type})"
