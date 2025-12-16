# ASCEND Envoy External Authorization Server - Makefile
# Author: ASCEND Platform Engineering

.PHONY: all build test lint clean docker helm

# Variables
APP_NAME := ascend-envoy-authz
VERSION := 1.0.0
DOCKER_REGISTRY := owkai
DOCKER_IMAGE := $(DOCKER_REGISTRY)/$(APP_NAME):$(VERSION)
HELM_CHART := helm/ascend-authz

# Go settings
GO := go
GOFLAGS := -ldflags="-w -s -X main.version=$(VERSION)"

all: lint test build

# Build the binary
build:
	@echo "Building $(APP_NAME)..."
	$(GO) build $(GOFLAGS) -o bin/server ./cmd/server
	@echo "Build complete: bin/server"

# Run tests
test:
	@echo "Running tests..."
	$(GO) test -v -race -cover ./...
	@echo "Tests complete"

# Run tests with coverage report
test-coverage:
	@echo "Running tests with coverage..."
	$(GO) test -v -race -coverprofile=coverage.out ./...
	$(GO) tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

# Run linting
lint:
	@echo "Running linters..."
	$(GO) vet ./...
	@if command -v golangci-lint &> /dev/null; then \
		golangci-lint run; \
	else \
		echo "golangci-lint not installed, skipping"; \
	fi
	@echo "Lint complete"

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf bin/
	rm -f coverage.out coverage.html
	@echo "Clean complete"

# Build Docker image
docker:
	@echo "Building Docker image $(DOCKER_IMAGE)..."
	docker build -t $(DOCKER_IMAGE) .
	docker tag $(DOCKER_IMAGE) $(DOCKER_REGISTRY)/$(APP_NAME):latest
	@echo "Docker image built: $(DOCKER_IMAGE)"

# Push Docker image
docker-push: docker
	@echo "Pushing Docker image..."
	docker push $(DOCKER_IMAGE)
	docker push $(DOCKER_REGISTRY)/$(APP_NAME):latest
	@echo "Docker image pushed"

# Lint Helm chart
helm-lint:
	@echo "Linting Helm chart..."
	helm lint $(HELM_CHART)
	@echo "Helm lint complete"

# Package Helm chart
helm-package: helm-lint
	@echo "Packaging Helm chart..."
	helm package $(HELM_CHART) -d helm/
	@echo "Helm chart packaged"

# Install with Helm (dry-run)
helm-dry-run:
	@echo "Helm install dry-run..."
	helm install ascend-authz $(HELM_CHART) \
		--namespace ascend-system \
		--create-namespace \
		--dry-run \
		--debug

# Install with Helm
helm-install:
	@echo "Installing with Helm..."
	helm upgrade --install ascend-authz $(HELM_CHART) \
		--namespace ascend-system \
		--create-namespace \
		--wait
	@echo "Helm install complete"

# Uninstall Helm release
helm-uninstall:
	@echo "Uninstalling Helm release..."
	helm uninstall ascend-authz --namespace ascend-system
	@echo "Helm uninstall complete"

# Run locally
run:
	@echo "Running locally..."
	$(GO) run ./cmd/server

# Run with test environment
run-test:
	@echo "Running with test config..."
	ASCEND_API_URL=https://test.ascend.owkai.app \
	ASCEND_API_KEY=test_key \
	LOG_LEVEL=debug \
	$(GO) run ./cmd/server

# Generate protobuf (if needed)
proto:
	@echo "Generating protobuf..."
	@echo "Using envoy-go-control-plane, no generation needed"

# Download dependencies
deps:
	@echo "Downloading dependencies..."
	$(GO) mod download
	$(GO) mod tidy
	@echo "Dependencies downloaded"

# Show help
help:
	@echo "ASCEND Envoy ext_authz Server - Available targets:"
	@echo ""
	@echo "  make build         - Build the binary"
	@echo "  make test          - Run tests"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make lint          - Run linters"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docker        - Build Docker image"
	@echo "  make docker-push   - Push Docker image"
	@echo "  make helm-lint     - Lint Helm chart"
	@echo "  make helm-package  - Package Helm chart"
	@echo "  make helm-dry-run  - Helm install dry-run"
	@echo "  make helm-install  - Install with Helm"
	@echo "  make helm-uninstall - Uninstall Helm release"
	@echo "  make run           - Run locally"
	@echo "  make deps          - Download dependencies"
	@echo ""
