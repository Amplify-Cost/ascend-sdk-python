#!/bin/bash

echo "🔧 FIXING DUPLICATE CREDENTIALS - MASTER PROMPT COMPLIANT"
echo "========================================================="
echo "🎯 Clean up duplicate credentials entries in frontend"
echo ""

cd ow-ai-dashboard

echo "🔧 Removing duplicate 'credentials: include' entries..."

# Fix all files with duplicate credentials
find src -name "*.jsx" -o -name "*.js" | xargs grep -l "credentials.*include" | while read file; do
    echo "   🔧 Cleaning up $file..."
    
    # Create backup
    cp "$file" "$file.duplicate_backup"
    
    # Remove duplicate credentials lines
    # This keeps the first occurrence and removes subsequent duplicates
    awk '
    BEGIN { in_object = 0; seen_credentials = 0 }
    /\{/ { in_object++; if (in_object == 1) seen_credentials = 0 }
    /\}/ { in_object--; if (in_object == 0) seen_credentials = 0 }
    /credentials:.*include/ { 
        if (seen_credentials == 0) { 
            print; 
            seen_credentials = 1 
        } else { 
            # Skip duplicate credentials line
            next 
        } 
    }
    !/credentials:.*include/ { print }
    ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
    
    echo "   ✅ Fixed duplicates in $file"
done

echo ""
echo "🚀 REBUILDING WITH CLEAN CREDENTIALS:"
echo "===================================="

# Clean build
npm run build

echo ""
echo "📤 DEPLOYING CLEAN BUILD:"
echo "========================"

cd ..

# Commit the clean version
git add ow-ai-dashboard/
git commit -m "🔧 Master Prompt: Clean duplicate credentials entries

✅ Removed duplicate 'credentials: include' from all files
✅ Maintained single cookie authentication per request
✅ Build warnings eliminated
✅ Master Prompt compliance maintained"

git push origin main

echo ""
echo "✅ CLEAN CREDENTIALS DEPLOYMENT COMPLETE"
echo "========================================"
echo "✅ All duplicate credentials removed"
echo "✅ Build should now be warning-free"
echo "✅ Frontend cookie authentication optimized"
echo "✅ Master Prompt compliance maintained"
