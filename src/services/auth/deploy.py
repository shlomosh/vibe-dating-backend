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
        # Define stack configurations
        stacks = {
            'apigateway': {
                'name': f'vibe-dating-auth-apigateway-{self.environment}',
                'template': '01-apigateway.yaml',
                'parameters': {
                    'Environment': self.environment,
                    'JWTAuthorizerFunctionArn': self.parameters_from_core['JWTAuthorizerFunctionArn'],
                    'ApiGatewayAuthorizerRoleArn': self.parameters_from_core['ApiGatewayAuthorizerRoleArn'],
                    'TelegramAuthFunctionArn': self.parameters_from_core['TelegramAuthFunctionArn']
                }
            },
            'lambda': {
                'name': f'vibe-dating-auth-lambda-{self.environment}',
                'template': '02-lambda.yaml',
                'parameters': {
                    'Environment': self.environment,
                    'LambdaCodeBucketName': self.parameters_from_core['LambdaCodeBucketName'],
                    'LambdaExecutionRoleArn': self.parameters_from_core['LambdaExecutionRoleArn']
                }
            },
        }
        
        # Deploy stacks in order
        stack_order = ['apigateway', 'lambda']
        self.deploy_stacks(stacks, stack_order)

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