#!/bin/bash

echo "🔍 DIRECTORY STRUCTURE DIAGNOSTIC"
echo "================================="
echo ""

# Show current directory
echo "📍 Current Directory:"
pwd
echo ""

# List contents of current directory
echo "📁 Current Directory Contents:"
ls -la
echo ""

# Look for package.json in various locations
echo "🔍 Searching for package.json files:"
find . -name "package.json" -type f 2>/dev/null
echo ""

# Look for OW_AI related directories
echo "🔍 Searching for project directories:"
find . -name "*OW*" -type d 2>/dev/null
find . -name "*ow-ai*" -type d 2>/dev/null
echo ""

# Check if we have the main project files
echo "🔍 Looking for key project files:"
if [ -f "main.py" ]; then
    echo "✅ main.py found in current directory"
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found in current directory"
fi

if [ -d "ow-ai-dashboard" ]; then
    echo "✅ ow-ai-dashboard directory found"
    echo "📁 Contents of ow-ai-dashboard:"
    ls -la ow-ai-dashboard/
else
    echo "❌ ow-ai-dashboard directory not found"
fi

echo ""
echo "🎯 RECOMMENDED ACTION:"
if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    echo "✅ You are in the correct project root directory"
    echo "🔧 Re-run the frontend recovery script"
else
    echo "❌ You need to navigate to the correct project directory"
    echo "💡 Try: cd OW_AI_Project"
    echo "💡 Or find the directory with: find ~ -name 'main.py' -type f 2>/dev/null"
fi
