#!/usr/bin/env python3
"""
Deployment script for Vibe Dating App Core Service CloudFormation stacks.
Deploys core infrastructure stacks (S3, DynamoDB, IAM) in the correct order.
"""

import argparse
import sys
from core.deploy_utils import ServiceDeployer


class CoreServiceDeployer(ServiceDeployer):
    """Deploys the Vibe Dating App core service infrastructure"""

    def __init__(
        self, region: str = None, environment: str = None, deployment_uuid: str = None
    ):
        """Initialize the core service deployer."""
        super().__init__("core", region, environment, deployment_uuid)

    def update(self):
        print("• Starting Core Service Lambda update...")

        try:
            # Get stack outputs to find function names
            lambda_stack_name = f"vibe-dating-core-lambda-{self.environment}"
            stack_outputs = self._get_stack_outputs(lambda_stack_name)

            if not stack_outputs:
                print(f"❌ Could not find stack outputs for {lambda_stack_name}")
                print("   Make sure the core infrastructure is deployed first")
                sys.exit(1)

            # Get bucket name for S3 updates
            s3_bucket = self.get_lambda_code_bucket_name()

            # Update Lambda functions
            updated_layers = []
        
            # Update Lambda layer
            if "CoreLayerArn" in stack_outputs:
                aws_layer_arn = stack_outputs["CoreLayerArn"]
                aws_layer_name = aws_layer_arn.split(":")[-2]
                aws_layer_version = aws_layer_arn.split(":")[-1]

                # Ask user if they want to update the layer
                update_question = input(
                    f"  Do you want to update layer {aws_layer_name}? (y/n): "
                ).lower()

                if update_question == "y":
                    print(
                        f"  Updating layer: {aws_layer_name}:{aws_layer_version}"
                    )
                    self._update_aws_layer(
                        aws_layer_name,
                        aws_layer_version,
                        s3_bucket,
                        "lambda/core_layer.zip",
                    )
                    updated_layers.append(aws_layer_name)
                else:
                    print(f"  Skipping layer update for: {aws_layer_name}")

            print(f"✅ Successfully updated {len(updated_layers)} Lambda layers:")
            for layer in updated_layers:
                print(f"   • {layer}")

        except Exception as e:
            print(f"❌ Core service update failed: {e}")
            sys.exit(1)

    def deploy(self):
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
                "parameters": {
                    "Environment": self.environment,
                },
            },
            "iam": {
                "name": f"vibe-dating-core-iam-{self.environment}",
                "template": "03-iam.yaml",
                "parameters": {
                    "Environment": self.environment,
                    "Region": self.parameters["ApiRegion"],
                    "DynamoDBTableArn": f"${{vibe-dating-core-dynamodb-{self.environment}.DynamoDBTableArn}}",
                    "DynamoDBKMSKeyArn": f"${{vibe-dating-core-dynamodb-{self.environment}.DynamoDBKMSKeyArn}}",
                    "LambdaCodeBucketArn": f"${{vibe-dating-core-s3-{self.environment}.LambdaCodeBucketArn}}",
                },
                "capabilities": ["CAPABILITY_NAMED_IAM"],
                "depends_on": ["s3", "dynamodb"],
            },
            "lambda": {
                "name": f"vibe-dating-core-lambda-{self.environment}",
                "template": "04-lambda.yaml",
                "parameters": {
                    "Environment": self.environment,
                    "Region": self.parameters["ApiRegion"],
                    "LambdaCodeBucketName": f"${{vibe-dating-core-s3-{self.environment}.LambdaCodeBucketName}}",
                },
                "depends_on": ["s3"],
            },
        }

        # Deploy stacks in order
        stack_order = ["s3", "dynamodb", "iam", "lambda"]
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
            templates=["01-s3.yaml", "02-dynamodb.yaml", "03-iam.yaml", "04-lambda.yaml"]
        )
    elif action == "deploy" or (action is None and not deployer.is_deployed()):
        deployer.deploy()
    elif action == "update" or (action is None and deployer.is_deployed()):
        deployer.update()
    else:
        raise ValueError(f"Invalid action: {action}")


if __name__ == "__main__":
    main()
