"""
Enterprise Policy Engine - REQUIREMENT 1 Implementation
Extends existing EnterpriseRiskEngine with dynamic policy management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
import hashlib
import json
from sqlalchemy.orm import Session
from models_mcp_governance import MCPPolicy
from database import get_db

class PolicyEngine:
    """
    Enterprise Policy Engine - Dynamic policy creation and management
    Integrates with existing smart rules infrastructure
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_policy_from_natural_language(
        self, 
        description: str, 
        creator: str,
        policy_name: str
    ) -> MCPPolicy:
        """
        Create policy from natural language description
        Integrates with existing LLM infrastructure
        """
        
        # Generate structured policy rules from natural language
        structured_rules = self._parse_natural_language(description)
        
        # Create policy with enterprise versioning
        policy = MCPPolicy(
            policy_name=policy_name,
            policy_description=f"Auto-generated from: {description}",
            natural_language_description=description,
            policy_status='draft',
            major_version=1,
            minor_version=0,
            patch_version=0,
            approval_required=True,
            server_patterns=structured_rules.get('servers', []),
            namespace_patterns=structured_rules.get('namespaces', []),
            verb_patterns=structured_rules.get('verbs', []),
            resource_patterns=structured_rules.get('resources', [])
        )
        
        # Generate version hash
        policy.version_hash = self._generate_version_hash(policy)
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        return policy
    
    def _parse_natural_language(self, description: str) -> Dict[str, List[str]]:
        """
        Parse natural language into structured policy rules
        TODO: Integrate with existing LLM infrastructure
        """
        # Simplified parsing - will be enhanced with LLM integration
        rules = {
            'servers': [],
            'namespaces': [],
            'verbs': [],
            'resources': []
        }
        
        # Basic keyword detection
        if 'file' in description.lower():
            rules['resources'].append('file:*')
        if 'read' in description.lower():
            rules['verbs'].append('read')
        if 'write' in description.lower():
            rules['verbs'].append('write')
            
        return rules
    
    def _generate_version_hash(self, policy: MCPPolicy) -> str:
        """Generate SHA256 hash of policy content for versioning"""
        content = {
            'name': policy.policy_name,
            'servers': policy.server_patterns,
            'namespaces': policy.namespace_patterns, 
            'verbs': policy.verb_patterns,
            'resources': policy.resource_patterns
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def deploy_policy(self, policy_id: str, deployed_by: str) -> bool:
        """
        Deploy approved policy with versioning tracking
        """
        policy = self.db.query(MCPPolicy).filter(MCPPolicy.id == policy_id).first()
        if not policy:
            return False
            
        if policy.policy_status != 'approved':
            raise ValueError("Policy must be approved before deployment")
            
        # Update deployment status
        policy.policy_status = 'deployed'
        policy.deployment_timestamp = datetime.now(UTC)
        
        self.db.commit()
        return True
        
    def rollback_policy(self, policy_id: str, target_version_id: str) -> bool:
        """
        Rollback policy to previous version
        """
        current_policy = self.db.query(MCPPolicy).filter(MCPPolicy.id == policy_id).first()
        target_policy = self.db.query(MCPPolicy).filter(MCPPolicy.id == target_version_id).first()
        
        if not current_policy or not target_policy:
            return False
            
        # Create rollback record
        current_policy.rollback_target_id = target_version_id
        current_policy.policy_status = 'deprecated'
        
        # Deploy target version
        target_policy.policy_status = 'deployed'
        target_policy.deployment_timestamp = datetime.now(UTC)
        
        self.db.commit()
        return True
