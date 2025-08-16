"""
Enterprise RBAC (Role-Based Access Control) Manager
6-Level Hierarchy with Separation of Duties
"""

from typing import Dict, List, Optional, Set
from enum import IntEnum
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class AccessLevel(IntEnum):
    """Enterprise Access Levels (0-5)"""
    RESTRICTED = 0      # Suspended/probationary users
    BASIC = 1          # Standard users - dashboard only
    POWER = 2          # Power users - analytics + alerts
    MANAGER = 3        # Managers - authorization capabilities
    ADMIN = 4          # Administrators - full system access
    EXECUTIVE = 5      # Executives - all privileges + reporting

class Permission:
    """Enterprise Permission System"""
    
    # Dashboard Permissions
    DASHBOARD_VIEW = "dashboard.view"
    DASHBOARD_EXPORT = "dashboard.export"
    
    # Analytics Permissions
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_REPORTS = "analytics.reports"
    ANALYTICS_EXPORT = "analytics.export"
    
    # Alert Permissions
    ALERTS_VIEW = "alerts.view"
    ALERTS_ACKNOWLEDGE = "alerts.acknowledge"
    ALERTS_CORRELATE = "alerts.correlate"
    ALERTS_DISMISS = "alerts.dismiss"
    
    # Rule Management
    RULES_VIEW = "rules.view"
    RULES_CREATE = "rules.create"
    RULES_MODIFY = "rules.modify"
    RULES_DELETE = "rules.delete"
    
    # Authorization & Approval
    AUTH_VIEW_PENDING = "auth.view_pending"
    AUTH_APPROVE_LOW = "auth.approve_low"        # Risk score 0-49
    AUTH_APPROVE_MEDIUM = "auth.approve_medium"  # Risk score 50-69
    AUTH_APPROVE_HIGH = "auth.approve_high"      # Risk score 70-89
    AUTH_APPROVE_CRITICAL = "auth.approve_critical"  # Risk score 90-100
    AUTH_EMERGENCY_OVERRIDE = "auth.emergency_override"
    
    # User Management
    USERS_VIEW = "users.view"
    USERS_CREATE = "users.create"
    USERS_MODIFY = "users.modify"
    USERS_DELETE = "users.delete"
    USERS_RESET_PASSWORD = "users.reset_password"
    USERS_MANAGE_ROLES = "users.manage_roles"
    
    # Audit & Compliance
    AUDIT_VIEW = "audit.view"
    AUDIT_EXPORT = "audit.export"
    AUDIT_DELETE = "audit.delete"
    
    # System Administration
    SYSTEM_CONFIG = "system.config"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_MAINTENANCE = "system.maintenance"

class EnterpriseRBAC:
    """Enterprise Role-Based Access Control Manager"""
    
    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
        self.separation_of_duties = self._initialize_separation_of_duties()
        
    def _initialize_role_permissions(self) -> Dict[AccessLevel, Set[str]]:
        """Initialize permission sets for each access level"""
        
        return {
            AccessLevel.RESTRICTED: set([
                # No permissions - restricted access
            ]),
            
            AccessLevel.BASIC: set([
                Permission.DASHBOARD_VIEW,
            ]),
            
            AccessLevel.POWER: set([
                Permission.DASHBOARD_VIEW,
                Permission.DASHBOARD_EXPORT,
                Permission.ANALYTICS_VIEW,
                Permission.ALERTS_VIEW,
                Permission.ALERTS_ACKNOWLEDGE,
            ]),
            
            AccessLevel.MANAGER: set([
                Permission.DASHBOARD_VIEW,
                Permission.DASHBOARD_EXPORT,
                Permission.ANALYTICS_VIEW,
                Permission.ANALYTICS_REPORTS,
                Permission.ANALYTICS_EXPORT,
                Permission.ALERTS_VIEW,
                Permission.ALERTS_ACKNOWLEDGE,
                Permission.ALERTS_CORRELATE,
                Permission.AUTH_VIEW_PENDING,
                Permission.AUTH_APPROVE_LOW,
                Permission.AUTH_APPROVE_MEDIUM,
                Permission.AUDIT_VIEW,
            ]),
            
            AccessLevel.ADMIN: set([
                Permission.DASHBOARD_VIEW,
                Permission.DASHBOARD_EXPORT,
                Permission.ANALYTICS_VIEW,
                Permission.ANALYTICS_REPORTS,
                Permission.ANALYTICS_EXPORT,
                Permission.ALERTS_VIEW,
                Permission.ALERTS_ACKNOWLEDGE,
                Permission.ALERTS_CORRELATE,
                Permission.ALERTS_DISMISS,
                Permission.RULES_VIEW,
                Permission.RULES_CREATE,
                Permission.RULES_MODIFY,
                Permission.RULES_DELETE,
                Permission.AUTH_VIEW_PENDING,
                Permission.AUTH_APPROVE_LOW,
                Permission.AUTH_APPROVE_MEDIUM,
                Permission.AUTH_APPROVE_HIGH,
                Permission.USERS_VIEW,
                Permission.USERS_CREATE,
                Permission.USERS_MODIFY,
                Permission.USERS_RESET_PASSWORD,
                Permission.AUDIT_VIEW,
                Permission.AUDIT_EXPORT,
                Permission.SYSTEM_CONFIG,
            ]),
            
            AccessLevel.EXECUTIVE: set([
                Permission.DASHBOARD_VIEW,
                Permission.DASHBOARD_EXPORT,
                Permission.ANALYTICS_VIEW,
                Permission.ANALYTICS_REPORTS,
                Permission.ANALYTICS_EXPORT,
                Permission.ALERTS_VIEW,
                Permission.ALERTS_ACKNOWLEDGE,
                Permission.ALERTS_CORRELATE,
                Permission.ALERTS_DISMISS,
                Permission.RULES_VIEW,
                Permission.RULES_CREATE,
                Permission.RULES_MODIFY,
                Permission.RULES_DELETE,
                Permission.AUTH_VIEW_PENDING,
                Permission.AUTH_APPROVE_LOW,
                Permission.AUTH_APPROVE_MEDIUM,
                Permission.AUTH_APPROVE_HIGH,
                Permission.AUTH_APPROVE_CRITICAL,
                Permission.AUTH_EMERGENCY_OVERRIDE,
                Permission.USERS_VIEW,
                Permission.USERS_CREATE,
                Permission.USERS_MODIFY,
                Permission.USERS_DELETE,
                Permission.USERS_MANAGE_ROLES,
                Permission.AUDIT_VIEW,
                Permission.AUDIT_EXPORT,
                Permission.AUDIT_DELETE,
                Permission.SYSTEM_CONFIG,
                Permission.SYSTEM_BACKUP,
                Permission.SYSTEM_MAINTENANCE,
            ])
        }
    
    def _initialize_separation_of_duties(self) -> Dict[str, Dict]:
        """Initialize Separation of Duties (SoD) rules"""
        
        return {
            "high_risk_approval": {
                "description": "High-risk actions require dual approval",
                "risk_threshold": 70,
                "required_approvers": 2,
                "required_levels": [AccessLevel.ADMIN, AccessLevel.EXECUTIVE],
                "cannot_approve_own": True
            },
            "critical_risk_approval": {
                "description": "Critical actions require executive + admin approval",
                "risk_threshold": 90,
                "required_approvers": 2,
                "required_levels": [AccessLevel.EXECUTIVE],
                "required_different_departments": True,
                "cannot_approve_own": True
            },
            "user_role_changes": {
                "description": "User role changes require manager + admin",
                "required_approvers": 2,
                "required_levels": [AccessLevel.MANAGER, AccessLevel.ADMIN],
                "cannot_approve_own": True
            },
            "emergency_override": {
                "description": "Emergency overrides require dual executive approval",
                "required_approvers": 2,
                "required_levels": [AccessLevel.EXECUTIVE],
                "required_justification": True,
                "audit_immediately": True
            }
        }
    
    def get_user_permissions(self, access_level: int) -> Set[str]:
        """Get all permissions for a user's access level"""
        try:
            level = AccessLevel(access_level)
            return self.role_permissions.get(level, set())
        except ValueError:
            logger.warning(f"Invalid access level: {access_level}")
            return set()
    
    def has_permission(self, user_access_level: int, required_permission: str) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user_access_level)
        return required_permission in user_permissions
    
    def can_approve_risk_level(self, user_access_level: int, risk_score: int) -> bool:
        """Check if user can approve actions with specific risk score"""
        
        if risk_score < 50:
            return self.has_permission(user_access_level, Permission.AUTH_APPROVE_LOW)
        elif risk_score < 70:
            return self.has_permission(user_access_level, Permission.AUTH_APPROVE_MEDIUM)
        elif risk_score < 90:
            return self.has_permission(user_access_level, Permission.AUTH_APPROVE_HIGH)
        else:
            return self.has_permission(user_access_level, Permission.AUTH_APPROVE_CRITICAL)
    
    def requires_separation_of_duties(self, action_type: str, risk_score: int = 0) -> Optional[Dict]:
        """Check if action requires separation of duties"""
        
        for sod_rule_name, sod_rule in self.separation_of_duties.items():
            # Check risk-based SoD
            if "risk_threshold" in sod_rule and risk_score >= sod_rule["risk_threshold"]:
                return {
                    "rule": sod_rule_name,
                    "required_approvers": sod_rule["required_approvers"],
                    "required_levels": sod_rule["required_levels"],
                    "description": sod_rule["description"]
                }
            
            # Check action-based SoD
            if action_type in sod_rule_name:
                return {
                    "rule": sod_rule_name,
                    "required_approvers": sod_rule["required_approvers"],
                    "required_levels": sod_rule["required_levels"],
                    "description": sod_rule["description"]
                }
        
        return None
    
    def get_access_level_name(self, level: int) -> str:
        """Get human-readable access level name"""
        level_names = {
            0: "Restricted",
            1: "Basic User",
            2: "Power User", 
            3: "Manager",
            4: "Administrator",
            5: "Executive"
        }
        return level_names.get(level, "Unknown")
    
    def get_role_summary(self, access_level: int) -> Dict:
        """Get complete role summary for user"""
        permissions = self.get_user_permissions(access_level)
        
        return {
            "access_level": access_level,
            "role_name": self.get_access_level_name(access_level),
            "permissions": list(permissions),
            "permission_count": len(permissions),
            "can_approve_low": self.can_approve_risk_level(access_level, 25),
            "can_approve_medium": self.can_approve_risk_level(access_level, 55),
            "can_approve_high": self.can_approve_risk_level(access_level, 75),
            "can_approve_critical": self.can_approve_risk_level(access_level, 95),
            "requires_sod_for_high_risk": access_level < AccessLevel.EXECUTIVE
        }

# Create global RBAC instance
enterprise_rbac = EnterpriseRBAC()

# Decorator for permission checking
def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get current user from kwargs (passed by FastAPI dependency)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_level = current_user.get('access_level', 0)
            if not enterprise_rbac.has_permission(user_level, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_minimum_level(min_level: int):
    """Decorator to require minimum access level"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_level = current_user.get('access_level', 0)
            if user_level < min_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient access level. Required: {min_level}, Current: {user_level}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator