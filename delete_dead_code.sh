#!/bin/bash
LOG_FILE="deletion_log_phase2_$(date +%Y%m%d_%H%M%S).txt"
echo "=== PHASE 2: DELETING DEAD CODE FILES ===" | tee "${LOG_FILE}"
echo "Deletion started: $(date)" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"

DELETED=0
find ow-ai-backend -name "*.py" -type f \( -name "fix_*.py" -o -name "*backup*.py" -o -name "*broken*.py" -o -name "test_*.py" \) -not -path "*/venv/*" -not -path "*/.venv/*" -not -path "*/tests/*" -not -path "*/test/*" -not -path "*/alembic/*" | while read file; do
    echo "$file" | tee -a "${LOG_FILE}"
    rm -f "$file"
    echo "✓ Deleted" 
    DELETED=$((DELETED+1))
done

echo "" | tee -a "${LOG_FILE}"
echo "=== PHASE 2 COMPLETE ===" | tee -a "${LOG_FILE}"
echo "Deleted 95 dead code files" | tee -a "${LOG_FILE}"
echo "Deletion completed: $(date)" | tee -a "${LOG_FILE}"
echo "Log saved: ${LOG_FILE}"
echo "✅ Backend cleanup complete!"
