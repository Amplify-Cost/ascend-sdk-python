#!/bin/bash
echo "🔍 Finding CREATE workflow call in frontend..."
echo "=" * 80

# Search for the workflows/create endpoint call
grep -r "workflows/create" src/components/*.jsx

echo ""
echo "Found in these components:"
grep -l "workflows/create" src/components/*.jsx

echo ""
echo "Let's see the exact code:"
for file in $(grep -l "workflows/create" src/components/*.jsx); do
    echo ""
    echo "=== $file ==="
    grep -B5 -A5 "workflows/create" "$file"
done
