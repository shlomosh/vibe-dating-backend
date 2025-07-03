#!/usr/bin/env python3
"""
Poetry-based Lambda build script for Vibe Backend

This script builds Lambda layers and function packages using Poetry for dependency management.
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

os.environ["AWS_PROFILE"] = "vibe-dating"
os.environ["AWS_REGION"] = "il-central-1"

class LambdaBuilder:
    """Builds Lambda layers and function packages using Poetry"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.lambda_dir = self.project_root / "src" / "services" / "auth" / "aws_lambdas"
        self.build_dir = self.project_root / "build" / "lambda"
        self.layer_dir = self.build_dir / "layer"
        
    def clean_build(self):
        """Clean previous build artifacts"""
        print("• Cleaning previous build...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
    def install_lambda_dependencies(self):
        """Install Lambda dependencies using existing requirements.txt"""
        print("• Installing Lambda dependencies...")
        
        # Create layer directory structure
        self.layer_dir.mkdir(parents=True, exist_ok=True)
        python_dir = self.layer_dir / "python"
        python_dir.mkdir(exist_ok=True)
        
        # Use existing requirements.txt from aws_lambdas directory
        requirements_file = self.lambda_dir / "requirements.txt"
        
        if not requirements_file.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
        
        # Install dependencies to the layer directory
        cmd = [
            "pip", "install",
            "-r", str(requirements_file),
            "-t", str(python_dir)
        ]
        
        subprocess.run(cmd, check=True)
        
    def copy_lambda_code(self):
        """Copy Lambda function code to build directory"""
        print("• Copying Lambda function code...")
        
        # Copy shared utilities
        shutil.copytree(
            self.lambda_dir / "core",
            self.build_dir / "core"
        )
        
        # Copy function directories
        for func_dir in ["telegram_auth", "jwt_authorizer"]:
            src_dir = self.lambda_dir / func_dir
            dst_dir = self.build_dir / func_dir
            if src_dir.exists():
                shutil.copytree(src_dir, dst_dir)
                
        # Copy test directory
        test_src = self.lambda_dir / "test"
        test_dst = self.build_dir / "test"
        if test_src.exists():
            shutil.copytree(test_src, test_dst)
            
    def create_lambda_layer(self):
        """Create Lambda layer package"""
        print("• Creating Lambda layer package...")
        
        layer_zip = self.build_dir / "vibe_base_layer.zip"
        
        with zipfile.ZipFile(layer_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.layer_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(self.layer_dir)
                    zipf.write(file_path, arc_name)
                    
        print(f"• Lambda layer created: {layer_zip}")
        return layer_zip
        
    def create_function_package(self, function_name: str) -> Path:
        """Create Lambda function package"""
        print(f"• Creating {function_name} function package...")
        
        func_dir = self.build_dir / function_name
        if not func_dir.exists():
            raise FileNotFoundError(f"Function directory not found: {func_dir}")
            
        # Create package directory
        pkg_dir = self.build_dir / f"{function_name}_pkg"
        if pkg_dir.exists():
            shutil.rmtree(pkg_dir)
        pkg_dir.mkdir()
        
        # Copy function code
        shutil.copytree(func_dir, pkg_dir / function_name, dirs_exist_ok=True)
        
        # Copy shared utilities
        shutil.copy2(
            self.build_dir / "core" / "auth_utils.py",
            pkg_dir / "auth_utils.py"
        )
        
        # Create ZIP file
        zip_path = self.build_dir / f"{function_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(pkg_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(pkg_dir)
                    zipf.write(file_path, arc_name)
                    
        print(f"• {function_name} package created: {zip_path}")
        return zip_path
        
    def build(self):
        """Main build process"""
        print("• Starting Poetry-based Lambda build...")
        
        try:
            self.clean_build()
            self.install_lambda_dependencies()
            self.copy_lambda_code()
            
            # Create Lambda layer
            layer_zip = self.create_lambda_layer()
            
            # Create function packages
            telegram_zip = self.create_function_package("telegram_auth")
            jwt_zip = self.create_function_package("jwt_authorizer")
            
            # Show build results
            print("\n• Build Summary:")
            print(f"  Lambda Layer: {layer_zip.name} ({layer_zip.stat().st_size / 1024:.1f} KB)")
            print(f"  Telegram Auth: {telegram_zip.name} ({telegram_zip.stat().st_size / 1024:.1f} KB)")
            print(f"  JWT Authorizer: {jwt_zip.name} ({jwt_zip.stat().st_size / 1024:.1f} KB)")
            
            print("\n✅ Build completed successfully!")
            
        except Exception as e:
            print(f"❌ Build failed: {e}")
            sys.exit(1)


def build_lambda():
    """Entry point for Poetry script"""
    builder = LambdaBuilder()
    builder.build()


if __name__ == "__main__":
    build_lambda() 