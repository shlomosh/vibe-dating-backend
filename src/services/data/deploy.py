#!/usr/bin/env python3

import argparse
import sys

import boto3

from core.config_utils import ServiceConfigUtils
from core.deploy_utils import ServiceDeployer


class DataServiceDeployer(ServiceDeployer):
    """Deploys the Vibe Dating App data service infrastructure"""

    def __init__(
        self, region: str = None, environment: str = None, deployment_uuid: str = None
    ):
        """Initialize the data service deployer."""
        super().__init__(
            "data",
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
        """Check if data infrastructure is already deployed"""
        data_stack_name = f"vibe-dating-data-{self.environment}"

        try:
            # Check if data stack exists and is in a completed state
            response = self.cf.describe_stacks(StackName=data_stack_name)
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
        print("• Starting Data Service Lambda update...")

        try:
            # Get S3 bucket name for Lambda code
            s3_bucket = self.get_lambda_code_bucket_name()

            self._update_aws_lambda(
                f"vibe-data-media-processing-{self.environment}",
                s3_bucket,
                "lambda/data_media_processing.zip",
            )

            print("✅ Data Service Lambda update completed successfully")

        except Exception as e:
            print(f"❌ Data Service Lambda update failed: {e}")
            sys.exit(1)

    def deploy(self):
        """Deploy data service infrastructure"""
        print("• Starting Data Service deployment...")
        print(f"    Parameters from *@core-service: {self.core_cfg}")
        print(f"    Parameters from *@auth-service: {self.auth_cfg}")

        try:
            # Check if already deployed
            if self.is_deployed():
                print(
                    "    ⚠️  Data infrastructure already deployed, updating Lambda code only"
                )
                self.update()
                return

            # Deploy data infrastructure stack
            data_stack = {
                "name": f"vibe-dating-data-{self.environment}",
                "template": "01-lambda.yaml",
                "parameters": {
                    "Environment": self.environment,
                    "Region": self.parameters["ApiRegion"],
                    "LambdaCodeBucketName": self.core_cfg["s3"]["LambdaCodeBucketName"],
                    "LambdaExecutionRoleArn": self.core_cfg["iam"][
                        "LambdaExecutionRoleArn"
                    ],
                    "DynamoDBTableName": self.core_cfg["dynamodb"]["DynamoDBTableName"],
                    "CoreLayerArn": self.core_cfg["lambda"]["CoreLayerArn"],
                    "ApiGatewayRestApiId": self.auth_cfg["apigateway"]["ApiGatewayId"],
                    "ApiGatewayRootResourceId": self.auth_cfg["apigateway"][
                        "ApiGatewayRootResourceId"
                    ],
                },
            }

            # Deploy CloudFormation stack
            is_deployed = self.deploy_stack(
                stack_name=data_stack["name"],
                template_file=data_stack["template"],
                parameters=data_stack["parameters"],
                capabilities=["CAPABILITY_IAM"],
            )

            if not is_deployed:
                print("❌ Failed to deploy data stack")
                sys.exit(1)

            print("✅ Data Service deployment completed successfully")

        except Exception as e:
            print(f"❌ Data Service deployment failed: {e}")
            sys.exit(1)


def main(action=None):
    """Main deployment function"""
    # Only parse arguments if not called from service script
    if action is None:
        ap = argparse.ArgumentParser(
            description="Deploy or Update Vibe Dating App Data Service Infrastructure"
        )
        ap.add_argument("task", default="deploy", help="task to run")
        ap.add_argument(
            "service", nargs="?", default="data", help="Service to run task for"
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
            "--deployment-uuid",
            help="Custom deployment UUID (override parameters.yaml)",
        )
        ap.add_argument(
            "--validate", action="store_true", help="Validate templates only"
        )
        args = ap.parse_args()

        deployer = DataServiceDeployer(
            region=args.region,
            environment=args.environment,
            deployment_uuid=args.deployment_uuid,
        )
    else:
        # Called from service script, use defaults
        deployer = DataServiceDeployer()

    if args.validate:
        deployer.validate_templates(templates=["01-lambda.yaml"])
    elif action == "deploy" or (action is None and not deployer.is_deployed()):
        deployer.deploy()
    elif action == "update" or (action is None and deployer.is_deployed()):
        deployer.update()
    else:
        raise ValueError(f"Invalid action: {action}")


if __name__ == "__main__":
    main()
