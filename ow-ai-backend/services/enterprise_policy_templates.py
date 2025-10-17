"""
Enterprise Policy Templates - Wiz-style structured policies for MCP servers and AI agents
"""
from typing import Dict, List, Any
from datetime import time

class PolicyTemplate:
    """Structured policy template"""
    def __init__(self, template_id: str, config: Dict[str, Any]):
        self.template_id = template_id
        self.name = config['name']
        self.description = config['description']
        self.resource_types = config['resource_types']
        self.actions = config['actions']
        self.effect = config['effect']
        self.severity = config['severity']
        self.conditions = config.get('conditions', {})
        self.compliance_frameworks = config.get('compliance_frameworks', [])

# Enterprise Policy Library - Pre-built templates
# Enterprise Policy Library - Updated with DSL conditions
ENTERPRISE_TEMPLATES = {
    "prevent_public_s3": {
        "name": "Prevent Public S3 Bucket Access",
        "description": "Block all agent actions that would make S3 buckets publicly accessible. Deny by default in production unless explicitly safe.",
        "resource_types": ["s3:bucket", "s3:object"],
        "actions": ["s3:PutBucketAcl", "s3:PutObjectAcl", "write", "modify"],
        "effect": "DENY",
        "severity": "CRITICAL",
        "conditions": {
            "any_of": [  # Block if ANY of these dangerous conditions
                {
                    "all_of": [  # Production write without safety confirmation
                        {
                            "field": "environment",
                            "operator": "in",
                            "value": ["production", "staging"],
                            "required": False
                        },
                        {
                            "none_of": [  # NOT explicitly marked as safe
                                {
                                    "field": "acl_confirmed_private",
                                    "operator": "equals",
                                    "value": True,
                                    "required": False
                                },
                                {
                                    "field": "security_approved",
                                    "operator": "equals",
                                    "value": True,
                                    "required": False
                                }
                            ]
                        }
                    ]
                },
                {
                    "any_of": [  # OR any of these explicit danger signals
                        {
                            "field": "acl_contains",
                            "operator": "contains",
                            "value": "public-read",
                            "required": False
                        },
                        {
                            "field": "acl_contains",
                            "operator": "contains",
                            "value": "public-write",
                            "required": False
                        },
                        {
                            "field": "permissions",
                            "operator": "contains",
                            "value": "AllUsers",
                            "required": False
                        }
                    ]
                }
            ]
        },
        "compliance_frameworks": ["SOC2", "GDPR", "HIPAA"]
    },
    
    "database_protection": {
        "name": "Database Deletion Protection",
        "description": "Prevent destructive database operations on production databases",
        "resource_types": ["database:*", "rds:*", "dynamodb:*"],
        "actions": ["DROP", "TRUNCATE", "DELETE", "database:delete"],
        "effect": "DENY",
        "severity": "CRITICAL",
        "conditions": {
            "any_of": [
                {
                    "field": "environment",
                    "operator": "equals",
                    "value": "production",
                    "required": True  # Must know environment
                },
                {
                    "field": "database_name",
                    "operator": "contains",
                    "value": "prod",
                    "required": False
                },
                {
                    "all_of": [
                        {
                            "field": "row_count",
                            "operator": "greater_than",
                            "value": 1000,
                            "required": False
                        },
                        {
                            "field": "has_backup",
                            "operator": "equals",
                            "value": False,
                            "required": False
                        }
                    ]
                }
            ]
        },
        "compliance_frameworks": ["SOC2", "ISO27001"]
    },
    
    "cross_region_transfer": {
        "name": "Cross-Region Data Transfer Control",
        "description": "Require approval for data transfers outside approved regions",
        "resource_types": ["s3:bucket", "database:*", "data:*"],
        "actions": ["transfer", "replicate", "copy", "sync"],
        "effect": "REQUIRE_APPROVAL",
        "severity": "HIGH",
        "conditions": {
            "all_of": [
                {
                    "field": "source_region",
                    "operator": "in",
                    "value": ["us-east-1", "us-west-2", "eu-west-1"],
                    "required": True
                },
                {
                    "field": "destination_region",
                    "operator": "not_in",
                    "value": ["us-east-1", "us-west-2", "eu-west-1"],
                    "required": True
                },
                {
                    "any_of": [
                        {
                            "field": "data_classification",
                            "operator": "in",
                            "value": ["confidential", "restricted"],
                            "required": False
                        },
                        {
                            "field": "contains_pii",
                            "operator": "equals",
                            "value": True,
                            "required": False
                        },
                        {
                            "field": "data_size_gb",
                            "operator": "greater_than",
                            "value": 100,
                            "required": False
                        }
                    ]
                }
            ]
        },
        "compliance_frameworks": ["GDPR", "CCPA"]
    },
    
    "credential_access": {
        "name": "Credential and Secret Access Control",
        "description": "Require approval for accessing credentials, API keys, and secrets",
        "resource_types": ["secrets:*", "credentials:*", "keys:*"],
        "actions": ["read", "access", "retrieve", "decrypt"],
        "effect": "REQUIRE_APPROVAL",
        "severity": "HIGH",
        "conditions": {
            "any_of": [
                {
                    "field": "secret_type",
                    "operator": "in",
                    "value": ["api_key", "database_password", "private_key", "oauth_token"],
                    "required": False
                },
                {
                    "field": "resource_name",
                    "operator": "regex",
                    "value": ".*(password|secret|key|token).*",
                    "required": False
                },
                {
                    "all_of": [
                        {
                            "field": "environment",
                            "operator": "equals",
                            "value": "production",
                            "required": False
                        },
                        {
                            "field": "access_count_today",
                            "operator": "greater_than",
                            "value": 5,
                            "required": False
                        }
                    ]
                }
            ]
        },
        "compliance_frameworks": ["SOC2", "ISO27001", "PCI-DSS"]
    },
    
    "api_rate_limiting": {
        "name": "API Rate Limiting Protection",
        "description": "Prevent API abuse by limiting high-frequency requests",
        "resource_types": ["api:*", "endpoint:*"],
        "actions": ["call", "request", "invoke"],
        "effect": "REQUIRE_APPROVAL",
        "severity": "MEDIUM",
        "conditions": {
            "any_of": [
                {
                    "field": "requests_per_minute",
                    "operator": "greater_than",
                    "value": 100,
                    "required": False
                },
                {
                    "field": "requests_per_hour",
                    "operator": "greater_than",
                    "value": 1000,
                    "required": False
                },
                {
                    "all_of": [
                        {
                            "field": "cost_per_request",
                            "operator": "greater_than",
                            "value": 0.01,
                            "required": False
                        },
                        {
                            "field": "total_requests",
                            "operator": "greater_than",
                            "value": 10000,
                            "required": False
                        }
                    ]
                }
            ]
        },
        "compliance_frameworks": ["SOC2"]
    },
    
    "financial_transaction": {
        "name": "Financial Transaction Control",
        "description": "Require approval for high-value financial transactions",
        "resource_types": ["payment:*", "transaction:*", "financial:*"],
        "actions": ["transfer", "payment", "charge", "refund"],
        "effect": "REQUIRE_APPROVAL",
        "severity": "CRITICAL",
        "conditions": {
            "any_of": [
                {
                    "field": "amount",
                    "operator": "greater_than",
                    "value": 1000,
                    "required": True  # Must know amount
                },
                {
                    "all_of": [
                        {
                            "field": "environment",
                            "operator": "not_equals",
                            "value": "sandbox",
                            "required": True
                        },
                        {
                            "field": "currency",
                            "operator": "not_in",
                            "value": ["USD", "EUR", "GBP"],
                            "required": False
                        }
                    ]
                }
            ]
        },
        "compliance_frameworks": ["PCI-DSS", "SOX", "SOC2"]
    }
}

class CustomPolicyBuilder:
    """
    Build custom policies with structured validation
    Customers can create policies beyond the template library
    """
    
    VALID_RESOURCE_TYPES = [
        "s3:bucket", "s3:object", 
        "database:*", "database:production:*", "rds:*",
        "mcp:server:*", "mcp:tool:*",
        "pii:*", "secrets:*", "credentials:*",
        "payment:*", "financial:*", "transaction:*",
        "api:*", "lambda:*", "ec2:*",
        "*:production:*"
    ]
    
    VALID_ACTIONS = [
        "read", "write", "modify", "delete", "create",
        "execute", "run", "export", "download", "access",
        "query", "bulk_read", "drop", "truncate", "alter",
        "s3:PutBucketAcl", "s3:PutObjectAcl"
    ]
    
    VALID_EFFECTS = ["DENY", "REQUIRE_APPROVAL", "ALLOW", "EVALUATE"]
    VALID_SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    
    def __init__(self):
        self.policy_data = {}
        self.validation_errors = []
    
    def set_basic_info(self, name: str, description: str, severity: str = "MEDIUM"):
        if not name or len(name) < 3:
            self.validation_errors.append("Policy name must be at least 3 characters")
        if severity not in self.VALID_SEVERITIES:
            self.validation_errors.append(f"Invalid severity")
        
        self.policy_data['name'] = name
        self.policy_data['description'] = description
        self.policy_data['severity'] = severity
        return self
    
    def set_resources(self, resource_types: List[str]):
        self.policy_data['resource_types'] = resource_types
        return self
    
    def set_actions(self, actions: List[str]):
        self.policy_data['actions'] = actions
        return self
    
    def set_effect(self, effect: str):
        self.policy_data['effect'] = effect
        return self
    
    def add_condition(self, condition_type: str, condition_value: Any):
        if 'conditions' not in self.policy_data:
            self.policy_data['conditions'] = {}
        self.policy_data['conditions'][condition_type] = condition_value
        return self
    
    def add_environment_restriction(self, environments: List[str]):
        return self.add_condition('environment', environments)
    
    def add_approval_requirements(self, min_approvers: int = 1):
        return self.add_condition('min_approvers', min_approvers)
    
    def build(self) -> Dict[str, Any]:
        required = ['name', 'description', 'resource_types', 'actions', 'effect', 'severity']
        missing = [f for f in required if f not in self.policy_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        if self.validation_errors:
            raise ValueError(f"Validation failed: {'; '.join(self.validation_errors)}")
        
        return self.policy_data

def get_template(template_id: str) -> PolicyTemplate:
    if template_id not in ENTERPRISE_TEMPLATES:
        raise ValueError(f"Unknown template: {template_id}")
    return PolicyTemplate(template_id, ENTERPRISE_TEMPLATES[template_id])

def list_templates() -> List[Dict[str, Any]]:
    templates = []
    for tid, config in ENTERPRISE_TEMPLATES.items():
        templates.append({
            "id": tid,
            "name": config['name'],
            "severity": config['severity'],
            "effect": config['effect'],
            "description": config['description']
        })
    return templates

    def to_natural_language(self) -> str:
        """Convert structured policy to natural language"""
        parts = []
        effect_map = {"DENY": "block", "REQUIRE_APPROVAL": "require approval for", "ALLOW": "allow", "EVALUATE": "evaluate"}
        parts.append(effect_map.get(self.policy_data['effect'], 'evaluate'))
        actions_str = ", ".join(self.policy_data['actions'][:3])
        parts.append(f"{actions_str} actions on")
        resources_str = ", ".join(self.policy_data['resource_types'][:2])
        parts.append(resources_str)
        if 'conditions' in self.policy_data:
            cond = self.policy_data['conditions']
            if 'environment' in cond:
                env = cond['environment'] if isinstance(cond['environment'], str) else ', '.join(cond['environment'])
                parts.append(f"in {env} environment")
            if 'min_approvers' in cond:
                parts.append(f"with {cond['min_approvers']} approvers required")
        return " ".join(parts)
