#!/usr/bin/env python3
"""
Deployment script entry points for Poetry commands.
This script provides entry points for deploying core and auth infrastructure.
"""

def deploy_core_service():
    """Entry point for Poetry script to deploy core infrastructure"""
    import sys
    from pathlib import Path
    
    # Add the src directory to the path so we can import from services
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Import and run the core deployment script
    from services.core.deploy import main as deploy_core_main
    deploy_core_main()

def deploy_auth_service():
    """Entry point for Poetry script to deploy auth infrastructure"""
    import sys
    from pathlib import Path
    
    # Add the src directory to the path so we can import from services
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Import and run the auth deployment script
    from services.auth.deploy import main as deploy_auth_main
    deploy_auth_main()


if __name__ == "__main__":
    # This allows running the script directly for testing
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "core":
            deploy_core_service()
        elif sys.argv[1] == "auth":
            deploy_auth_service()
        else:
            print("Usage: python deploy.py [core|auth]")
    else:
        print("Usage: python deploy.py [core|auth]") 