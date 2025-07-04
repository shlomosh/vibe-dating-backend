#!/usr/bin/env python3
"""
Common deployment utilities for Vibe Dating App services.
Provides a base ServiceDeployer class with shared CloudFormation deployment functionality.
"""

import os
import boto3
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

os.environ["AWS_PROFILE"] = "vibe-dating"


class ServiceDeployer(ABC):
    """Base class for deploying Vibe Dating App service infrastructure"""
    
    def __init__(self, service_name: str, region: Optional[str] = None, 
                 environment: Optional[str] = None, deployment_uuid: Optional[str] = None):
        """Initialize the service deployer."""
        self.service_name = service_name
        
        # Get project root and template directory
        self.project_root = Path(__file__).parent.parent.parent
        self.template_dir = Path(__file__).parent.parent / "services" / service_name / "cloudformation"

        # Load parameters from parameters.json
        with open(self.project_root / "src" / "config" / "parameters.json") as f:
            self.parameters = json.load(f)

        # Override parameters if provided
        self.region = region or self.parameters["Region"]
        self.environment = environment or self.parameters["Environment"]
        self.deployment_uuid = deployment_uuid or self.parameters["DeploymentUUID"]

        # Setup AWS session
        self.cf = boto3.client('cloudformation', region_name=self.region)
        self.s3 = boto3.client('s3', region_name=self.region)
        
        self.stack_outputs = {}
        
    def check_prerequisites(self, required_templates: List[str]):
        """Check that all prerequisites are met"""
        print("Checking prerequisites...")
        
        # Check if AWS CLI is installed
        try:
            subprocess.run(["aws", "--version"], check=True, capture_output=True)
            print("  AWS CLI is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  AWS CLI is not installed. Please install AWS CLI first.")
            sys.exit(1)
            
        # Check AWS credentials
        try:
            boto3.client('sts').get_caller_identity()
            print("  AWS credentials are configured")
        except Exception as e:
            print(f"  AWS credentials not configured: {e}")
            sys.exit(1)
            
        # Check if template files exist
        for template in required_templates:
            template_path = self.template_dir / template
            if not template_path.exists():
                print(f"  Template file not found: {template_path}")
                sys.exit(1)
            print(f"  Template found: {template}")
            
        print("  All prerequisites met")
        
    def deploy_stack(self, stack_name: str, template_file: str, parameters: Dict[str, Any] = None, capabilities: list = None) -> bool:
        """Deploy a single CloudFormation stack."""
        print(f"\nDeploying stack: {stack_name}")
        
        # Read template file
        template_path = self.template_dir / template_file
        with open(template_path, 'r') as f:
            template_body = f.read()
        
        # Prepare parameters
        cf_parameters = []
        if parameters:
            for key, value in parameters.items():
                cf_parameters.append({
                    'ParameterKey': key,
                    'ParameterValue': str(value)
                })
        
        # Prepare capabilities
        if not capabilities:
            capabilities = []
        
        try:
            # Check if stack exists
            try:
                self.cf.describe_stacks(StackName=stack_name)
                stack_exists = True
                print(f"  Stack {stack_name} exists, updating...")
            except self.cf.exceptions.ClientError as e:
                if 'does not exist' in str(e):
                    stack_exists = False
                    print(f"  Creating new stack {stack_name}...")
                else:
                    raise
            
            if stack_exists:
                # Update stack
                response = self.cf.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=cf_parameters,
                    Capabilities=capabilities,
                    Tags=[
                        {'Key': 'Environment', 'Value': self.environment},
                        {'Key': 'Service', 'Value': self.service_name}
                    ]
                )
            else:
                # Create stack
                response = self.cf.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=cf_parameters,
                    Capabilities=capabilities,
                    Tags=[
                        {'Key': 'Environment', 'Value': self.environment},
                        {'Key': 'Service', 'Value': self.service_name}
                    ]
                )
            
            print(f"  Waiting for stack {stack_name} to complete...")
            self._wait_for_stack(stack_name, stack_exists)
            
            # Get stack outputs
            outputs = self._get_stack_outputs(stack_name)
            self.stack_outputs[stack_name] = outputs
            
            print(f"  Stack {stack_name} deployed successfully!")
            return True
            
        except Exception as e:
            print(f"  Failed to deploy stack {stack_name}: {str(e)}")
            return False

    def _wait_for_stack(self, stack_name: str, stack_exists: bool):
        """Wait for stack to complete."""
        waiter_name = 'stack_update_complete' if stack_exists else 'stack_create_complete'
        waiter = self.cf.get_waiter(waiter_name)
        try:
            waiter.wait(StackName=stack_name)
        except Exception as e:
            # Check if it's a no-update scenario
            if 'No updates are to be performed' in str(e):
                print(f"  No updates needed for stack {stack_name}")
                return
            raise

    def _get_stack_outputs(self, stack_name: str) -> Dict[str, str]:
        """Get stack outputs."""
        try:
            response = self.cf.describe_stacks(StackName=stack_name)
            outputs = {}
            for output in response['Stacks'][0].get('Outputs', []):
                outputs[output['OutputKey']] = output['OutputValue']
            return outputs
        except Exception:
            return {}

    def get_output_value(self, stack_name: str, output_key: str) -> Optional[str]:
        """Get a specific output value from a stack."""
        if stack_name in self.stack_outputs:
            return self.stack_outputs[stack_name].get(output_key)
        return None

    def deploy_stacks(self, stacks: Dict[str, Dict], stack_order: List[str]):
        """Deploy multiple stacks in the specified order with dependency resolution."""
        print(f"Starting {self.service_name.title()} Service Infrastructure Deployment")
        print(f"   Environment: {self.environment}")
        print(f"   Region: {self.region}")
        print(f"   Deployment UUID: {self.deployment_uuid}")
        
        # Check prerequisites
        required_templates = [stack_config['template'] for stack_config in stacks.values()]
        self.check_prerequisites(required_templates)
        
        # Deploy stacks in order
        deployed_stacks = []
        
        for stack_key in stack_order:
            stack_config = stacks[stack_key]
            
            # Check dependencies
            if 'depends_on' in stack_config:
                for dep in stack_config['depends_on']:
                    if dep not in deployed_stacks:
                        print(f"  Cannot deploy {stack_key}: dependency {dep} not deployed")
                        sys.exit(1)
            
            # Update parameters with actual values from deployed stacks
            parameters = stack_config['parameters'].copy()
            for param_key, param_value in parameters.items():
                if param_value.startswith('${') and param_value.endswith('}'):
                    # Extract stack and output from placeholder
                    placeholder = param_value[2:-1]  # Remove ${ and }
                    if 'PLACEHOLDER' not in placeholder:
                        # This is a real dependency, get the actual value
                        for deployed_stack in deployed_stacks:
                            if deployed_stack in placeholder:
                                output_key = placeholder.split('.')[-1]
                                actual_value = self.get_output_value(
                                    stacks[deployed_stack]['name'], 
                                    output_key
                                )
                                if actual_value:
                                    parameters[param_key] = actual_value
                                    break
            
            # Deploy the stack
            success = self.deploy_stack(
                stack_name=stack_config['name'],
                template_file=stack_config['template'],
                parameters=parameters,
                capabilities=stack_config.get('capabilities', [])
            )
            
            if success:
                deployed_stacks.append(stack_key)
            else:
                print(f"  Failed to deploy {stack_key}, stopping deployment")
                sys.exit(1)
        
        print(f"\nAll {self.service_name} infrastructure stacks deployed successfully!")
        print(f"   Deployed stacks: {', '.join(deployed_stacks)}")
        
        # Save final outputs
        self.save_deployment_outputs()
        
    def save_deployment_outputs(self, output_filename: str = None):
        """Save deployment outputs to a JSON file."""
        if output_filename is None:
            output_filename = f"{self.service_name}.json"
            
        # Save outputs to JSON file
        outputs = {}
        for stack_name, stack_outputs in self.stack_outputs.items():
            if stack_outputs:
                outputs[stack_name] = stack_outputs
                
        output_file = self.project_root / "src" / "config" / output_filename
        with open(output_file, "w") as f:
            json.dump(outputs, f, indent=2)

        print(f"\nDeployment Outputs: {outputs}")
        
    @abstractmethod
    def deploy_infrastructure(self):
        """Deploy the service infrastructure. Must be implemented by subclasses."""
        pass 