#!/usr/bin/env python3
"""
Common build utilities for Lambda package creation.

This module provides shared functionality for building Lambda layers and function packages
across different services in the Vibe Dating Backend.
"""

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.core_utils import ServiceConstructor

os.environ["AWS_PROFILE"] = "vibe-dev"


class ServiceBuilder(ServiceConstructor):
    """Common utilities for building Lambda packages"""

    def __init__(self, service: str, cfg: Dict[str, Any]):
        """Initialize build utilities with project root path"""
        super().__init__(service, cfg)

    def clean_previous_builds(self):
        print("• Cleaning previous builds...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)

    def install_python_packages(
        self, aws_layer_name: str, requirements_file: Path
    ) -> Path:
        """Install dependencies to a Lambda layer directory"""
        print("• Installing Lambda dependencies...")

        pkg_dir = self.build_dir / f"{aws_layer_name}" / "python"
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # Check if requirements.json exists, otherwise fall back to requirements.txt
        requirements_json_file = requirements_file.parent / "requirements.json"
        if requirements_json_file.exists():
            print(f"• Using requirements.json: {requirements_json_file}")
            return self._install_from_requirements_json(requirements_json_file, pkg_dir)
        else:
            print(f"• Using requirements.txt: {requirements_file}")
            return self._install_from_requirements_txt(requirements_file, pkg_dir)

    def _install_from_requirements_json(self, requirements_json_file: Path, pkg_dir: Path) -> Path:
        """Install dependencies from requirements.json format"""
        if not requirements_json_file.exists():
            raise FileNotFoundError(f"Requirements JSON file not found: {requirements_json_file}")

        try:
            with open(requirements_json_file, 'r') as f:
                requirements_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {requirements_json_file}: {e}")

        print(f"• Loaded requirements for packages: {list(requirements_data.keys())}")

        # Install each package with its specific pip parameters
        for package_spec, pip_params in requirements_data.items():
            cmd = ["pip", "install", package_spec, "-t", str(pkg_dir)]
            
            if isinstance(pip_params, list) and pip_params:
                print(f"• Installing {package_spec} with parameters: {pip_params}")
                cmd.extend(pip_params)
            else:
                print(f"• Installing {package_spec}")
            
            subprocess.run(cmd, check=True)

        return pkg_dir

    def _install_from_requirements_txt(self, requirements_file: Path, pkg_dir: Path) -> Path:
        """Install dependencies from traditional requirements.txt format with pip parameters"""
        if not requirements_file.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")

        # Check for pip parameters file
        pip_params_file = requirements_file.parent / "requirements_pip_params.json"
        pip_params = {}
        if pip_params_file.exists():
            print(f"• Found pip parameters file: {pip_params_file}")
            try:
                with open(pip_params_file, 'r') as f:
                    pip_params = json.load(f)
                print(f"• Loaded pip parameters for packages: {list(pip_params.keys())}")
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Invalid JSON in {pip_params_file}: {e}")
                pip_params = {}

        # Read requirements file to get package names
        package_names = []
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (remove version specifiers)
                        package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].split('!=')[0].split('>')[0].split('<')[0].strip()
                        package_names.append(package_name)
        except Exception as e:
            print(f"⚠️  Warning: Could not parse requirements file: {e}")

        # Install dependencies to the layer directory
        cmd = ["pip", "install", "-r", str(requirements_file), "-t", str(pkg_dir)]

        # Add pip parameters for specific packages if specified
        for package_name in package_names:
            if package_name in pip_params:
                package_params = pip_params[package_name]
                if isinstance(package_params, list):
                    print(f"• Adding pip parameters for {package_name}: {package_params}")
                    cmd.extend(package_params)
                else:
                    print(f"⚠️  Warning: Invalid pip parameters for {package_name}, expected list")

        subprocess.run(cmd, check=True)
        return pkg_dir

    def copy_lambda_files(
        self,
        src_path: Path,
        dst_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> None:
        """Copy service code to build directory with optional filtering"""
        print(f"• Copying code from {src_path} to {dst_path}...")

        if include_patterns is None:
            include_patterns = ["*"]
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", "*.pyc", ".pytest_cache", "test"]

        def should_copy(path: Path) -> bool:
            """Check if a path should be copied based on patterns"""
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

        if src_path.is_file():
            if should_copy(src_path):
                dst_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
        else:
            copy_directory(src_path, dst_path)

    def create_zip_package(
        self, source_dir: Path, output_path: Path, base_path: Optional[Path] = None
    ) -> Path:
        """Create a ZIP package from a directory"""
        print(f"• Creating ZIP package: {output_path.name}")

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
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

    def create_aws_layer_package(self, aws_layer: Dict[str, Any]) -> Path:
        """Create a Lambda layer package"""
        pkg_file = self.build_dir / f"{aws_layer['name']}.zip"
        pkg_dir = self.build_dir / aws_layer["name"]
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # Install python packages
        self.install_python_packages(
            aws_layer_name=aws_layer["name"],
            requirements_file=self.service_dir
            / "aws_lambdas"
            / aws_layer["requirements"],
        )

        # Create zip package
        return self.create_zip_package(pkg_dir, pkg_file)

    def create_aws_lambda_package(self, aws_lambda: Dict[str, Any]) -> Path:
        """Create a Lambda function package"""
        pkg_file = self.build_dir / f"{aws_lambda['name']}.zip"
        pkg_dir = self.build_dir / aws_lambda["name"]
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # Copy function code
        self.copy_lambda_files(
            src_path=self.service_dir / "aws_lambdas" / aws_lambda["name"],
            dst_path=pkg_dir,
            include_patterns=aws_lambda.get("include_patterns", None),
            exclude_patterns=aws_lambda.get("exclude_patterns", None),
        )

        # Copy extra files
        for extra_file in aws_lambda.get("extra_files", []):
            extra_file_path = Path(extra_file).parent
            for drop_prefix in aws_lambda.get("drop_prefixes", []):
                try:
                    extra_file_path = extra_file_path.relative_to(Path(drop_prefix))
                    break
                except ValueError:
                    continue
            self.copy_lambda_files(
                src_path=self.project_dir / extra_file,
                dst_path=pkg_dir / extra_file_path,
            )

        # Create zip package
        return self.create_zip_package(pkg_dir, pkg_file)

    def print_build_summary(self, packages: List[Path]) -> None:
        """Print a summary of created packages"""
        print("\n• Build Summary:")
        for package in packages:
            size_kb = package.stat().st_size / 1024
            print(f"  {package.name}: {size_kb:.1f} KB")
        print("\n✅ Build completed successfully!")

    def upload(self, src_file: Path):
        """Upload Lambda ZIP file to S3 bucket"""
        dst_file = f"s3://{self.get_lambda_code_bucket_name()}/lambda/{src_file.name}"
        print(f"Uploading {src_file} to {dst_file}")
        subprocess.run(["aws", "s3", "cp", str(src_file), str(dst_file)], check=True)

    def build(self, upload_to_s3: bool = True):
        """Main build process for service

        Args:
            upload_to_s3: Whether to upload packages to S3
        """
        print("• Starting Service Lambda build...")

        # Clean and prepare build directory
        self.clean_previous_builds()

        packages = []

        # Build layers
        for aws_layer in self.cfg["aws_layers"]:
            package_file = self.create_aws_layer_package(aws_layer)
            packages.append(package_file)
            if upload_to_s3:
                self.upload(package_file)

        # Build functions
        for aws_lambda in self.cfg["aws_lambdas"]:
            # Create function package
            package_file = self.create_aws_lambda_package(aws_lambda)
            packages.append(package_file)
            if upload_to_s3:
                self.upload(package_file)

        # Print build summary
        self.print_build_summary(packages)
