#!/bin/bash

LISTENER_ARN="arn:aws:elasticloadbalancing:us-east-2:110948415588:listener/app/owkai-pilot-alb/4e3b31109b6f1eb3/3a8ceb96556352f9"
BACKEND_TG="arn:aws:elasticloadbalancing:us-east-2:110948415588:targetgroup/owkai-pilot-backend-tg/f36c394e1d527ae0"

echo "Finding and deleting ALL /alerts/* rules..."

# Get all rules with /alerts/* pattern
RULE_ARNS=$(aws elbv2 describe-rules \
  --listener-arn $LISTENER_ARN \
  --region us-east-2 \
  --query 'Rules[?Conditions[?Values[?contains(@, `/alerts`)]]].RuleArn' \
  --output text)

for RULE_ARN in $RULE_ARNS; do
  echo "Deleting rule: $RULE_ARN"
  aws elbv2 delete-rule --rule-arn $RULE_ARN --region us-east-2
done

echo ""
echo "Creating NEW rule at priority 5 (high priority)..."
aws elbv2 create-rule \
  --listener-arn $LISTENER_ARN \
  --priority 5 \
  --conditions Field=path-pattern,Values='/alerts/*',Field=path-pattern,Values='/alerts' \
  --actions Type=forward,TargetGroupArn=$BACKEND_TG \
  --region us-east-2

echo ""
echo "Waiting 10 seconds for ALB to update..."
sleep 10

echo "Testing /alerts..."
curl -s https://pilot.owkai.app/alerts | head -3

echo ""
echo "If still HTML, wait another 30 seconds and test again"
