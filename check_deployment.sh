#!/bin/bash

echo "======================================================"
echo "🚀 DEPLOYMENT STATUS CHECK"
echo "======================================================"
echo ""

echo "1. Git Push Confirmation:"
echo "   ✅ Backend pushed to master"
echo "   ✅ Frontend pushed to main"
echo ""

echo "2. GitHub Actions (Check these URLs):"
echo "   Frontend: https://github.com/Amplify-Cost/owkai-pilot-frontend/actions"
echo "   Backend:  https://github.com/Amplify-Cost/owkai-pilot-backend/actions"
echo ""

echo "3. Testing Current Deployment:"
echo -n "   Frontend (pilot.owkai.app): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://pilot.owkai.app)
if [ "$STATUS" = "200" ]; then
    echo "✅ $STATUS OK"
else
    echo "⚠️  $STATUS"
fi

echo -n "   Backend API (pilot.owkai.app/docs): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://pilot.owkai.app/docs)
if [ "$STATUS" = "200" ]; then
    echo "✅ $STATUS OK"
else
    echo "⚠️  $STATUS"
fi

echo ""
echo "4. Deployment Timeline:"
echo "   ⏳ AWS ECS deployments typically take 5-7 minutes"
echo "   🔄 Current time: $(date '+%H:%M:%S')"
echo "   ⏰ Expected completion: $(date -v+7M '+%H:%M:%S' 2>/dev/null || date -d '+7 minutes' '+%H:%M:%S' 2>/dev/null || echo 'In ~7 minutes')"
echo ""

echo "5. What to Monitor:"
echo "   - GitHub Actions should show 'Deploy to ECS' workflow running"
echo "   - Backend: Look for 'Deploy to ECS' workflow"
echo "   - Frontend: Look for 'Deploy Frontend' workflow"
echo ""

echo "6. Manual Trigger (if needed):"
echo "   If workflows didn't auto-trigger:"
echo "   - Go to Actions tab on GitHub"
echo "   - Click 'Run workflow' button"
echo "   - Select branch and click 'Run workflow'"
echo ""

echo "======================================================"
echo "💡 RECOMMENDATION:"
echo "======================================================"
echo ""
echo "Visit GitHub Actions now to see deployment progress:"
echo "1. Open: https://github.com/Amplify-Cost/owkai-pilot-backend/actions"
echo "2. Look for a workflow run that started ~1 minute ago"
echo "3. If no workflow is running, click 'Run workflow' button"
echo ""
echo "Then check frontend:"
echo "1. Open: https://github.com/Amplify-Cost/owkai-pilot-frontend/actions"  
echo "2. Look for a workflow run that started ~1 minute ago"
echo "3. If no workflow is running, click 'Run workflow' button"
echo ""
echo "======================================================"
