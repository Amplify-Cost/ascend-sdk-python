with open('services/cedar_enforcement_service.py', 'r') as f:
    lines = f.readlines()

# Find where to insert (after imports, before first class)
insert_index = None
for i, line in enumerate(lines):
    if line.startswith('class CedarStylePolicy:'):
        insert_index = i
        break

if insert_index is None:
    print("Could not find insertion point")
    exit(1)

# Create validation code
validation_code = '''class PolicyValidationError(Exception):
    """Raised when policy validation fails"""
    pass

class PolicyValidator:
    """Validate policy inputs and structure"""
    
    @staticmethod
    def validate_natural_language(text: str) -> tuple:
        """Validate natural language policy input"""
        errors = []
        
        if not text or not text.strip():
            errors.append("Policy text cannot be empty")
        elif len(text.strip()) < 10:
            errors.append("Policy too short - provide more details (min 10 characters)")
        elif len(text) > 5000:
            errors.append("Policy too long - maximum 5000 characters")
        
        # Check for at least one action indicator
        action_keywords = ["block", "deny", "allow", "permit", "require", "approval", 
                          "read", "write", "delete", "modify", "create", "execute", "prevent"]
        if not any(kw in text.lower() for kw in action_keywords):
            errors.append("Policy must specify an action (e.g., block, allow, require approval)")
        
        return (len(errors) == 0, errors)

'''

# Insert validation code
lines.insert(insert_index, validation_code)

with open('services/cedar_enforcement_service.py', 'w') as f:
    f.writelines(lines)

print("Inserted validation classes")
