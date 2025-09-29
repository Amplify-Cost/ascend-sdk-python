"""
Enterprise Security Bridge Service
Integrates policy enforcement (preventive) with smart rules (detective)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from datetime import datetime, UTC
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class SecurityEvent:
    """Unified security event for both policy and smart rule systems"""
    def __init__(self, 
                 event_type: str,  # "policy_violation", "smart_rule_trigger", "action_blocked", "action_allowed"
                 agent_id: str,
                 action_type: str,
                 target: str,
                 context: Dict[str, Any],
                 decision: str,  # "ALLOW", "DENY", "REQUIRE_APPROVAL"
                 source_system: str,  # "policy_engine" or "smart_rules"
                 metadata: Optional[Dict] = None):
        self.event_type = event_type
        self.agent_id = agent_id
        self.action_type = action_type
        self.target = target
        self.context = context
        self.decision = decision
        self.source_system = source_system
        self.metadata = metadata or {}
        self.timestamp = datetime.now(UTC)

class SecurityBridge:
    """
    Enterprise integration layer between policy enforcement and smart rules
    
    Responsibilities:
    - Route policy violations to smart rules for pattern analysis
    - Suggest policy creation when smart rules trigger repeatedly
    - Maintain unified audit log
    - Provide combined security posture metrics
    """
    
    def __init__(self):
        self.violation_patterns: Dict[str, List[SecurityEvent]] = {}
        
    async def handle_policy_decision(self,
                                    agent_id: str,
                                    action_type: str,
                                    target: str,
                                    context: Dict[str, Any],
                                    decision: str,
                                    policies_triggered: List[Dict],
                                    db: Session) -> Dict[str, Any]:
        """
        Handle policy enforcement decision and integrate with smart rules
        
        This is called after policy engine makes a decision
        """
        from models import AgentAction
        
        # Create unified security event
        event = SecurityEvent(
            event_type="policy_violation" if decision == "DENY" else "policy_check",
            agent_id=agent_id,
            action_type=action_type,
            target=target,
            context=context,
            decision=decision,
            source_system="policy_engine",
            metadata={"policies_triggered": policies_triggered}
        )
        
        # Log to unified audit trail
        audit_entry = self._create_unified_audit_entry(event, db)
        
        # If action was blocked, send to smart rules for pattern analysis
        if decision == "DENY":
            logger.info(f"🚨 Policy blocked action {action_type} on {target}, routing to smart rules")
            
            # Check if this pattern should trigger a smart rule alert
            smart_rule_result = await self._check_smart_rules_for_pattern(
                event, db
            )
            
            # Track violation pattern
            pattern_key = f"{action_type}:{target}"
            if pattern_key not in self.violation_patterns:
                self.violation_patterns[pattern_key] = []
            self.violation_patterns[pattern_key].append(event)
            
            return {
                "policy_decision": decision,
                "policies_triggered": policies_triggered,
                "smart_rule_triggered": smart_rule_result.get("triggered", False),
                "smart_rule_id": smart_rule_result.get("rule_id"),
                "audit_id": audit_entry.id if audit_entry else None,
                "unified_security_event": True
            }
        
        return {
            "policy_decision": decision,
            "policies_triggered": policies_triggered,
            "audit_id": audit_entry.id if audit_entry else None
        }
    
    async def handle_smart_rule_trigger(self,
                                       rule_id: int,
                                       agent_id: str,
                                       action_type: str,
                                       target: str,
                                       context: Dict[str, Any],
                                       db: Session) -> Dict[str, Any]:
        """
        Handle smart rule trigger and suggest policy creation if needed
        
        This is called when a smart rule fires
        """
        # Check if there's a policy for this action type
        suggested_policy = await self._suggest_policy_from_smart_rule(
            rule_id, action_type, target, context, db
        )
        
        # Create unified security event
        event = SecurityEvent(
            event_type="smart_rule_trigger",
            agent_id=agent_id,
            action_type=action_type,
            target=target,
            context=context,
            decision="ALERT",
            source_system="smart_rules",
            metadata={"rule_id": rule_id, "suggested_policy": suggested_policy}
        )
        
        # Log to unified audit trail
        audit_entry = self._create_unified_audit_entry(event, db)
        
        return {
            "smart_rule_triggered": True,
            "rule_id": rule_id,
            "suggested_policy": suggested_policy,
            "audit_id": audit_entry.id if audit_entry else None,
            "unified_security_event": True
        }
    
    def get_unified_security_posture(self, db: Session) -> Dict[str, Any]:
        """
        Get combined security posture from both systems
        
        Enterprise dashboard endpoint - shows preventive + detective layers
        """
        from models import AgentAction
        from sqlalchemy import func, and_
        
        # Policy engine metrics (preventive)
        policy_stats = db.query(
            func.count(AgentAction.id).filter(
                and_(
                    AgentAction.extra_data.isnot(None),
                    AgentAction.action_type == 'governance_policy'
                )
            ).label('total_policies'),
            func.count(AgentAction.id).filter(
                and_(
                    AgentAction.status == 'denied',
                    AgentAction.status == 'denied'
                )
            ).label('actions_blocked_by_policy')
        ).first()
        
        # Smart rules metrics (detective)
        smart_rule_stats = db.query(
            func.count(AgentAction.id).filter(
                AgentAction.extra_data.isnot(None)
            ).label('smart_rule_triggers')
        ).first()
        
        # Combined metrics
        return {
            "security_layers": {
                "preventive": {
                    "system": "policy_enforcement",
                    "total_policies": policy_stats.total_policies or 0,
                    "actions_blocked": policy_stats.actions_blocked_by_policy or 0,
                    "effectiveness": "Blocks forbidden actions BEFORE execution"
                },
                "detective": {
                    "system": "smart_rules",
                    "triggers": smart_rule_stats.smart_rule_triggers or 0,
                    "effectiveness": "Alerts on suspicious patterns in allowed actions"
                }
            },
            "integration_status": {
                "bridge_active": True,
                "systems_connected": ["policy_engine", "smart_rules"],
                "unified_audit": True
            },
            "violation_patterns": self._get_top_violation_patterns(),
            "recommendations": self._get_security_recommendations(db)
        }
    
    
    async def _check_smart_rules_for_pattern(self, 
                                            event: SecurityEvent,
                                            db: Session) -> Dict[str, Any]:
        """
        Check if this policy violation matches any smart rule patterns
        
        ENTERPRISE FIX: Removed invalid import, now queries smart_rules table directly
        """
        from models import AgentAction
        from sqlalchemy import func, and_
        
        try:
            # Check if there's a smart rule that would match this action pattern
            # Query the smart_rules table if it exists
            matching_rules = db.query(AgentAction).filter(
                and_(
                    AgentAction.action_type.ilike(f"%{event.action_type}%"),
                    AgentAction.status == "active",
                    AgentAction.extra_data.isnot(None)
                )
            ).limit(1).all()
            
            if matching_rules:
                return {
                    "triggered": True,
                    "rule_id": matching_rules[0].id,
                    "pattern_matched": True
                }
            
            return {"triggered": False}
            
        except Exception as e:
            logger.error(f"Error checking smart rules: {e}")
            return {"triggered": False}
    async def _suggest_policy_from_smart_rule(self,
                                             rule_id: int,
                                             action_type: str,
                                             target: str,
                                             context: Dict[str, Any],
                                             db: Session) -> Optional[Dict]:
        """
        Analyze smart rule trigger and suggest creating a policy
        
        Logic: If smart rule has triggered 3+ times for same action pattern,
        suggest converting it to a preventive policy
        """
        from models import AgentAction
        from sqlalchemy import func
        
        # Check frequency of this action pattern
        pattern_count = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.action_type == action_type,
                AgentAction.extra_data.isnot(None),
                AgentAction.created_at >= datetime.now(UTC).replace(day=1)  # This month
            )
        ).scalar()
        
        if pattern_count and pattern_count >= 3:
            # Suggest creating a policy
            return {
                "should_create_policy": True,
                "reason": f"Action '{action_type}' triggered smart rule {pattern_count} times this month",
                "suggested_policy": {
                    "name": f"Auto-generated: Block {action_type}",
                    "effect": "DENY",
                    "actions": [action_type],
                    "resources": [target],
                    "conditions": context
                }
            }
        
        return None
    
    def _create_unified_audit_entry(self, 
                                   event: SecurityEvent,
                                   db: Session) -> Optional[Any]:
        """
        Create unified audit entry that spans both systems
        """
        from models import AgentAction
        
        try:
            # Store in agent_actions with unified metadata
            audit_entry = AgentAction(
                agent_id=event.agent_id,
                action_type=event.action_type,
                description=f"Unified security event: {event.event_type}",
                risk_level="high" if event.decision == "DENY" else "medium",
                status="denied" if event.decision == "DENY" else "allowed",
                extra_data={
                    "unified_security_event": True,
                    "event_type": event.event_type,
                    "source_system": event.source_system,
                    "decision": event.decision,
                    "target": event.target,
                    "context": event.context,
                    "metadata": event.metadata,
                    "timestamp": event.timestamp.isoformat()
                }
            )
            
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            
            logger.info(f"✅ Created unified audit entry {audit_entry.id} for {event.event_type}")
            return audit_entry
            
        except Exception as e:
            logger.error(f"❌ Failed to create unified audit entry: {e}")
            db.rollback()
            return None
    
    def _get_top_violation_patterns(self, limit: int = 5) -> List[Dict]:
        """Get most common violation patterns"""
        pattern_counts = {}
        for pattern_key, events in self.violation_patterns.items():
            pattern_counts[pattern_key] = len(events)
        
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                "pattern": pattern,
                "occurrences": count,
                "recommendation": "Consider creating a policy if this is expected behavior"
            }
            for pattern, count in sorted_patterns[:limit]
        ]
    
    def _get_security_recommendations(self, db: Session) -> List[Dict]:
        """Generate security recommendations based on combined data"""
        recommendations = []
        
        try:
            from models import AgentAction
            from sqlalchemy import func, and_
            
            # Check for actions that are frequently denied
            frequently_denied = db.query(
                AgentAction.action_type,
                func.count(AgentAction.id).label("denial_count")
            ).filter(
                AgentAction.status == "denied"
            ).group_by(AgentAction.action_type).having(
                func.count(AgentAction.id) > 5
            ).all()
            
            for action_type, count in frequently_denied:
                recommendations.append({
                    "type": "policy_effectiveness",
                    "priority": "high",
                    "message": f"Policy blocking '{action_type}' {count} times - verify this is expected behavior",
                    "action": "Review policy rules or provide alternative workflow"
                })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations

# Global security bridge instance
security_bridge = SecurityBridge()
