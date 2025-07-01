#!/bin/bash

# Vibe Backend Deployment Script
# This script deploys the Vibe backend infrastructure and Lambda functions using CloudFormation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
STACK_NAME="vibe-backend-${ENVIRONMENT}"

echo -e "${BLUE}🚀 Starting Vibe Backend Deployment${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
echo -e "${BLUE}Stack Name: ${STACK_NAME}${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_status "Python dependencies installed"
    else
        print_warning "requirements.txt not found, skipping Python dependencies"
    fi
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    if [ -d "tests" ]; then
        python3 -m pytest tests/ -v --tb=short
        print_status "Tests completed"
    else
        print_warning "Tests directory not found, skipping tests"
    fi
}

# Build Lambda package
build_lambda_package() {
    print_status "Building Lambda package..."
    
    # Create build directory
    mkdir -p build
    
    # Copy source code
    cp -r src/ build/
    cp requirements.txt build/
    
    # Install dependencies in build directory
    cd build
    pip3 install -r requirements.txt -t .
    
    # Create ZIP file
    zip -r ../lambda-package.zip .
    cd ..
    
    print_status "Lambda package created: lambda-package.zip"
}

# Deploy infrastructure with CloudFormation
deploy_infrastructure() {
    print_status "Deploying infrastructure with CloudFormation..."
    
    # Set environment-specific parameters
    case $ENVIRONMENT in
        "dev")
            DYNAMODB_TABLE_NAME="vibe-app-data-dev"
            S3_BUCKET_NAME="vibe-media-bucket-dev"
            API_NAME="vibe-backend-api-dev"
            API_DOMAIN_NAME="api-dev.vibe-dating.io"
            LOG_GROUP_NAME="/aws/lambda/vibe-backend-dev"
            LAMBDA_TIMEOUT=30
            LAMBDA_MEMORY_SIZE=512
            LOG_RETENTION_DAYS=7
            ;;
        "staging")
            DYNAMODB_TABLE_NAME="vibe-app-data-staging"
            S3_BUCKET_NAME="vibe-media-bucket-staging"
            API_NAME="vibe-backend-api-staging"
            API_DOMAIN_NAME="api-staging.vibe-dating.io"
            LOG_GROUP_NAME="/aws/lambda/vibe-backend-staging"
            LAMBDA_TIMEOUT=30
            LAMBDA_MEMORY_SIZE=1024
            LOG_RETENTION_DAYS=14
            ;;
        "prod")
            DYNAMODB_TABLE_NAME="vibe-app-data-prod"
            S3_BUCKET_NAME="vibe-media-bucket-prod"
            API_NAME="vibe-backend-api-prod"
            API_DOMAIN_NAME="api.vibe-dating.io"
            LOG_GROUP_NAME="/aws/lambda/vibe-backend-prod"
            LAMBDA_TIMEOUT=60
            LAMBDA_MEMORY_SIZE=2048
            LOG_RETENTION_DAYS=90
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    # Deploy CloudFormation stack
    aws cloudformation deploy \
        --template-file infrastructure/cloudformation/main.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            DynamoDBTableName="$DYNAMODB_TABLE_NAME" \
            S3BucketName="$S3_BUCKET_NAME" \
            APIName="$API_NAME" \
            APIDomainName="$API_DOMAIN_NAME" \
            LogGroupName="$LOG_GROUP_NAME" \
            LambdaTimeout="$LAMBDA_TIMEOUT" \
            LambdaMemorySize="$LAMBDA_MEMORY_SIZE" \
            LogRetentionDays="$LOG_RETENTION_DAYS" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --no-fail-on-empty-changeset
    
    print_status "Infrastructure deployed successfully"
}

# Deploy Lambda functions
deploy_lambda_functions() {
    print_status "Deploying Lambda functions..."
    
    # Get Lambda function name from CloudFormation outputs
    LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
        --output text)
    
    if [ -z "$LAMBDA_FUNCTION_NAME" ]; then
        print_error "Could not retrieve Lambda function name from CloudFormation outputs"
        exit 1
    fi
    
    print_status "Deploying Lambda function: $LAMBDA_FUNCTION_NAME"
    
    # Update Lambda function code
    aws lambda update-function-code \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --zip-file fileb://lambda-package.zip \
        --region "$REGION"
    
    # Wait for update to complete
    aws lambda wait function-updated \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --region "$REGION"
    
    print_status "Lambda functions deployed successfully"
}

# Update environment variables
update_environment_variables() {
    print_status "Updating environment variables..."
    
    # Get Lambda function name from CloudFormation outputs
    LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
        --output text)
    
    # Get DynamoDB table name from CloudFormation outputs
    DYNAMODB_TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
        --output text)
    
    # Get S3 bucket name from CloudFormation outputs
    S3_BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
        --output text)
    
    # Update Lambda environment variables
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --environment "Variables={
            ENVIRONMENT=$ENVIRONMENT,
            DYNAMODB_TABLE_NAME=$DYNAMODB_TABLE_NAME,
            S3_BUCKET_NAME=$S3_BUCKET_NAME,
            AWS_REGION=$REGION
        }" \
        --region "$REGION"
    
    print_status "Environment variables updated"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # For DynamoDB, this might involve creating/updating tables
    # The CloudFormation template handles table creation
    # Additional migrations can be added here if needed
    
    print_status "Database migrations completed"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Get API Gateway URL from CloudFormation outputs
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text)
    
    if [ -z "$API_URL" ]; then
        print_error "Could not retrieve API Gateway URL from CloudFormation outputs"
        exit 1
    fi
    
    # Wait for API to be ready
    print_status "Waiting for API to be ready..."
    sleep 30
    
    # Test health endpoint
    if curl -f "${API_URL}/health" > /dev/null 2>&1; then
        print_status "Health check passed"
        echo -e "${BLUE}API Gateway URL: ${API_URL}${NC}"
    else
        print_warning "Health check failed - API might still be initializing"
        echo -e "${BLUE}API Gateway URL: ${API_URL}${NC}"
    fi
    
    # Show custom domain information for production
    if [ "$ENVIRONMENT" = "prod" ]; then
        CUSTOM_DOMAIN=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayCustomDomain`].OutputValue' \
            --output text)
        
        if [ -n "$CUSTOM_DOMAIN" ]; then
            echo -e "${BLUE}Custom Domain: ${CUSTOM_DOMAIN}${NC}"
            print_warning "Note: Custom domain may take time to become active after SSL certificate validation"
        fi
    fi
}

# Cleanup
cleanup() {
    print_status "Cleaning up build artifacts..."
    
    rm -rf build/
    rm -f lambda-package.zip
    
    print_status "Cleanup completed"
}

# Show stack outputs
show_outputs() {
    print_status "Stack outputs:"
    
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output table
}

# Show domain information
show_domain_info() {
    if [ "$ENVIRONMENT" = "prod" ]; then
        print_status "Domain Configuration:"
        echo -e "${BLUE}Base Domain: vibe-dating.io${NC}"
        echo -e "${BLUE}API Domain: api.vibe-dating.io${NC}"
        echo -e "${BLUE}Media Domain: media.vibe-dating.io${NC}"
        echo ""
        print_warning "Important: After deployment, you need to:"
        echo "1. Validate the SSL certificate in AWS Certificate Manager"
        echo "2. Update your domain's nameservers to point to Route53"
        echo "3. Wait for DNS propagation (can take up to 24 hours)"
    fi
}

# Main deployment flow
main() {
    echo -e "${BLUE}Starting deployment process...${NC}"
    
    check_prerequisites
    install_dependencies
    run_tests
    build_lambda_package
    deploy_infrastructure
    deploy_lambda_functions
    update_environment_variables
    run_migrations
    health_check
    cleanup
    show_outputs
    show_domain_info
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
}

# Run main function
main "$@" 