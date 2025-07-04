#!/usr/bin/env python3
"""
Build script entry points for Poetry commands.
This script provides entry points for building Lambda packages for different services.
"""

def build_auth_service():
    """Entry point for Poetry script to build auth service Lambda packages"""
    import sys
    from pathlib import Path
    
    # Add the src directory to the path so we can import from services
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Import and run the auth build script
    from services.auth.build import main as build_auth_main
    build_auth_main()


def build_lambda():
    """Legacy entry point - now builds auth service by default"""
    build_auth_service()


if __name__ == "__main__":
    # This allows running the script directly for testing
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "auth":
            build_auth_service()
        else:
            print("Usage: python build.py [auth]")
            print("Default: builds auth service")
    else:
        # Default to auth service build
        build_auth_service() 