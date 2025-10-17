"""
Enterprise Action Taxonomy - Semantic action matching for policy enforcement
"""
from typing import Set, Dict, List

# Comprehensive action synonym mapping
ACTION_TAXONOMY: Dict[str, Set[str]] = {
    "write": {
        "write", "modify", "update", "put", "create", "insert", "edit", "alter",
        "s3:PutObject", "s3:PutBucketAcl", "s3:PutObjectAcl",
        "rds:ModifyDBInstance", "lambda:UpdateFunctionCode"
    },
    "read": {
        "read", "get", "query", "access", "view", "list", "describe", "fetch",
        "s3:GetObject", "s3:ListBucket", "rds:DescribeDBInstances"
    },
    "delete": {
        "delete", "remove", "drop", "truncate", "destroy", "purge", "erase",
        "s3:DeleteObject", "s3:DeleteBucket", "rds:DeleteDBInstance"
    },
    "execute": {
        "execute", "run", "invoke", "trigger", "call", "launch", "start",
        "lambda:Invoke", "ecs:RunTask"
    },
    "export": {
        "export", "download", "extract", "copy", "transfer", "exfiltrate"
    }
}

# Resource hierarchy - for matching wildcards properly
RESOURCE_HIERARCHY = {
    "s3": ["s3://*", "s3:bucket", "s3:object", "s3:*"],
    "database": ["database:*", "database:production:*", "rds:*"],
    "mcp": ["mcp:*", "mcp:server:*", "mcp:tool:*"],
    "financial": ["payment:*", "financial:*", "transaction:*"],
    "pii": ["pii:*", "secrets:*", "credentials:*"]
}

def normalize_action(action: str) -> str:
    """Convert action to lowercase and strip common prefixes"""
    action = action.lower().strip()
    # Remove common prefixes
    for prefix in ["action:", "verb:", "type:"]:
        if action.startswith(prefix):
            action = action[len(prefix):]
    return action

def get_action_family(action: str) -> str:
    """Get the action family for a given action"""
    action = normalize_action(action)
    for family, synonyms in ACTION_TAXONOMY.items():
        if action in synonyms or any(syn in action for syn in synonyms):
            return family
    return action  # Return as-is if no family found

def actions_match(policy_action: str, actual_action: str) -> bool:
    """
    Check if policy action matches actual action using semantic matching
    """
    policy_normalized = normalize_action(policy_action)
    actual_normalized = normalize_action(actual_action)
    
    # Direct match
    if policy_normalized in actual_normalized or actual_normalized in policy_normalized:
        return True
    
    # Wildcard match
    if policy_normalized == "*":
        return True
    
    # Family match - both actions in same semantic family
    policy_family = get_action_family(policy_normalized)
    actual_family = get_action_family(actual_normalized)
    
    if policy_family == actual_family:
        return True
    
    # Check if actual action contains any synonym from policy action's family
    if policy_family in ACTION_TAXONOMY:
        policy_synonyms = ACTION_TAXONOMY[policy_family]
        if any(syn in actual_normalized for syn in policy_synonyms):
            return True
    
    return False

def normalize_resource(resource: str) -> str:
    """Normalize resource identifier"""
    return resource.lower().strip()

def resource_matches(policy_resource: str, actual_resource: str) -> bool:
    """
    Check if policy resource pattern matches actual resource
    Handles wildcards and hierarchy properly
    """
    policy_normalized = normalize_resource(policy_resource)
    actual_normalized = normalize_resource(actual_resource)
    
    # Wildcard match
    if policy_normalized == "*":
        return True
    
    # Direct match
    if policy_normalized == actual_normalized:
        return True
    
    # Pattern matching with wildcards
    import re
    pattern = policy_normalized.replace("*", ".*").replace(":", r"\:")
    pattern = f"^{pattern}$"
    
    try:
        if re.match(pattern, actual_normalized):
            return True
    except re.error:
        pass
    
    # Hierarchy matching - s3:* matches s3://anything
    for resource_type, patterns in RESOURCE_HIERARCHY.items():
        if any(p == policy_normalized for p in patterns):
            if resource_type in actual_normalized:
                return True
    
    # Prefix matching for paths
    if policy_normalized.endswith("*"):
        prefix = policy_normalized[:-1]
        if actual_normalized.startswith(prefix):
            return True
    
    return False
