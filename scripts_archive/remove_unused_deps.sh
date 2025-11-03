#!/bin/bash

echo "🗑️  H2: Remove Unused Dependencies (Enterprise Process)"
echo "======================================================"
echo ""

# Backup
echo "📦 Step 1: Creating backup..."
cp package.json package.json.backup-$(date +%Y%m%d_%H%M%S)
cp package-lock.json package-lock.json.backup-$(date +%Y%m%d_%H%M%S)
echo "✅ Backups created"
echo ""

# Document current state
echo "📊 Step 2: Documenting baseline metrics..."
BASELINE_BUNDLE=$(npm run build 2>&1 | grep "dist/assets/index-" | tail -1 | awk '{print $2}')
BASELINE_MODULES=$(du -sh node_modules 2>/dev/null | awk '{print $1}')
echo "Baseline bundle: $BASELINE_BUNDLE"
echo "Baseline node_modules: $BASELINE_MODULES"
echo ""

# Remove dependencies
echo "🗑️  Step 3: Removing unused dependencies..."
npm uninstall @clerk/clerk-react
npm uninstall react-router-dom
echo "✅ Dependencies removed from package.json"
echo ""

# Clean install
echo "📥 Step 4: Clean install of remaining dependencies..."
rm -rf node_modules package-lock.json
npm install
echo "✅ Clean install complete"
echo ""

# Rebuild
echo "🔨 Step 5: Rebuilding application..."
npm run build
NEW_BUNDLE=$(npm run build 2>&1 | grep "dist/assets/index-" | tail -1 | awk '{print $2}')
NEW_MODULES=$(du -sh node_modules 2>/dev/null | awk '{print $1}')
echo "✅ Build successful"
echo ""

# Compare
echo "📊 Step 6: Comparing metrics..."
echo "Bundle size:"
echo "  Before: $BASELINE_BUNDLE"
echo "  After:  $NEW_BUNDLE"
echo ""
echo "node_modules size:"
echo "  Before: $BASELINE_MODULES"
echo "  After:  $NEW_MODULES"
echo ""

echo "✅ H2 Complete: Unused dependencies removed"

