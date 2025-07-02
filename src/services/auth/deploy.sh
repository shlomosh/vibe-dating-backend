#!/bin/bash

# Vibe Dating App - Authentication Service Deployment Script

set -e

# Configuration
STACK_NAME="vibe-auth-service"
TEMPLATE_FILE="cloudformation/template.yaml"
PARAMETERS_FILE="cloudformation/parameters.yaml"
REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
}

# Function to check if user is authenticated
check_aws_auth() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
}

# Function to validate CloudFormation template
validate_template() {
    print_status "Validating CloudFormation template..."
    if aws cloudformation validate-template --template-body file://$TEMPLATE_FILE --region $REGION &> /dev/null; then
        print_status "Template validation successful"
    else
        print_error "Template validation failed"
        exit 1
    fi
}

# Function to check if stack exists
stack_exists() {
    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null
}

# Function to deploy stack
deploy_stack() {
    local operation=$1
    
    print_status "Starting $operation for stack: $STACK_NAME"
    
    aws cloudformation $operation-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters file://$PARAMETERS_FILE \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION \
        --tags Key=Environment,Value=dev Key=Service,Value=auth
    
    print_status "Waiting for stack $operation to complete..."
    aws cloudformation wait stack-$operation-complete --stack-name $STACK_NAME --region $REGION
    
    if [ $? -eq 0 ]; then
        print_status "Stack $operation completed successfully!"
        
        # Get stack outputs
        print_status "Stack outputs:"
        aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --region $REGION \
            --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
            --output table
    else
        print_error "Stack $operation failed!"
        exit 1
    fi
}

# Function to build Lambda packages
build_lambda_packages() {
    print_status "Building Lambda function packages..."
    
    if [ -f "./build.sh" ]; then
        ./build.sh
    else
        print_error "Build script not found. Please run this script from the auth service directory."
        exit 1
    fi
}

# Function to upload Lambda packages to S3
upload_lambda_packages() {
    print_status "Uploading Lambda packages to S3..."
    
    # Get the S3 bucket name from CloudFormation outputs or create it
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaCodeBucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$BUCKET_NAME" ]; then
        # Create S3 bucket first
        BUCKET_NAME="vibe-auth-lambda-${ENVIRONMENT}-$(aws sts get-caller-identity --query Account --output text)"
        aws s3 mb s3://$BUCKET_NAME --region $REGION
        
        # Wait for bucket to be available
        aws s3api wait bucket-exists --bucket $BUCKET_NAME
    fi
    
    # Upload packages
    aws s3 cp build/telegram_auth.zip s3://$BUCKET_NAME/lambda/
    aws s3 cp build/jwt_authorizer.zip s3://$BUCKET_NAME/lambda/
    
    print_status "Lambda packages uploaded to s3://$BUCKET_NAME/lambda/"
}

# Function to update parameters
update_parameters() {
    print_warning "Please update the parameters in $PARAMETERS_FILE before deployment:"
    echo "1. Set TelegramBotToken to your actual bot token"
    echo "2. Set JWTSecret to a secure random string"
    echo "3. Update DomainName if needed"
    echo ""
    read -p "Press Enter to continue after updating parameters..."
}

# Main deployment logic
main() {
    print_status "Starting Vibe Authentication Service deployment..."
    
    # Pre-deployment checks
    check_aws_cli
    check_aws_auth
    validate_template
    update_parameters
    
    # Build and upload Lambda packages
    build_lambda_packages
    upload_lambda_packages
    
    # Deploy or update stack
    if stack_exists; then
        print_status "Stack exists, updating..."
        deploy_stack "update"
    else
        print_status "Stack does not exist, creating..."
        deploy_stack "create"
    fi
    
    print_status "Deployment completed successfully!"
    print_status "API Gateway URL: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text)"
}

# Function to delete stack
delete_stack() {
    print_warning "This will delete the entire stack and all its resources!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deleting stack: $STACK_NAME"
        aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
        
        print_status "Waiting for stack deletion to complete..."
        aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION
        
        if [ $? -eq 0 ]; then
            print_status "Stack deleted successfully!"
        else
            print_error "Stack deletion failed!"
            exit 1
        fi
    else
        print_status "Deletion cancelled"
    fi
}

# Function to show stack status
show_status() {
    if stack_exists; then
        print_status "Stack status:"
        aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --region $REGION \
            --query 'Stacks[0].[StackStatus,StackStatusReason]' \
            --output table
        
        print_status "Stack outputs:"
        aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --region $REGION \
            --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
            --output table
    else
        print_warning "Stack does not exist"
    fi
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "delete")
        delete_stack
        ;;
    "status")
        show_status
        ;;
    "validate")
        check_aws_cli
        validate_template
        ;;
    *)
        echo "Usage: $0 {deploy|delete|status|validate}"
        echo "  deploy   - Deploy or update the stack (default)"
        echo "  delete   - Delete the stack"
        echo "  status   - Show stack status and outputs"
        echo "  validate - Validate the CloudFormation template"
        exit 1
        ;;
esac 