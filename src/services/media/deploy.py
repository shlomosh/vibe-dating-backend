#!/usr/bin/env python3
"""
Deployment script for Vibe Dating App Media Service CloudFormation stacks.
Deploys media infrastructure stacks (S3, CloudFront, Lambda, API Gateway) in the correct order.
If infrastructure already exists, updates Lambda function code only.
"""

import argparse
import sys

import boto3

from core.config_utils import ServiceConfigUtils
from core.deploy_utils import ServiceDeployer


class MediaServiceDeployer(ServiceDeployer):
    """Deploys the Vibe Dating App media service infrastructure"""

    def __init__(
        self, region: str = None, environment: str = None, deployment_uuid: str = None
    ):
        """Initialize the media service deployer."""
        super().__init__(
            "media",
            cfg={},
            region=region,
            environment=environment,
            deployment_uuid=deployment_uuid,
        )

        # Get core-stack parameters from AWS CloudFormation outputs
        self.core_cfg = ServiceConfigUtils(
            "core", region=self.region, environment=self.environment
        ).get_stacks_outputs()
        print(f"    Parameters from core: {self.core_cfg}")

        # Get auth-stack parameters for API Gateway
        self.auth_cfg = ServiceConfigUtils(
            "auth", region=self.region, environment=self.environment
        ).get_stacks_outputs()
        print(f"    Parameters from auth: {self.auth_cfg}")

        # Initialize Lambda client for updates
        self.lambda_client = boto3.client("lambda", region_name=self.region)

    def is_deployed(self) -> bool:
        """Check if media infrastructure is already deployed"""
        media_stack_name = f"vibe-dating-media-{self.environment}"

        try:
            # Check if media stack exists and is in a completed state
            response = self.cf.describe_stacks(StackName=media_stack_name)
            stack_status = response["Stacks"][0]["StackStatus"]

            # Only consider it deployed if it's in a completed state
            completed_states = ["CREATE_COMPLETE", "UPDATE_COMPLETE"]
            return stack_status in completed_states

        except self.cf.exceptions.ClientError as e:
            if "does not exist" in str(e):
                return False
            raise

    def _update_aws_lambda(self, aws_lambda_name: str, s3_bucket: str, s3_key: str):
        """Update a Lambda function with code from S3"""
        try:
            self.lambda_client.update_function_code(
                FunctionName=aws_lambda_name, S3Bucket=s3_bucket, S3Key=s3_key
            )

            print(f"    ✅ Updated function code for {aws_lambda_name} from S3")

        except Exception as e:
            print(f"    ❌ Failed to update function {aws_lambda_name}: {e}")
            raise

    def _update_aws_layer(
        self, aws_layer_name: str, aws_layer_version: str, s3_bucket: str, s3_key: str
    ):
        """Update a Lambda layer with code from S3"""
        try:
            # List layer versions to get latest version number
            response = self.lambda_client.list_layer_versions(LayerName=aws_layer_name)

            # Publish new layer version from S3 with incremented version number
            new_version_response = self.lambda_client.publish_layer_version(
                LayerName=aws_layer_name,
                Content={"S3Bucket": s3_bucket, "S3Key": s3_key},
                CompatibleRuntimes=["python3.11"],
            )

            print(
                f"    ✅ Published new layer version {new_version_response['Version']} for {aws_layer_name} from S3"
            )

            # Update functions to use new layer version
            # This would require updating the CloudFormation stack or individual functions
            # For now, we'll just note that the layer was updated
            print(
                f"    ⚠️  Note: Functions using this layer need to be updated to use version {new_version_response['Version']}"
            )

        except Exception as e:
            print(f"    ❌ Failed to update layer {aws_layer_name}: {e}")
            raise

    def update(self):
        """Update Lambda function code without redeploying infrastructure"""
        print("• Starting Media Service Lambda update...")

        try:
            # Get S3 bucket name for Lambda code
            s3_bucket = self.core_cfg["s3"]["LambdaCodeBucketName"]

            # Update Lambda layer
            self._update_aws_layer(
                f"vibe-media-layer-{self.environment}",
                "latest",
                s3_bucket,
                "lambda/media_layer.zip",
            )

            # Update Lambda functions
            self._update_aws_lambda(
                f"vibe-media-upload-{self.environment}",
                s3_bucket,
                "lambda/media_upload.zip",
            )

            self._update_aws_lambda(
                f"vibe-media-processing-{self.environment}",
                s3_bucket,
                "lambda/media_processing.zip",
            )

            self._update_aws_lambda(
                f"vibe-media-management-{self.environment}",
                s3_bucket,
                "lambda/media_management.zip",
            )

            print("✅ Media Service Lambda update completed successfully")

        except Exception as e:
            print(f"❌ Media Service Lambda update failed: {e}")
            sys.exit(1)

    def deploy(self):
        """Deploy media service infrastructure"""
        print("• Starting Media Service deployment...")

        try:
            # Check if already deployed
            if self.is_deployed():
                print(
                    "    ⚠️  Media infrastructure already deployed, updating Lambda code only"
                )
                self.update()
                return

            # Deploy media infrastructure stack
            stack_name = f"vibe-dating-media-{self.environment}"
            template_file = self.service_dir / "cloudformation" / "template.yaml"

            # Prepare parameters
            parameters = {
                "Environment": self.environment,
                "Region": self.region,
                "LambdaCodeBucketName": self.core_cfg["s3"]["LambdaCodeBucketName"],
                "LambdaExecutionRoleArn": self.core_cfg["iam"][
                    "LambdaExecutionRoleArn"
                ],
                "DynamoDBTableName": self.core_cfg["dynamodb"]["DynamoDBTableName"],
                "ApiGatewayRestApiId": self.auth_cfg["apigateway"]["ApiGatewayId"],
                "ApiGatewayRootResourceId": self.auth_cfg["apigateway"][
                    "ApiGatewayRootResourceId"
                ],
            }

            # Deploy CloudFormation stack
            self.deploy_stack(
                stack_name=stack_name,
                template_file=str(template_file),
                parameters=parameters,
                capabilities=["CAPABILITY_IAM"],
            )

            print("✅ Media Service deployment completed successfully")

        except Exception as e:
            print(f"❌ Media Service deployment failed: {e}")
            sys.exit(1)


def main(action=None):
    """Main deployment function"""
    # Only parse arguments if not called from service script
    if action is None:
        parser = argparse.ArgumentParser(description="Deploy Media Service")
        parser.add_argument(
            "--region",
            default="il-central-1",
            help="AWS region (default: il-central-1)",
        )
        parser.add_argument(
            "--environment", default="dev", help="Environment (default: dev)"
        )
        parser.add_argument("--deployment-uuid", help="Deployment UUID for tracking")

        args = parser.parse_args()

        deployer = MediaServiceDeployer(
            region=args.region,
            environment=args.environment,
            deployment_uuid=args.deployment_uuid,
        )
    else:
        # Called from service script, use defaults
        deployer = MediaServiceDeployer()

    if action == "deploy":
        deployer.deploy()
    elif action == "update":
        deployer.update()
    else:
        # Default to deploy
        deployer.deploy()


if __name__ == "__main__":
    main()
