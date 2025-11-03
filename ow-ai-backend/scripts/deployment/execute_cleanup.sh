#!/bin/bash
echo "🎯 EXECUTING ENTERPRISE CLEANUP"
echo "════════════════════════════════════════"

# Safety: Commit and backup
git add -A
git commit -m "checkpoint: Before enterprise cleanup" || true
git branch cleanup-backup-$(date +%Y%m%d_%H%M%S)

# Phase 1: Create Structure
echo "🏗️ Creating directory structure..."
mkdir -p config scripts/{database,deployment,maintenance,development}
mkdir -p docs/{api,architecture,deployment}
mkdir -p archive/{backups,old-scripts,temp-files}
mkdir -p deployment/{docker,aws}

# Phase 2: Archive backups (keep NOTHING in root with .backup/.bak/.old)
echo "📦 Archiving backup files..."
find . -maxdepth 1 -type f \( -name "*.backup*" -o -name "*.bak" -o -name "*.old*" \) -exec mv {} archive/backups/ \; 2>/dev/null

# Phase 3: Archive temp files
echo "🗂️ Archiving temporary files..."
find . -maxdepth 1 -type f \( -name "test_*.py" -o -name "temp_*.py" -o -name "debug_*.py" -o -name "fix_*.py" -o -name "add_*.py" -o -name "check_*.py" -o -name "try_*.py" \) -exec mv {} archive/temp-files/ \; 2>/dev/null

# Phase 4: Organize scripts
echo "📝 Organizing scripts..."
find . -maxdepth 1 -type f \( -name "*database*.py" -o -name "create_*.py" -o -name "seed_*.py" -o -name "populate_*.py" -o -name "migrate_*.py" \) ! -name "database.py" -exec mv {} scripts/database/ \; 2>/dev/null

find . -maxdepth 1 -type f \( -name "deploy_*.py" -o -name "*deployment*.py" -o -name "*.sh" \) -exec mv {} scripts/deployment/ \; 2>/dev/null

find . -maxdepth 1 -type f \( -name "analyze*.py" -o -name "audit*.py" -o -name "diagnose*.py" -o -name "validate*.py" \) -exec mv {} scripts/development/ \; 2>/dev/null

# Phase 5: Organize docs
echo "📚 Organizing documentation..."
find . -maxdepth 1 -type f -name "*.md" ! -name "README.md" -exec mv {} docs/architecture/ \; 2>/dev/null
find . -maxdepth 1 -type f -name "*.html" -exec mv {} docs/api/ \; 2>/dev/null
find . -maxdepth 1 -type f -name "*.txt" -exec mv {} docs/ \; 2>/dev/null

# Phase 6: Organize deployment
echo "🚀 Organizing deployment files..."
find . -maxdepth 1 -type f -name "Dockerfile*" -exec mv {} deployment/docker/ \; 2>/dev/null
find . -maxdepth 1 -type f -name "*task*.json" -exec mv {} deployment/aws/ \; 2>/dev/null
find . -maxdepth 1 -type f -name "*.sql" -exec mv {} scripts/database/ \; 2>/dev/null

# Phase 7: Move remaining Python utility files to old-scripts
echo "🔧 Archiving old utility scripts..."
find . -maxdepth 1 -type f -name "*.py" ! -name "main.py" ! -name "database.py" ! -name "dependencies.py" ! -name "auth_utils.py" ! -name "*_utils.py" ! -name "models.py" ! -name "schemas.py" -exec mv {} archive/old-scripts/ \; 2>/dev/null

# Phase 8: Move remaining files
echo "🗄️ Archiving miscellaneous files..."
find . -maxdepth 1 -type f -name "*.json" ! -name "package*.json" -exec mv {} archive/old-scripts/ \; 2>/dev/null
find . -maxdepth 1 -type f -name "*.zip" -exec mv {} archive/old-scripts/ \; 2>/dev/null
find . -maxdepth 1 -type f -name "*.log" -exec mv {} archive/old-scripts/ \; 2>/dev/null

echo ""
echo "✅ CLEANUP COMPLETE!"
echo ""
echo "📊 Results:"
echo "Root directory now contains:"
ls -1 | wc -l | xargs echo "  Files/folders:"
echo ""
echo "📁 New structure:"
tree -L 1 -d . 2>/dev/null || ls -d */
