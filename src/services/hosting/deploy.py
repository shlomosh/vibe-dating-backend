#!/usr/bin/env python3
"""
Deployment script for Vibe Dating App Hosting Service CloudFormation stacks.
Deploys hosting infrastructure stacks (S3, CloudFront, Route53) in the correct order.
"""

import argparse
import subprocess
import sys

import boto3

from core.config_utils import ServiceConfigUtils
from core.deploy_utils import ServiceDeployer


class HostingServiceDeployer(ServiceDeployer):
    """Deploys the Vibe Dating App hosting service infrastructure"""

    def __init__(
        self, region: str = None, environment: str = None, deployment_uuid: str = None
    ):
        """Initialize the hosting service deployer."""
        super().__init__(
            "hosting",
            cfg={},
            region=region,
            environment=environment,
            deployment_uuid=deployment_uuid,
        )

        # Get core-stack parameters from AWS CloudFormation outputs
        self.core_cfg = ServiceConfigUtils("core", region=self.region, environment=self.environment).get_stacks_outputs()
        print(f"    Parameters from core: {self.core_cfg}")

    def is_deployed(self) -> bool:
        """Check if hosting infrastructure is already deployed"""
        s3_stack_name = f"vibe-dating-hosting-s3-{self.environment}"

        try:
            # Check if S3 stack exists
            self.cf.describe_stacks(StackName=s3_stack_name)
            return True
        except self.cf.exceptions.ClientError as e:
            if "does not exist" in str(e):
                return False
            raise

    def deploy(self):
        """Deploy all hosting infrastructure stacks in the correct order."""
        # Deploy S3 stack first (without CloudFront ARN)
        s3_stack_name = f"vibe-dating-hosting-s3-{self.environment}"
        s3_stack = {
            "name": s3_stack_name,
            "template": "01-s3.yaml",
            "parameters": {
                "Environment": self.environment,
                "DeploymentUUID": self.deployment_uuid,
                "CloudFrontDistributionArn": "",  # Will be updated after CloudFront deployment
            },
        }
        self.deploy_stack(
            stack_name=s3_stack["name"],
            template_file=s3_stack["template"],
            parameters=s3_stack["parameters"],
        )

        # Fetch outputs from S3 stack
        s3_cfg = self._get_stack_outputs(s3_stack_name)

        # Deploy CloudFront stack using outputs from S3 stack
        cloudfront_stack_name = f"vibe-dating-hosting-cloudfront-{self.environment}"
        cloudfront_stack = {
            "name": cloudfront_stack_name,
            "template": "02-cloudfront.yaml",
            "parameters": {
                "Environment": self.environment,
                "AppDomainName": self.parameters["AppDomainName"],
                "AllowedOrigins": self.parameters["AllowedOrigins"],
                "FrontendBucketName": s3_cfg["FrontendBucketName"],
                "CertificateArn": "arn:aws:acm:us-east-1:555171060142:certificate/faa3b179-b4c8-426c-a9a3-c5f0536bba62",
            },
        }
        self.deploy_stack(
            stack_name=cloudfront_stack["name"],
            template_file=cloudfront_stack["template"],
            parameters=cloudfront_stack["parameters"],
        )

        # Fetch outputs from CloudFront stack
        cloudfront_cfg = self._get_stack_outputs(cloudfront_stack_name)

        # Update S3 stack with CloudFront distribution ARN
        s3_update_parameters = {
            "Environment": self.environment,
            "DeploymentUUID": self.deployment_uuid,
            "CloudFrontDistributionArn": cloudfront_cfg["CloudFrontDistributionArn"],
        }
        self.deploy_stack(
            stack_name=s3_stack_name,
            template_file="01-s3.yaml",
            parameters=s3_update_parameters,
        )

        # Deploy Route53 stack using outputs from CloudFront stack
        route53_stack = {
            "name": f"vibe-dating-hosting-route53-{self.environment}",
            "template": "03-route53.yaml",
            "parameters": {
                "Environment": self.environment,
                "AppDomainName": self.parameters["AppDomainName"],
                "CloudFrontDistributionDomainName": cloudfront_cfg["CloudFrontDistributionDomainName"],
            },
        }
        self.deploy_stack(
            stack_name=route53_stack["name"],
            template_file=route53_stack["template"],
            parameters=route53_stack["parameters"],
        )

        # Print deployment summary
        self.print_deployment_summary()

    def print_deployment_summary(self):
        """Print a summary of the deployed infrastructure"""
        print("\n" + "="*60)
        print("🎉 HOSTING SERVICE DEPLOYMENT COMPLETED")
        print("="*60)
        
        # Get stack outputs
        config = ServiceConfigUtils("hosting", region=self.region, environment=self.environment)
        stack_outputs = config.get_stacks_outputs()
        
        print(f"\n📋 Deployment Information:")
        print(f"   Environment: {self.environment}")
        print(f"   Region: {self.region}")
        print(f"   Domain: {self.parameters['AppDomainName']}")
        
        if "s3" in stack_outputs:
            s3_outputs = stack_outputs["s3"]
            print(f"\n📦 S3 Bucket:")
            print(f"   Bucket Name: {s3_outputs.get('FrontendBucketName', 'N/A')}")
            print(f"   Bucket ARN: {s3_outputs.get('FrontendBucketArn', 'N/A')}")
        
        if "cloudfront" in stack_outputs:
            cf_outputs = stack_outputs["cloudfront"]
            print(f"\n🌐 CloudFront Distribution:")
            print(f"   Distribution ID: {cf_outputs.get('CloudFrontDistributionId', 'N/A')}")
            print(f"   Distribution Domain: {cf_outputs.get('CloudFrontDistributionDomainName', 'N/A')}")
            print(f"   Distribution ARN: {cf_outputs.get('CloudFrontDistributionArn', 'N/A')}")
        
        if "route53" in stack_outputs:
            route53_outputs = stack_outputs["route53"]
            print(f"\n🔗 DNS Configuration:")
            print(f"   Frontend Domain: {route53_outputs.get('FrontendDomainName', 'N/A')}")
            print(f"   A Record: {route53_outputs.get('FrontendARecordName', 'N/A')}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Set VIBE_FRONTEND_PATH environment variable to your frontend repository path")
        print(f"   2. Run: poetry run service-build hosting")
        print(f"   3. Your frontend will be available at: https://{self.parameters['AppDomainName']}")
        
        print(f"\n📚 Documentation:")
        print(f"   - Service README: src/services/hosting/README.md")
        print(f"   - API Documentation: docs/api.md")
        
        print("="*60)

    def update(self):
        """Update existing hosting infrastructure"""
        print("🔄 Updating Hosting Service infrastructure...")
        self.deploy()

    def validate_templates(self):
        """Validate CloudFormation templates"""
        print("🔍 Validating CloudFormation templates...")
        
        required_templates = ["01-s3.yaml", "02-cloudfront.yaml", "03-route53.yaml"]
        
        for template in required_templates:
            template_path = self.template_dir / template
            if not template_path.exists():
                print(f"❌ Template not found: {template_path}")
                sys.exit(1)
            
            try:
                # Validate template using AWS CLI
                subprocess.run([
                    "aws", "cloudformation", "validate-template",
                    "--template-body", f"file://{template_path}"
                ], check=True, capture_output=True)
                print(f"✅ Template validated: {template}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Template validation failed: {template}")
                print(f"   Error: {e}")
                sys.exit(1)
        
        print("✅ All templates validated successfully")


def main(action=None):
    """Main entry point for hosting service deployment"""
    ap = argparse.ArgumentParser(
        description="Deploy Vibe Dating App Hosting Service Infrastructure"
    )
    ap.add_argument("task", default="deploy", help="task to run")
    ap.add_argument(
        "service", nargs="?", default="hosting", help="Service to run task for"
    )
    ap.add_argument(
        "--environment",
        default=None,
        choices=["dev", "staging", "prod"],
        help="Environment to deploy (override parameters.yaml)",
    )
    ap.add_argument(
        "--region", default=None, help="AWS region (override parameters.yaml)"
    )
    ap.add_argument(
        "--deployment-uuid", help="Custom deployment UUID (override parameters.yaml)"
    )
    ap.add_argument("--validate", action="store_true", help="Validate templates only")
    
    args = ap.parse_args()
    
    try:
        deployer = HostingServiceDeployer(
            region=args.region,
            environment=args.environment,
            deployment_uuid=args.deployment_uuid
        )
        
        if args.validate:
            deployer.validate_templates()
        elif action == "update" or (action is None and deployer.is_deployed()):
            deployer.update()
        elif action == "deploy" or (action is None and not deployer.is_deployed()):
            deployer.deploy()
        else:
            raise ValueError(f"Invalid action: {action}")
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 