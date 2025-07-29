#!/usr/bin/env python3
"""
Deployment script for Vibe Dating App Hosting Service CloudFormation stacks.
Deploys hosting infrastructure stacks (S3, CloudFront, Route53) in the correct order.
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to the path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

    def get_region_from_parameters(self) -> str:
        """Get the region for the service from parameters.yaml."""
        return self.parameters["AppRegion"]

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

    def update(self):
        """Update existing hosting infrastructure"""
        raise NotImplementedError(
            "Updating hosting infrastructure is not supported by service."
        )

    def deploy(self):
        """Deploy all hosting infrastructure stacks in the correct order."""
        app_s3_bucket_name = (
            f"vibe-dating-frontend-{self.environment}-{self.deployment_uuid}"
        )

        # Deploy CloudFront stack using outputs from S3 stack
        cloudfront_stack_name = f"vibe-dating-hosting-cloudfront-{self.environment}"
        cloudfront_stack = {
            "name": cloudfront_stack_name,
            "template": "01-cloudfront.yaml",
            "parameters": {
                "Environment": self.environment,
                "Region": self.parameters["AppRegion"],
                "AppDomainName": self.parameters["AppDomainName"],
                "AppAllowedOrigins": self.parameters["AppAllowedOrigins"],
                "AppCertificateArn": self.parameters["AppCertificateArn"],
                "AppBucketName": app_s3_bucket_name,
            },
        }
        self.deploy_stack(
            stack_name=cloudfront_stack["name"],
            template_file=cloudfront_stack["template"],
            parameters=cloudfront_stack["parameters"],
        )

        # Fetch outputs from CloudFront stack
        cloudfront_cfg = self._get_stack_outputs(cloudfront_stack_name)

        # Deploy S3 stack first (without CloudFront ARN)
        s3_stack_name = f"vibe-dating-hosting-s3-{self.environment}"
        s3_stack = {
            "name": s3_stack_name,
            "template": "02-s3.yaml",
            "parameters": {
                "Environment": self.environment,
                "DeploymentUUID": self.deployment_uuid,
                "Region": self.parameters["AppRegion"],
                "AppBucketName": app_s3_bucket_name,
                "CloudFrontDistributionArn": cloudfront_cfg[
                    "CloudFrontDistributionArn"
                ],
            },
        }
        self.deploy_stack(
            stack_name=s3_stack["name"],
            template_file=s3_stack["template"],
            parameters=s3_stack["parameters"],
        )

        # Fetch outputs from S3 stack
        s3_cfg = self._get_stack_outputs(s3_stack_name)

        # Deploy Route53 stack using outputs from CloudFront stack
        route53_stack = {
            "name": f"vibe-dating-hosting-route53-{self.environment}",
            "template": "03-route53.yaml",
            "parameters": {
                "Environment": self.environment,
                "AppDomainName": self.parameters["AppDomainName"],
                "CloudFrontDistributionDomainName": cloudfront_cfg[
                    "CloudFrontDistributionDomainName"
                ],
            },
        }
        self.deploy_stack(
            stack_name=route53_stack["name"],
            template_file=route53_stack["template"],
            parameters=route53_stack["parameters"],
        )

        if False:
            # Deploy Website stack
            website_stack = {
                "name": f"vibe-dating-hosting-website-{self.environment}",
                "template": "04-website.yaml",
                "parameters": {
                    "Environment": self.environment,
                    "DeploymentUUID": self.deployment_uuid,
                    "Region": self.parameters["WebRegion"],
                    "WebDomainName": self.parameters["WebDomainName"],
                    "WebHostedZoneId": self.parameters["WebHostedZoneId"],
                },
            }
            self.deploy_stack(
                stack_name=website_stack["name"],
                template_file=website_stack["template"],
                parameters=website_stack["parameters"],
            )


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

    # Create deployer
    deployer = HostingServiceDeployer(
        region=args.region,
        environment=args.environment,
        deployment_uuid=args.deployment_uuid,
    )

    if args.validate:
        deployer.validate_templates(
            templates=["01-cloudfront.yaml", "02-s3.yaml", "03-route53.yaml"]
        )
    elif action == "update" or (action is None and deployer.is_deployed()):
        deployer.update()
    elif action == "deploy" or (action is None and not deployer.is_deployed()):
        deployer.deploy()
    else:
        raise ValueError(f"Invalid action: {action}")


if __name__ == "__main__":
    main()
