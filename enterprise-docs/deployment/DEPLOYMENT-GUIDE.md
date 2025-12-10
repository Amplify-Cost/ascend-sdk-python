# OW-AI Platform - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Deployment](#database-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Load Balancer Configuration](#load-balancer-configuration)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Monitoring Setup](#monitoring-setup)
9. [Production Validation](#production-validation)
10. [Rollback Procedures](#rollback-procedures)

## Prerequisites

### Required Access & Accounts
- [ ] AWS Account with administrative access
- [ ] Domain name with DNS management access
- [ ] GitHub account with repository access
- [ ] Docker Hub or AWS ECR access for container images
- [ ] SSL certificate authority access (or AWS Certificate Manager)

### Required Tools & Software
- [ ] AWS CLI v2.x installed and configured
- [ ] Docker 20.10+ installed
- [ ] kubectl 1.24+ (if using EKS)
- [ ] Terraform 1.3+ (for infrastructure as code)
- [ ] Git 2.30+
- [ ] Node.js 18+ and npm 8+ (for frontend builds)
- [ ] Python 3.11+ (for local testing)

### Network Requirements
- [ ] VPC with public and private subnets across 2+ AZs
- [ ] Internet Gateway attached to VPC
- [ ] NAT Gateway in public subnet for private subnet internet access
- [ ] Security groups configured for web traffic (443, 80) and database (5432)

### Security Requirements
- [ ] IAM roles and policies configured for ECS, RDS, and ALB
- [ ] KMS keys created for encryption
- [ ] Secrets Manager configured for sensitive credentials
- [ ] CloudTrail enabled for audit logging

## Environment Setup

### 1. AWS Infrastructure Setup

#### VPC and Networking
```bash
# Create VPC with Terraform
cat > vpc.tf << 'EOF'
resource "aws_vpc" "owkai_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "owkai-pilot-vpc"
    Environment = "production"
  }
}

resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.owkai_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "owkai-public-subnet-1"
    Type = "public"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.owkai_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "owkai-public-subnet-2"
    Type = "public"
  }
}

resource "aws_subnet" "private_subnet_1" {
  vpc_id            = aws_vpc.owkai_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "owkai-private-subnet-1"
    Type = "private"
  }
}

resource "aws_subnet" "private_subnet_2" {
  vpc_id            = aws_vpc.owkai_vpc.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "owkai-private-subnet-2"
    Type = "private"
  }
}
EOF

# Apply infrastructure
terraform init
terraform plan
terraform apply
```

#### Security Groups
```bash
# Security group for Application Load Balancer
aws ec2 create-security-group \
  --group-name owkai-alb-sg \
  --description "Security group for OW-AI ALB" \
  --vpc-id vpc-xxxxxxxxx

# Allow HTTPS traffic
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow HTTP traffic (for redirect to HTTPS)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Security group for ECS tasks
aws ec2 create-security-group \
  --group-name owkai-ecs-sg \
  --description "Security group for OW-AI ECS tasks" \
  --vpc-id vpc-xxxxxxxxx

# Allow traffic from ALB
aws ec2 authorize-security-group-ingress \
  --group-id sg-yyyyyyyyy \
  --protocol tcp \
  --port 8000 \
  --source-group sg-xxxxxxxxx
```

### 2. Secrets Management Setup

```bash
# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "owkai/database/credentials" \
  --description "Database credentials for OW-AI Platform" \
  --secret-string '{
    "username": "owkai_admin",
    "password": "YourSecurePassword123!",
    "engine": "postgres",
    "host": "owkai-pilot-db.cluster-xxx.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "dbname": "owkai_pilot"
  }'

# Create JWT secret
aws secretsmanager create-secret \
  --name "owkai/jwt/secret" \
  --description "JWT signing secret for OW-AI Platform" \
  --secret-string '{"secret": "'$(openssl rand -base64 32)'"}'

# Create application configuration
aws secretsmanager create-secret \
  --name "owkai/app/config" \
  --description "Application configuration for OW-AI Platform" \
  --secret-string '{
    "environment": "production",
    "debug": false,
    "cors_origins": ["https://pilot.owkai.app"],
    "session_timeout": 1800,
    "max_login_attempts": 5
  }'
```

## Database Deployment

### 1. RDS PostgreSQL Setup

#### Create Database Cluster
```bash
# Create RDS subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name owkai-db-subnet-group \
  --db-subnet-group-description "Subnet group for OW-AI database" \
  --subnet-ids subnet-xxxxxxxxx subnet-yyyyyyyyy

# Create database security group
aws ec2 create-security-group \
  --group-name owkai-db-sg \
  --description "Security group for OW-AI database" \
  --vpc-id vpc-xxxxxxxxx

# Allow PostgreSQL traffic from ECS security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-zzzzzzzzz \
  --protocol tcp \
  --port 5432 \
  --source-group sg-yyyyyyyyy

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier owkai-pilot-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 14.9 \
  --master-username owkai_admin \
  --master-user-password YourSecurePassword123! \
  --allocated-storage 50 \
  --storage-type gp2 \
  --storage-encrypted \
  --backup-retention-period 7 \
  --multi-az \
  --vpc-security-group-ids sg-zzzzzzzzz \
  --db-subnet-group-name owkai-db-subnet-group \
  --deletion-protection
```

#### Database Configuration
```sql
-- Connect to the database and run initial setup
-- Use psql or your preferred PostgreSQL client

-- Create application database
CREATE DATABASE owkai_pilot;

-- Create application user with limited privileges
CREATE USER owkai_app WITH PASSWORD 'AppUserPassword123!';

-- Grant necessary permissions
GRANT CONNECT ON DATABASE owkai_pilot TO owkai_app;
GRANT USAGE ON SCHEMA public TO owkai_app;
GRANT CREATE ON SCHEMA public TO owkai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO owkai_app;
GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA public TO owkai_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO owkai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, USAGE ON SEQUENCES TO owkai_app;
```

### 2. Database Migration

```bash
# Clone the repository
git clone https://github.com/your-org/ow-ai-backend.git
cd ow-ai-backend

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set database connection
export DATABASE_URL="postgresql://owkai_admin:YourSecurePassword123!@owkai-pilot-db.cluster-xxx.us-east-1.rds.amazonaws.com:5432/owkai_pilot"

# Run database migrations
alembic upgrade head

# Create initial admin user
python create_admin_user.py

# Seed initial data (optional)
python seed_data.py
```

## Backend Deployment

### 1. Container Image Build

#### Dockerfile Optimization
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
WORKDIR /app
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash owkai
RUN chown -R owkai:owkai /app
USER owkai

# Set Python path
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Build and Push Image
```bash
# Build Docker image
# SEC-095: CRITICAL - Always specify --platform for ECS Fargate (AMD64)
# Without this flag, Mac M1/M2 will build ARM64 images that fail on ECS
docker build --platform linux/amd64 -t owkai/backend:latest .

# Tag for ECR (replace with your ECR URI)
docker tag owkai/backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/owkai/backend:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/owkai/backend:latest
```

### 2. ECS Service Deployment

#### Task Definition
```json
{
  "family": "owkai-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "owkai-backend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/owkai/backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:owkai/database/url-xxxxx"
        },
        {
          "name": "JWT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:owkai/jwt/secret-xxxxx"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/owkai-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### ECS Service Configuration
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name owkai-production

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster owkai-production \
  --service-name owkai-backend-service \
  --task-definition owkai-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxx,subnet-yyyyyyyyy],securityGroups=[sg-yyyyyyyyy],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/owkai-backend/xxxxxxxxxxxxxxxxxx,containerName=owkai-backend,containerPort=8000" \
  --enable-execute-command
```

## Frontend Deployment

### 1. Build Frontend Application

```bash
# Clone frontend repository
git clone https://github.com/your-org/owkai-pilot-frontend.git
cd owkai-pilot-frontend

# Install dependencies
npm install

# Build for production
REACT_APP_API_URL=https://api.pilot.owkai.app npm run build

# Verify build
ls -la build/
```

### 2. S3 and CloudFront Setup

#### S3 Bucket Configuration
```bash
# Create S3 bucket for static hosting
aws s3 mb s3://owkai-pilot-frontend

# Configure bucket for website hosting
aws s3 website s3://owkai-pilot-frontend \
  --index-document index.html \
  --error-document error.html

# Set bucket policy for public read access
cat > bucket-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::owkai-pilot-frontend/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket owkai-pilot-frontend \
  --policy file://bucket-policy.json

# Upload build files
aws s3 sync build/ s3://owkai-pilot-frontend/ --delete
```

#### CloudFront Distribution
```bash
# Create CloudFront distribution
cat > cloudfront-config.json << 'EOF'
{
  "CallerReference": "owkai-pilot-$(date +%s)",
  "Comment": "OW-AI Pilot Frontend Distribution",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-owkai-pilot-frontend",
        "DomainName": "owkai-pilot-frontend.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-owkai-pilot-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "MinTTL": 0,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    }
  },
  "Enabled": true,
  "PriceClass": "PriceClass_100"
}
EOF

aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

## Load Balancer Configuration

### 1. Application Load Balancer Setup

```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name owkai-pilot-alb \
  --subnets subnet-xxxxxxxxx subnet-yyyyyyyyy \
  --security-groups sg-xxxxxxxxx \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Create target group
aws elbv2 create-target-group \
  --name owkai-backend-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxxxxxx \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/owkai-pilot-alb/xxxxxxxxxxxxxxxxxx \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/owkai-backend-targets/xxxxxxxxxxxxxxxxxx

# Create HTTP listener (redirect to HTTPS)
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/owkai-pilot-alb/xxxxxxxxxxxxxxxxxx \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'
```

### 2. Health Check Configuration

```bash
# Configure advanced health checks
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/owkai-backend-targets/xxxxxxxxxxxxxxxxxx \
  --health-check-path "/health" \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --health-check-grace-period-seconds 300
```

## SSL/TLS Setup

### 1. Certificate Request via ACM

```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name pilot.owkai.app \
  --subject-alternative-names "*.pilot.owkai.app" \
  --validation-method DNS \
  --key-algorithm RSA_2048

# Get certificate details
aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 2. DNS Validation

```bash
# Add CNAME record to your DNS provider
# Example for Route 53:
aws route53 change-resource-record-sets \
  --hosted-zone-id ZXXXXXXXXXXXXX \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "_validation.pilot.owkai.app",
          "Type": "CNAME",
          "TTL": 300,
          "ResourceRecords": [
            {
              "Value": "_validation.example.acm-validations.aws."
            }
          ]
        }
      }
    ]
  }'
```

### 3. DNS Configuration

```bash
# Point domain to ALB
aws route53 change-resource-record-sets \
  --hosted-zone-id ZXXXXXXXXXXXXX \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "pilot.owkai.app",
          "Type": "A",
          "AliasTarget": {
            "DNSName": "owkai-pilot-alb-xxxxxxxxxx.us-east-1.elb.amazonaws.com",
            "EvaluateTargetHealth": true,
            "HostedZoneId": "Z35SXDOTRQ7X7K"
          }
        }
      }
    ]
  }'
```

## Monitoring Setup

### 1. CloudWatch Configuration

```bash
# Create CloudWatch log groups
aws logs create-log-group --log-group-name /ecs/owkai-backend
aws logs create-log-group --log-group-name /aws/lambda/owkai-monitoring

# Set log retention
aws logs put-retention-policy \
  --log-group-name /ecs/owkai-backend \
  --retention-in-days 30
```

### 2. Custom Metrics and Alarms

```bash
# Create custom metrics for application monitoring
cat > custom-metrics.json << 'EOF'
{
  "MetricData": [
    {
      "MetricName": "PolicyEvaluationTime",
      "Dimensions": [
        {
          "Name": "Environment",
          "Value": "production"
        }
      ],
      "Unit": "Milliseconds",
      "Value": 0.0
    }
  ],
  "Namespace": "OWKAIPlatform/Performance"
}
EOF

# Create CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "OWKAIHighCPUUtilization" \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:owkai-alerts
```

### 3. Application Performance Monitoring

```bash
# Install and configure application monitoring
pip install prometheus-client
pip install opentelemetry-api opentelemetry-sdk

# Configure monitoring endpoints in application
# Add to main.py:
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Production Validation

### 1. Smoke Tests

```bash
#!/bin/bash
# smoke-test.sh - Basic functionality verification

echo "Running OW-AI Platform smoke tests..."

BASE_URL="https://pilot.owkai.app"
API_URL="$BASE_URL/api"

# Test 1: Health check
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $HEALTH_RESPONSE"
    exit 1
fi

# Test 2: Authentication
echo "Testing authentication..."
AUTH_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@owkai.com","password":"admin123"}')

TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
    echo "✅ Authentication passed"
else
    echo "❌ Authentication failed"
    exit 1
fi

# Test 3: Protected endpoint
echo "Testing protected endpoint..."
DASHBOARD_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/agent-control/dashboard")

if [ "$DASHBOARD_RESPONSE" = "200" ]; then
    echo "✅ Protected endpoint access passed"
else
    echo "❌ Protected endpoint access failed: $DASHBOARD_RESPONSE"
    exit 1
fi

echo "🎉 All smoke tests passed!"
```

### 2. Load Testing

```bash
# Install Apache Bench or use a more advanced tool
# Basic load test example:
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" https://pilot.owkai.app/health

# More comprehensive load testing with k6
cat > load-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Sustain 100 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
};

export default function () {
  let response = http.get('https://pilot.owkai.app/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
EOF

k6 run load-test.js
```

### 3. Security Validation

```bash
# SSL/TLS configuration check
sslscan pilot.owkai.app

# Security headers check
curl -I https://pilot.owkai.app

# OWASP ZAP security scan (if available)
zap-baseline.py -t https://pilot.owkai.app
```

## Rollback Procedures

### 1. Application Rollback

```bash
# Rollback ECS service to previous task definition
aws ecs update-service \
  --cluster owkai-production \
  --service owkai-backend-service \
  --task-definition owkai-backend:PREVIOUS_REVISION

# Monitor rollback status
aws ecs wait services-stable \
  --cluster owkai-production \
  --services owkai-backend-service

# Verify rollback success
aws ecs describe-services \
  --cluster owkai-production \
  --services owkai-backend-service
```

### 2. Database Rollback

```bash
# Create database snapshot before rollback
aws rds create-db-snapshot \
  --db-instance-identifier owkai-pilot-db \
  --db-snapshot-identifier owkai-rollback-$(date +%Y%m%d-%H%M%S)

# Rollback database migrations
cd ow-ai-backend
export DATABASE_URL="your_database_url"
alembic downgrade -1  # Rollback one migration
# Or specific revision:
# alembic downgrade REVISION_ID
```

### 3. Frontend Rollback

```bash
# Rollback frontend to previous version
aws s3 sync s3://owkai-pilot-frontend-backup/ s3://owkai-pilot-frontend/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id EXXXXXXXXXXXXX \
  --paths "/*"
```

### 4. Complete Environment Rollback

```bash
#!/bin/bash
# complete-rollback.sh

echo "Initiating complete environment rollback..."

# 1. Rollback application
echo "Rolling back application..."
aws ecs update-service \
  --cluster owkai-production \
  --service owkai-backend-service \
  --task-definition owkai-backend:$PREVIOUS_REVISION

# 2. Rollback database
echo "Rolling back database..."
alembic downgrade $PREVIOUS_DB_REVISION

# 3. Rollback frontend
echo "Rolling back frontend..."
aws s3 sync s3://owkai-pilot-frontend-backup-$BACKUP_DATE/ s3://owkai-pilot-frontend/ --delete

# 4. Invalidate CDN
echo "Invalidating CDN cache..."
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

# 5. Update monitoring
echo "Updating monitoring configuration..."
# Update any monitoring configuration that may have changed

echo "Rollback completed. Running validation tests..."
./smoke-test.sh

if [ $? -eq 0 ]; then
    echo "✅ Rollback successful and validated"
else
    echo "❌ Rollback validation failed - manual intervention required"
    exit 1
fi
```

### 5. Emergency Procedures

#### Complete Service Shutdown
```bash
# Emergency shutdown procedure
aws ecs update-service \
  --cluster owkai-production \
  --service owkai-backend-service \
  --desired-count 0

# Update Route 53 to point to maintenance page
aws route53 change-resource-record-sets \
  --hosted-zone-id ZXXXXXXXXXXXXX \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "pilot.owkai.app",
          "Type": "A",
          "TTL": 60,
          "ResourceRecords": [{"Value": "MAINTENANCE_PAGE_IP"}]
        }
      }
    ]
  }'
```

#### Database Emergency Recovery
```bash
# Restore from latest automated backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier owkai-pilot-db-recovery \
  --db-snapshot-identifier owkai-pilot-db-backup-YYYYMMDD

# Point application to recovery database
aws secretsmanager update-secret \
  --secret-id owkai/database/credentials \
  --secret-string '{"host": "owkai-pilot-db-recovery.cluster-xxx.us-east-1.rds.amazonaws.com", ...}'
```

This deployment guide provides comprehensive procedures for safely deploying, managing, and recovering the OW-AI Platform in production environments. Always test procedures in staging environments before applying to production.