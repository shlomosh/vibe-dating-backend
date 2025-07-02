#!/bin/bash

# Vibe Authentication Service - Lambda Build Script

set -e

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

# Configuration
LAMBDA_DIR="lambda"
BUILD_DIR="build"
TELEGRAM_AUTH_ZIP="telegram_auth.zip"
JWT_AUTHORIZER_ZIP="jwt_authorizer.zip"

# Clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    rm -rf $BUILD_DIR
    mkdir -p $BUILD_DIR
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv $BUILD_DIR/venv
    source $BUILD_DIR/venv/bin/activate
    
    # Install dependencies
    pip install -r $LAMBDA_DIR/requirements.txt -t $BUILD_DIR/
    
    # Deactivate virtual environment
    deactivate
}

# Copy Lambda function code
copy_lambda_code() {
    print_status "Copying Lambda function code..."
    cp $LAMBDA_DIR/lambda_function.py $BUILD_DIR/
}

# Create Telegram Auth package
create_telegram_auth_package() {
    print_status "Creating Telegram Auth Lambda package..."
    
    cd $BUILD_DIR
    
    # Create package directory
    mkdir -p telegram_auth
    cp lambda_function.py telegram_auth/
    cp -r *.dist-info telegram_auth/ 2>/dev/null || true
    cp -r PyJWT* telegram_auth/ 2>/dev/null || true
    cp -r boto3* telegram_auth/ 2>/dev/null || true
    cp -r botocore* telegram_auth/ 2>/dev/null || true
    cp -r jmespath* telegram_auth/ 2>/dev/null || true
    cp -r s3transfer* telegram_auth/ 2>/dev/null || true
    cp -r urllib3* telegram_auth/ 2>/dev/null || true
    cp -r certifi* telegram_auth/ 2>/dev/null || true
    cp -r python_dateutil* telegram_auth/ 2>/dev/null || true
    cp -r six* telegram_auth/ 2>/dev/null || true
    
    # Create ZIP file
    cd telegram_auth
    zip -r ../$TELEGRAM_AUTH_ZIP .
    cd ..
    
    print_status "Telegram Auth package created: $TELEGRAM_AUTH_ZIP"
}

# Create JWT Authorizer package
create_jwt_authorizer_package() {
    print_status "Creating JWT Authorizer Lambda package..."
    
    cd $BUILD_DIR
    
    # Create package directory
    mkdir -p jwt_authorizer
    cp lambda_function.py jwt_authorizer/
    cp -r *.dist-info jwt_authorizer/ 2>/dev/null || true
    cp -r PyJWT* jwt_authorizer/ 2>/dev/null || true
    
    # Create ZIP file
    cd jwt_authorizer
    zip -r ../$JWT_AUTHORIZER_ZIP .
    cd ..
    
    print_status "JWT Authorizer package created: $JWT_AUTHORIZER_ZIP"
}

# Upload to S3 (optional)
upload_to_s3() {
    if [ -n "$S3_BUCKET" ]; then
        print_status "Uploading packages to S3..."
        aws s3 cp $BUILD_DIR/$TELEGRAM_AUTH_ZIP s3://$S3_BUCKET/lambda/
        aws s3 cp $BUILD_DIR/$JWT_AUTHORIZER_ZIP s3://$S3_BUCKET/lambda/
        print_status "Packages uploaded to s3://$S3_BUCKET/lambda/"
    else
        print_warning "S3_BUCKET not set, skipping upload"
    fi
}

# Main build process
main() {
    print_status "Starting Lambda function build process..."
    
    # Check if we're in the right directory
    if [ ! -f "$LAMBDA_DIR/requirements.txt" ]; then
        print_error "requirements.txt not found. Please run this script from the auth service directory."
        exit 1
    fi
    
    # Build process
    clean_build
    install_dependencies
    copy_lambda_code
    create_telegram_auth_package
    create_jwt_authorizer_package
    upload_to_s3
    
    print_status "Build completed successfully!"
    print_status "Packages created:"
    echo "  - $BUILD_DIR/$TELEGRAM_AUTH_ZIP"
    echo "  - $BUILD_DIR/$JWT_AUTHORIZER_ZIP"
    
    # Show package sizes
    echo ""
    print_status "Package sizes:"
    ls -lh $BUILD_DIR/*.zip
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean     Clean build directory only"
    echo "  --upload    Upload packages to S3 (requires S3_BUCKET env var)"
    echo "  --help      Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  S3_BUCKET   S3 bucket for uploading packages"
    echo ""
    echo "Examples:"
    echo "  $0                    # Build packages"
    echo "  $0 --clean            # Clean build directory"
    echo "  S3_BUCKET=my-bucket $0 --upload  # Build and upload to S3"
}

# Parse command line arguments
case "${1:-build}" in
    "build")
        main
        ;;
    "clean")
        clean_build
        print_status "Build directory cleaned"
        ;;
    "upload")
        if [ -n "$S3_BUCKET" ]; then
            main
        else
            print_error "S3_BUCKET environment variable not set"
            exit 1
        fi
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac 