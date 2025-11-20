#!/bin/bash
set -e

# OW-KAI Enterprise Testing Environment - Infrastructure Setup
# Creates lightweight VPC, ECS cluster, and agent infrastructure

PROJECT="owkai-test"
REGION="us-east-2"

echo "========================================="
echo "OW-KAI Enterprise Testing Environment"
echo "Creating AWS Infrastructure"
echo "========================================="
echo ""

# 1. Create VPC
echo "📦 Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.100.0.0/16 \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$PROJECT-vpc},{Key=Project,Value=$PROJECT}]" \
  --region $REGION \
  --query 'Vpc.VpcId' \
  --output text)

echo "✅ VPC created: $VPC_ID"

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $REGION
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --region $REGION

# 2. Create Internet Gateway
echo "🌐 Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=$PROJECT-igw},{Key=Project,Value=$PROJECT}]" \
  --region $REGION \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID --region $REGION
echo "✅ Internet Gateway created: $IGW_ID"

# 3. Create Public Subnet
echo "🔌 Creating public subnet..."
SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.100.1.0/24 \
  --availability-zone ${REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PROJECT-public-1},{Key=Project,Value=$PROJECT}]" \
  --region $REGION \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Subnet created: $SUBNET_ID"

# 4. Create Route Table
echo "🛣️  Creating route table..."
RT_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=$PROJECT-public-rt},{Key=Project,Value=$PROJECT}]" \
  --region $REGION \
  --query 'RouteTable.RouteTableId' \
  --output text)

aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $REGION
aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET_ID --region $REGION
echo "✅ Route table created: $RT_ID"

# 5. Create Security Group
echo "🔒 Creating security group..."
SG_ID=$(aws ec2 create-security-group \
  --group-name $PROJECT-ecs-sg \
  --description "Security group for OW-KAI test agents" \
  --vpc-id $VPC_ID \
  --region $REGION \
  --query 'GroupId' \
  --output text)

# Allow outbound HTTPS
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --ip-permissions IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges="[{CidrIp=0.0.0.0/0,Description='HTTPS to OW-KAI'}]" \
  --region $REGION 2>/dev/null || true

echo "✅ Security group created: $SG_ID"

# 6. Create ECS Cluster
echo "🐳 Creating ECS cluster..."
aws ecs create-cluster \
  --cluster-name $PROJECT-cluster \
  --region $REGION \
  --tags key=Project,value=$PROJECT >/dev/null

echo "✅ ECS cluster created: $PROJECT-cluster"

# 7. Create CloudWatch Log Group
echo "📝 Creating log group..."
aws logs create-log-group \
  --log-group-name /ecs/$PROJECT \
  --region $REGION 2>/dev/null || true

aws logs put-retention-policy \
  --log-group-name /ecs/$PROJECT \
  --retention-in-days 7 \
  --region $REGION

echo "✅ Log group created: /ecs/$PROJECT"

# 8. Create ECR Repository
echo "📦 Creating ECR repository..."
aws ecr create-repository \
  --repository-name $PROJECT-compliance-agent \
  --region $REGION \
  --tags Key=Project,Value=$PROJECT 2>/dev/null || true

ECR_URI=$(aws ecr describe-repositories \
  --repository-names $PROJECT-compliance-agent \
  --region $REGION \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo "✅ ECR repository created: $ECR_URI"

# Save configuration
cat > /Users/mac_001/OW_AI_Project/enterprise-testing-environment/live-deployment/config.sh << EOFCONFIG
# OW-KAI Enterprise Testing Environment Configuration
export PROJECT="$PROJECT"
export REGION="$REGION"
export VPC_ID="$VPC_ID"
export SUBNET_ID="$SUBNET_ID"
export SECURITY_GROUP_ID="$SG_ID"
export ECS_CLUSTER="$PROJECT-cluster"
export LOG_GROUP="/ecs/$PROJECT"
export ECR_URI="$ECR_URI"
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
EOFCONFIG

echo ""
echo "========================================="
echo "✅ Infrastructure Created Successfully!"
echo "========================================="
echo ""
echo "Configuration saved to: live-deployment/config.sh"
echo ""
echo "Resources created:"
echo "  VPC:              $VPC_ID"
echo "  Subnet:           $SUBNET_ID"
echo "  Security Group:   $SG_ID"
echo "  ECS Cluster:      $PROJECT-cluster"
echo "  ECR Repository:   $ECR_URI"
echo "  Log Group:        /ecs/$PROJECT"
echo ""
echo "Next step: Build and deploy agents"
echo ""
