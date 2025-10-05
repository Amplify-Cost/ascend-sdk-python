with open('routes/unified_governance_routes.py', 'r') as f:
    lines = f.readlines()

output = []
first_datetime_import_fixed = False

for line in lines:
    # Fix the first datetime import (module level)
    if 'from datetime import datetime, timedelta' in line and not first_datetime_import_fixed and 'UTC' not in line:
        output.append(line.replace('from datetime import datetime, timedelta', 'from datetime import datetime, timedelta, UTC'))
        first_datetime_import_fixed = True
    # Remove any other datetime imports inside functions
    elif line.strip() == 'from datetime import datetime, timedelta':
        continue  # Skip this line
    elif 'from datetime import datetime, UTC' in line:
        continue  # Skip this line too
    else:
        output.append(line)

with open('routes/unified_governance_routes.py', 'w') as f:
    f.writelines(output)

print("✅ Fixed imports")
