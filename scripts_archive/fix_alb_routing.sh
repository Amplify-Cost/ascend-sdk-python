#!/bin/bash

echo "======================================================"
echo "🔧 FIXING ALB ROUTING FOR /alerts ENDPOINT"
echo "======================================================"
echo ""

# Set region
AWS_REGION="us-east-2"

# Step 1: Find the Load Balancer
echo "1. Finding Load Balancer..."
LB_ARN=$(aws elbv2 describe-load-balancers \
  --region $AWS_REGION \
  --query 'LoadBalancers[?contains(LoadBalancerName, `owkai`) || contains(LoadBalancerName, `pilot`)].LoadBalancerArn' \
  --output text 2>/dev/null | head -1)

if [ -z "$LB_ARN" ]; then
  echo "❌ Could not find load balancer"
  echo "Please provide the Load Balancer name or ARN"
  exit 1
fi

echo "   ✅ Found: $LB_ARN"

# Step 2: Find the HTTPS Listener
echo ""
echo "2. Finding HTTPS Listener..."
LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $LB_ARN \
  --region $AWS_REGION \
  --query 'Listeners[?Port==`443`].ListenerArn' \
  --output text 2>/dev/null)

if [ -z "$LISTENER_ARN" ]; then
  echo "❌ Could not find HTTPS listener"
  exit 1
fi

echo "   ✅ Found: $LISTENER_ARN"

# Step 3: Find Backend Target Group
echo ""
echo "3. Finding Backend Target Group..."
BACKEND_TG_ARN=$(aws elbv2 describe-target-groups \
  --region $AWS_REGION \
  --query 'TargetGroups[?contains(TargetGroupName, `backend`)].TargetGroupArn' \
  --output text 2>/dev/null | head -1)

if [ -z "$BACKEND_TG_ARN" ]; then
  echo "❌ Could not find backend target group"
  exit 1
fi

echo "   ✅ Found: $BACKEND_TG_ARN"

# Step 4: Check existing rules
echo ""
echo "4. Checking existing rules..."
aws elbv2 describe-rules \
  --listener-arn $LISTENER_ARN \
  --region $AWS_REGION \
  --query 'Rules[].[Priority,Conditions[0].Values[0]]' \
  --output table

# Step 5: Find next available priority
echo ""
echo "5. Finding next available priority..."
PRIORITIES=$(aws elbv2 describe-rules \
  --listener-arn $LISTENER_ARN \
  --region $AWS_REGION \
  --query 'Rules[?Priority!=`default`].Priority' \
  --output text)

NEXT_PRIORITY=10
for p in $PRIORITIES; do
  if [ "$p" -ge "$NEXT_PRIORITY" ]; then
    NEXT_PRIORITY=$((p + 1))
  fi
done

echo "   ✅ Using priority: $NEXT_PRIORITY"

# Step 6: Create rule for /alerts/*
echo ""
echo "6. Creating ALB rule for /alerts/* → backend..."
aws elbv2 create-rule \
  --listener-arn $LISTENER_ARN \
  --priority $NEXT_PRIORITY \
  --conditions Field=path-pattern,Values='/alerts/*' \
  --actions Type=forward,TargetGroupArn=$BACKEND_TG_ARN \
  --region $AWS_REGION

if [ $? -eq 0 ]; then
  echo "   ✅ Rule created successfully!"
else
  echo "   ❌ Failed to create rule"
  exit 1
fi

# Step 7: Test the fix
echo ""
echo "7. Testing the fix..."
sleep 5
echo "   Testing /alerts endpoint..."
RESPONSE=$(curl -s https://pilot.owkai.app/alerts)

if echo "$RESPONSE" | grep -q "<!DOCTYPE"; then
  echo "   ❌ Still returning HTML (frontend)"
  echo "   Wait 30 seconds for ALB to update and try again"
else
  echo "   ✅ Returns JSON (backend)!"
fi

echo ""
echo "======================================================"
echo "✅ ALB ROUTING FIX COMPLETE"
echo "======================================================"
echo ""
echo "If /alerts still returns HTML, wait 30-60 seconds"
echo "for ALB changes to propagate, then test again."
echo ""
echo "Test with: curl https://pilot.owkai.app/alerts"
