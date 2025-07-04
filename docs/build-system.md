# Build System Documentation

## Overview

The Vibe Dating Backend uses a modular, service-oriented build system that creates optimized Lambda packages for AWS deployment. The build system has been reorganized to provide better separation of concerns and reusability.

## Architecture

### Core Components

- **`src/core/build_utils.py`**: Common build utilities shared across all services
- **`src/services/{service}/build.py`**: Service-specific build scripts
- **`scripts/build.py`**: Entry point script for Poetry commands

### Build Flow

1. **Entry Point**: `scripts/build.py` provides Poetry script entry points
2. **Service Build**: Each service has its own build script in `src/services/{service}/build.py`
3. **Common Utils**: All services use shared utilities from `src/core/build_utils.py`

## Usage

### Poetry Commands

```bash
# Build auth service Lambda packages
poetry run build-auth

# Legacy command (still works)
poetry run build-lambda

# Direct script execution
python -m scripts.build auth
```

### Service-Specific Builds

Each service can have its own build script that uses the common utilities:

```python
from core.build_utils import BuildUtils

class MyServiceBuilder:
    def __init__(self):
        self.build_utils = BuildUtils()
        
    def build(self):
        # Use common utilities for building
        self.build_utils.clean_build_directory()
        # ... service-specific build logic
```

## Build Artifacts

### Auth Service

The auth service build creates:

- **`vibe_base_layer.zip`**: Shared Python dependencies layer (~14.8 MB)
- **`telegram_auth.zip`**: Telegram authentication function (~4.2 KB)
- **`jwt_authorizer.zip`**: JWT authorization function (~2.2 KB)

### Build Directory Structure

```
build/lambda/
├── vibe_base_layer.zip      # Shared dependencies layer
├── telegram_auth.zip        # Telegram auth function
├── jwt_authorizer.zip       # JWT authorizer function
├── layer/                   # Layer source directory
│   └── python/             # Python dependencies
├── core/                    # Shared utilities
├── telegram_auth/           # Function source
└── jwt_authorizer/          # Function source
```

## Common Build Utilities

### BuildUtils Class

The `BuildUtils` class provides reusable functionality:

- **`clean_build_directory()`**: Clean and prepare build directory
- **`install_dependencies_to_layer()`**: Install Python dependencies to layer
- **`copy_service_code()`**: Copy service code with filtering
- **`create_zip_package()`**: Create ZIP packages from directories
- **`create_lambda_layer()`**: Create Lambda layer packages
- **`create_function_package()`**: Create function packages with additional files
- **`print_build_summary()`**: Display build results

### Example Usage

```python
from core.build_utils import BuildUtils

build_utils = BuildUtils()

# Clean build directory
build_utils.clean_build_directory()

# Install dependencies
build_utils.install_dependencies_to_layer(
    requirements_file=Path("requirements.txt"),
    layer_dir=Path("build/lambda/layer")
)

# Create packages
layer_zip = build_utils.create_lambda_layer(
    layer_dir=Path("build/lambda/layer"),
    output_path=Path("build/lambda/layer.zip")
)
```

## Adding New Services

To add a new service build:

1. **Create service build script**: `src/services/{service}/build.py`
2. **Add Poetry script**: Update `pyproject.toml` with new entry point
3. **Use common utilities**: Leverage `BuildUtils` for shared functionality

### Example Service Build Script

```python
#!/usr/bin/env python3
"""
My Service Lambda Build Script
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from core.build_utils import BuildUtils

class MyServiceBuilder:
    def __init__(self):
        self.build_utils = BuildUtils()
        self.service_dir = self.build_utils.project_root / "src" / "services" / "myservice"
        
    def build(self):
        print("• Starting My Service Lambda build...")
        
        try:
            # Use common utilities
            self.build_utils.clean_build_directory()
            # ... service-specific build logic
            
        except Exception as e:
            print(f"❌ My service build failed: {e}")
            sys.exit(1)

def main():
    builder = MyServiceBuilder()
    builder.build()

if __name__ == "__main__":
    main()
```

## Benefits

### Modularity
- Each service has its own build logic
- Common functionality is shared and reusable
- Easy to add new services

### Maintainability
- Clear separation of concerns
- Consistent build patterns across services
- Centralized common utilities

### Extensibility
- Easy to add new build features
- Service-specific customizations possible
- Backward compatibility maintained

## Migration Notes

The build system maintains backward compatibility:

- **`poetry run build-lambda`**: Still works, now builds auth service
- **`poetry run build-auth`**: New explicit auth service build command
- **Build artifacts**: Same output structure and naming
- **Dependencies**: Same requirements.txt usage 