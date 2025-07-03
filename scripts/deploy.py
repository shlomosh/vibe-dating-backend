#!/usr/bin/env python3
"""
Poetry-based deployment script for Vibe Auth Service

This script deploys the authentication service using Poetry for dependency management.
"""

import os
import sys
import subprocess
import boto3
from pathlib import Path

os.environ["AWS_PROFILE"] = "vibe-dating"
os.environ["AWS_REGION"] = "il-central-1"

class AuthDeployer:
    """Deploys the Vibe authentication service using Poetry"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.auth_dir = self.project_root / "src" / "services" / "auth"
        self.build_dir = self.project_root / "build" / "lambda"
        self.config_dir = self.project_root / "src" / "config"
        
        # AWS configuration
        self.stack_name = "vibe-dating-auth-service"
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.region = os.getenv("AWS_REGION", "il-central-1")
        
    def check_prerequisites(self):
        """Check that all prerequisites are met"""
        print("• Checking prerequisites...")
        
        # Check if Poetry is installed
        try:
            subprocess.run(["poetry", "--version"], check=True, capture_output=True)
            print("• Poetry is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Poetry is not installed. Please install Poetry first.")
            sys.exit(1)
            
        # Check if AWS CLI is installed
        try:
            subprocess.run(["aws", "--version"], check=True, capture_output=True)
            print("• AWS CLI is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ AWS CLI is not installed. Please install AWS CLI first.")
            sys.exit(1)
            
        # Check AWS credentials
        try:
            boto3.client('sts').get_caller_identity()
            print("• AWS credentials are configured")
        except Exception as e:
            print(f"❌ AWS credentials not configured: {e}")
            sys.exit(1)
            
        # Check if build artifacts exist
        if not self.build_dir.exists():
            print("❌ Build artifacts not found. Run 'poetry run build-lambda' first.")
            sys.exit(1)
            
        print("• All prerequisites met")
        
    def build_lambda_packages(self):
        """Build Lambda packages using Poetry"""
        print("• Building Lambda packages...")
        
        try:
            subprocess.run(["poetry", "run", "build-lambda"], check=True, cwd=self.project_root)
            print("• Lambda packages built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build Lambda packages: {e}")
            sys.exit(1)
            
    def upload_to_s3(self):
        """Upload Lambda packages to S3"""
        print("• Uploading packages to S3...")
        
        # Get or create S3 bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = f"vibe-dating-code-{self.environment}-d6aa50da-5809-11f0-bcae-1fb18ef3af1c"
        
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"• Using existing S3 bucket: {bucket_name}")
        except:
            print(f"• Creating S3 bucket: {bucket_name}")
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': self.region} if self.region != 'us-east-1' else {}
            )
            
        # Upload packages
        packages = [
            "vibe_base_layer.zip",
            "telegram_auth.zip", 
            "jwt_authorizer.zip"
        ]
        
        for package in packages:
            package_path = self.build_dir / package
            if package_path.exists():
                s3_key = f"lambda/{package}"
                s3_client.upload_file(str(package_path), bucket_name, s3_key)
                print(f"• Uploaded {package} to s3://{bucket_name}/{s3_key}")
            else:
                print(f"⚠️  Package not found: {package_path}")
                
        return bucket_name
        
    def validate_cloudformation(self):
        """Validate CloudFormation template"""
        print("• Validating CloudFormation template...")
        
        template_file = self.auth_dir / "cloudformation" / "template.yaml"
        parameters_file = self.config_dir / "cloudformation" / "parameters.yaml"
        
        if not template_file.exists():
            print(f"❌ CloudFormation template not found: {template_file}")
            sys.exit(1)
            
        try:
            subprocess.run([
                "aws", "cloudformation", "validate-template",
                "--template-body", f"file://{template_file}",
                "--region", self.region
            ], check=True)
            print("• CloudFormation template is valid")
        except subprocess.CalledProcessError as e:
            print(f"❌ CloudFormation template validation failed: {e}")
            sys.exit(1)
            
    def deploy_stack(self, bucket_name: str):
        """Deploy CloudFormation stack"""
        print(f"• Deploying CloudFormation stack: {self.stack_name}")
        
        template_file = self.auth_dir / "cloudformation" / "template.yaml"
        parameters_file = self.config_dir / "cloudformation" / "parameters.yaml"
        
        # Check if stack exists
        cf_client = boto3.client('cloudformation')
        try:
            cf_client.describe_stacks(StackName=self.stack_name)
            operation = "update"
            print("📝 Stack exists, updating...")
        except cf_client.exceptions.ClientError:
            operation = "create"
            print("🆕 Stack does not exist, creating...")
            
        # Deploy stack
        cmd = [
            "aws", "cloudformation", f"{operation}-stack",
            "--stack-name", self.stack_name,
            "--template-body", f"file://{template_file}",
            "--parameters", f"file://{parameters_file}",
            "--capabilities", "CAPABILITY_NAMED_IAM",
            "--region", self.region,
            "--tags", f"Key=Environment,Value={self.environment}", f"Key=Service,Value=auth"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"• Stack {operation} initiated successfully")
            
            # Wait for completion
            print("• Waiting for stack operation to complete...")
            waiter = cf_client.get_waiter(f'stack_{operation}_complete')
            waiter.wait(StackName=self.stack_name)
            print("• Stack operation completed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Stack {operation} failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error during stack operation: {e}")
            sys.exit(1)
            
    def show_outputs(self):
        """Show CloudFormation stack outputs"""
        print("• Stack outputs:")
        
        cf_client = boto3.client('cloudformation')
        try:
            response = cf_client.describe_stacks(StackName=self.stack_name)
            outputs = response['Stacks'][0].get('Outputs', [])
            
            for output in outputs:
                print(f"  {output['OutputKey']}: {output['OutputValue']}")
                
        except Exception as e:
            print(f"⚠️  Could not retrieve stack outputs: {e}")
            
    def deploy(self):
        """Main deployment process"""
        print("• Starting Poetry-based deployment...")
        
        try:
            self.check_prerequisites()
            self.build_lambda_packages()
            bucket_name = self.upload_to_s3()
            self.validate_cloudformation()
            self.deploy_stack(bucket_name)
            self.show_outputs()
            
            print("\n✅ Deployment completed successfully!")
            print(f"API Gateway URL: https://{self.stack_name}.execute-api.{self.region}.amazonaws.com/{self.environment}")
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            sys.exit(1)


def deploy_auth_service():
    """Entry point for Poetry script"""
    deployer = AuthDeployer()
    deployer.deploy()


if __name__ == "__main__":
    deploy_auth_service() 