#!/bin/bash

# Validate CloudFormation Template Script

set -e

TEMPLATE_FILE="cloudformation/template.yaml"
REGION="us-east-1"

echo "🔍 Validating CloudFormation template..."

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Template file not found: $TEMPLATE_FILE"
    exit 1
fi

# Validate template
if aws cloudformation validate-template --template-body file://$TEMPLATE_FILE --region $REGION > /dev/null 2>&1; then
    echo "✅ Template validation successful!"
    echo "📋 Template structure is valid and ready for deployment."
else
    echo "❌ Template validation failed!"
    echo "🔧 Please check the template syntax and structure."
    exit 1
fi

echo ""
echo "📝 Next steps:"
echo "1. Update parameters in cloudformation/parameters.yaml"
echo "2. Run ./deploy.sh deploy to deploy the stack"
echo "3. Run ./deploy.sh status to check deployment status" 