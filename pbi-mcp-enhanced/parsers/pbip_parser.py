"""
PBIP Structure Parser
Navigates and validates Power BI Project folder structure
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PBIPStructure:
    """Represents the structure of a .pbip project"""
    root_path: Path
    has_report: bool
    has_semantic_model: bool
    report_definition_path: Optional[Path]
    model_bim_path: Optional[Path]
    model_tmdl_path: Optional[Path]
    dataset_definition_path: Optional[Path]
    errors: List[str]
    warnings: List[str]


class PBIPParser:
    """Parser for Power BI Project (.pbip) structure"""
    
    def __init__(self, pbip_path: str):
        """
        Initialize the PBIP parser
        
        Args:
            pbip_path: Path to the .pbip project directory or .pbip JSON file
        """
        pbip_path = str(pbip_path).strip()
        self.pbip_path = self._resolve_pbip_path(pbip_path)
        self.structure: Optional[PBIPStructure] = None
        
        if not self.pbip_path.exists():
            raise FileNotFoundError(f"PBIP project not found: {pbip_path}")
        
        if not self.pbip_path.is_dir():
            raise ValueError(f"PBIP path must be a directory: {self.pbip_path}")
    
    def _resolve_pbip_path(self, pbip_input: str) -> Path:
        """
        Resolve PBIP path from either .pbip JSON file or directory
        
        Args:
            pbip_input: Path to .pbip JSON file, project directory, or parent directory
            
        Returns:
            Path to the PBIP project directory
        """
        input_path = Path(pbip_input)
        
        # If input is a .pbip JSON file
        if input_path.suffix.lower() == '.pbip' and input_path.is_file():
            # Get parent directory and project name
            project_dir = input_path.parent
            project_name = input_path.stem
            
            # Try to find Report and SemanticModel folders
            # Format: {ProjectName}.Report and {ProjectName}.SemanticModel
            report_folder = project_dir / f"{project_name}.Report"
            semantic_folder = project_dir / f"{project_name}.SemanticModel"
            
            # Create a virtual PBIP structure by returning the project directory
            # We'll handle this by returning the parent, and the parse() method will
            # look for associated folders
            return project_dir
        
        # If it's a directory, check if it contains .pbip files (parent directory scenario)
        if input_path.is_dir():
            pbip_files = list(input_path.glob("*.pbip"))
            
            # If this directory contains .pbip files, use the first one
            if pbip_files:
                first_pbip = pbip_files[0]
                project_name = first_pbip.stem
                
                # Verify associated folders exist
                report_folder = input_path / f"{project_name}.Report"
                semantic_folder = input_path / f"{project_name}.SemanticModel"
                
                if report_folder.exists() or semantic_folder.exists():
                    # Return the parent directory
                    return input_path
            
            # Otherwise, return the directory as-is (assume it's a .pbip directory with semantic-model/report)
            return input_path
        
        # Return as is
        return input_path
    
    def parse(self) -> PBIPStructure:
        """
        Parse the PBIP project structure
        
        Returns:
            PBIPStructure object with paths and validation results
        """
        errors = []
        warnings = []
        
        # Try to extract project name from current directory for folder lookup
        project_name = self.pbip_path.name
        
        # Check if this directory contains .pbip files (parent directory scenario)
        pbip_files_in_dir = list(self.pbip_path.glob("*.pbip"))
        
        if pbip_files_in_dir and project_name not in [p.stem for p in pbip_files_in_dir]:
            # This looks like a parent directory with multiple projects
            # Use the first .pbip file's name as the project
            first_pbip = pbip_files_in_dir[0]
            project_name = first_pbip.stem
            search_parent = self.pbip_path
        else:
            # Normal case - use parent directory for searching associated folders
            search_parent = self.pbip_path.parent
        
        # Look for report definition in standard location
        report_def = self._find_file("report/definition.pbir")
        has_report = report_def is not None
        
        # If not found, try looking in associated .Report folder
        if not report_def:
            report_folder = search_parent / f"{project_name}.Report"
            if report_folder.exists():
                report_def_alt = report_folder / "definition.pbir"
                if report_def_alt.exists():
                    report_def = report_def_alt
                    has_report = True
        
        if not has_report:
            warnings.append("No report definition found (report/definition.pbir)")
        
        # Look for semantic model in standard location
        model_bim = self._find_file("semantic-model/model.bim")
        dataset_def = self._find_file("semantic-model/definition.pbism")
        
        # Alternative locations
        if not model_bim:
            model_bim = self._find_file("*.Dataset/model.bim")
        
        if not dataset_def:
            dataset_def = self._find_file("*.Dataset/definition.pbidataset")
        
        # If not found, try looking in associated .SemanticModel folder
        if not model_bim and not dataset_def:
            semantic_folder = search_parent / f"{project_name}.SemanticModel"
            if semantic_folder.exists():
                model_bim_alt = semantic_folder / "model.bim"
                if model_bim_alt.exists():
                    model_bim = model_bim_alt
                
                # Also check for TMDL in SemanticModel folder
                tmdl_alt = semantic_folder / "definition"
                if tmdl_alt.exists() and tmdl_alt.is_dir():
                    model_tmdl = tmdl_alt
                    has_semantic_model_tmdl = True
                
                dataset_def_alt = semantic_folder / "definition.pbism"
                if dataset_def_alt.exists():
                    dataset_def = dataset_def_alt
        
        has_semantic_model = model_bim is not None or dataset_def is not None
        
        if not has_semantic_model:
            errors.append("No semantic model found (model.bim or definition.pbism)")
        
        # Look for TMDL format (alternative to model.bim)
        model_tmdl = self._find_directory("semantic-model/definition")
        
        # Check for .SemanticModel folder (modern format)
        if not model_bim and not model_tmdl:
            semantic_folders = list(search_parent.glob(f"{project_name}.SemanticModel"))
            if semantic_folders:
                semantic_folder = semantic_folders[0]
                # Try model.bim in this folder
                model_bim_alt = semantic_folder / "model.bim"
                if model_bim_alt.exists():
                    model_bim = model_bim_alt
                # Try TMDL
                tmdl_alt = semantic_folder / "definition"
                if tmdl_alt.exists() and tmdl_alt.is_dir():
                    model_tmdl = tmdl_alt
        if not model_tmdl:
            model_tmdl = self._find_directory("*.Dataset/definition")
        
        # Validate minimum requirements
        if not has_report and not has_semantic_model:
            errors.append("Invalid PBIP structure: neither report nor semantic model found")
        
        self.structure = PBIPStructure(
            root_path=self.pbip_path,
            has_report=has_report,
            has_semantic_model=has_semantic_model,
            report_definition_path=report_def,
            model_bim_path=model_bim,
            model_tmdl_path=model_tmdl,
            dataset_definition_path=dataset_def,
            errors=errors,
            warnings=warnings
        )
        
        return self.structure
    
    def _find_file(self, pattern: str) -> Optional[Path]:
        """
        Find a file matching the pattern within the PBIP project
        
        Args:
            pattern: File pattern (can include wildcards)
        
        Returns:
            Path to the file if found, None otherwise
        """
        if "*" in pattern:
            # Use glob for wildcard patterns
            matches = list(self.pbip_path.glob(pattern))
            return matches[0] if matches else None
        else:
            # Direct path
            file_path = self.pbip_path / pattern
            return file_path if file_path.exists() else None
    
    def _find_directory(self, pattern: str) -> Optional[Path]:
        """
        Find a directory matching the pattern within the PBIP project
        
        Args:
            pattern: Directory pattern (can include wildcards)
        
        Returns:
            Path to the directory if found, None otherwise
        """
        if "*" in pattern:
            matches = list(self.pbip_path.glob(pattern))
            matches = [m for m in matches if m.is_dir()]
            return matches[0] if matches else None
        else:
            dir_path = self.pbip_path / pattern
            return dir_path if dir_path.is_dir() else None
    
    def get_structure(self) -> PBIPStructure:
        """
        Get the parsed structure (must call parse() first)
        
        Returns:
            PBIPStructure object
        """
        if self.structure is None:
            raise RuntimeError("Must call parse() before get_structure()")
        return self.structure
    
    def is_valid(self) -> bool:
        """
        Check if the PBIP structure is valid
        
        Returns:
            True if valid, False otherwise
        """
        if self.structure is None:
            return False
        return len(self.structure.errors) == 0
    
    def get_model_path(self) -> Optional[Path]:
        """
        Get the path to the model definition (either model.bim or TMDL directory)
        
        Returns:
            Path to model definition
        """
        if self.structure is None:
            return None
        
        # Prefer model.bim over TMDL
        if self.structure.model_bim_path:
            return self.structure.model_bim_path
        
        return self.structure.model_tmdl_path
    
    def list_files(self) -> List[Tuple[str, Path]]:
        """
        List all important files in the PBIP structure
        
        Returns:
            List of (description, path) tuples
        """
        if self.structure is None:
            raise RuntimeError("Must call parse() first")
        
        files = []
        
        if self.structure.report_definition_path:
            files.append(("Report Definition", self.structure.report_definition_path))
        
        if self.structure.model_bim_path:
            files.append(("Model BIM", self.structure.model_bim_path))
        
        if self.structure.model_tmdl_path:
            files.append(("Model TMDL", self.structure.model_tmdl_path))
        
        if self.structure.dataset_definition_path:
            files.append(("Dataset Definition", self.structure.dataset_definition_path))
        
        return files
    
    def __repr__(self) -> str:
        """String representation of the parser"""
        return f"PBIPParser(path={self.pbip_path}, parsed={self.structure is not None})"
