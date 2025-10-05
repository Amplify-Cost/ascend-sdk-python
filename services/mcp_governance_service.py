"""
MCP Server Governance Service
Integrates with existing audit system and agent governance patterns
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, UTC, timedelta
import hashlib
import json
import uuid

# Import your existing models
from models_mcp_governance import MCPServerAction, MCPServer, MCPSession, MCPPolicy
from services.cedar_enforcement_service import enforcement_engine
from models_audit import ImmutableAuditLog  # Your existing audit model
from services.immutable_audit_service import ImmutableAuditService

logger = logging.getLogger(__name__)

class MCPGovernanceService:
    """
    Enterprise MCP Server Governance Service
    Extends existing agent governance patterns to MCP servers
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = ImmutableAuditService(db)
    
    async def evaluate_mcp_action(
        self,
        server_id: str,
        namespace: str,
        verb: str,
        resource: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, str],
        session_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Evaluate MCP action using UNIFIED Cedar enforcement engine
        Returns governance decision with risk score and required approvals
        """
        # Use unified policy enforcement
        policy_decision = enforcement_engine.evaluate(
            principal=f"mcp_server:{server_id}",
            action=verb,
            resource=f"mcp:server:{server_id}:{namespace}:{resource}",
            context={
                "user": user_context.get("user_id"),
                "namespace": namespace,
                **session_context
            }
        )
        try:
            # Create MCP action record
            mcp_action = MCPServerAction(
                mcp_server_id=server_id,
                mcp_server_name=await self._get_server_name(server_id),
                namespace=namespace,
                verb=verb,
                resource=resource,
                parameters=parameters,
                request_id=session_context.get('request_id', str(uuid.uuid4())),
                session_id=session_context.get('session_id'),
                client_id=session_context.get('client_id'),
                user_id=user_context.get('user_id'),
                user_email=user_context.get('user_email'),
                user_role=user_context.get('role'),
                source_ip=session_context.get('source_ip'),
                user_agent=session_context.get('user_agent'),
                payload_size=len(json.dumps(parameters))
            )
            
            # Calculate risk score using same algorithm as agents
            risk_assessment = await self._calculate_mcp_risk_score(
                server_id, namespace, verb, resource, parameters, user_context
            )
            
            mcp_action.risk_score = risk_assessment['score']
            mcp_action.risk_level = risk_assessment['level']
            mcp_action.risk_factors = risk_assessment['factors']
            
            # Apply MCP policies
            policy_result = await self._apply_mcp_policies(mcp_action)
            mcp_action.policy_result = policy_result['action']
            mcp_action.rule_id = policy_result.get('rule_id')
            mcp_action.policy_reason = policy_result.get('reason')
            
            # Determine approval requirements
            approval_decision = await self._determine_approval_requirements(mcp_action)
            mcp_action.requires_approval = approval_decision['required']
            mcp_action.approval_level = approval_decision['level']
            mcp_action.status = approval_decision['status']
            
            # Set compliance tags based on risk and context
            mcp_action.compliance_tags = await self._determine_compliance_tags(mcp_action)
            
            # Save to database
            self.db.add(mcp_action)
            self.db.commit()
            
            # Log to immutable audit trail using your existing service
            await self._log_mcp_governance_event(mcp_action, 'MCP_ACTION_EVALUATED')
            
            return {
                'action_id': str(mcp_action.id),
                'decision': mcp_action.policy_result,
                'status': mcp_action.status,
                'risk_score': mcp_action.risk_score,
                'risk_level': mcp_action.risk_level,
                'requires_approval': mcp_action.requires_approval,
                'approval_level': mcp_action.approval_level,
                'reason': mcp_action.policy_reason,
                'estimated_review_time_minutes': approval_decision.get('estimated_time', 5)
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate MCP action: {e}")
            # Fail-closed: deny by default on error
            return {
                'decision': 'DENY',
                'status': 'FAILED',
                'risk_score': 100,
                'risk_level': 'CRITICAL',
                'reason': f'Governance evaluation failed: {str(e)}'
            }
    
    async def _get_server_name(self, server_id: str) -> str:
        """Get human-readable server name"""
        server = self.db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
        return server.server_name if server else server_id
    
    async def _calculate_mcp_risk_score(
        self,
        server_id: str,
        namespace: str,
        verb: str,
        resource: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Calculate risk score for MCP action using enterprise risk factors
        """
        base_score = 0
        risk_factors = []
        
        # Server risk assessment
        server_risk = await self._assess_server_risk(server_id)
        base_score += server_risk['score']
        risk_factors.extend(server_risk['factors'])
        
        # Namespace risk assessment
        namespace_risk = self._assess_namespace_risk(namespace)
        base_score += namespace_risk['score']
        risk_factors.extend(namespace_risk['factors'])
        
        # Verb risk assessment
        verb_risk = self._assess_verb_risk(verb)
        base_score += verb_risk['score']
        risk_factors.extend(verb_risk['factors'])
        
        # Resource risk assessment
        resource_risk = self._assess_resource_risk(resource, namespace)
        base_score += resource_risk['score']
        risk_factors.extend(resource_risk['factors'])
        
        # User context risk
        user_risk = self._assess_user_risk(user_context)
        base_score += user_risk['score']
        risk_factors.extend(user_risk['factors'])
        
        # Environment risk
        env_risk = self._assess_environment_risk(parameters)
        base_score += env_risk['score']
        risk_factors.extend(env_risk['factors'])
        
        # Cap at 100
        final_score = min(base_score, 100)
        
        # Determine risk level
        if final_score >= 80:
            risk_level = 'CRITICAL'
        elif final_score >= 60:
            risk_level = 'HIGH'
        elif final_score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'score': final_score,
            'level': risk_level,
            'factors': risk_factors
        }
    
    async def _assess_server_risk(self, server_id: str) -> Dict[str, Any]:
        """Assess risk based on MCP server characteristics"""
        risk_score = 0
        factors = []
        
        # Get server info
        server = self.db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
        
        if not server:
            # Unknown server gets default medium risk
            return {'score': 30, 'factors': ['unknown_server']}
        
        # Trust level assessment
        trust_levels = {'sandbox': 0, 'restricted': 20, 'trusted': 10}
        risk_score += trust_levels.get(server.trust_level, 30)
        
        if server.trust_level != 'trusted':
            factors.append(f'server_trust_{server.trust_level}')
        
        # Historical failure rate
        if server.total_actions > 0:
            failure_rate = (server.failed_actions / server.total_actions) * 100
            if failure_rate > 10:
                risk_score += 15
                factors.append('high_failure_rate')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_namespace_risk(self, namespace: str) -> Dict[str, Any]:
        """Assess risk based on MCP namespace"""
        # High-risk namespaces
        high_risk_namespaces = {
            'filesystem': 30,
            'database': 35,
            'network': 25,
            'system': 40,
            'exec': 45,
            'admin': 50
        }
        
        # Medium-risk namespaces
        medium_risk_namespaces = {
            'tools': 15,
            'api': 20,
            'data': 25
        }
        
        risk_score = high_risk_namespaces.get(namespace.lower(), 
                     medium_risk_namespaces.get(namespace.lower(), 10))
        
        factors = []
        if risk_score >= 30:
            factors.append(f'high_risk_namespace_{namespace}')
        elif risk_score >= 15:
            factors.append(f'medium_risk_namespace_{namespace}')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_verb_risk(self, verb: str) -> Dict[str, Any]:
        """Assess risk based on MCP verb/action"""
        # Critical verbs
        critical_verbs = {
            'delete', 'remove', 'destroy', 'drop', 'truncate', 'kill',
            'exec', 'execute', 'run', 'eval', 'sudo', 'rm', 'unlink'
        }
        
        # High-risk verbs
        high_risk_verbs = {
            'write', 'create', 'modify', 'update', 'insert', 'alter',
            'grant', 'revoke', 'chmod', 'chown', 'move', 'mv'
        }
        
        # Medium-risk verbs
        medium_risk_verbs = {
            'copy', 'cp', 'rename', 'link', 'mount', 'unmount', 'mkdir'
        }
        
        verb_lower = verb.lower()
        
        if any(cv in verb_lower for cv in critical_verbs):
            return {'score': 40, 'factors': [f'critical_verb_{verb}']}
        elif any(hv in verb_lower for hv in high_risk_verbs):
            return {'score': 25, 'factors': [f'high_risk_verb_{verb}']}
        elif any(mv in verb_lower for mv in medium_risk_verbs):
            return {'score': 15, 'factors': [f'medium_risk_verb_{verb}']}
        else:
            return {'score': 5, 'factors': []}
    
    def _assess_resource_risk(self, resource: str, namespace: str) -> Dict[str, Any]:
        """Assess risk based on target resource"""
        risk_score = 0
        factors = []
        
        resource_lower = resource.lower()
        
        # System critical paths
        critical_paths = [
            '/etc/passwd', '/etc/shadow', '/etc/hosts', '/etc/fstab',
            '/boot/', '/sys/', '/proc/', '/dev/', '/root/',
            'c:\\windows\\system32', 'c:\\windows\\boot',
            '/usr/bin/', '/usr/sbin/', '/bin/', '/sbin/'
        ]
        
        if any(cp in resource_lower for cp in critical_paths):
            risk_score += 35
            factors.append('system_critical_path')
        
        # Production indicators
        prod_indicators = ['prod', 'production', 'live', 'master', 'main']
        if any(pi in resource_lower for pi in prod_indicators):
            risk_score += 20
            factors.append('production_resource')
        
        # Database tables (if namespace is database)
        if namespace.lower() == 'database':
            sensitive_tables = ['users', 'passwords', 'tokens', 'keys', 'secrets', 'auth']
            if any(st in resource_lower for st in sensitive_tables):
                risk_score += 25
                factors.append('sensitive_database_table')
        
        # Configuration files
        config_indicators = ['config', 'conf', '.env', 'settings', 'ini']
        if any(ci in resource_lower for ci in config_indicators):
            risk_score += 15
            factors.append('configuration_file')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_user_risk(self, user_context: Dict[str, str]) -> Dict[str, Any]:
        """Assess risk based on user context"""
        risk_score = 0
        factors = []
        
        # User role assessment
        user_role = user_context.get('role', '').lower()
        
        # High-privilege roles get lower risk (they're supposed to do risky things)
        admin_roles = ['admin', 'administrator', 'root', 'superuser', 'sysadmin']
        if any(ar in user_role for ar in admin_roles):
            risk_score += 0  # No additional risk for admin users
        else:
            risk_score += 10  # Non-admin users get additional scrutiny
            factors.append('non_admin_user')
        
        # Check for service accounts
        user_email = user_context.get('user_email', '')
        if 'service' in user_email or 'bot' in user_email or 'system' in user_email:
            risk_score += 5
            factors.append('service_account')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_environment_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk based on environment and parameters"""
        risk_score = 0
        factors = []
        
        # Check for sensitive data in parameters
        param_str = json.dumps(parameters).lower()
        
        sensitive_keywords = [
            'password', 'token', 'key', 'secret', 'credential',
            'private', 'confidential', 'restricted', 'api_key',
            'auth', 'session'
        ]
        
        for keyword in sensitive_keywords:
            if keyword in param_str:
                risk_score += 10
                factors.append(f'sensitive_parameter_{keyword}')
                break
        
        # Large payload risk
        if len(param_str) > 10000:  # 10KB threshold
            risk_score += 5
            factors.append('large_payload')
        
        # Check for code execution patterns
        code_patterns = ['eval', 'exec', 'system', 'shell', 'cmd']
        for pattern in code_patterns:
            if pattern in param_str:
                risk_score += 20
                factors.append('code_execution_detected')
                break
        
        return {'score': risk_score, 'factors': factors}
    
    async def _apply_mcp_policies(self, mcp_action: MCPServerAction) -> Dict[str, Any]:
        """Apply MCP governance policies"""
        # Get applicable policies
        policies = self.db.query(MCPPolicy).filter(
            MCPPolicy.is_active == True
        ).order_by(MCPPolicy.priority.desc()).all()
        
        for policy in policies:
            if await self._policy_matches_action(policy, mcp_action):
                return {
                    'action': policy.action,
                    'rule_id': str(policy.id),
                    'reason': f'Policy: {policy.policy_name}'
                }
        
        # Default policy: evaluate based on risk
        if mcp_action.risk_score >= 80:
            return {'action': 'DENY', 'reason': 'High risk score - blocked'}
        elif mcp_action.risk_score >= 50:
            return {'action': 'EVALUATE', 'reason': 'Medium risk - requires approval'}
        else:
            return {'action': 'ALLOW', 'reason': 'Low risk - auto-approved'}
    
    async def _policy_matches_action(self, policy: MCPPolicy, action: MCPServerAction) -> bool:
        """Check if policy matches MCP action"""
        # Check server patterns
        if policy.server_patterns:
            if not any(pattern in action.mcp_server_id for pattern in policy.server_patterns):
                return False
        
        # Check namespace patterns
        if policy.namespace_patterns:
            if not any(pattern in action.namespace for pattern in policy.namespace_patterns):
                return False
        
        # Check verb patterns
        if policy.verb_patterns:
            if not any(pattern in action.verb for pattern in policy.verb_patterns):
                return False
        
        # Check resource patterns
        if policy.resource_patterns:
            if not any(pattern in action.resource for pattern in policy.resource_patterns):
                return False
        
        # Check risk threshold
        if action.risk_score < policy.risk_threshold:
            return False
        
        return True
    
    async def _determine_approval_requirements(self, mcp_action: MCPServerAction) -> Dict[str, Any]:
        """Determine approval requirements based on risk and policy"""
        
        if mcp_action.policy_result == 'ALLOW':
            return {
                'required': False,
                'level': 0,
                'status': 'AUTO_APPROVED',
                'estimated_time': 0
            }
        
        if mcp_action.policy_result == 'DENY':
            return {
                'required': False,
                'level': 0,
                'status': 'DENIED',
                'estimated_time': 0
            }
        
        # Determine approval level based on risk score (same as agent actions)
        if mcp_action.risk_score >= 90:
            level = 5  # Executive approval
            estimated_time = 60
        elif mcp_action.risk_score >= 80:
            level = 4  # Senior management
            estimated_time = 30
        elif mcp_action.risk_score >= 70:
            level = 3  # Department head
            estimated_time = 15
        elif mcp_action.risk_score >= 50:
            level = 2  # Team lead
            estimated_time = 10
        else:
            level = 1  # Peer review
            estimated_time = 5
        
        return {
            'required': True,
            'level': level,
            'status': 'PENDING_APPROVAL',
            'estimated_time': estimated_time
        }
    
    async def _determine_compliance_tags(self, mcp_action: MCPServerAction) -> List[str]:
        """Determine compliance tags based on action characteristics"""
        tags = ['MCP_GOVERNANCE', 'AI_SAFETY']
        
        # Add risk-based tags
        if mcp_action.risk_score >= 80:
            tags.append('HIGH_RISK')
        
        # Add namespace-based tags
        if mcp_action.namespace.lower() in ['database', 'filesystem']:
            tags.append('DATA_ACCESS')
        
        if mcp_action.namespace.lower() in ['system', 'admin']:
            tags.append('SYSTEM_ADMIN')
        
        # Add verb-based tags
        if any(verb in mcp_action.verb.lower() for verb in ['write', 'create', 'modify', 'delete']):
            tags.append('DATA_MODIFICATION')
        
        if any(verb in mcp_action.verb.lower() for verb in ['exec', 'execute', 'run']):
            tags.append('CODE_EXECUTION')
        
        # Add environment-based tags
        if mcp_action.environment == 'production':
            tags.append('PRODUCTION')
        
        return tags
    
    async def _log_mcp_governance_event(self, mcp_action: MCPServerAction, event_type: str):
        """Log MCP governance event to immutable audit trail"""
        try:
            audit_id = await self.audit_service.log_event(
                event_type=event_type,
                actor_id=mcp_action.user_email,
                resource_type="MCP_SERVER",
                resource_id=f"{mcp_action.mcp_server_id}:{mcp_action.namespace}",
                action=mcp_action.verb,
                event_data={
                    "mcp_action_id": str(mcp_action.id),
                    "server_id": mcp_action.mcp_server_id,
                    "namespace": mcp_action.namespace,
                    "verb": mcp_action.verb,
                    "resource": mcp_action.resource,
                    "risk_score": mcp_action.risk_score,
                    "risk_level": mcp_action.risk_level,
                    "risk_factors": mcp_action.risk_factors,
                    "policy_result": mcp_action.policy_result,
                    "requires_approval": mcp_action.requires_approval,
                    "approval_level": mcp_action.approval_level,
                    "session_id": mcp_action.session_id,
                    "client_id": mcp_action.client_id,
                    "payload_size": mcp_action.payload_size
                },
                risk_level=mcp_action.risk_level,
                compliance_tags=mcp_action.compliance_tags,
                ip_address=mcp_action.source_ip,
                user_agent=mcp_action.user_agent
            )
            
            # Link audit trail
            mcp_action.audit_trail_id = audit_id
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log MCP governance event: {e}")
    
    async def register_mcp_server(
        self,
        server_id: str,
        server_name: str,
        endpoint_url: str,
        capabilities: Dict[str, Any],
        trust_level: str = 'restricted'
    ) -> MCPServer:
        """Register new MCP server"""
        
        server = MCPServer(
            server_id=server_id,
            server_name=server_name,
            endpoint_url=endpoint_url,
            capabilities=capabilities,
            trust_level=trust_level,
            supported_namespaces=capabilities.get('namespaces', []),
            requires_auth=True,
            requires_approval_by_default=True
        )
        
        self.db.add(server)
        self.db.commit()
        
        return server
    
    async def get_pending_mcp_actions(self, limit: int = 50) -> List[MCPServerAction]:
        """Get pending MCP actions requiring approval"""
        return self.db.query(MCPServerAction).filter(
            MCPServerAction.status == 'PENDING_APPROVAL'
        ).order_by(desc(MCPServerAction.risk_score), MCPServerAction.created_at).limit(limit).all()
    
    async def approve_mcp_action(
        self,
        action_id: str,
        approver_email: str,
        approval_reason: str
    ) -> Dict[str, Any]:
        """Approve MCP action"""
        
        action = self.db.query(MCPServerAction).filter(
            MCPServerAction.id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"MCP action {action_id} not found")
        
        action.status = 'APPROVED'
        action.approver_email = approver_email
        action.approved_at = datetime.now(UTC)
        action.approval_reason = approval_reason
        
        self.db.commit()
        
        # Log approval event
        await self._log_mcp_governance_event(action, 'MCP_ACTION_APPROVED')
        
        return {
            'action_id': action_id,
            'status': 'APPROVED',
            'approved_by': approver_email,
            'approved_at': action.approved_at.isoformat()
        }
    
    async def deny_mcp_action(
        self,
        action_id: str,
        approver_email: str,
        denial_reason: str
    ) -> Dict[str, Any]:
        """Deny MCP action"""
        
        action = self.db.query(MCPServerAction).filter(
            MCPServerAction.id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"MCP action {action_id} not found")
        
        action.status = 'DENIED'
        action.approver_email = approver_email
        action.approved_at = datetime.now(UTC)
        action.approval_reason = denial_reason
        
        self.db.commit()
        
        # Log denial event
        await self._log_mcp_governance_event(action, 'MCP_ACTION_DENIED')
        
        return {
            'action_id': action_id,
            'status': 'DENIED',
            'denied_by': approver_email,
            'denied_at': action.approved_at.isoformat()
        }
    
    async def get_mcp_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get MCP governance analytics"""
        
        # Time range filter
        time_threshold = datetime.now(UTC) - timedelta(hours=hours)
        
        # Total actions in time range
        total_actions = self.db.query(MCPServerAction).filter(
            MCPServerAction.created_at >= time_threshold
        ).count()
        
        # Status distribution
        status_counts = self.db.query(
            MCPServerAction.status,
            func.count(MCPServerAction.id).label('count')
        ).filter(
            MCPServerAction.created_at >= time_threshold
        ).group_by(MCPServerAction.status).all()
        
        # Risk level distribution
        risk_counts = self.db.query(
            MCPServerAction.risk_level,
            func.count(MCPServerAction.id).label('count')
        ).filter(
            MCPServerAction.created_at >= time_threshold
        ).group_by(MCPServerAction.risk_level).all()
        
        # Top active servers
        server_activity = self.db.query(
            MCPServerAction.mcp_server_id,
            MCPServerAction.mcp_server_name,
            func.count(MCPServerAction.id).label('total_actions'),
            func.avg(MCPServerAction.risk_score).label('avg_risk_score')
        ).filter(
            MCPServerAction.created_at >= time_threshold
        ).group_by(
            MCPServerAction.mcp_server_id,
            MCPServerAction.mcp_server_name
        ).order_by(desc('total_actions')).limit(10).all()
        
        return {
            'time_range_hours': hours,
            'total_actions': total_actions,
            'status_distribution': [{'status': status, 'count': count} for status, count in status_counts],
            'risk_distribution': [{'risk_level': risk, 'count': count} for risk, count in risk_counts],
            'top_servers': [
                {
                    'server_id': server_id,
                    'server_name': server_name,
                    'total_actions': total,
                    'avg_risk_score': float(avg_risk) if avg_risk else 0
                } for server_id, server_name, total, avg_risk in server_activity
            ]
        }# ============================================================================
# File: ow-ai-backend/services/mcp_governance_service.py
# MCP Server Governance Service
# ============================================================================

import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, UTC, timedelta

from models_mcp_governance import MCPServerAction, MCPServer, MCPSession, MCPPolicy
from services.immutable_audit_service import ImmutableAuditService

logger = logging.getLogger(__name__)

class MCPGovernanceService:
    """
    Enterprise MCP Server Governance Service
    Extends existing agent governance to MCP servers
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = ImmutableAuditService(db)
    
    async def evaluate_mcp_action(
        self,
        server_id: str,
        namespace: str,
        verb: str,
        resource: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, str],
        session_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Evaluate MCP action using same risk assessment as agent actions
        
        Returns governance decision with risk score and required approvals
        """
        try:
            # Create MCP action record
            mcp_action = MCPServerAction(
                mcp_server_id=server_id,
                namespace=namespace,
                verb=verb,
                resource=resource,
                parameters=parameters,
                request_id=session_context.get('request_id'),
                session_id=session_context.get('session_id'),
                client_id=session_context.get('client_id'),
                user_id=user_context.get('user_id'),
                user_email=user_context.get('user_email'),
                user_role=user_context.get('role'),
                source_ip=session_context.get('source_ip'),
                user_agent=session_context.get('user_agent')
            )
            
            # Calculate risk score using same algorithm as agents
            risk_assessment = await self._calculate_mcp_risk_score(
                server_id, namespace, verb, resource, parameters, user_context
            )
            
            mcp_action.risk_score = risk_assessment['score']
            mcp_action.risk_level = risk_assessment['level']
            mcp_action.risk_factors = risk_assessment['factors']
            
            # Apply MCP policies
            policy_result = await self._apply_mcp_policies(mcp_action)
            mcp_action.policy_result = policy_result['action']
            mcp_action.rule_id = policy_result.get('rule_id')
            mcp_action.policy_reason = policy_result.get('reason')
            
            # Determine approval requirements
            approval_decision = await self._determine_approval_requirements(mcp_action)
            mcp_action.requires_approval = approval_decision['required']
            mcp_action.approval_level = approval_decision['level']
            mcp_action.status = approval_decision['status']
            
            # Save to database
            self.db.add(mcp_action)
            self.db.commit()
            
            # Log to immutable audit trail
            await self._log_mcp_governance_event(mcp_action, 'MCP_ACTION_EVALUATED')
            
            return {
                'action_id': str(mcp_action.id),
                'decision': mcp_action.policy_result,
                'status': mcp_action.status,
                'risk_score': mcp_action.risk_score,
                'risk_level': mcp_action.risk_level,
                'requires_approval': mcp_action.requires_approval,
                'approval_level': mcp_action.approval_level,
                'reason': mcp_action.policy_reason,
                'estimated_review_time_minutes': approval_decision.get('estimated_time', 5)
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate MCP action: {e}")
            # Fail-closed: deny by default on error
            return {
                'decision': 'DENY',
                'status': 'FAILED',
                'risk_score': 100,
                'risk_level': 'CRITICAL',
                'reason': f'Governance evaluation failed: {str(e)}'
            }
    
    async def _calculate_mcp_risk_score(
        self,
        server_id: str,
        namespace: str,
        verb: str,
        resource: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Calculate risk score for MCP action using enterprise risk factors
        """
        base_score = 0
        risk_factors = []
        
        # Server risk assessment
        server_risk = await self._assess_server_risk(server_id)
        base_score += server_risk['score']
        risk_factors.extend(server_risk['factors'])
        
        # Namespace risk assessment
        namespace_risk = self._assess_namespace_risk(namespace)
        base_score += namespace_risk['score']
        risk_factors.extend(namespace_risk['factors'])
        
        # Verb risk assessment
        verb_risk = self._assess_verb_risk(verb)
        base_score += verb_risk['score']
        risk_factors.extend(verb_risk['factors'])
        
        # Resource risk assessment
        resource_risk = self._assess_resource_risk(resource, namespace)
        base_score += resource_risk['score']
        risk_factors.extend(resource_risk['factors'])
        
        # User context risk
        user_risk = self._assess_user_risk(user_context)
        base_score += user_risk['score']
        risk_factors.extend(user_risk['factors'])
        
        # Environment risk
        env_risk = self._assess_environment_risk(parameters)
        base_score += env_risk['score']
        risk_factors.extend(env_risk['factors'])
        
        # Cap at 100
        final_score = min(base_score, 100)
        
        # Determine risk level
        if final_score >= 80:
            risk_level = 'CRITICAL'
        elif final_score >= 60:
            risk_level = 'HIGH'
        elif final_score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'score': final_score,
            'level': risk_level,
            'factors': risk_factors
        }
    
    async def _assess_server_risk(self, server_id: str) -> Dict[str, Any]:
        """Assess risk based on MCP server characteristics"""
        risk_score = 0
        factors = []
        
        # Get server info
        server = self.db.query(MCPServer).filter(MCPServer.server_id == server_id).first()
        
        if not server:
            return {'score': 50, 'factors': ['unknown_server']}
        
        # Trust level assessment
        trust_levels = {'sandbox': 0, 'restricted': 20, 'trusted': 10}
        risk_score += trust_levels.get(server.trust_level, 30)
        
        if server.trust_level != 'trusted':
            factors.append(f'server_trust_{server.trust_level}')
        
        # Historical failure rate
        if server.total_actions > 0:
            failure_rate = (server.failed_actions / server.total_actions) * 100
            if failure_rate > 10:
                risk_score += 15
                factors.append('high_failure_rate')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_namespace_risk(self, namespace: str) -> Dict[str, Any]:
        """Assess risk based on MCP namespace"""
        # High-risk namespaces
        high_risk_namespaces = {
            'filesystem': 30,
            'database': 35,
            'network': 25,
            'system': 40,
            'exec': 45,
            'admin': 50
        }
        
        # Medium-risk namespaces
        medium_risk_namespaces = {
            'tools': 15,
            'api': 20,
            'data': 25
        }
        
        risk_score = high_risk_namespaces.get(namespace, 
                     medium_risk_namespaces.get(namespace, 10))
        
        factors = []
        if risk_score >= 30:
            factors.append(f'high_risk_namespace_{namespace}')
        elif risk_score >= 15:
            factors.append(f'medium_risk_namespace_{namespace}')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_verb_risk(self, verb: str) -> Dict[str, Any]:
        """Assess risk based on MCP verb/action"""
        # Critical verbs
        critical_verbs = {
            'delete', 'remove', 'destroy', 'drop', 'truncate', 'kill',
            'exec', 'execute', 'run', 'eval', 'sudo'
        }
        
        # High-risk verbs
        high_risk_verbs = {
            'write', 'create', 'modify', 'update', 'insert', 'alter',
            'grant', 'revoke', 'chmod', 'chown'
        }
        
        # Medium-risk verbs
        medium_risk_verbs = {
            'copy', 'move', 'rename', 'link', 'mount', 'unmount'
        }
        
        verb_lower = verb.lower()
        
        if any(cv in verb_lower for cv in critical_verbs):
            return {'score': 40, 'factors': [f'critical_verb_{verb}']}
        elif any(hv in verb_lower for hv in high_risk_verbs):
            return {'score': 25, 'factors': [f'high_risk_verb_{verb}']}
        elif any(mv in verb_lower for mv in medium_risk_verbs):
            return {'score': 15, 'factors': [f'medium_risk_verb_{verb}']}
        else:
            return {'score': 5, 'factors': []}
    
    def _assess_resource_risk(self, resource: str, namespace: str) -> Dict[str, Any]:
        """Assess risk based on target resource"""
        risk_score = 0
        factors = []
        
        resource_lower = resource.lower()
        
        # System critical paths
        critical_paths = {
            '/etc/passwd', '/etc/shadow', '/etc/hosts', '/etc/fstab',
            '/boot/', '/sys/', '/proc/', '/dev/',
            'c:\\windows\\system32', 'c:\\windows\\boot'
        }
        
        if any(cp in resource_lower for cp in critical_paths):
            risk_score += 35
            factors.append('system_critical_path')
        
        # Production indicators
        prod_indicators = {'prod', 'production', 'live', 'master', 'main'}
        if any(pi in resource_lower for pi in prod_indicators):
            risk_score += 20
            factors.append('production_resource')
        
        # Database tables
        if namespace == 'database':
            sensitive_tables = {'users', 'passwords', 'tokens', 'keys', 'secrets'}
            if any(st in resource_lower for st in sensitive_tables):
                risk_score += 25
                factors.append('sensitive_database_table')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_user_risk(self, user_context: Dict[str, str]) -> Dict[str, Any]:
        """Assess risk based on user context"""
        risk_score = 0
        factors = []
        
        # User role assessment
        user_role = user_context.get('role', '').lower()
        
        # High-privilege roles get lower risk (they're supposed to do risky things)
        admin_roles = {'admin', 'administrator', 'root', 'superuser', 'sysadmin'}
        if any(ar in user_role for ar in admin_roles):
            risk_score += 0  # No additional risk for admin users
        else:
            risk_score += 10  # Non-admin users get additional scrutiny
            factors.append('non_admin_user')
        
        # Check for service accounts
        user_email = user_context.get('user_email', '')
        if 'service' in user_email or 'bot' in user_email:
            risk_score += 5
            factors.append('service_account')
        
        return {'score': risk_score, 'factors': factors}
    
    def _assess_environment_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk based on environment and parameters"""
        risk_score = 0
        factors = []
        
        # Check for sensitive data in parameters
        param_str = json.dumps(parameters).lower()
        
        sensitive_keywords = {
            'password', 'token', 'key', 'secret', 'credential',
            'private', 'confidential', 'restricted'
        }
        
        for keyword in sensitive_keywords:
            if keyword in param_str:
                risk_score += 10
                factors.append(f'sensitive_parameter_{keyword}')
                break
        
        # Large payload risk
        if len(param_str) > 10000:  # 10KB threshold
            risk_score += 5
            factors.append('large_payload')
        
        return {'score': risk_score, 'factors': factors}
    
    async def _apply_mcp_policies(self, mcp_action: MCPServerAction) -> Dict[str, Any]:
        """Apply MCP governance policies"""
        # Get applicable policies
        policies = self.db.query(MCPPolicy).filter(
            MCPPolicy.is_active == True
        ).order_by(MCPPolicy.priority.desc()).all()
        
        for policy in policies:
            if await self._policy_matches_action(policy, mcp_action):
                return {
                    'action': policy.action,
                    'rule_id': str(policy.id),
                    'reason': f'Policy: {policy.policy_name}'
                }
        
        # Default policy: evaluate based on risk
        if mcp_action.risk_score >= 80:
            return {'action': 'DENY', 'reason': 'High risk score'}
        elif mcp_action.risk_score >= 50:
            return {'action': 'EVALUATE', 'reason': 'Medium risk - requires approval'}
        else:
            return {'action': 'ALLOW', 'reason': 'Low risk - auto-approved'}
    
    async def _policy_matches_action(self, policy: MCPPolicy, action: MCPServerAction) -> bool:
        """Check if policy matches MCP action"""
        # Simple pattern matching - can be enhanced with CEL or more complex rules
        
        # Check server patterns
        if policy.server_patterns:
            if not any(pattern in action.mcp_server_id for pattern in policy.server_patterns):
                return False
        
        # Check namespace patterns
        if policy.namespace_patterns:
            if not any(pattern in action.namespace for pattern in policy.namespace_patterns):
                return False
        
        # Check verb patterns
        if policy.verb_patterns:
            if not any(pattern in action.verb for pattern in policy.verb_patterns):
                return False
        
        # Check resource patterns
        if policy.resource_patterns:
            if not any(pattern in action.resource for pattern in policy.resource_patterns):
                return False
        
        # Check risk threshold
        if action.risk_score < policy.risk_threshold:
            return False
        
        return True
    
    async def _determine_approval_requirements(self, mcp_action: MCPServerAction) -> Dict[str, Any]:
        """Determine approval requirements based on risk and policy"""
        
        if mcp_action.policy_result == 'ALLOW':
            return {
                'required': False,
                'level': 0,
                'status': 'AUTO_APPROVED',
                'estimated_time': 0
            }
        
        if mcp_action.policy_result == 'DENY':
            return {
                'required': False,
                'level': 0,
                'status': 'DENIED',
                'estimated_time': 0
            }
        
        # Determine approval level based on risk score
        if mcp_action.risk_score >= 90:
            level = 5  # Executive approval
            estimated_time = 60
        elif mcp_action.risk_score >= 80:
            level = 4  # Senior management
            estimated_time = 30
        elif mcp_action.risk_score >= 70:
            level = 3  # Department head
            estimated_time = 15
        elif mcp_action.risk_score >= 50:
            level = 2  # Team lead
            estimated_time = 10
        else:
            level = 1  # Peer review
            estimated_time = 5
        
        return {
            'required': True,
            'level': level,
            'status': 'PENDING_APPROVAL',
            'estimated_time': estimated_time
        }
    
    async def _log_mcp_governance_event(self, mcp_action: MCPServerAction, event_type: str):
        """Log MCP governance event to immutable audit trail"""
        try:
            audit_id = await self.audit_service.log_event(
                event_type=event_type,
                actor_id=mcp_action.user_email,
                resource_type="MCP_SERVER",
                resource_id=f"{mcp_action.mcp_server_id}:{mcp_action.namespace}",
                action=mcp_action.verb,
                event_data={
                    "mcp_action_id": str(mcp_action.id),
                    "server_id": mcp_action.mcp_server_id,
                    "namespace": mcp_action.namespace,
                    "verb": mcp_action.verb,
                    "resource": mcp_action.resource,
                    "risk_score": mcp_action.risk_score,
                    "risk_level": mcp_action.risk_level,
                    "policy_result": mcp_action.policy_result,
                    "requires_approval": mcp_action.requires_approval,
                    "approval_level": mcp_action.approval_level,
                    "session_id": mcp_action.session_id,
                    "client_id": mcp_action.client_id
                },
                risk_level=mcp_action.risk_level,
                compliance_tags=["MCP_GOVERNANCE", "AI_SAFETY"] + mcp_action.compliance_tags,
                ip_address=mcp_action.source_ip,
                user_agent=mcp_action.user_agent
            )
            
            # Link audit trail
            mcp_action.audit_trail_id = audit_id
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log MCP governance event: {e}")
    
    async def register_mcp_server(
        self,
        server_id: str,
        server_name: str,
        endpoint_url: str,
        capabilities: Dict[str, Any],
        trust_level: str = 'restricted'
    ) -> MCPServer:
        """Register new MCP server"""
        
        server = MCPServer(
            server_id=server_id,
            server_name=server_name,
            endpoint_url=endpoint_url,
            capabilities=capabilities,
            trust_level=trust_level,
            supported_namespaces=capabilities.get('namespaces', []),
            requires_auth=True,
            requires_approval_by_default=True
        )
        
        self.db.add(server)
        self.db.commit()
        
        return server
    
    async def get_pending_mcp_actions(self, limit: int = 50) -> List[MCPServerAction]:
        """Get pending MCP actions requiring approval"""
        return self.db.query(MCPServerAction).filter(
            MCPServerAction.status == 'PENDING_APPROVAL'
        ).order_by(desc(MCPServerAction.risk_score), MCPServerAction.created_at).limit(limit).all()
    
    async def approve_mcp_action(
        self,
        action_id: str,
        approver_email: str,
        approval_reason: str
    ) -> Dict[str, Any]:
        """Approve MCP action"""
        
        action = self.db.query(MCPServerAction).filter(
            MCPServerAction.id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"MCP action {action_id} not found")
        
        action.status = 'APPROVED'
        action.approver_email = approver_email
        action.approved_at = datetime.now(UTC)
        action.approval_reason = approval_reason
        
        self.db.commit()
        
        # Log approval event
        await self._log_mcp_governance_event(action, 'MCP_ACTION_APPROVED')
        
        return {
            'action_id': action_id,
            'status': 'APPROVED',
            'approved_by': approver_email,
            'approved_at': action.approved_at.isoformat()
        }
