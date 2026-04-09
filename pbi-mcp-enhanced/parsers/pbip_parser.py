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
            pbip_path: Path to the .pbip project file or directory
        """
        self.pbip_path = Path(pbip_path)
        self.structure: Optional[PBIPStructure] = None
        self._is_pbip_file = False
        
        if not self.pbip_path.exists():
            raise FileNotFoundError(f"PBIP project not found: {pbip_path}")
        
        if self.pbip_path.is_file():
            if self.pbip_path.suffix.lower() != '.pbip':
                raise ValueError(f"File must have .pbip extension: {pbip_path}")
            self._is_pbip_file = True
        elif not self.pbip_path.is_dir():
            raise ValueError(f"PBIP path must be a .pbip file or directory: {pbip_path}")
    
    def parse(self) -> PBIPStructure:
        """
        Parse the PBIP project structure
        
        Returns:
            PBIPStructure object with paths and validation results
        """
        errors = []
        warnings = []

        # When given a .pbip file, the Report and SemanticModel folders are
        # siblings of the file named "{stem}.Report" and "{stem}.SemanticModel".
        if self._is_pbip_file:
            project_root = self.pbip_path.parent
            stem = self.pbip_path.stem
            report_def = self._check_path(project_root / f"{stem}.Report" / "definition.pbir")
            model_bim = self._check_path(project_root / f"{stem}.SemanticModel" / "model.bim")
            dataset_def = self._check_path(project_root / f"{stem}.SemanticModel" / "definition.pbism")
            model_tmdl_candidate = project_root / f"{stem}.SemanticModel" / "definition"
            model_tmdl = model_tmdl_candidate if model_tmdl_candidate.is_dir() else None
            # Fallback: legacy folder names without stem prefix
            if not report_def:
                report_def = self._check_path(project_root / "report" / "definition.pbir")
            if not model_bim:
                model_bim = self._check_path(project_root / "semantic-model" / "model.bim")
            if not dataset_def:
                dataset_def = self._check_path(project_root / "semantic-model" / "definition.pbism")
            if not model_tmdl:
                tmdl_legacy = project_root / "semantic-model" / "definition"
                model_tmdl = tmdl_legacy if tmdl_legacy.is_dir() else None
            root_path = project_root
        else:
            # Directory-based project: look inside the directory first, then check
            # for a sibling "{stem}.SemanticModel" folder (modern Power BI format).
            report_def = self._find_file("report/definition.pbir")
            model_bim = self._find_file("semantic-model/model.bim")
            dataset_def = self._find_file("semantic-model/definition.pbism")

            # Alternative locations
            if not model_bim:
                model_bim = self._find_file("*.Dataset/model.bim")
            if not dataset_def:
                dataset_def = self._find_file("*.Dataset/definition.pbidataset")

            # Look for TMDL format (alternative to model.bim)
            model_tmdl = self._find_directory("semantic-model/definition")

            # Check for sibling .SemanticModel folder (e.g. "Name.SemanticModel" next
            # to a "Name.pbip" directory) — used in the modern Power BI project layout.
            if not model_bim and not model_tmdl:
                semantic_folders = list(self.pbip_path.parent.glob(f"{self.pbip_path.stem}.SemanticModel"))
                if semantic_folders:
                    semantic_folder = semantic_folders[0]
                    model_bim_alt = semantic_folder / "model.bim"
                    if model_bim_alt.exists():
                        model_bim = model_bim_alt
                    tmdl_alt = semantic_folder / "definition"
                    if tmdl_alt.exists() and tmdl_alt.is_dir():
                        model_tmdl = tmdl_alt
            if not model_tmdl:
                model_tmdl = self._find_directory("*.Dataset/definition")

            root_path = self.pbip_path

        has_report = report_def is not None
        has_semantic_model = model_bim is not None or dataset_def is not None

        if not has_report:
            warnings.append("No report definition found (report/definition.pbir)")

        if not has_semantic_model:
            errors.append("No semantic model found (model.bim or definition.pbism)")

        # Validate minimum requirements
        if not has_report and not has_semantic_model:
            errors.append("Invalid PBIP structure: neither report nor semantic model found")

        self.structure = PBIPStructure(
            root_path=root_path,
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
    
    def _check_path(self, path: Path) -> Optional[Path]:
        """Return path if it exists as a file, otherwise None"""
        return path if path.is_file() else None

    def _find_file(self, pattern: str) -> Optional[Path]:
        """
        Find a file matching the pattern within the PBIP project directory
        
        Args:
            pattern: File pattern (can include wildcards)
        
        Returns:
            Path to the file if found, None otherwise
        """
        base = self.pbip_path if self.pbip_path.is_dir() else self.pbip_path.parent
        if "*" in pattern:
            # Use glob for wildcard patterns
            matches = list(base.glob(pattern))
            return matches[0] if matches else None
        else:
            # Direct path
            file_path = base / pattern
            return file_path if file_path.exists() else None
    
    def _find_directory(self, pattern: str) -> Optional[Path]:
        """
        Find a directory matching the pattern within the PBIP project
        
        Args:
            pattern: Directory pattern (can include wildcards)
        
        Returns:
            Path to the directory if found, None otherwise
        """
        base = self.pbip_path if self.pbip_path.is_dir() else self.pbip_path.parent
        if "*" in pattern:
            matches = list(base.glob(pattern))
            matches = [m for m in matches if m.is_dir()]
            return matches[0] if matches else None
        else:
            dir_path = base / pattern
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
