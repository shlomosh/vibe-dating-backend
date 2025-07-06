#!/usr/bin/env python3
"""
Deployment script for Vibe Dating App Auth Service CloudFormation stacks.
Deploys authentication infrastructure stacks (API Gateway, Lambda) in the correct order.
"""

import json
import argparse

from core.deploy_utils import ServiceDeployer


class AuthServiceDeployer(ServiceDeployer):
    """Deploys the Vibe Dating App authentication service infrastructure"""
    
    def __init__(self, region: str = None, environment: str = None, deployment_uuid: str = None):
        """Initialize the auth service deployer."""
        super().__init__("auth", region, environment, deployment_uuid)
        
        # Load core-stack parameters from core.json
        with open(self.project_root / "src" / "config" / "core.json") as f:
            self.parameters_from_core = json.load(f)

    def deploy_infrastructure(self):
        """Deploy all authentication infrastructure stacks in the correct order."""
        # Deploy Lambda stack first
        lambda_stack_name = f'vibe-dating-auth-lambda-{self.environment}'
        lambda_stack = {
            'name': lambda_stack_name,
            'template': '02-lambda.yaml',
            'parameters': {
                'Environment': self.environment,
                'LambdaCodeBucketName': self.parameters_from_core['vibe-dating-core-s3-dev']['LambdaCodeBucketName'],
                'LambdaExecutionRoleArn': self.parameters_from_core['vibe-dating-core-iam-dev']['LambdaExecutionRoleArn']
            }
        }
        self.deploy_stack(
            stack_name=lambda_stack['name'],
            template_file=lambda_stack['template'],
            parameters=lambda_stack['parameters']
        )
        # Fetch outputs from Lambda stack
        lambda_outputs = self._get_stack_outputs(lambda_stack_name)
        # Now deploy API Gateway stack, using outputs from Lambda stack
        apigateway_stack = {
            'name': f'vibe-dating-auth-apigateway-{self.environment}',
            'template': '01-apigateway.yaml',
            'parameters': {
                'Environment': self.environment,
                'JWTAuthorizerFunctionArn': lambda_outputs['JWTAuthorizerFunctionArn'],
                'ApiGatewayAuthorizerRoleArn': self.parameters_from_core['vibe-dating-core-iam-dev']['ApiGatewayAuthorizerRoleArn'],
                'TelegramAuthFunctionArn': lambda_outputs['TelegramAuthFunctionArn']
            }
        }
        self.deploy_stack(
            stack_name=apigateway_stack['name'],
            template_file=apigateway_stack['template'],
            parameters=apigateway_stack['parameters']
        )

def main():
    ap = argparse.ArgumentParser(description='Deploy Vibe Dating App Auth Service Infrastructure')
    ap.add_argument('--environment', default=None, choices=['dev', 'staging', 'prod'], help='Environment to deploy (overide parameters.json)')
    ap.add_argument('--region', default=None, help='AWS region (overide parameters.json)')
    ap.add_argument('--deployment-uuid', help='Custom deployment UUID (overide parameters.json)')
    args = ap.parse_args()
    
    # Create deployer
    deployer = AuthServiceDeployer(
        region=args.region,
        environment=args.environment,
        deployment_uuid=args.deployment_uuid
    )
    
    # Deploy auth infrastructure
    deployer.deploy_infrastructure()

if __name__ == '__main__':
    main() 