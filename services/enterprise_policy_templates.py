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
ENTERPRISE_TEMPLATES = {
    "prevent_public_s3": {
        "name": "Prevent Public S3 Bucket Access",
        "description": "Block all agent actions that would make S3 buckets publicly accessible",
        "resource_types": ["s3:bucket", "s3:object"],
        "actions": ["s3:PutBucketAcl", "s3:PutObjectAcl", "write", "modify"],
        "effect": "DENY",
        "severity": "CRITICAL",
        "conditions": {
            "acl_contains": ["public-read", "public-read-write"],
            "environment": ["production", "staging"]
        },
        "compliance_frameworks": ["SOC2", "GDPR", "HIPAA"],
        "rationale": "Public buckets expose sensitive data and violate compliance requirements"
    },
    
    "production_db_protection": {
        "name": "Production Database Modification Control",
        "description": "Require manager approval for any production database modifications",
        "resource_types": ["database:production:*", "rds:*"],
        "actions": ["delete", "modify", "drop", "truncate", "alter"],
        "effect": "REQUIRE_APPROVAL",
        "severity": "HIGH",
        "conditions": {
            "environment": "production",
            "min_approvers": 2
        },
        "compliance_frameworks": ["SOC2", "ISO27001"],
        "rationale": "Production data changes require oversight to prevent data loss"
    },
    
    "mcp_server_pii_access": {
        "name": "MCP Server PII Access Control",
        "description": "Control AI agent access to PII through MCP servers",
        "resource_types": ["mcp:server:*", "pii:*"],
        "actions": ["read", "query", "export", "access"],
        "effect": "REQUIRE_APPROVAL",
        "severity": "HIGH",
        "conditions": {
            "data_classification": "PII",
            "requires_audit_log": True
        },
        "compliance_frameworks": ["GDPR", "CCPA", "HIPAA"],
        "rationale": "PII access must be logged and approved per privacy regulations"
    },
    
    "financial_transaction_block": {
        "name": "AI Agent Financial Transaction Prevention",
        "description": "Completely block AI agents from initiating financial transactions",
        "resource_types": ["payment:*", "financial:*", "transaction:*"],
        "actions": ["create", "execute", "approve", "transfer"],
        "effect": "DENY",
        "severity": "CRITICAL",
        "conditions": {
            "agent_initiated": True
        },
        "compliance_frameworks": ["PCI-DSS", "SOC2"],
        "rationale": "Financial transactions must always have human authorization"
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
