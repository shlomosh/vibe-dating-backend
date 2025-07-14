#!/usr/bin/env python3
"""
Generic configuration utilities for Vibe Dating App services.
Provides functions to retrieve CloudFormation stack outputs and configuration for any service.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import yaml

from src.core.core_utils import ServiceConstructor

os.environ["AWS_PROFILE"] = "vibe-dev"


class ServiceConfigUtils(ServiceConstructor):
    """Generic utilities for any Vibe Dating App service"""

    def __init__(self, service: str, region: str = None, environment: str = None):
        """Initialize service configuration utilities."""
        super().__init__(service, cfg={})

        # Load parameters from parameters.yaml
        with open(self.config_dir / "parameters.yaml") as f:
            self.parameters = yaml.safe_load(f)

        # Override parameters if provided
        self.region = region or self.parameters["Region"]
        self.environment = environment or self.parameters["Environment"]

        # Setup AWS CloudFormation client
        self.cf = boto3.client("cloudformation", region_name=self.region)

        # Get service template directory
        self.template_dir = (
            Path(__file__).parent.parent / "services" / service / "cloudformation"
        )

    def _get_stack_outputs(self, stack_name: str) -> Dict[str, str]:
        """
        Get outputs from a specific CloudFormation stack.

        Args:
            stack_name: Name of the CloudFormation stack

        Returns:
            Dictionary of stack outputs with output keys as keys and output values as values
        """
        try:
            response = self.cf.describe_stacks(StackName=stack_name)
            outputs = {}
            for output in response["Stacks"][0].get("Outputs", []):
                outputs[output["OutputKey"]] = output["OutputValue"]
            return outputs
        except Exception as e:
            print(f"Error getting outputs for stack {stack_name}: {e}")
            return {}

    def _discover_service_stacks(self) -> Dict[str, str]:
        """
        Discover available CloudFormation stacks for this service by reading template files.

        Returns:
            Dictionary mapping stack types to stack names
        """
        stacks = {}

        if not self.template_dir.exists():
            print(f"Warning: Template directory not found: {self.template_dir}")
            return stacks

        # Read all YAML template files
        for template_file in self.template_dir.glob("*.yaml"):
            try:
                yaml.SafeLoader.add_constructor(None, lambda loader, node: None)
                with open(template_file, "r") as f:
                    template_content = yaml.safe_load(f)

                # Extract stack type from filename (e.g., "01-lambda.yaml" -> "lambda")
                stack_type = self._extract_stack_type_from_filename(template_file.name)

                # Construct stack name based on service and environment
                stack_name = (
                    f"vibe-dating-{self.service}-{stack_type}-{self.environment}"
                )

                stacks[stack_type] = stack_name

            except Exception as e:
                print(f"Warning: Could not parse template {template_file}: {e}")
                continue

        return stacks

    def _extract_stack_type_from_filename(self, filename: str) -> str:
        """
        Extract stack type from template filename.

        Args:
            filename: Template filename (e.g., "01-lambda.yaml", "02-apigateway.yaml")

        Returns:
            Stack type (e.g., "lambda", "apigateway")
        """
        # Remove extension and prefix numbers
        name_without_ext = filename.replace(".yaml", "").replace(".yml", "")

        # Split by dash and get the last part (after the number prefix)
        parts = name_without_ext.split("-")

        # Find the part that comes after the numeric prefix
        for i, part in enumerate(parts):
            if part.isdigit():
                # Return everything after the number
                return "-".join(parts[i + 1 :])

        # If no numeric prefix found, return the whole name
        return name_without_ext

    def get_stacks_list(self) -> List[str]:
        """
        List all CloudFormation stacks for this service.

        Returns:
            List of service stack names
        """
        return list(self._discover_service_stacks())

    def get_stacks_outputs(self) -> Dict[str, Dict[str, str]]:
        """
        Get outputs from service CloudFormation stacks.

        Args:
            stack_type: Optional stack type filter (e.g., 'lambda', 'apigateway', 's3', etc.)

        Returns:
            Dictionary of stack outputs. If stack_type is specified, returns outputs for that stack only.
            If stack_type is None, returns outputs from all service stacks.
        """
        all_outputs = {}
        for stack_key, stack_name in self._discover_service_stacks().items():
            outputs = self._get_stack_outputs(stack_name)
            all_outputs[stack_key] = outputs

        return all_outputs
