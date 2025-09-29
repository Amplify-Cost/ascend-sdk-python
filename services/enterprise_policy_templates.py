
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
        """Set basic policy information"""
        if not name or len(name) < 3:
            self.validation_errors.append("Policy name must be at least 3 characters")
        if severity not in self.VALID_SEVERITIES:
            self.validation_errors.append(f"Invalid severity. Must be one of: {self.VALID_SEVERITIES}")
        
        self.policy_data['name'] = name
        self.policy_data['description'] = description
        self.policy_data['severity'] = severity
        return self
    
    def set_resources(self, resource_types: List[str]):
        """Define which resources this policy applies to"""
        invalid = [r for r in resource_types if r not in self.VALID_RESOURCE_TYPES and not r.endswith('*')]
        if invalid:
            self.validation_errors.append(f"Invalid resource types: {invalid}")
        
        self.policy_data['resource_types'] = resource_types
        return self
    
    def set_actions(self, actions: List[str]):
        """Define which actions this policy controls"""
        invalid = [a for a in actions if a not in self.VALID_ACTIONS and a != "*"]
        if invalid:
            self.validation_errors.append(f"Invalid actions: {invalid}")
        
        self.policy_data['actions'] = actions
        return self
    
    def set_effect(self, effect: str):
        """Set policy enforcement effect"""
        if effect not in self.VALID_EFFECTS:
            self.validation_errors.append(f"Invalid effect. Must be one of: {self.VALID_EFFECTS}")
        
        self.policy_data['effect'] = effect
        return self
    
    def add_condition(self, condition_type: str, condition_value: Any):
        """Add custom conditions"""
        if 'conditions' not in self.policy_data:
            self.policy_data['conditions'] = {}
        
        self.policy_data['conditions'][condition_type] = condition_value
        return self
    
    def add_time_restriction(self, start_time: str, end_time: str, days: List[str] = None):
        """Add time-based restrictions"""
        self.add_condition('time_range', {'start': start_time, 'end': end_time})
        if days:
            self.add_condition('days', days)
        return self
    
    def add_environment_restriction(self, environments: List[str]):
        """Restrict to specific environments"""
        self.add_condition('environment', environments)
        return self
    
    def add_approval_requirements(self, min_approvers: int = 1, approval_roles: List[str] = None):
        """Set approval requirements"""
        self.add_condition('min_approvers', min_approvers)
        if approval_roles:
            self.add_condition('approval_roles', approval_roles)
        return self
    
    def add_rate_limit(self, max_per_hour: int = 100, max_concurrent: int = 5):
        """Add rate limiting"""
        self.add_condition('max_executions_per_hour', max_per_hour)
        self.add_condition('max_concurrent', max_concurrent)
        return self
    
    def add_data_thresholds(self, max_records: int = None, max_size_mb: int = None):
        """Add data volume thresholds"""
        if max_records:
            self.add_condition('record_count_threshold', max_records)
        if max_size_mb:
            self.add_condition('data_size_mb_threshold', max_size_mb)
        return self
    
    def add_compliance_tags(self, frameworks: List[str]):
        """Tag policy with compliance frameworks"""
        self.policy_data['compliance_frameworks'] = frameworks
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and validate the custom policy"""
        # Required fields check
        required = ['name', 'description', 'resource_types', 'actions', 'effect', 'severity']
        missing = [f for f in required if f not in self.policy_data]
        if missing:
            self.validation_errors.append(f"Missing required fields: {missing}")
        
        if self.validation_errors:
            raise ValueError(f"Policy validation failed: {'; '.join(self.validation_errors)}")
        
        return self.policy_data
    
    def to_natural_language(self) -> str:
        """Convert structured policy to natural language for compiler"""
        parts = []
        
        # Effect
        effect_map = {
            "DENY": "block",
            "REQUIRE_APPROVAL": "require approval for",
            "ALLOW": "allow",
            "EVALUATE": "evaluate"
        }
        parts.append(effect_map.get(self.policy_data['effect'], 'evaluate'))
        
        # Actions
        actions_str = ", ".join(self.policy_data['actions'][:3])
        parts.append(f"{actions_str} actions on")
        
        # Resources
        resources_str = ", ".join(self.policy_data['resource_types'][:2])
        parts.append(resources_str)
        
        # Conditions
        if 'conditions' in self.policy_data:
            cond = self.policy_data['conditions']
            if 'environment' in cond:
                parts.append(f"in {cond['environment']} environment")
            if 'min_approvers' in cond:
                parts.append(f"with {cond['min_approvers']} approvers required")
        
        return " ".join(parts)
