#!/usr/bin/env python3
"""
Deployment script for Vibe Dating App Auth Service CloudFormation stacks.
Deploys authentication infrastructure stacks (API Gateway, Lambda) in the correct order.
If infrastructure already exists, updates Lambda function code only.
"""

import argparse
import sys

import boto3

from core.config_utils import ServiceConfigUtils
from core.deploy_utils import ServiceDeployer


class AuthServiceDeployer(ServiceDeployer):
    """Deploys the Vibe Dating App authentication service infrastructure"""

    def __init__(
        self, region: str = None, environment: str = None, deployment_uuid: str = None
    ):
        """Initialize the auth service deployer."""
        super().__init__(
            "auth",
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

        # Initialize Lambda client for updates
        self.lambda_client = boto3.client("lambda", region_name=self.region)

    def is_deployed(self) -> bool:
        """Check if auth infrastructure is already deployed"""
        lambda_stack_name = f"vibe-dating-auth-lambda-{self.environment}"

        try:
            # Check if Lambda stack exists
            self.cf.describe_stacks(StackName=lambda_stack_name)
            return True
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
        print("• Starting Auth Service Lambda update...")

        try:
            # Get stack outputs to find function names
            lambda_stack_name = f"vibe-dating-auth-lambda-{self.environment}"
            stack_outputs = self._get_stack_outputs(lambda_stack_name)

            if not stack_outputs:
                print(f"❌ Could not find stack outputs for {lambda_stack_name}")
                print("   Make sure the auth infrastructure is deployed first")
                sys.exit(1)

            # Get bucket name for S3 updates
            s3_bucket = self.get_lambda_code_bucket_name()

            # Update Lambda functions
            updated_functions = []

            # Update platform auth function
            if "AuthPlatformFunctionArn" in stack_outputs:
                aws_lambda_arn = stack_outputs["AuthPlatformFunctionArn"]
                aws_lambda_name = aws_lambda_arn.split(":")[-1]

                # Ask user if they want to update the function
                update_question = input(
                    f"  Do you want to update function {aws_lambda_name}? (y/n): "
                ).lower()

                if update_question == "y":
                    print(f"  Updating function: {aws_lambda_name}")
                    self._update_aws_lambda(
                        aws_lambda_name, s3_bucket, "lambda/auth_platform.zip"
                    )
                    updated_functions.append(aws_lambda_name)
                else:
                    print(f"  Skipping function update for: {aws_lambda_name}")

            # Update JWT authorizer function
            if "AuthJWTAuthorizerFunctionArn" in stack_outputs:
                aws_lambda_arn = stack_outputs["AuthJWTAuthorizerFunctionArn"]
                aws_lambda_name = aws_lambda_arn.split(":")[-1]

                # Ask user if they want to update the function
                update_question = input(
                    f"  Do you want to update function {aws_lambda_name}? (y/n): "
                ).lower()

                if update_question == "y":
                    print(f"  Updating function: {aws_lambda_name}")
                    self._update_aws_lambda(
                        aws_lambda_name, s3_bucket, "lambda/auth_jwt_authorizer.zip"
                    )
                    updated_functions.append(aws_lambda_name)
                else:
                    print(f"  Skipping function update for: {aws_lambda_name}")

            print(f"✅ Successfully updated {len(updated_functions)} Lambda resources:")
            for func in updated_functions:
                print(f"   • {func}")

        except Exception as e:
            print(f"❌ Auth service update failed: {e}")
            sys.exit(1)

    def deploy(self):
        print(f"    Parameters from *@core-service: {self.core_cfg}")

        # Deploy Lambda stack first
        lambda_stack_name = f"vibe-dating-auth-lambda-{self.environment}"
        lambda_stack = {
            "name": lambda_stack_name,
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
            },
        }
        is_deployed = self.deploy_stack(
            stack_name=lambda_stack["name"],
            template_file=lambda_stack["template"],
            parameters=lambda_stack["parameters"],
        )
        if not is_deployed:
            print("❌ Failed to deploy Lambda stack")
            sys.exit(1)

        # Fetch outputs from Lambda stack
        lambda_cfg = self._get_stack_outputs(lambda_stack_name)
        print(f"    Parameters from lambda@auth-service: {lambda_cfg}")

        # Now deploy API Gateway stack, using outputs from Lambda stack
        apigateway_stack = {
            "name": f"vibe-dating-auth-apigateway-{self.environment}",
            "template": "02-apigateway.yaml",
            "parameters": {
                "Environment": self.environment,
                "Region": self.parameters["ApiRegion"],
                "ApiDomainName": self.parameters["ApiDomainName"],
                "ApiHostedZoneId": self.parameters["ApiHostedZoneId"],
                "ApiCertificateArn": self.parameters["ApiCertificateArn"],
                "ApiGatewayAuthorizerRoleArn": self.core_cfg["iam"][
                    "ApiGatewayAuthorizerRoleArn"
                ],
                "AuthJWTAuthorizerFunctionArn": lambda_cfg[
                    "AuthJWTAuthorizerFunctionArn"
                ],
                "AuthPlatformFunctionArn": lambda_cfg["AuthPlatformFunctionArn"],
            },
        }

        is_deployed = self.deploy_stack(
            stack_name=apigateway_stack["name"],
            template_file=apigateway_stack["template"],
            parameters=apigateway_stack["parameters"],
        )
        if not is_deployed:
            print("❌ Failed to deploy API Gateway stack")
            sys.exit(1)

        # Fetch outputs from API Gateway stack
        apigateway_cfg = self._get_stack_outputs(apigateway_stack["name"])
        print(f"    Parameters from apigateway@auth-service: {apigateway_cfg}")


def main(action=None):
    ap = argparse.ArgumentParser(
        description="Deploy or Update Vibe Dating App Auth Service Infrastructure"
    )
    ap.add_argument("task", default="deploy", help="task to run")
    ap.add_argument(
        "service", nargs="?", default="auth", help="Service to run task for"
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
    deployer = AuthServiceDeployer(
        region=args.region,
        environment=args.environment,
        deployment_uuid=args.deployment_uuid,
    )

    if args.validate:
        deployer.validate_templates(templates=["01-lambda.yaml", "02-apigateway.yaml"])
    elif action == "deploy" or (action is None and not deployer.is_deployed()):
        deployer.deploy()
    elif action == "update" or (action is None and deployer.is_deployed()):
        deployer.update()
    else:
        raise ValueError(f"Invalid action: {action}")


if __name__ == "__main__":
    main()
