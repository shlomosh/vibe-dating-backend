#!/usr/bin/env python3
"""
Deployment script entry points for Poetry commands.
This script provides entry points for deploying/updating services infrastructure.
"""

import argparse
from pathlib import Path
from importlib import import_module
from typing import Optional


def _execute(task: str, action: Optional[str] = None, service: Optional[str] = None):
    services_list = [
        p.parent.name
        for p in Path(__file__).parent.parent.glob(f"src/services/*/{task}.py")
    ]
    
    if service is None:
        ap = argparse.ArgumentParser(description=f"Run {task} for services")
        ap.add_argument("service", choices=services_list, help=f"Service to {task}")    
        args = ap.parse_args()
        service = args.service
    else:
        if service not in services_list:
            raise ValueError(f"Unknown service: {service}")

    print(f"Running {task} for {service} service...")
    # Add the src directory to the path so we can import from services
    src_path = Path(__file__).parent.parent / "src"
    import sys
    sys.path.insert(0, str(src_path))
    
    task_main = import_module(f"services.{service}.{task}").main
    task_main(action=action)


def build():
    _execute(task="build")


def deploy():
    _execute(task="deploy", action="deploy")


def update():
    _execute(task="deploy", action="update")


def test():
    _execute(task="test")


def main():
    ap = argparse.ArgumentParser(description="Run tasks for services")
    ap.add_argument("task", choices=["build", "deploy", "update", "test"], help="task to run")
    ap.add_argument("service", nargs="?", help="Service to run task for")
    args = ap.parse_args()

    _execute(task=args.task, service=args.service)

if __name__ == "__main__":
    main()
