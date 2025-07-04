#!/usr/bin/env python3
"""
Common build utilities for Lambda package creation.

This module provides shared functionality for building Lambda layers and function packages
across different services in the Vibe Dating Backend.
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import List, Optional

os.environ["AWS_PROFILE"] = "vibe-dating"


class ServiceBuilder:
    """Common utilities for building Lambda packages"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize build utilities with project root path"""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.build_dir = self.project_root / "build" / "lambda"
        
    def clean_build_directory(self, build_dir: Optional[Path] = None) -> Path:
        """Clean and create build directory"""
        if build_dir is None:
            build_dir = self.build_dir
            
        print("• Cleaning previous build...")
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)
        return build_dir
        
    def install_dependencies_to_layer(
        self, 
        requirements_file: Path, 
        layer_dir: Path
    ) -> Path:
        """Install dependencies to a Lambda layer directory"""
        print("• Installing Lambda dependencies...")
        
        # Create layer directory structure
        layer_dir.mkdir(parents=True, exist_ok=True)
        python_dir = layer_dir / "python"
        python_dir.mkdir(exist_ok=True)
        
        if not requirements_file.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
        
        # Install dependencies to the layer directory
        cmd = [
            "pip", "install",
            "-r", str(requirements_file),
            "-t", str(python_dir)
        ]
        
        subprocess.run(cmd, check=True)
        return python_dir
        
    def copy_service_code(
        self, 
        source_dir: Path, 
        build_dir: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> None:
        """Copy service code to build directory with optional filtering"""
        print("• Copying service code...")
        
        if include_patterns is None:
            include_patterns = ["*"]
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", "*.pyc", ".pytest_cache"]
            
        def should_copy(path: Path) -> bool:
            """Check if a path should be copied based on patterns"""
            path_str = str(path)
            
            # Check include patterns
            if not any(path.match(pattern) for pattern in include_patterns):
                return False
                
            # Check exclude patterns
            if any(path.match(pattern) for pattern in exclude_patterns):
                return False
                
            return True
        
        def copy_directory(src: Path, dst: Path):
            """Recursively copy directory with filtering"""
            dst.mkdir(parents=True, exist_ok=True)
            
            for item in src.iterdir():
                if item.is_file() and should_copy(item):
                    shutil.copy2(item, dst / item.name)
                elif item.is_dir() and should_copy(item):
                    copy_directory(item, dst / item.name)
        
        if source_dir.is_file():
            if should_copy(source_dir):
                shutil.copy2(source_dir, build_dir / source_dir.name)
        else:
            copy_directory(source_dir, build_dir)
            
    def create_zip_package(
        self, 
        source_dir: Path, 
        output_path: Path,
        base_path: Optional[Path] = None
    ) -> Path:
        """Create a ZIP package from a directory"""
        print(f"• Creating ZIP package: {output_path.name}")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    
                    if base_path:
                        arc_name = file_path.relative_to(base_path)
                    else:
                        arc_name = file_path.relative_to(source_dir)
                        
                    zipf.write(file_path, arc_name)
                    
        size_kb = output_path.stat().st_size / 1024
        print(f"• Package created: {output_path.name} ({size_kb:.1f} KB)")
        return output_path
        
    def create_lambda_layer(
        self, 
        layer_dir: Path, 
        output_path: Path
    ) -> Path:
        """Create a Lambda layer package"""
        return self.create_zip_package(layer_dir, output_path)
        
    def create_function_package(
        self, 
        function_dir: Path, 
        output_path: Path,
        additional_files: Optional[List[Path]] = None
    ) -> Path:
        """Create a Lambda function package with optional additional files"""
        # Create temporary package directory
        pkg_dir = output_path.parent / f"{output_path.stem}_temp"
        if pkg_dir.exists():
            shutil.rmtree(pkg_dir)
        pkg_dir.mkdir()
        
        try:
            # Copy function code
            if function_dir.is_dir():
                shutil.copytree(function_dir, pkg_dir / function_dir.name, dirs_exist_ok=True)
            else:
                shutil.copy2(function_dir, pkg_dir / function_dir.name)
            
            # Copy additional files
            if additional_files:
                for file_path in additional_files:
                    if file_path.exists():
                        shutil.copy2(file_path, pkg_dir / file_path.name)
            
            # Create ZIP package
            return self.create_zip_package(pkg_dir, output_path)
            
        finally:
            # Clean up temporary directory
            if pkg_dir.exists():
                shutil.rmtree(pkg_dir)
                
    def get_package_size(self, package_path: Path) -> float:
        """Get package size in KB"""
        return package_path.stat().st_size / 1024
        
    def print_build_summary(self, packages: List[Path]) -> None:
        """Print a summary of created packages"""
        print("\n• Build Summary:")
        for package in packages:
            size_kb = self.get_package_size(package)
            print(f"  {package.name}: {size_kb:.1f} KB")
        print("\n✅ Build completed successfully!") 