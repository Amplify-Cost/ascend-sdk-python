#!/bin/bash
echo "🔍 Finding workflow create data structure..."

# Find where workflows/create is called
grep -A20 "workflows/create" src/components/*.jsx | grep -A15 "fetch\|body\|JSON.stringify"
