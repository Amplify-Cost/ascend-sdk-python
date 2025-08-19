#!/bin/bash

echo "Fixing API imports in all components..."

# Find all JS/JSX files and update API_BASE_URL usage
find src/components -name "*.jsx" -o -name "*.js" | while read file; do
  if grep -q "API_BASE_URL" "$file"; then
    echo "Updating $file..."
    
    # Add import at the top if not present
    if ! grep -q "import.*API_BASE_URL.*from.*config/api" "$file"; then
      # Insert import after existing imports or at the top
      sed -i '1i import { API_BASE_URL } from "../config/api.js";' "$file"
    fi
    
    # Remove any local API_BASE_URL definitions
    sed -i '/const API_BASE_URL = /d' "$file"
  fi
done

echo "✅ All components updated to use centralized API config"
