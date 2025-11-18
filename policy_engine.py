"""
Enterprise Real-Time Policy Evaluation Engine - Phase 1.2 Core Implementation

This module provides the real-time policy evaluation engine that transforms 
Policy Management into live governance decisions for the Authorization Center.

Features:
- Sub-200ms policy evaluation performance
- Natural language rule parsing and execution
- 0-100 risk scoring across 4 categories (financial, data, security, compliance)
- Enterprise caching for high-performance lookups
- Real-time policy lookup and application
- Comprehensive audit trail integration

Author: Enterprise Security Team
Version: 1.2.0
Security Level: Enterprise
Performance Target: <200ms response time
"""

import asyncio
import json
import re
import time
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import logging
from functools import lru_cache
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
from models_mcp_governance import MCPPolicy
from models import User, AgentAction, LogAuditTrail

# Configure logging
logger = logging.getLogger(__name__)


# ========== ENTERPRISE DATA STRUCTURES ==========

class RiskCategory(str, Enum):
    """Risk assessment categories for comprehensive scoring."""
    FINANCIAL = "financial"
    DATA = "data" 
    SECURITY = "security"
    COMPLIANCE = "compliance"


class PolicyDecision(str, Enum):
    """Policy evaluation decisions."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    ESCALATE = "escalate"
    CONDITIONAL = "conditional"


class MatchType(str, Enum):
    """Pattern matching types for policy rules."""
    EXACT = "exact"
    WILDCARD = "wildcard" 
    REGEX = "regex"
    CONTAINS = "contains"


@dataclass
class PolicyEvaluationContext:
    """Context for policy evaluation."""
    user_id: str
    user_email: str
    user_role: str
    action_type: str
    resource: str
    namespace: str
    environment: str = "production"
    client_ip: str = ""
    timestamp: datetime = None
    session_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        if self.session_data is None:
            self.session_data = {}


@dataclass
class RiskScoreResult:
    """Comprehensive risk scoring result."""
    total_score: int  # 0-100 overall risk score
    category_scores: Dict[RiskCategory, int]  # Individual category scores
    risk_factors: List[str]  # Identified risk factors
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    requires_approval: bool
    approval_level: int  # 1-5 escalation levels
    
    @property
    def is_high_risk(self) -> bool:
        return self.total_score >= 70
        
    @property
    def is_critical_risk(self) -> bool:
        return self.total_score >= 90


@dataclass
class PolicyMatch:
    """Policy matching result with scoring."""
    policy_id: str
    policy_name: str
    matched: bool
    confidence: float  # 0.0-1.0 matching confidence
    match_details: Dict[str, Any]
    decision: PolicyDecision
    conditions: List[str]
    execution_time_ms: float


@dataclass
class PolicyEvaluationResult:
    """Complete policy evaluation result."""
    evaluation_id: str
    decision: PolicyDecision
    risk_score: RiskScoreResult
    matched_policies: List[PolicyMatch]
    evaluation_time_ms: float
    cache_hit: bool
    audit_trail_id: str
    recommendations: List[str]
    next_review_date: Optional[datetime] = None


# ========== ENTERPRISE CACHING LAYER ==========

class PolicyCache:
    """High-performance policy caching with TTL and invalidation."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl: Dict[str, datetime] = {}
        self._policy_version_cache: Dict[str, str] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached policy evaluation result."""
        if key not in self._cache:
            self.misses += 1
            return None
            
        if key in self._ttl and datetime.now(UTC) > self._ttl[key]:
            # Cache expired
            del self._cache[key]
            del self._ttl[key]
            self.misses += 1
            return None
            
        self.hits += 1
        return self._cache[key]
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> None:
        """Set cached policy evaluation result."""
        if ttl is None:
            ttl = self.default_ttl
            
        self._cache[key] = value
        self._ttl[key] = datetime.now(UTC) + timedelta(seconds=ttl)
    
    def invalidate_policy(self, policy_id: str) -> int:
        """Invalidate all cache entries for a specific policy."""
        keys_to_remove = []
        for key in self._cache.keys():
            if policy_id in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
            if key in self._ttl:
                del self._ttl[key]
                
        return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._ttl.clear()
        self.hits = 0
        self.misses = 0
    
    @property 
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / max(total, 1)


# ========== NATURAL LANGUAGE RULE PARSER ==========

class NaturalLanguageParser:
    """Enterprise natural language policy rule parser."""
    
    # Pattern mappings for natural language to structured rules
    ACTION_PATTERNS = {
        r'(?:block|deny|prevent|forbid)': PolicyDecision.DENY,
        r'(?:allow|permit|grant|authorize)': PolicyDecision.ALLOW,
        r'(?:require approval|needs approval|must approve)': PolicyDecision.REQUIRE_APPROVAL,
        r'(?:escalate|elevate|critical review)': PolicyDecision.ESCALATE,
    }
    
    RESOURCE_PATTERNS = {
        r'(?:file|document)s?': 'file:*',
        r'(?:database|db|data)': 'database:*', 
        r'(?:system|server)s?': 'system:*',
        r'(?:network|net)': 'network:*',
        r'(?:api|endpoint)s?': 'api:*',
    }
    
    RISK_INDICATORS = {
        'financial': [r'(?:money|payment|financial|billing|cost|revenue)',
                     r'(?:transaction|purchase|invoice|accounting)'],
        'data': [r'(?:pii|personal|private|confidential|sensitive)',
                r'(?:customer data|user data|personal information)'],
        'security': [r'(?:password|credential|token|key|certificate)',
                    r'(?:access|permission|privilege|admin|root)'],
        'compliance': [r'(?:audit|compliance|regulatory|legal|policy)',
                      r'(?:sox|hipaa|gdpr|pci|iso)']
    }
    
    @classmethod
    def parse_natural_language_rule(cls, description: str) -> Dict[str, Any]:
        """
        Parse natural language policy description into structured rule.
        
        Args:
            description: Natural language policy description
            
        Returns:
            Structured policy rule with patterns and conditions
        """
        description_lower = description.lower()
        
        # Extract decision
        decision = PolicyDecision.REQUIRE_APPROVAL  # Default
        for pattern, policy_decision in cls.ACTION_PATTERNS.items():
            if re.search(pattern, description_lower, re.IGNORECASE):
                decision = policy_decision
                break
        
        # Extract resource patterns
        resource_patterns = []
        for pattern, resource_type in cls.RESOURCE_PATTERNS.items():
            if re.search(pattern, description_lower, re.IGNORECASE):
                resource_patterns.append(resource_type)
        
        if not resource_patterns:
            resource_patterns = ['*']  # Default to all resources
        
        # Extract risk indicators
        risk_factors = []
        for category, patterns in cls.RISK_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, description_lower, re.IGNORECASE):
                    risk_factors.append(f"{category}_risk_detected")
        
        # Extract conditions from common patterns
        conditions = cls._extract_conditions(description)
        
        # Determine approval requirements
        approval_required = decision == PolicyDecision.REQUIRE_APPROVAL or decision == PolicyDecision.ESCALATE
        approval_level = 1
        
        if 'critical' in description_lower or 'high risk' in description_lower:
            approval_level = 3
        elif 'sensitive' in description_lower or 'important' in description_lower:
            approval_level = 2
            
        return {
            'decision': decision.value,
            'resource_patterns': resource_patterns,
            'risk_factors': risk_factors,
            'conditions': conditions,
            'approval_required': approval_required,
            'approval_level': approval_level,
            'parsed_from_nl': True,
            'confidence': cls._calculate_parsing_confidence(description)
        }
    
    @classmethod
    def _extract_conditions(cls, description: str) -> List[Dict[str, Any]]:
        """Extract conditional logic from natural language."""
        conditions = []
        
        # Time-based conditions
        if 'during business hours' in description.lower():
            conditions.append({
                'type': 'time_range',
                'start_hour': 9,
                'end_hour': 17,
                'timezone': 'UTC'
            })
        
        # User role conditions  
        role_match = re.search(r'(?:for|when|if)\s+(\w+)\s+(?:role|user)', description.lower())
        if role_match:
            conditions.append({
                'type': 'user_role',
                'role': role_match.group(1)
            })
        
        # Environment conditions
        if 'production' in description.lower():
            conditions.append({
                'type': 'environment',
                'value': 'production'
            })
            
        return conditions
    
    @classmethod
    def _calculate_parsing_confidence(cls, description: str) -> float:
        """Calculate confidence score for natural language parsing."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for recognized patterns
        for pattern in cls.ACTION_PATTERNS.keys():
            if re.search(pattern, description, re.IGNORECASE):
                confidence += 0.2
                break
        
        # Boost for resource recognition
        for pattern in cls.RESOURCE_PATTERNS.keys():
            if re.search(pattern, description, re.IGNORECASE):
                confidence += 0.1
                break
        
        # Boost for risk indicators
        risk_found = False
        for patterns in cls.RISK_INDICATORS.values():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    confidence += 0.1
                    risk_found = True
                    break
            if risk_found:
                break
                
        return min(confidence, 1.0)


# ========== RISK SCORING ENGINE ==========

class EnterpriseRiskScorer:
    """Enterprise risk scoring across 4 categories with ML-ready features."""
    
    # Base risk scores by category
    BASE_SCORES = {
        RiskCategory.FINANCIAL: {
            'low': 15, 'medium': 40, 'high': 70, 'critical': 95
        },
        RiskCategory.DATA: {
            'low': 20, 'medium': 45, 'high': 75, 'critical': 90
        },
        RiskCategory.SECURITY: {
            'low': 25, 'medium': 50, 'high': 80, 'critical': 95
        },
        RiskCategory.COMPLIANCE: {
            'low': 10, 'medium': 35, 'high': 65, 'critical': 85
        }
    }
    
    # Risk multipliers by context
    CONTEXT_MULTIPLIERS = {
        'production': 1.5,
        'staging': 1.2,
        'development': 0.8,
        'admin_user': 1.4,
        'service_account': 1.3,
        'external_access': 2.0,
        'after_hours': 1.3,
        'bulk_operation': 1.6
    }
    
    @classmethod
    def calculate_comprehensive_risk_score(
        cls, 
        context: PolicyEvaluationContext,
        matched_policies: List[PolicyMatch],
        action_metadata: Dict[str, Any] = None
    ) -> RiskScoreResult:
        """
        Calculate comprehensive 0-100 risk score across all categories.
        
        Args:
            context: Policy evaluation context
            matched_policies: List of matched policies
            action_metadata: Additional action-specific metadata
            
        Returns:
            Comprehensive risk scoring result
        """
        start_time = time.time()
        
        if action_metadata is None:
            action_metadata = {}
        
        # Initialize category scores
        category_scores = {}
        risk_factors = []
        
        # Calculate base risk for each category
        for category in RiskCategory:
            base_score = cls._calculate_category_base_score(
                category, context, action_metadata
            )
            
            # Apply policy adjustments
            policy_adjustment = cls._calculate_policy_adjustments(
                category, matched_policies
            )
            
            # Apply context multipliers
            context_multiplier = cls._calculate_context_multipliers(
                context, action_metadata
            )
            
            # Calculate final category score
            final_score = min(100, int(base_score * context_multiplier + policy_adjustment))
            category_scores[category] = final_score
            
            # Track risk factors
            if final_score >= 60:
                risk_factors.append(f"{category.value}_high_risk")
        
        # Calculate total weighted score
        total_score = cls._calculate_weighted_total(category_scores)
        
        # Determine risk level and approval requirements  
        risk_level, requires_approval, approval_level = cls._determine_risk_level(
            total_score, category_scores
        )
        
        logger.debug(f"Risk calculation completed in {(time.time() - start_time)*1000:.2f}ms")
        
        return RiskScoreResult(
            total_score=total_score,
            category_scores=category_scores,
            risk_factors=risk_factors,
            risk_level=risk_level,
            requires_approval=requires_approval,
            approval_level=approval_level
        )
    
    @classmethod
    def _calculate_category_base_score(
        cls,
        category: RiskCategory, 
        context: PolicyEvaluationContext,
        metadata: Dict[str, Any]
    ) -> int:
        """Calculate base risk score for specific category."""
        
        if category == RiskCategory.FINANCIAL:
            # Financial risk assessment
            if 'billing' in context.action_type.lower():
                return cls.BASE_SCORES[category]['high']
            elif 'payment' in context.resource.lower():
                return cls.BASE_SCORES[category]['medium']
            else:
                return cls.BASE_SCORES[category]['low']
                
        elif category == RiskCategory.DATA:
            # Data sensitivity assessment
            if any(indicator in context.resource.lower() 
                   for indicator in ['pii', 'personal', 'customer', 'sensitive']):
                return cls.BASE_SCORES[category]['high']
            elif context.namespace in ['database', 'storage']:
                return cls.BASE_SCORES[category]['medium']
            else:
                return cls.BASE_SCORES[category]['low']
                
        elif category == RiskCategory.SECURITY:
            # Security risk assessment
            if any(indicator in context.action_type.lower()
                   for indicator in ['admin', 'privilege', 'access', 'credential']):
                return cls.BASE_SCORES[category]['high']
            elif context.user_role in ['admin', 'superuser']:
                return cls.BASE_SCORES[category]['medium']
            else:
                return cls.BASE_SCORES[category]['low']
                
        elif category == RiskCategory.COMPLIANCE:
            # Compliance risk assessment
            if context.environment == 'production':
                return cls.BASE_SCORES[category]['medium']
            elif any(framework in context.resource.lower()
                    for framework in ['audit', 'compliance', 'regulatory']):
                return cls.BASE_SCORES[category]['high']
            else:
                return cls.BASE_SCORES[category]['low']
        
        return cls.BASE_SCORES[category]['medium']  # Default
    
    @classmethod
    def _calculate_policy_adjustments(
        cls,
        category: RiskCategory,
        matched_policies: List[PolicyMatch]
    ) -> int:
        """Calculate risk adjustments based on matched policies."""
        adjustment = 0
        
        for policy in matched_policies:
            if policy.decision == PolicyDecision.DENY:
                adjustment += 30  # High risk if policy would deny
            elif policy.decision == PolicyDecision.ESCALATE:
                adjustment += 20
            elif policy.decision == PolicyDecision.REQUIRE_APPROVAL:
                adjustment += 10
            elif policy.decision == PolicyDecision.ALLOW:
                adjustment -= 5  # Slight reduction for explicit allow
                
        return min(30, max(-10, adjustment))  # Cap adjustments
    
    @classmethod
    def _calculate_context_multipliers(
        cls,
        context: PolicyEvaluationContext,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate context-based risk multipliers."""
        multiplier = 1.0
        
        # Environment multiplier
        if context.environment in cls.CONTEXT_MULTIPLIERS:
            multiplier *= cls.CONTEXT_MULTIPLIERS[context.environment]
        
        # User role multiplier
        if context.user_role in ['admin', 'superuser']:
            multiplier *= cls.CONTEXT_MULTIPLIERS.get('admin_user', 1.0)
        
        # Time-based multiplier
        current_hour = context.timestamp.hour
        if current_hour < 6 or current_hour > 22:  # After hours
            multiplier *= cls.CONTEXT_MULTIPLIERS.get('after_hours', 1.0)
        
        # External access
        if context.client_ip and not context.client_ip.startswith(('10.', '192.168.', '172.')):
            multiplier *= cls.CONTEXT_MULTIPLIERS.get('external_access', 1.0)
            
        return min(2.5, multiplier)  # Cap multiplier
    
    @classmethod
    def _calculate_weighted_total(cls, category_scores: Dict[RiskCategory, int]) -> int:
        """Calculate weighted total risk score."""
        # Category weights (must sum to 1.0)
        weights = {
            RiskCategory.SECURITY: 0.35,
            RiskCategory.DATA: 0.30, 
            RiskCategory.COMPLIANCE: 0.20,
            RiskCategory.FINANCIAL: 0.15
        }
        
        total = sum(
            category_scores[category] * weights[category]
            for category in RiskCategory
        )
        
        return min(100, max(0, int(total)))
    
    @classmethod
    def _determine_risk_level(
        cls,
        total_score: int,
        category_scores: Dict[RiskCategory, int]
    ) -> Tuple[str, bool, int]:
        """Determine risk level and approval requirements."""
        
        # Check for critical risks in any category
        if any(score >= 90 for score in category_scores.values()):
            return "CRITICAL", True, 5
        elif total_score >= 80:
            return "HIGH", True, 3
        elif total_score >= 50:
            return "MEDIUM", True, 2
        elif total_score >= 25:
            return "LOW", False, 1
        else:
            return "MINIMAL", False, 0


# ========== MAIN POLICY ENGINE ==========

class EnterpriseRealTimePolicyEngine:
    """
    Enterprise real-time policy evaluation engine.
    
    Provides sub-200ms policy evaluation with comprehensive
    risk scoring, caching, and audit trail integration.
    """
    
    def __init__(self, db: Session, cache_ttl: int = 300):
        self.db = db
        self.cache = PolicyCache(cache_ttl)
        self.nl_parser = NaturalLanguageParser()
        self.risk_scorer = EnterpriseRiskScorer()
        
        # Performance metrics
        self.total_evaluations = 0
        self.avg_evaluation_time_ms = 0.0
        self.cache_hit_rate = 0.0
        
        logger.info("Enterprise Real-Time Policy Engine initialized")
    
    async def evaluate_policy(
        self,
        context: PolicyEvaluationContext,
        action_metadata: Dict[str, Any] = None
    ) -> PolicyEvaluationResult:
        """
        Main policy evaluation method with sub-200ms performance target.
        
        Args:
            context: Policy evaluation context
            action_metadata: Additional action-specific metadata
            
        Returns:
            Complete policy evaluation result
        """
        evaluation_start = time.time()
        evaluation_id = self._generate_evaluation_id(context)
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(context)
            cached_result = self.cache.get(cache_key)
            
            if cached_result:
                logger.debug(f"Policy evaluation cache hit for {evaluation_id}")
                return PolicyEvaluationResult(
                    evaluation_id=evaluation_id,
                    decision=PolicyDecision(cached_result['decision']),
                    risk_score=RiskScoreResult(**cached_result['risk_score']),
                    matched_policies=[PolicyMatch(**p) for p in cached_result['matched_policies']], 
                    evaluation_time_ms=(time.time() - evaluation_start) * 1000,
                    cache_hit=True,
                    audit_trail_id=cached_result['audit_trail_id'],
                    recommendations=cached_result['recommendations']
                )
            
            # Perform real-time policy matching
            matched_policies = await self._match_policies(context)
            
            # Calculate comprehensive risk score
            risk_score = self.risk_scorer.calculate_comprehensive_risk_score(
                context, matched_policies, action_metadata
            )
            
            # Determine final decision
            final_decision = self._determine_final_decision(matched_policies, risk_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                context, matched_policies, risk_score
            )
            
            # Create audit trail
            audit_trail_id = await self._create_audit_trail(
                evaluation_id, context, matched_policies, risk_score, final_decision
            )
            
            # Calculate total evaluation time
            evaluation_time_ms = (time.time() - evaluation_start) * 1000
            
            # Build result
            result = PolicyEvaluationResult(
                evaluation_id=evaluation_id,
                decision=final_decision,
                risk_score=risk_score,
                matched_policies=matched_policies,
                evaluation_time_ms=evaluation_time_ms,
                cache_hit=False,
                audit_trail_id=audit_trail_id,
                recommendations=recommendations
            )
            
            # Cache result for future lookups
            self._cache_result(cache_key, result)
            
            # Update performance metrics
            self._update_metrics(evaluation_time_ms)
            
            logger.info(f"Policy evaluation {evaluation_id} completed in {evaluation_time_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Policy evaluation {evaluation_id} failed: {str(e)}")
            # Return safe default
            return self._create_safe_default_result(evaluation_id, context, evaluation_start)
    
    async def _match_policies(
        self, 
        context: PolicyEvaluationContext
    ) -> List[PolicyMatch]:
        """Match active policies against the evaluation context."""
        match_start = time.time()
        matched_policies = []
        
        # Query active policies from database
        policies_query = """
            SELECT id, policy_name, natural_language_description,
                   resource_patterns, namespace_patterns, verb_patterns,
                   actions, conditions, priority
            FROM mcp_policies
            WHERE is_active = true AND policy_status = 'deployed'
            ORDER BY priority DESC, created_at ASC
        """
        
        policy_results = self.db.execute(text(policies_query)).fetchall()
        
        for policy_row in policy_results:
            match_result = await self._evaluate_policy_match(policy_row, context)
            if match_result.matched:
                matched_policies.append(match_result)
        
        # Sort by confidence and priority
        matched_policies.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.debug(f"Policy matching completed in {(time.time() - match_start)*1000:.2f}ms, found {len(matched_policies)} matches")
        
        return matched_policies
    
    async def _evaluate_policy_match(
        self,
        policy_row: Any,
        context: PolicyEvaluationContext
    ) -> PolicyMatch:
        """Evaluate if a single policy matches the context."""
        
        policy_id = str(policy_row[0])
        policy_name = policy_row[1]
        
        # Parse patterns from database
        resource_patterns = policy_row[3] if policy_row[3] else []
        namespace_patterns = policy_row[4] if policy_row[4] else []
        verb_patterns = policy_row[5] if policy_row[5] else []
        
        # Calculate match confidence
        confidence = 0.0
        match_details = {}
        
        # Resource pattern matching
        if self._matches_patterns(context.resource, resource_patterns):
            confidence += 0.4
            match_details['resource_match'] = True
        
        # Namespace pattern matching
        if self._matches_patterns(context.namespace, namespace_patterns):
            confidence += 0.3
            match_details['namespace_match'] = True
        
        # Action type pattern matching  
        if self._matches_patterns(context.action_type, verb_patterns):
            confidence += 0.3
            match_details['action_match'] = True
        
        # Evaluate conditions
        conditions_met = await self._evaluate_conditions(
            policy_row[7] if policy_row[7] else {}, context
        )
        if conditions_met:
            match_details['conditions_met'] = True
        else:
            confidence *= 0.5  # Reduce confidence if conditions not met
        
        # Determine if policy matches
        matched = confidence >= 0.3  # Minimum confidence threshold
        
        # Parse policy decision with proper enum mapping
        policy_action = policy_row[6] if policy_row[6] else 'REQUIRE_APPROVAL'
        
        # Map database values to PolicyDecision enum
        decision_mapping = {
            'DENY': PolicyDecision.DENY,
            'ALLOW': PolicyDecision.ALLOW,
            'REQUIRE_APPROVAL': PolicyDecision.REQUIRE_APPROVAL,
            'ESCALATE': PolicyDecision.ESCALATE,
            'CONDITIONAL': PolicyDecision.CONDITIONAL
        }
        
        policy_decision = decision_mapping.get(policy_action, PolicyDecision.REQUIRE_APPROVAL)
        
        return PolicyMatch(
            policy_id=policy_id,
            policy_name=policy_name,
            matched=matched,
            confidence=confidence,
            match_details=match_details,
            decision=policy_decision,
            conditions=list(policy_row[7].keys()) if policy_row[7] else [],
            execution_time_ms=0.5  # Placeholder - could measure actual time
        )
    
    def _matches_patterns(self, value: str, patterns: List[str]) -> bool:
        """Check if value matches any of the given patterns."""
        if not patterns:
            return True  # Empty patterns match everything
        
        value_lower = value.lower()
        
        for pattern in patterns:
            if not pattern:
                continue
                
            pattern_lower = pattern.lower()
            
            # Wildcard matching
            if '*' in pattern_lower:
                import fnmatch
                if fnmatch.fnmatch(value_lower, pattern_lower):
                    return True
            # Exact matching
            elif pattern_lower == value_lower:
                return True
            # Contains matching
            elif pattern_lower in value_lower:
                return True
        
        return False
    
    async def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: PolicyEvaluationContext
    ) -> bool:
        """Evaluate policy conditions against context."""
        if not conditions:
            return True
        
        # Time-based conditions
        if 'time_range' in conditions:
            time_condition = conditions['time_range']
            current_hour = context.timestamp.hour
            if not (time_condition.get('start_hour', 0) <= current_hour <= time_condition.get('end_hour', 23)):
                return False
        
        # User role conditions
        if 'user_role' in conditions:
            required_role = conditions['user_role']
            if context.user_role != required_role:
                return False
        
        # Environment conditions
        if 'environment' in conditions:
            required_env = conditions['environment'] 
            if context.environment != required_env:
                return False
        
        return True
    
    def _determine_final_decision(
        self,
        matched_policies: List[PolicyMatch],
        risk_score: RiskScoreResult
    ) -> PolicyDecision:
        """Determine final policy decision based on matches and risk."""
        
        # If any policy explicitly denies, deny
        for policy in matched_policies:
            if policy.decision == PolicyDecision.DENY and policy.confidence > 0.7:
                return PolicyDecision.DENY
        
        # If critical risk, escalate  
        if risk_score.is_critical_risk:
            return PolicyDecision.ESCALATE
        
        # If high risk, require approval
        if risk_score.is_high_risk or risk_score.requires_approval:
            return PolicyDecision.REQUIRE_APPROVAL
        
        # Check for explicit allows
        high_confidence_allows = [
            p for p in matched_policies 
            if p.decision == PolicyDecision.ALLOW and p.confidence > 0.8
        ]
        
        if high_confidence_allows:
            return PolicyDecision.ALLOW
        
        # Default to require approval for safety
        return PolicyDecision.REQUIRE_APPROVAL
    
    def _generate_recommendations(
        self,
        context: PolicyEvaluationContext,
        matched_policies: List[PolicyMatch],
        risk_score: RiskScoreResult
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Risk-based recommendations
        if risk_score.is_critical_risk:
            recommendations.append("🚨 CRITICAL RISK: Requires executive approval and security review")
        elif risk_score.is_high_risk:
            recommendations.append("⚠️  HIGH RISK: Requires manager approval and audit logging")
        
        # Category-specific recommendations
        for category, score in risk_score.category_scores.items():
            if score >= 70:
                if category == RiskCategory.SECURITY:
                    recommendations.append("🔒 Enhanced security monitoring recommended")
                elif category == RiskCategory.DATA:
                    recommendations.append("🗃️  Data protection controls should be verified")
                elif category == RiskCategory.COMPLIANCE:
                    recommendations.append("📋 Compliance documentation required")
                elif category == RiskCategory.FINANCIAL:
                    recommendations.append("💰 Financial impact assessment needed")
        
        # Policy-specific recommendations
        denied_policies = [p for p in matched_policies if p.decision == PolicyDecision.DENY]
        if denied_policies:
            recommendations.append(f"❌ Action blocked by {len(denied_policies)} policies")
        
        return recommendations
    
    async def _create_audit_trail(
        self,
        evaluation_id: str,
        context: PolicyEvaluationContext,
        matched_policies: List[PolicyMatch],
        risk_score: RiskScoreResult,
        decision: PolicyDecision
    ) -> str:
        """Create comprehensive audit trail entry."""
        
        audit_details = {
            'evaluation_id': evaluation_id,
            'user_context': {
                'user_id': context.user_id,
                'user_email': context.user_email, 
                'user_role': context.user_role,
                'client_ip': context.client_ip
            },
            'action_context': {
                'action_type': context.action_type,
                'resource': context.resource,
                'namespace': context.namespace,
                'environment': context.environment
            },
            'policy_evaluation': {
                'matched_policies': len(matched_policies),
                'policy_ids': [p.policy_id for p in matched_policies],
                'final_decision': decision.value
            },
            'risk_assessment': asdict(risk_score),
            'timestamp': context.timestamp.isoformat()
        }
        
        try:
            # ENTERPRISE FIX: LogAuditTrail doesn't have timestamp field
            # Store timestamp in details JSON instead
            audit_log = LogAuditTrail(
                user_id=1,  # System user for policy engine
                action="policy_evaluation",
                details=json.dumps(audit_details),
                ip_address=context.client_ip or "policy_engine",
                risk_level=risk_score.risk_level
                # timestamp removed - store in details instead (already there)
            )

            self.db.add(audit_log)
            self.db.flush()  # ENTERPRISE PATTERN: Use flush() instead of commit()

            return str(audit_log.id)

        except Exception as e:
            # ENTERPRISE FIX: Rollback the session to prevent pending rollback errors
            # This allows the calling code to continue with their own commit
            self.db.rollback()
            logger.error(f"Failed to create audit trail: {str(e)}")
            return f"audit_trail_error_{evaluation_id}"
    
    def _generate_evaluation_id(self, context: PolicyEvaluationContext) -> str:
        """Generate unique evaluation ID."""
        content = f"{context.user_id}:{context.action_type}:{context.resource}:{context.timestamp.isoformat()}"
        hash_obj = hashlib.sha256(content.encode())
        return f"eval_{hash_obj.hexdigest()[:16]}"
    
    def _generate_cache_key(self, context: PolicyEvaluationContext) -> str:
        """Generate cache key for policy evaluation."""
        # Create cache key from context elements (excluding timestamp for cacheability)
        key_elements = [
            context.user_role,
            context.action_type, 
            context.resource,
            context.namespace,
            context.environment
        ]
        return hashlib.sha256(":".join(key_elements).encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: PolicyEvaluationResult) -> None:
        """Cache policy evaluation result."""
        cache_data = {
            'decision': result.decision.value,
            'risk_score': asdict(result.risk_score),
            'matched_policies': [asdict(p) for p in result.matched_policies],
            'audit_trail_id': result.audit_trail_id,
            'recommendations': result.recommendations
        }
        
        # Cache for shorter time if high risk
        ttl = 60 if result.risk_score.is_high_risk else 300
        self.cache.set(cache_key, cache_data, ttl)
    
    def _update_metrics(self, evaluation_time_ms: float) -> None:
        """Update performance metrics."""
        self.total_evaluations += 1
        
        # Calculate rolling average
        if self.avg_evaluation_time_ms == 0:
            self.avg_evaluation_time_ms = evaluation_time_ms
        else:
            self.avg_evaluation_time_ms = (
                (self.avg_evaluation_time_ms * (self.total_evaluations - 1) + evaluation_time_ms) 
                / self.total_evaluations
            )
        
        self.cache_hit_rate = self.cache.hit_rate
    
    def _create_safe_default_result(
        self,
        evaluation_id: str,
        context: PolicyEvaluationContext,
        evaluation_start: float
    ) -> PolicyEvaluationResult:
        """Create safe default result when evaluation fails."""
        
        return PolicyEvaluationResult(
            evaluation_id=evaluation_id,
            decision=PolicyDecision.REQUIRE_APPROVAL,  # Safe default
            risk_score=RiskScoreResult(
                total_score=75,  # Conservative high risk
                category_scores={
                    RiskCategory.SECURITY: 75,
                    RiskCategory.DATA: 75,
                    RiskCategory.COMPLIANCE: 75,
                    RiskCategory.FINANCIAL: 75
                },
                risk_factors=['evaluation_error'],
                risk_level='HIGH',
                requires_approval=True,
                approval_level=3
            ),
            matched_policies=[],
            evaluation_time_ms=(time.time() - evaluation_start) * 1000,
            cache_hit=False,
            audit_trail_id="error_default",
            recommendations=["⚠️ Policy evaluation error - manual review required"]
        )
    
    # ========== PUBLIC METRICS AND ADMIN METHODS ==========
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics."""
        return {
            'total_evaluations': self.total_evaluations,
            'avg_evaluation_time_ms': round(self.avg_evaluation_time_ms, 2),
            'cache_hit_rate': round(self.cache_hit_rate * 100, 1),
            'cache_entries': len(self.cache._cache),
            'performance_target_met': self.avg_evaluation_time_ms < 200,
            'last_updated': datetime.now(UTC).isoformat()
        }
    
    def clear_cache(self) -> Dict[str, int]:
        """Clear policy cache and return statistics."""
        entries_cleared = len(self.cache._cache)
        self.cache.clear()
        
        return {
            'entries_cleared': entries_cleared,
            'cache_hit_rate_before_clear': self.cache_hit_rate
        }
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """Get policy engine statistics."""
        try:
            stats_query = """
                SELECT 
                    COUNT(*) as total_policies,
                    COUNT(*) FILTER (WHERE is_active = true) as active_policies,
                    COUNT(*) FILTER (WHERE policy_status = 'deployed') as deployed_policies,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as created_today
                FROM mcp_policies
            """
            
            result = self.db.execute(text(stats_query)).fetchone()
            
            return {
                'total_policies': result[0] if result else 0,
                'active_policies': result[1] if result else 0,
                'deployed_policies': result[2] if result else 0,
                'created_today': result[3] if result else 0,
                'engine_uptime_hours': (datetime.now(UTC) - datetime.now(UTC)).total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Failed to get policy statistics: {str(e)}")
            return {
                'total_policies': 0,
                'active_policies': 0,
                'deployed_policies': 0,
                'created_today': 0,
                'error': str(e)
            }


# ========== FACTORY AND UTILITY FUNCTIONS ==========

def create_policy_engine(db: Session, cache_ttl: int = 300) -> EnterpriseRealTimePolicyEngine:
    """Factory function to create policy engine instance."""
    return EnterpriseRealTimePolicyEngine(db, cache_ttl)


def create_evaluation_context(
    user_id: str,
    user_email: str,
    user_role: str,
    action_type: str,
    resource: str,
    namespace: str = "default",
    environment: str = "production",
    client_ip: str = "",
    session_data: Dict[str, Any] = None
) -> PolicyEvaluationContext:
    """Factory function to create policy evaluation context."""
    return PolicyEvaluationContext(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        action_type=action_type,
        resource=resource,
        namespace=namespace,
        environment=environment,
        client_ip=client_ip,
        session_data=session_data or {}
    )


# Export main classes
__all__ = [
    'EnterpriseRealTimePolicyEngine',
    'PolicyEvaluationContext', 
    'PolicyEvaluationResult',
    'RiskScoreResult',
    'PolicyDecision',
    'RiskCategory',
    'create_policy_engine',
    'create_evaluation_context'
]