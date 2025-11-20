# OW-KAI Enterprise Testing Environment - Access Guide

## Overview
This guide shows you how to access and monitor your running compliance monitoring agent deployed on AWS ECS.

## AWS Account Information
- **Account ID**: 110948415588
- **Region**: us-east-2 (US East Ohio)
- **Environment**: owkai-test

## Infrastructure Deployed

### 1. Network Infrastructure
- **VPC ID**: vpc-0a68f4ede22bce87c
- **CIDR Block**: 10.100.0.0/16
- **Subnet ID**: subnet-0be319bcecde37fe7
- **Security Group**: sg-0a4fd2e9932848396

### 2. ECS Resources
- **Cluster**: owkai-test-cluster
- **Task Definition**: owkai-test-compliance-agent
- **Running Task**: 5e619766ef56443b8c688e2ea7c8cb88

### 3. Container Registry
- **ECR Repository**: 110948415588.dkr.ecr.us-east-2.amazonaws.com/owkai-test-compliance-agent
- **Image Tags**: latest, v1, v2

### 4. Logging
- **CloudWatch Log Group**: /ecs/owkai-test
- **Log Stream**: compliance-agent/compliance-agent/[task-id]

## How to Access via AWS Console

### Step 1: Login to AWS Console
1. Go to https://console.aws.amazon.com/
2. Sign in with your credentials for account **110948415588**
3. Select region: **US East (Ohio) us-east-2**

### Step 2: View ECS Cluster
1. Navigate to **ECS (Elastic Container Service)**
2. Click on cluster: **owkai-test-cluster**
3. You'll see your running task listed

### Step 3: View Running Task
1. Click on the **Tasks** tab
2. Click on the running task ID: **5e619766ef56443b8c688e2ea7c8cb88**
3. You can see:
   - Task status (RUNNING)
   - Container status
   - Network configuration
   - Task definition details

### Step 4: View Real-Time Logs
1. From the task details page, click on the **Logs** tab
2. OR navigate to **CloudWatch** > **Log Groups** > **/ecs/owkai-test**
3. Click on the latest log stream: **compliance-agent/compliance-agent/5e619766ef56443b8c688e2ea7c8cb88**
4. You'll see real-time compliance scanning activity

## How to Access via AWS CLI

### Prerequisites
Ensure your AWS CLI is configured with credentials for account 110948415588

### View ECS Task Status
```bash
aws ecs describe-tasks \
  --cluster owkai-test-cluster \
  --tasks 5e619766ef56443b8c688e2ea7c8cb88 \
  --region us-east-2 \
  --query 'tasks[0].{Status:lastStatus,Health:healthStatus,Started:startedAt}' \
  --output table
```

### View Real-Time Logs
```bash
# View latest logs
aws logs tail /ecs/owkai-test --follow --region us-east-2

# Or get specific log stream
aws logs get-log-events \
  --log-group-name /ecs/owkai-test \
  --log-stream-name compliance-agent/compliance-agent/5e619766ef56443b8c688e2ea7c8cb88 \
  --region us-east-2 \
  --limit 50 \
  --query 'events[*].message' \
  --output text
```

### List All Running Tasks
```bash
aws ecs list-tasks \
  --cluster owkai-test-cluster \
  --region us-east-2
```

### View Container Images in ECR
```bash
aws ecr list-images \
  --repository-name owkai-test-compliance-agent \
  --region us-east-2 \
  --output table
```

## What the Agent Does

### Compliance Monitoring Agent
The agent continuously monitors AI models and actions on pilot.owkai.app for:

1. **SOC2 Compliance**
   - CC6.1: Logical access controls
   - CC7.2: System operations monitoring
   - CC8.1: Change management

2. **GDPR Compliance**
   - Article 5: Data processing principles
   - Article 25: Data protection by design
   - Article 32: Security of processing

3. **HIPAA Compliance**
   - Administrative Safeguards
   - Physical Safeguards
   - Technical Safeguards

### Scan Frequency
- Scans run every **60 seconds**
- Each scan checks all models/actions from the unified governance endpoint
- Compliance results are logged to CloudWatch

### Current Activity
Based on the latest logs, the agent is:
- ✅ Successfully authenticating to pilot.owkai.app
- ✅ Retrieving 10 models/actions per scan
- ✅ Detecting compliance violations:
  - **Risk Level 65**: Models missing owner/access control
  - Framework: SOC2 (CC6.1 violation)
- ✅ Running continuously every 60 seconds

## Network Configuration

### Security Group Rules
- **Outbound**: HTTPS (443) to 0.0.0.0/0 (allows agent to reach pilot.owkai.app)
- **Inbound**: None (agent doesn't accept incoming connections)

### Public IP
The task has a public IP assigned for outbound internet access

## Cost Information

### Estimated Costs (per hour)
- **ECS Fargate Task**: $0.012/hour (0.25 vCPU, 0.5 GB memory)
- **NAT Gateway**: N/A (using public subnet)
- **CloudWatch Logs**: ~$0.50/GB ingested
- **Data Transfer**: Minimal (outbound to pilot.owkai.app)

### Daily Cost Estimate: ~$0.30-$0.50

## Monitoring and Troubleshooting

### Check if Agent is Running
```bash
aws ecs describe-tasks \
  --cluster owkai-test-cluster \
  --tasks 5e619766ef56443b8c688e2ea7c8cb88 \
  --region us-east-2 \
  --query 'tasks[0].lastStatus'
```

### Check for Errors in Logs
```bash
aws logs filter-log-events \
  --log-group-name /ecs/owkai-test \
  --filter-pattern "ERROR" \
  --region us-east-2 \
  --query 'events[*].message'
```

### Restart the Agent
```bash
# Stop current task
aws ecs stop-task \
  --cluster owkai-test-cluster \
  --task 5e619766ef56443b8c688e2ea7c8cb88 \
  --region us-east-2

# Start new task
aws ecs run-task \
  --cluster owkai-test-cluster \
  --task-definition owkai-test-compliance-agent \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0be319bcecde37fe7],securityGroups=[sg-0a4fd2e9932848396],assignPublicIp=ENABLED}" \
  --region us-east-2
```

## Next Steps

### To Add More Agents
1. Create new agent code (e.g., risk_assessment_agent.py)
2. Build Docker image
3. Push to ECR
4. Register new task definition
5. Run task on same ECS cluster

### To Modify Agent Behavior
1. Edit agent code in `enterprise-testing-environment/agents/compliance-monitor/compliance_agent.py`
2. Rebuild Docker image with new version tag
3. Push to ECR
4. Stop old task
5. Start new task with updated image

### To Clean Up Everything
See `CLEANUP.sh` for automated teardown of all resources

## Support

For issues or questions:
1. Check CloudWatch logs first
2. Verify task status in ECS console
3. Check security group rules
4. Review IAM role permissions

## Important Notes

- The agent uses credentials (admin@owkai.com/admin123) embedded in the task definition
- For production use, store credentials in AWS Secrets Manager
- The agent runs continuously until manually stopped
- All logs are retained in CloudWatch (default retention: never expire)
- Remember to clean up resources when testing is complete to avoid ongoing charges
