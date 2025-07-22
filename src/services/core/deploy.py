#!/usr/bin/env python3
"""
Deployment script for Vibe Dating App Core Service CloudFormation stacks.
Deploys core infrastructure stacks (S3, DynamoDB, IAM) in the correct order.
"""

import argparse

from core.deploy_utils import ServiceDeployer


class CoreServiceDeployer(ServiceDeployer):
    """Deploys the Vibe Dating App core service infrastructure"""

    def __init__(
        self, region: str = None, environment: str = None, deployment_uuid: str = None
    ):
        """Initialize the core service deployer."""
        super().__init__("core", region, environment, deployment_uuid)

    def update(self):
        """Update existing hosting infrastructure"""
        raise NotImplementedError(
            "Updating hosting infrastructure is not supported by service."
        )

    def deploy(self):
        """Deploy all core infrastructure stacks in the correct order."""
        # Define stack configurations
        stacks = {
            "s3": {
                "name": f"vibe-dating-core-s3-{self.environment}",
                "template": "01-s3.yaml",
                "parameters": {
                    "Environment": self.environment,
                    "DeploymentUUID": self.deployment_uuid,
                },
            },
            "dynamodb": {
                "name": f"vibe-dating-core-dynamodb-{self.environment}",
                "template": "02-dynamodb.yaml",
                "parameters": {"Environment": self.environment},
            },
            "iam": {
                "name": f"vibe-dating-core-iam-{self.environment}",
                "template": "03-iam.yaml",
                "parameters": {
                    "Environment": self.environment,
                    "DynamoDBTableArn": f"${{vibe-dating-core-dynamodb-{self.environment}.DynamoDBTableArn}}",
                    "DynamoDBKMSKeyArn": f"${{vibe-dating-core-dynamodb-{self.environment}.DynamoDBKMSKeyArn}}",
                    "LambdaCodeBucketArn": f"${{vibe-dating-core-s3-{self.environment}.LambdaCodeBucketArn}}",
                },
                "capabilities": ["CAPABILITY_NAMED_IAM"],
                "depends_on": ["s3", "dynamodb"],
            },
        }

        # Deploy stacks in order
        stack_order = ["s3", "dynamodb", "iam"]
        self.deploy_stacks(stacks, stack_order)


def main(action=None):
    ap = argparse.ArgumentParser(
        description="Deploy Vibe Dating App Core Service Infrastructure"
    )
    ap.add_argument("task", default="deploy", help="task to run")
    ap.add_argument(
        "service", nargs="?", default="core", help="Service to run task for"
    )
    ap.add_argument(
        "--environment",
        default=None,
        choices=["dev", "staging", "prod"],
        help="Environment to deploy (overide parameters.yaml)",
    )
    ap.add_argument(
        "--region", default=None, help="AWS region (overide parameters.yaml)"
    )
    ap.add_argument(
        "--deployment-uuid", help="Custom deployment UUID (overide parameters.yaml)"
    )
    ap.add_argument("--validate", action="store_true", help="Validate templates only")
    args = ap.parse_args()

    # Create deployer
    deployer = CoreServiceDeployer(
        region=args.region,
        environment=args.environment,
        deployment_uuid=args.deployment_uuid,
    )

    if args.validate:
        deployer.validate_templates(
            templates=["01-s3.yaml", "02-dynamodb.yaml", "03-iam.yaml"]
        )
    elif action == "deploy" or (action is None and not deployer.is_deployed()):
        deployer.deploy()
    elif action == "update" or (action is None and deployer.is_deployed()):
        deployer.update()
    else:
        raise ValueError(f"Invalid action: {action}")


if __name__ == "__main__":
    main()
