#!/bin/bash
set -e

# Load configuration
source /Users/mac_001/OW_AI_Project/enterprise-testing-environment/live-deployment/config.sh

echo "=========================================="
echo "OW-KAI Enterprise Testing Environment"
echo "CLEANUP SCRIPT"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will delete ALL resources"
echo "   - ECS tasks and cluster"
echo "   - ECR repository and images"
echo "   - VPC, subnets, and security groups"
echo "   - IAM roles"
echo "   - CloudWatch log groups"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# 1. Stop all running tasks
echo "🛑 Stopping all running tasks..."
TASKS=$(aws ecs list-tasks \
  --cluster $ECS_CLUSTER \
  --region $REGION \
  --query 'taskArns[]' \
  --output text)

if [ ! -z "$TASKS" ]; then
    for TASK in $TASKS; do
        echo "   Stopping task: $TASK"
        aws ecs stop-task \
          --cluster $ECS_CLUSTER \
          --task $TASK \
          --region $REGION \
          --output text >/dev/null
    done
    echo "   Waiting for tasks to stop..."
    sleep 10
else
    echo "   No tasks running"
fi

# 2. Delete ECS service (if any)
echo "🗑️  Deleting ECS services..."
SERVICES=$(aws ecs list-services \
  --cluster $ECS_CLUSTER \
  --region $REGION \
  --query 'serviceArns[]' \
  --output text)

if [ ! -z "$SERVICES" ]; then
    for SERVICE in $SERVICES; do
        SERVICE_NAME=$(basename $SERVICE)
        echo "   Deleting service: $SERVICE_NAME"
        aws ecs delete-service \
          --cluster $ECS_CLUSTER \
          --service $SERVICE_NAME \
          --force \
          --region $REGION \
          --output text >/dev/null
    done
else
    echo "   No services to delete"
fi

# 3. Deregister task definitions
echo "🗑️  Deregistering task definitions..."
TASK_DEFS=$(aws ecs list-task-definitions \
  --family-prefix ${PROJECT}-compliance-agent \
  --region $REGION \
  --query 'taskDefinitionArns[]' \
  --output text)

if [ ! -z "$TASK_DEFS" ]; then
    for TD in $TASK_DEFS; do
        echo "   Deregistering: $(basename $TD)"
        aws ecs deregister-task-definition \
          --task-definition $TD \
          --region $REGION \
          --output text >/dev/null
    done
else
    echo "   No task definitions to deregister"
fi

# 4. Delete ECS cluster
echo "🗑️  Deleting ECS cluster..."
aws ecs delete-cluster \
  --cluster $ECS_CLUSTER \
  --region $REGION \
  --output text >/dev/null || echo "   Cluster already deleted"

# 5. Delete ECR repository
echo "🗑️  Deleting ECR repository (including all images)..."
aws ecr delete-repository \
  --repository-name ${PROJECT}-compliance-agent \
  --region $REGION \
  --force \
  --output text >/dev/null || echo "   Repository already deleted"

# 6. Delete CloudWatch log group
echo "🗑️  Deleting CloudWatch log group..."
aws logs delete-log-group \
  --log-group-name $LOG_GROUP \
  --region $REGION || echo "   Log group already deleted"

# 7. Wait for tasks to fully stop
echo "⏳ Waiting for all resources to be released..."
sleep 15

# 8. Detach IAM policies and delete roles
echo "🗑️  Deleting IAM roles..."
for ROLE in "${PROJECT}-ecs-execution-role" "${PROJECT}-ecs-task-role"; do
    echo "   Detaching policies from $ROLE..."
    POLICIES=$(aws iam list-attached-role-policies \
      --role-name $ROLE \
      --query 'AttachedPolicies[].PolicyArn' \
      --output text 2>/dev/null || true)

    if [ ! -z "$POLICIES" ]; then
        for POLICY in $POLICIES; do
            aws iam detach-role-policy \
              --role-name $ROLE \
              --policy-arn $POLICY \
              --region $REGION 2>/dev/null || true
        done
    fi

    echo "   Deleting role $ROLE..."
    aws iam delete-role \
      --role-name $ROLE \
      --region $REGION 2>/dev/null || echo "      Role not found"
done

# 9. Delete security group
echo "🗑️  Deleting security group..."
aws ec2 delete-security-group \
  --group-id $SECURITY_GROUP_ID \
  --region $REGION || echo "   Security group already deleted"

# 10. Delete subnet
echo "🗑️  Deleting subnet..."
aws ec2 delete-subnet \
  --subnet-id $SUBNET_ID \
  --region $REGION || echo "   Subnet already deleted"

# 11. Detach and delete internet gateway
echo "🗑️  Deleting internet gateway..."
IGW_ID=$(aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
  --region $REGION \
  --query 'InternetGateways[0].InternetGatewayId' \
  --output text 2>/dev/null || true)

if [ ! -z "$IGW_ID" ] && [ "$IGW_ID" != "None" ]; then
    echo "   Detaching IGW: $IGW_ID"
    aws ec2 detach-internet-gateway \
      --internet-gateway-id $IGW_ID \
      --vpc-id $VPC_ID \
      --region $REGION 2>/dev/null || true

    echo "   Deleting IGW: $IGW_ID"
    aws ec2 delete-internet-gateway \
      --internet-gateway-id $IGW_ID \
      --region $REGION 2>/dev/null || true
else
    echo "   No internet gateway found"
fi

# 12. Delete route table
echo "🗑️  Deleting route tables..."
ROUTE_TABLES=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --region $REGION \
  --query 'RouteTables[?Associations[0].Main==`false`].RouteTableId' \
  --output text 2>/dev/null || true)

if [ ! -z "$ROUTE_TABLES" ]; then
    for RT in $ROUTE_TABLES; do
        echo "   Deleting route table: $RT"
        aws ec2 delete-route-table \
          --route-table-id $RT \
          --region $REGION 2>/dev/null || true
    done
else
    echo "   No custom route tables to delete"
fi

# 13. Delete VPC
echo "🗑️  Deleting VPC..."
aws ec2 delete-vpc \
  --vpc-id $VPC_ID \
  --region $REGION || echo "   VPC already deleted"

# 14. Clean up local config file
echo "🗑️  Cleaning up configuration files..."
rm -f /Users/mac_001/OW_AI_Project/enterprise-testing-environment/live-deployment/config.sh

echo ""
echo "=========================================="
echo "✅ CLEANUP COMPLETED"
echo "=========================================="
echo ""
echo "All resources have been deleted:"
echo "   ✓ ECS cluster and tasks"
echo "   ✓ ECR repository"
echo "   ✓ IAM roles"
echo "   ✓ CloudWatch logs"
echo "   ✓ VPC and networking"
echo ""
echo "Your AWS account is clean!"
echo ""

# Summary of deleted resources
echo "Summary of deleted resources:"
echo "   VPC:              $VPC_ID"
echo "   Subnet:           $SUBNET_ID"
echo "   Security Group:   $SECURITY_GROUP_ID"
echo "   ECS Cluster:      $ECS_CLUSTER"
echo "   ECR Repository:   ${PROJECT}-compliance-agent"
echo "   Log Group:        $LOG_GROUP"
echo "   IAM Roles:        ${PROJECT}-ecs-execution-role, ${PROJECT}-ecs-task-role"
echo ""
