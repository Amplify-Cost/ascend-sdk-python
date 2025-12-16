# ASCEND Lambda Authorizer - Build & Deploy Makefile
# ==================================================

.PHONY: all clean test lint build package deploy local-test

# Configuration
STACK_NAME ?= ascend-authorizer
ENVIRONMENT ?= production
AWS_REGION ?= us-east-1
S3_BUCKET ?= $(STACK_NAME)-deployment-$(AWS_REGION)

# Python settings
PYTHON := python3
PIP := pip3
PYTEST := pytest

all: clean lint test build

# Clean build artifacts
clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf tests/__pycache__
	rm -rf .aws-sam
	rm -rf .coverage
	rm -f coverage.xml
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# Install development dependencies
install-dev:
	$(PIP) install -r requirements.txt

# Run linting
lint:
	@echo "Running lint checks..."
	$(PYTHON) -m py_compile src/*.py
	@echo "Lint passed!"

# Run all tests
test:
	@echo "Running tests..."
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing
	@echo "Tests passed!"

# Run only unit tests (fast)
test-unit:
	$(PYTEST) tests/test_handler.py -v

# Run performance tests
test-perf:
	$(PYTEST) tests/test_performance.py -v -s

# Build the Lambda package
build:
	@echo "Building Lambda package..."
	sam build --template-file cloudformation/template.yaml
	@echo "Build complete!"

# Package for deployment
package:
	@echo "Packaging for deployment..."
	sam package \
		--template-file .aws-sam/build/template.yaml \
		--output-template-file packaged.yaml \
		--s3-bucket $(S3_BUCKET) \
		--region $(AWS_REGION)
	@echo "Package complete: packaged.yaml"

# Deploy to AWS
deploy: build package
	@echo "Deploying to AWS..."
	sam deploy \
		--template-file packaged.yaml \
		--stack-name $(STACK_NAME)-$(ENVIRONMENT) \
		--capabilities CAPABILITY_IAM \
		--region $(AWS_REGION) \
		--parameter-overrides \
			Environment=$(ENVIRONMENT)
	@echo "Deployment complete!"

# Deploy with guided wizard
deploy-guided:
	sam deploy --guided --template-file cloudformation/template.yaml

# Local testing with SAM
local-test:
	@echo "Starting local Lambda..."
	sam local invoke AscendAuthorizerFunction \
		--template-file cloudformation/template.yaml \
		--event tests/events/sample_request.json

# Generate sample event
generate-event:
	@mkdir -p tests/events
	@echo '{"type":"REQUEST","methodArn":"arn:aws:execute-api:us-east-1:123456789012:abc123/prod/GET/users","resource":"/users","path":"/users","httpMethod":"GET","headers":{"X-Ascend-Agent-Id":"test-agent-001","Content-Type":"application/json"},"queryStringParameters":{},"pathParameters":{},"requestContext":{"accountId":"123456789012","apiId":"abc123","stage":"prod","requestId":"test-request-id","identity":{"sourceIp":"192.168.1.1"}}}' > tests/events/sample_request.json
	@echo "Generated tests/events/sample_request.json"

# View CloudWatch logs
logs:
	aws logs tail /aws/lambda/$(STACK_NAME)-$(ENVIRONMENT) --follow --region $(AWS_REGION)

# Get stack outputs
outputs:
	aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME)-$(ENVIRONMENT) \
		--region $(AWS_REGION) \
		--query 'Stacks[0].Outputs' \
		--output table

# Delete the stack
delete:
	@echo "Deleting stack $(STACK_NAME)-$(ENVIRONMENT)..."
	aws cloudformation delete-stack \
		--stack-name $(STACK_NAME)-$(ENVIRONMENT) \
		--region $(AWS_REGION)
	@echo "Stack deletion initiated"

# Help
help:
	@echo "ASCEND Lambda Authorizer - Available targets:"
	@echo ""
	@echo "  make all            - Clean, lint, test, and build"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make lint           - Run lint checks"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-perf      - Run performance tests"
	@echo "  make build          - Build the Lambda package"
	@echo "  make package        - Package for deployment"
	@echo "  make deploy         - Deploy to AWS"
	@echo "  make deploy-guided  - Deploy with guided wizard"
	@echo "  make local-test     - Test locally with SAM"
	@echo "  make logs           - Tail CloudWatch logs"
	@echo "  make outputs        - Show stack outputs"
	@echo "  make delete         - Delete the stack"
	@echo ""
	@echo "Environment variables:"
	@echo "  STACK_NAME    - CloudFormation stack name (default: ascend-authorizer)"
	@echo "  ENVIRONMENT   - Deployment environment (default: production)"
	@echo "  AWS_REGION    - AWS region (default: us-east-1)"
	@echo "  S3_BUCKET     - S3 bucket for deployment artifacts"
