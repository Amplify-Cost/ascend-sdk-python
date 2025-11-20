#!/bin/bash
set -e

# Load configuration
source /Users/mac_001/OW_AI_Project/enterprise-testing-environment/live-deployment/config.sh

echo "==========================================="
echo "Deploying Compliance Monitoring Agent"
echo "==========================================="
echo ""

# 1. Build Docker image
echo "🐳 Building Docker image..."
cd /Users/mac_001/OW_AI_Project/enterprise-testing-environment/agents/compliance-monitor

docker build --platform linux/amd64 -t compliance-agent:latest .

echo "✅ Docker image built"

# 2. Tag for ECR
echo "🏷️  Tagging image for ECR..."
docker tag compliance-agent:latest $ECR_URI:latest
docker tag compliance-agent:latest $ECR_URI:v1

# 3. Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

# 4. Push to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:latest
docker push $ECR_URI:v1

echo "✅ Image pushed to ECR"

# 5. Create IAM roles if they don't exist
echo "🔑 Creating IAM roles..."

# Task execution role
aws iam create-role \
  --role-name ${PROJECT}-ecs-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' --region $REGION 2>/dev/null || true

aws iam attach-role-policy \
  --role-name ${PROJECT}-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --region $REGION 2>/dev/null || true

# Task role  
aws iam create-role \
  --role-name ${PROJECT}-ecs-task-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' --region $REGION 2>/dev/null || true

EXECUTION_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT}-ecs-execution-role"
TASK_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT}-ecs-task-role"

echo "✅ IAM roles ready"

# 6. Register task definition
echo "📝 Registering ECS task definition..."

cat > /tmp/task-def.json << EOFTASK
{
  "family": "${PROJECT}-compliance-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "$EXECUTION_ROLE_ARN",
  "taskRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "compliance-agent",
      "image": "${ECR_URI}:latest",
      "essential": true,
      "environment": [
        {"name": "OWKAI_URL", "value": "https://pilot.owkai.app"},
        {"name": "OWKAI_EMAIL", "value": "admin@owkai.com"},
        {"name": "OWKAI_REDACTED-CREDENTIAL", "value": "admin123"},
        {"name": "SCAN_INTERVAL", "value": "60"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "$LOG_GROUP",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "compliance-agent"
        }
      }
    }
  ]
}
EOFTASK

aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-def.json \
  --region $REGION >/dev/null

echo "✅ Task definition registered"

# 7. Run task
echo "🚀 Starting agent on ECS..."

TASK_ARN=$(aws ecs run-task \
  --cluster $ECS_CLUSTER \
  --task-definition ${PROJECT}-compliance-agent \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
  --region $REGION \
  --query 'tasks[0].taskArn' \
  --output text)

echo "✅ Agent started: $TASK_ARN"

# Save task ARN
echo "export TASK_ARN='$TASK_ARN'" >> /Users/mac_001/OW_AI_Project/enterprise-testing-environment/live-deployment/config.sh

echo ""
echo "==========================================="
echo "✅ Agent Deployed Successfully!"
echo "==========================================="
echo ""
echo "Task ARN: $TASK_ARN"
echo ""
echo "View logs:"
echo "  aws logs tail $LOG_GROUP --follow --region $REGION"
echo ""
echo "Check task status:"
echo "  aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN --region $REGION"
echo ""
