#!/bin/bash

echo "🔄 H10: Replacing Console Statements with Enterprise Logger"
echo "==========================================================="
echo ""

# Backup files that will be modified
echo "📦 Creating backups..."
BACKUP_DIR="console_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Find all files with console statements
FILES=$(grep -rl "console\." src --include="*.jsx" --include="*.js" | grep -v "logger.js" | grep -v "logger.test.js")

for file in $FILES; do
    cp "$file" "$BACKUP_DIR/$(basename $file).backup"
done

echo "✅ Backed up $(echo "$FILES" | wc -l | tr -d ' ') files"
echo ""

# Replace console statements with logger
echo "🔄 Replacing console statements..."

python3 << 'PYTHON'
import re
import os

# Files to process
files_to_process = []
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith(('.jsx', '.js')) and file not in ['logger.js', 'logger.test.js']:
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                if 'console.' in content:
                    files_to_process.append(filepath)

total_replacements = 0

for filepath in files_to_process:
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    replacements = 0
    
    # Check if logger is already imported
    has_logger_import = 'import logger from' in content or "import logger from" in content
    
    # Replace console.log with logger.debug
    content = re.sub(r'console\.log\(', 'logger.debug(', content)
    replacements += len(re.findall(r'logger\.debug\(', content)) - len(re.findall(r'logger\.debug\(', original_content))
    
    # Replace console.error with logger.error
    content = re.sub(r'console\.error\(', 'logger.error(', content)
    replacements += len(re.findall(r'logger\.error\(', content)) - len(re.findall(r'logger\.error\(', original_content))
    
    # Replace console.warn with logger.warn  
    content = re.sub(r'console\.warn\(', 'logger.warn(', content)
    replacements += len(re.findall(r'logger\.warn\(', content)) - len(re.findall(r'logger\.warn\(', original_content))
    
    # Replace console.info with logger.info
    content = re.sub(r'console\.info\(', 'logger.info(', content)
    replacements += len(re.findall(r'logger\.info\(', content)) - len(re.findall(r'logger\.info\(', original_content))
    
    # Add logger import if needed and replacements were made
    if replacements > 0 and not has_logger_import:
        # Find the last import statement
        import_lines = [i for i, line in enumerate(content.split('\n')) if line.startswith('import ')]
        if import_lines:
            lines = content.split('\n')
            last_import_line = import_lines[-1]
            lines.insert(last_import_line + 1, "import logger from '../utils/logger.js';")
            content = '\n'.join(lines)
    
    if replacements > 0:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ {filepath}: {replacements} replacements")
        total_replacements += replacements

print(f"\n📊 Total: {total_replacements} console statements replaced")
PYTHON

echo ""
echo "✅ Console statements replaced with enterprise logger"

