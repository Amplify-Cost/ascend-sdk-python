#!/bin/bash

echo "=== AWS Infrastructure Status Check ==="
echo ""

echo "1. ECS Cluster:"
aws ecs describe-clusters --clusters owkai-test-cluster --region us-east-2 --query 'clusters[0].[clusterName,status,runningTasksCount]' --output table

echo ""
echo "2. Running ECS Tasks:"
aws ecs list-tasks --cluster owkai-test-cluster --region us-east-2

echo ""
echo "3. ECR Repository:"
aws ecr describe-repositories --repository-names owkai-test-compliance-agent --region us-east-2 --query 'repositories[0].[repositoryName,repositoryUri]' --output table

echo ""
echo "4. ECR Images:"
aws ecr list-images --repository-name owkai-test-compliance-agent --region us-east-2 --query 'imageIds[*].imageTag' --output table

echo ""
echo "5. VPC:"
aws ec2 describe-vpcs --vpc-ids vpc-0a68f4ede22bce87c --region us-east-2 --query 'Vpcs[0].[VpcId,CidrBlock,State]' --output table
