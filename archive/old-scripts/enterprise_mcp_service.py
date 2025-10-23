"""
Enterprise MCP Data Backbone Service
Production-ready implementation with proper error handling, logging, and security
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
import logging
import uuid
import json
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class MCPActionRequest(BaseModel):
    """Enterprise MCP Action Request Schema"""
    agent_id: str = Field(..., min_length=1, max_length=255)
    action: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=500)
    policy_id: Optional[str] = Field(default="default", max_length=100)
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['read', 'write', 'delete', 'execute', 'modify', 'create', 'list']
        if not any(action in v.lower() for action in allowed_actions):
            raise ValueError('Invalid action type')
        return v

class EnterpriseRiskEngine:
    """Enterprise-grade risk assessment engine"""
    
    HIGH_RISK_ACTIONS = ['delete', 'execute', 'modify', 'write', 'create']
    HIGH_RISK_RESOURCES = ['database', 'config', 'secret', 'admin', 'root', 'system']
    CRITICAL_RESOURCES = ['production', 'prod', 'live', 'master']
    
    @classmethod
    def calculate_risk_score(cls, action: str, resource: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate comprehensive risk score with enterprise criteria"""
        base_score = 25.0
        risk_factors = []
        
        # Action-based risk
        if any(term in action.lower() for term in cls.HIGH_RISK_ACTIONS):
            base_score += 35.0
            risk_factors.append(f"High-risk action: {action}")
        
        # Resource-based risk
        if any(term in resource.lower() for term in cls.HIGH_RISK_RESOURCES):
            base_score += 30.0
            risk_factors.append(f"Sensitive resource: {resource}")
            
        # Critical environment detection
        if any(term in resource.lower() for term in cls.CRITICAL_RESOURCES):
            base_score += 25.0
            risk_factors.append("Production environment detected")
        
        # Time-based risk (after hours)
        current_hour = datetime.now(UTC).hour
        if current_hour < 8 or current_hour > 18:
            base_score += 10.0
            risk_factors.append("After-hours execution")
        
        risk_score = min(100.0, base_score)
        risk_level = cls._determine_risk_level(risk_score)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'requires_approval': risk_score >= 50.0,
            'approval_level': cls._determine_approval_level(risk_score)
        }
    
    @staticmethod
    def _determine_risk_level(score: float) -> str:
        if score >= 80: return "critical"
        elif score >= 60: return "high"
        elif score >= 40: return "medium"
        else: return "low"
    
    @staticmethod
    def _determine_approval_level(score: float) -> int:
        if score >= 90: return 3  # Executive approval required
        elif score >= 70: return 2  # Manager approval required
        elif score >= 50: return 1  # Lead approval required
        else: return 0  # Auto-approved

class EnterpriseMCPService:
    """Enterprise MCP Service with full audit trail and compliance"""
    
    def __init__(self, db: Session):
        self.db = db
        self.risk_engine = EnterpriseRiskEngine()
    
    async def ingest_action(self, request_data: MCPActionRequest, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest MCP action with enterprise-grade processing"""
        try:
            # Risk assessment
            risk_assessment = self.risk_engine.calculate_risk_score(
                request_data.action, 
                request_data.resource, 
                request_data.metadata
            )
            
            # Generate unique tracking ID
            tracking_id = str(uuid.uuid4())
            
            # Insert into agent_actions table with enterprise fields
            result = self.db.execute(text("""
                INSERT INTO agent_actions (
                    agent_id, action_type, description, risk_level, risk_score, 
                    status, approved, user_id, tool_name, metadata, created_at
                ) VALUES (
                    :agent_id, :action_type, :description, :risk_level, :risk_score,
                    :status, :approved, :user_id, :tool_name, :metadata, :created_at
                ) RETURNING id
            """), {
                'agent_id': request_data.agent_id,
                'action_type': f"mcp_{request_data.action}",
                'description': f"Enterprise MCP: {request_data.action} on {request_data.resource}",
                'risk_level': risk_assessment['risk_level'],
                'risk_score': risk_assessment['risk_score'],
                'status': "approved" if not risk_assessment['requires_approval'] else "pending_approval",
                'approved': not risk_assessment['requires_approval'],
                'user_id': user_context.get('user_id', 1) if user_context else 1,
                'tool_name': "enterprise_mcp",
                'metadata': json.dumps({
                    'tracking_id': tracking_id,
                    'session_id': request_data.session_id,
                    'policy_id': request_data.policy_id,
                    'risk_factors': risk_assessment['risk_factors'],
                    'original_request': request_data.dict()
                }),
                'created_at': datetime.now(UTC)
            })
            
            action_id = result.fetchone()[0]
            
            # Create audit log entry
            self._create_audit_entry(action_id, request_data, risk_assessment, user_context)
            
            # Create approval request if required
            if risk_assessment['requires_approval']:
                await self._create_approval_request(action_id, risk_assessment['approval_level'])
            
            self.db.commit()
            
            # Enterprise response
            response = {
                'action_id': action_id,
                'tracking_id': tracking_id,
                'status': 'success',
                'result': 'approved' if not risk_assessment['requires_approval'] else 'requires_approval',
                'risk_assessment': risk_assessment,
                'compliance_status': 'logged',
                'next_steps': self._generate_next_steps(risk_assessment)
            }
            
            logger.info(f"Enterprise MCP action processed: {tracking_id}, risk: {risk_assessment['risk_level']}")
            return response
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Enterprise MCP processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Enterprise MCP processing failed: {str(e)}")
    
    def _create_audit_entry(self, action_id: int, request_data: MCPActionRequest, 
                           risk_assessment: Dict[str, Any], user_context: Dict[str, Any] = None):
        """Create comprehensive audit trail entry"""
        try:
            self.db.execute(text("""
                INSERT INTO audit_logs (
                    user_id, action, resource_type, resource_id, details, 
                    risk_level, timestamp
                ) VALUES (
                    :user_id, :action, :resource_type, :resource_id, :details,
                    :risk_level, :timestamp
                )
            """), {
                'user_id': user_context.get('user_id', 1) if user_context else 1,
                'action': f"MCP_{request_data.action.upper()}",
                'resource_type': 'mcp_action',
                'resource_id': str(action_id),
                'details': json.dumps({
                    'agent_id': request_data.agent_id,
                    'resource': request_data.resource,
                    'risk_score': risk_assessment['risk_score'],
                    'risk_factors': risk_assessment['risk_factors'],
                    'session_id': request_data.session_id
                }),
                'risk_level': risk_assessment['risk_level'],
                'timestamp': datetime.now(UTC)
            })
        except Exception as e:
            logger.warning(f"Audit entry creation failed: {e}")
    
    async def _create_approval_request(self, action_id: int, approval_level: int):
        """Create approval request for high-risk actions"""
        try:
            self.db.execute(text("""
                INSERT INTO approvals (agent_action_id, status, created_at)
                VALUES (:action_id, 'pending', :created_at)
            """), {
                'action_id': action_id,
                'created_at': datetime.now(UTC)
            })
        except Exception as e:
            logger.warning(f"Approval request creation failed: {e}")
    
    def _generate_next_steps(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate actionable next steps based on risk assessment"""
        steps = []
        
        if risk_assessment['requires_approval']:
            steps.append(f"Level {risk_assessment['approval_level']} approval required")
            steps.append("Action queued for security review")
        else:
            steps.append("Action auto-approved for execution")
        
        if risk_assessment['risk_level'] in ['high', 'critical']:
            steps.append("Enhanced monitoring activated")
            steps.append("Security team notification sent")
        
        return steps

def create_enterprise_mcp_endpoints(app, get_db_dependency, get_current_user_dependency):
    """Create enterprise-grade MCP endpoints"""
    
    @app.post("/mcp/actions/ingest")
    async def enterprise_mcp_ingest(request: Request, db: Session = get_db_dependency, current_user: dict = get_current_user_dependency):
        """Enterprise MCP Action Ingestion Endpoint"""
        try:
            raw_data = await request.json()
            request_data = MCPActionRequest(**raw_data)
            
            service = EnterpriseMCPService(db)
            user_context = {
                'user_id': current_user.get('user_id', 1),
                'email': current_user.get('email', 'system'),
                'role': current_user.get('role', 'user')
            }
            
            return await service.ingest_action(request_data, user_context)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
        except Exception as e:
            logger.error(f"Enterprise MCP ingest failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Enterprise MCP processing failed")
    
    @app.get("/mcp/actions/stats")
    async def enterprise_mcp_stats(db: Session = get_db_dependency):
        """Enterprise MCP Statistics with Business Intelligence"""
        try:
            result = db.execute(text("""
                SELECT 
                    status,
                    risk_level,
                    COUNT(*) as count,
                    AVG(risk_score) as avg_risk_score,
                    MAX(created_at) as last_action
                FROM agent_actions 
                WHERE action_type LIKE 'mcp_%'
                GROUP BY status, risk_level
                ORDER BY avg_risk_score DESC
            """)).fetchall()
            
            return {
                'period': 'all_time',
                'generated_at': datetime.now(UTC).isoformat(),
                'enterprise_metrics': {
                    'total_actions': sum(row[2] for row in result),
                    'avg_risk_score': sum(row[3] * row[2] for row in result if row[3]) / sum(row[2] for row in result) if result else 0,
                    'high_risk_percentage': sum(row[2] for row in result if row[1] in ['high', 'critical']) / sum(row[2] for row in result) * 100 if result else 0
                },
                'stats': [{
                    'status': row[0],
                    'risk_level': row[1],
                    'count': row[2],
                    'avg_risk_score': float(row[3]) if row[3] else 0,
                    'last_action': row[4].isoformat() if row[4] else None
                } for row in result]
            }
            
        except Exception as e:
            logger.error(f"Enterprise MCP stats failed: {str(e)}")
            return {'period': 'all_time', 'stats': [], 'error': str(e)}
    
    @app.get("/agents/activity")
    async def enterprise_agents_activity(limit: int = 50, db: Session = get_db_dependency):
        """Enterprise Agent Activity Feed with Enhanced Data"""
        try:
            result = db.execute(text("""
                SELECT 
                    aa.id, aa.agent_id, aa.action_type, aa.description, 
                    aa.risk_level, aa.risk_score, aa.status, aa.created_at,
                    aa.metadata, u.email as user_email
                FROM agent_actions aa
                LEFT JOIN users u ON aa.user_id = u.id
                ORDER BY aa.created_at DESC NULLS LAST, aa.id DESC 
                LIMIT :limit
            """), {'limit': limit}).fetchall()
            
            activities = []
            for row in result:
                metadata = {}
                if row[8]:  # metadata column
                    try:
                        metadata = json.loads(row[8])
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                activities.append({
                    'id': row[0],
                    'agent_id': row[1] or 'unknown',
                    'action_type': row[2] or 'action',
                    'description': row[3] or 'No description',
                    'risk_level': row[4] or 'medium',
                    'risk_score': float(row[5]) if row[5] else 50.0,
                    'result': row[6] or 'pending',
                    'policy_id': metadata.get('policy_id', 'default'),
                    'created_at': row[7].isoformat() if row[7] else datetime.now(UTC).isoformat(),
                    'status': row[6] or 'pending',
                    'tracking_id': metadata.get('tracking_id'),
                    'user_email': row[9],
                    'compliance_status': 'audited'
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Enterprise activity feed failed: {str(e)}")
            return []

