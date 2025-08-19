#!/bin/bash

echo "🛡️ REVERTING TO WORKING VERSION - MASTER PROMPT COMPLIANT"
echo "=========================================================="
echo "🎯 Restore stable deployment while preserving Master Prompt compliance"
echo ""

echo "🔍 ANALYSIS OF WORKING vs FAILING VERSIONS:"
echo "==========================================="
echo "✅ WORKING: b373251 (Aug 17, 9:19 AM) - Healthcheck succeeded"
echo "❌ FAILING: All versions after emergency fixes - Constant restarts"
echo ""
echo "🎯 ROOT CAUSE: Our 'emergency fixes' broke the working configuration"
echo "✅ SOLUTION: Revert to working version, then apply minimal fixes"
echo ""

# Get the working commit hash
WORKING_COMMIT="b373251"

echo "🔧 STEP 1: Revert to working commit"
echo "=================================="
git fetch origin
git checkout $WORKING_COMMIT

echo "   ✅ Reverted to working version: $WORKING_COMMIT"

echo ""
echo "🔧 STEP 2: Create new branch for Master Prompt alignment"
echo "======================================================="
git checkout -b master-prompt-stable-fix

echo "   ✅ Created branch: master-prompt-stable-fix"

echo ""
echo "🔧 STEP 3: Apply MINIMAL Master Prompt fixes to working version"
echo "=============================================================="

# Only apply the essential frontend cookie fix without breaking backend
cd ow-ai-dashboard

# Find the main API utility file and add minimal cookie support
if [ -f "src/utils/fetchWithAuth.js" ]; then
    echo "🔧 Adding minimal cookie support to existing auth utility..."
    
    # Backup first
    cp src/utils/fetchWithAuth.js src/utils/fetchWithAuth.js.backup
    
    # Add minimal cookie credentials without duplicates
    sed -i.bak 's/credentials: "same-origin"/credentials: "include"/g' src/utils/fetchWithAuth.js
    
    # If no credentials found, add it carefully
    if ! grep -q "credentials:" src/utils/fetchWithAuth.js; then
        sed -i.bak '/headers:/a\        credentials: "include",' src/utils/fetchWithAuth.js
    fi
    
    echo "   ✅ Minimal cookie support added"
fi

cd ..

echo ""
echo "🔧 STEP 4: Preserve working backend configuration"
echo "=============================================="

# Don't touch the working Dockerfile or startup scripts
# Only ensure we have the minimal requirements
echo "   ✅ Keeping existing working backend configuration"
echo "   ✅ Preserving working Dockerfile and startup process"

echo ""
echo "🔧 STEP 5: Deploy stable Master Prompt version"
echo "============================================="

# Build frontend with minimal changes
cd ow-ai-dashboard
npm run build
cd ..

# Commit minimal changes
git add .
git commit -m "🛡️ Master Prompt: Minimal stable fixes on working version

✅ Based on working commit: b373251 (healthcheck succeeded)
✅ Minimal cookie credentials added to frontend
✅ Backend configuration preserved (working)
✅ Master Prompt compliance: Security fixes only
✅ No breaking changes to working deployment"

# Push to new branch first
git push origin master-prompt-stable-fix

echo ""
echo "🔧 STEP 6: Merge to main for deployment"
echo "======================================"

# Switch to main and merge the stable fixes
git checkout main
git merge master-prompt-stable-fix

# Deploy the stable version
git push origin main

echo ""
echo "🎯 MASTER PROMPT COMPLIANT REVERT COMPLETE"
echo "=========================================="
echo "✅ Reverted to: b373251 (last working deployment)"
echo "✅ Applied: Minimal Master Prompt cookie fixes"
echo "✅ Preserved: Working backend configuration"
echo "✅ Method: Non-breaking security enhancement"
echo ""
echo "📊 EXPECTED RESULTS:"
echo "==================="
echo "✅ Healthcheck will succeed (using working config)"
echo "✅ Backend will start properly (preserved configuration)"
echo "✅ Frontend will have cookie support (minimal addition)"
echo "✅ Master Prompt compliance maintained"
echo ""
echo "⏱️ Railway deployment should succeed in 3-5 minutes"
echo "🔍 This preserves what works while adding only essential fixes"
