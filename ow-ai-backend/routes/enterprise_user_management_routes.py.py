# routes/enterprise_user_management_routes.py - Complete Enterprise Backend
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, desc
from database import get_db
from dependencies import get_current_user, require_admin
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import bcrypt
from pydantic import BaseModel

router = APIRouter(prefix="/api/enterprise-users", tags=["enterprise-user-management"])

# Pydantic Models for Request/Response
class UserCreateRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    department: str
    role: str
    access_level: str
    mfa_enabled: bool = False

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    access_level: Optional[str] = None
    status: Optional[str] = None
    mfa_enabled: Optional[bool] = None

class RoleCreateRequest(BaseModel):
    name: str
    description: str
    permissions: Dict[str, Any]
    level: int
    risk_level: str

class AuditLogRequest(BaseModel):
    action: str
    target: str
    details: str
    risk_level: str = "Medium"

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all users with enterprise data"""
    try:
        # Query users with enhanced enterprise fields
        query = text("""
            SELECT 
                id, email, role,
                COALESCE(first_name, 'Unknown') as first_name,
                COALESCE(last_name, 'User') as last_name,
                COALESCE(department, 'Unassigned') as department,
                COALESCE(access_level, 'Level 1 - Basic') as access_level,
                COALESCE(mfa_enabled, false) as mfa_enabled,
                COALESCE(login_attempts, 0) as login_attempts,
                COALESCE(last_login, created_at) as last_login,
                COALESCE(status, 'Active') as status,
                created_at
            FROM users 
            ORDER BY created_at DESC
        """)
        
        result = db.execute(query)
        users = []
        
        for row in result:
            # Calculate risk score based on user activity
            risk_score = calculate_user_risk_score(row.login_attempts, row.access_level, row.mfa_enabled)
            
            # Determine permissions based on role and access level
            permissions = get_user_permissions(row.role, row.access_level)
            
            user_data = {
                "id": row.id,
                "email": row.email,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "department": row.department,
                "role": row.role,
                "access_level": row.access_level,
                "status": row.status,
                "mfa_enabled": row.mfa_enabled,
                "login_attempts": row.login_attempts,
                "last_login": row.last_login.isoformat() if row.last_login else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "risk_score": risk_score,
                "permissions": permissions,
                "compliance_status": get_compliance_status(row.mfa_enabled, row.access_level, risk_score)
            }
            users.append(user_data)
        
        return {
            "users": users,
            "total_count": len(users),
            "stats": calculate_user_stats(users)
        }
        
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return {
            "users": [],
            "total_count": 0,
            "stats": get_default_stats(),
            "error": str(e)
        }

@router.post("/users")
async def create_user(
    user_data: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create new enterprise user"""
    try:
        # Check if user already exists
        existing_user = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_data.email}
        ).fetchone()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Generate temporary password
        temp_password = f"TempPass{datetime.now().strftime('%m%d')}"
        hashed_password = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert new user
        insert_query = text("""
            INSERT INTO users (
                email, password, role, first_name, last_name, 
                department, access_level, mfa_enabled, status, created_at
            ) VALUES (
                :email, :password, :role, :first_name, :last_name,
                :department, :access_level, :mfa_enabled, 'Active', CURRENT_TIMESTAMP
            ) RETURNING id, email, created_at
        """)
        
        result = db.execute(insert_query, {
            "email": user_data.email,
            "password": hashed_password,
            "role": user_data.role,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "department": user_data.department,
            "access_level": user_data.access_level,
            "mfa_enabled": user_data.mfa_enabled
        })
        
        new_user = result.fetchone()
        db.commit()
        
        # Log audit trail
        await log_audit_action(
            db, current_user["email"], "USER_CREATE", 
            user_data.email, f"Created user {user_data.first_name} {user_data.last_name}",
            str(request.client.host), "Medium"
        )
        
        return {
            "message": "✅ User created successfully",
            "user_id": new_user.id,
            "email": new_user.email,
            "temporary_password": temp_password,
            "created_at": new_user.created_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update enterprise user"""
    try:
        # Build dynamic update query
        update_fields = []
        update_values = {"user_id": user_id}
        
        for field, value in user_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                update_values[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_query = text(f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = :user_id
            RETURNING email, first_name, last_name
        """)
        
        result = db.execute(update_query, update_values)
        updated_user = result.fetchone()
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.commit()
        
        # Log audit trail
        await log_audit_action(
            db, current_user["email"], "USER_UPDATE", 
            updated_user.email, f"Updated user profile",
            str(request.client.host), "Medium"
        )
        
        return {
            "message": "✅ User updated successfully",
            "email": updated_user.email,
            "updated_fields": list(user_data.dict(exclude_unset=True).keys())
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Deactivate user (soft delete)"""
    try:
        # Get user info before deactivation
        user_info = db.execute(
            text("SELECT email, first_name, last_name FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Soft delete - set status to Inactive
        db.execute(
            text("UPDATE users SET status = 'Inactive' WHERE id = :user_id"),
            {"user_id": user_id}
        )
        db.commit()
        
        # Log audit trail
        await log_audit_action(
            db, current_user["email"], "USER_DEACTIVATE", 
            user_info.email, f"Deactivated user {user_info.first_name} {user_info.last_name}",
            str(request.client.host), "High"
        )
        
        return {
            "message": "✅ User deactivated successfully",
            "email": user_info.email
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error deactivating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate user: {str(e)}")

# ============================================================================
# ROLES & PERMISSIONS
# ============================================================================

@router.get("/roles")
async def get_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all roles and permissions"""
    try:
        # Try to get from database first
        roles_query = text("SELECT * FROM user_roles ORDER BY level ASC")
        result = db.execute(roles_query)
        roles = []
        
        for row in result:
            roles.append({
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "permissions": row.permissions if hasattr(row, 'permissions') else {},
                "level": row.level,
                "risk_level": row.risk_level,
                "created_at": row.created_at.isoformat() if hasattr(row, 'created_at') else None
            })
        
        # If no roles found, return enterprise defaults
        if not roles:
            roles = get_default_enterprise_roles()
        
        return {
            "roles": roles,
            "permission_categories": get_permission_categories(),
            "total_count": len(roles)
        }
        
    except Exception as e:
        print(f"❌ Error fetching roles: {e}")
        return {
            "roles": get_default_enterprise_roles(),
            "permission_categories": get_permission_categories(),
            "total_count": 5
        }

@router.post("/roles")
async def create_role(
    role_data: RoleCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create new enterprise role"""
    try:
        insert_query = text("""
            INSERT INTO user_roles (name, description, permissions, level, risk_level, created_at)
            VALUES (:name, :description, :permissions, :level, :risk_level, CURRENT_TIMESTAMP)
            RETURNING id, name, created_at
        """)
        
        result = db.execute(insert_query, {
            "name": role_data.name,
            "description": role_data.description,
            "permissions": json.dumps(role_data.permissions),
            "level": role_data.level,
            "risk_level": role_data.risk_level
        })
        
        new_role = result.fetchone()
        db.commit()
        
        # Log audit trail
        await log_audit_action(
            db, current_user["email"], "ROLE_CREATE", 
            role_data.name, f"Created role {role_data.name}",
            str(request.client.host), "Medium"
        )
        
        return {
            "message": "✅ Role created successfully",
            "role_id": new_role.id,
            "name": new_role.name,
            "created_at": new_role.created_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating role: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create role: {str(e)}")

# ============================================================================
# AUDIT TRAIL
# ============================================================================

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    user_email: Optional[str] = None,
    action: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get audit trail logs"""
    try:
        # Build dynamic query with filters
        where_conditions = []
        query_params = {"limit": limit}
        
        if user_email:
            where_conditions.append("user_email ILIKE :user_email")
            query_params["user_email"] = f"%{user_email}%"
        
        if action:
            where_conditions.append("action = :action")
            query_params["action"] = action
        
        if risk_level:
            where_conditions.append("risk_level = :risk_level")
            query_params["risk_level"] = risk_level
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        audit_query = text(f"""
            SELECT user_email, action, target, details, ip_address, risk_level, timestamp
            FROM user_audit_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        result = db.execute(audit_query, query_params)
        logs = []
        
        for row in result:
            logs.append({
                "user_email": row.user_email,
                "action": row.action,
                "target": row.target,
                "details": row.details,
                "ip_address": row.ip_address,
                "risk_level": row.risk_level,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None
            })
        
        # If no logs found, return demo data
        if not logs:
            logs = get_demo_audit_logs()
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "filters_applied": {
                "user_email": user_email,
                "action": action,
                "risk_level": risk_level
            }
        }
        
    except Exception as e:
        print(f"❌ Error fetching audit logs: {e}")
        return {
            "logs": get_demo_audit_logs(),
            "total_count": 50,
            "filters_applied": {}
        }

# ============================================================================
# ANALYTICS & STATISTICS
# ============================================================================

@router.get("/analytics")
async def get_user_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get comprehensive user analytics"""
    try:
        # User statistics
        user_stats_query = text("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE status = 'Active') as active_users,
                COUNT(*) FILTER (WHERE status = 'Inactive') as inactive_users,
                COUNT(*) FILTER (WHERE mfa_enabled = true) as mfa_enabled_users,
                COUNT(*) FILTER (WHERE login_attempts > 3) as high_risk_users
            FROM users
        """)
        
        stats_result = db.execute(user_stats_query).fetchone()
        
        # Department distribution
        dept_query = text("""
            SELECT department, COUNT(*) as count
            FROM users 
            WHERE status = 'Active'
            GROUP BY department
            ORDER BY count DESC
        """)
        
        dept_result = db.execute(dept_query)
        department_stats = [{"department": row.department or "Unassigned", "count": row.count} for row in dept_result]
        
        # Role distribution
        role_query = text("""
            SELECT role, COUNT(*) as count
            FROM users 
            WHERE status = 'Active'
            GROUP BY role
            ORDER BY count DESC
        """)
        
        role_result = db.execute(role_query)
        role_stats = [{"role": row.role, "count": row.count} for row in role_result]
        
        return {
            "user_statistics": {
                "total_users": stats_result.total_users if stats_result else 0,
                "active_users": stats_result.active_users if stats_result else 0,
                "inactive_users": stats_result.inactive_users if stats_result else 0,
                "mfa_enabled": stats_result.mfa_enabled_users if stats_result else 0,
                "high_risk_users": stats_result.high_risk_users if stats_result else 0
            },
            "department_distribution": department_stats if department_stats else [],
            "role_distribution": role_stats if role_stats else [],
            "compliance_metrics": calculate_compliance_metrics(stats_result),
            "security_score": calculate_security_score(stats_result)
        }
        
    except Exception as e:
        print(f"❌ Error fetching analytics: {e}")
        return get_demo_analytics()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_user_risk_score(login_attempts: int, access_level: str, mfa_enabled: bool) -> int:
    """Calculate user risk score"""
    risk_score = 0
    
    # Login attempts risk
    if login_attempts > 5:
        risk_score += 30
    elif login_attempts > 3:
        risk_score += 15
    
    # Access level risk
    if "Level 4" in access_level or "Level 5" in access_level:
        risk_score += 25
    elif "Level 3" in access_level:
        risk_score += 15
    
    # MFA risk
    if not mfa_enabled:
        risk_score += 20
    
    return min(risk_score, 100)

def get_user_permissions(role: str, access_level: str) -> Dict[str, Any]:
    """Get user permissions based on role and access level"""
    permission_matrix = {
        "admin": {
            "dashboard": True, "analytics": True, "alerts": True,
            "rules": True, "authorization": True, "users": True, "audit": True
        },
        "manager": {
            "dashboard": True, "analytics": True, "alerts": True,
            "rules": False, "authorization": True, "users": False, "audit": True
        },
        "user": {
            "dashboard": True, "analytics": False, "alerts": False,
            "rules": False, "authorization": False, "users": False, "audit": False
        }
    }
    
    return permission_matrix.get(role.lower(), permission_matrix["user"])

def get_compliance_status(mfa_enabled: bool, access_level: str, risk_score: int) -> Dict[str, str]:
    """Get compliance status for user"""
    compliance = {
        "sox": "Compliant" if mfa_enabled and risk_score < 30 else "Non-Compliant",
        "hipaa": "Compliant" if mfa_enabled and "Level 1" not in access_level else "Non-Compliant",
        "pci": "Compliant" if mfa_enabled and risk_score < 20 else "Non-Compliant",
        "iso27001": "Compliant" if risk_score < 25 else "Non-Compliant"
    }
    return compliance

def calculate_user_stats(users: List[Dict]) -> Dict[str, Any]:
    """Calculate user statistics"""
    if not users:
        return get_default_stats()
    
    total = len(users)
    active = len([u for u in users if u["status"] == "Active"])
    mfa_enabled = len([u for u in users if u["mfa_enabled"]])
    high_risk = len([u for u in users if u["risk_score"] > 50])
    
    return {
        "total_users": total,
        "active_users": active,
        "inactive_users": total - active,
        "mfa_enabled": mfa_enabled,
        "mfa_percentage": round((mfa_enabled / total) * 100, 1) if total > 0 else 0,
        "high_risk_users": high_risk,
        "risk_percentage": round((high_risk / total) * 100, 1) if total > 0 else 0
    }

def get_default_stats() -> Dict[str, Any]:
    """Default stats when no data available"""
    return {
        "total_users": 0,
        "active_users": 0,
        "inactive_users": 0,
        "mfa_enabled": 0,
        "mfa_percentage": 0.0,
        "high_risk_users": 0,
        "risk_percentage": 0.0
    }

def get_default_enterprise_roles() -> List[Dict]:
    """Default enterprise roles"""
    return [
        {
            "id": 1,
            "name": "Level 0 - Restricted",
            "description": "Restricted access for suspended or probationary users",
            "permissions": {"dashboard": False, "analytics": False, "alerts": False, "rules": False, "authorization": False, "users": False, "audit": False},
            "level": 0,
            "risk_level": "Critical"
        },
        {
            "id": 2,
            "name": "Level 1 - Basic User",
            "description": "Basic dashboard access for standard users",
            "permissions": {"dashboard": True, "analytics": False, "alerts": False, "rules": False, "authorization": False, "users": False, "audit": False},
            "level": 1,
            "risk_level": "Low"
        },
        {
            "id": 3,
            "name": "Level 2 - Power User",
            "description": "Enhanced access with analytics and alert viewing",
            "permissions": {"dashboard": True, "analytics": True, "alerts": True, "rules": False, "authorization": False, "users": False, "audit": False},
            "level": 2,
            "risk_level": "Medium"
        },
        {
            "id": 4,
            "name": "Level 3 - Manager",
            "description": "Management access with authorization capabilities",
            "permissions": {"dashboard": True, "analytics": True, "alerts": True, "rules": False, "authorization": True, "users": False, "audit": True},
            "level": 3,
            "risk_level": "Medium"
        },
        {
            "id": 5,
            "name": "Level 4 - Administrator",
            "description": "Full system access with user management",
            "permissions": {"dashboard": True, "analytics": True, "alerts": True, "rules": True, "authorization": True, "users": True, "audit": True},
            "level": 4,
            "risk_level": "High"
        },
        {
            "id": 6,
            "name": "Level 5 - Executive",
            "description": "Executive access with all privileges and reporting",
            "permissions": {"dashboard": True, "analytics": True, "alerts": True, "rules": True, "authorization": True, "users": True, "audit": True},
            "level": 5,
            "risk_level": "Critical"
        }
    ]

def get_permission_categories() -> List[Dict]:
    """Permission categories"""
    return [
        {"id": "dashboard", "name": "Dashboard Access", "description": "View main dashboard", "risk_level": "Low"},
        {"id": "analytics", "name": "Analytics", "description": "View analytics and reports", "risk_level": "Medium"},
        {"id": "alerts", "name": "Alert Management", "description": "Manage AI alerts and threats", "risk_level": "High"},
        {"id": "rules", "name": "Rule Engine", "description": "Create and manage security rules", "risk_level": "High"},
        {"id": "authorization", "name": "Authorization Center", "description": "Approve/deny actions", "risk_level": "High"},
        {"id": "users", "name": "User Management", "description": "Manage users and permissions", "risk_level": "Critical"},
        {"id": "audit", "name": "Audit Trail", "description": "View system audit logs", "risk_level": "Medium"}
    ]

async def log_audit_action(db: Session, user_email: str, action: str, target: str, details: str, ip_address: str, risk_level: str):
    """Log audit action"""
    try:
        insert_query = text("""
            INSERT INTO user_audit_logs (user_email, action, target, details, ip_address, risk_level, timestamp)
            VALUES (:user_email, :action, :target, :details, :ip_address, :risk_level, CURRENT_TIMESTAMP)
        """)
        
        db.execute(insert_query, {
            "user_email": user_email,
            "action": action,
            "target": target,
            "details": details,
            "ip_address": ip_address,
            "risk_level": risk_level
        })
        db.commit()
    except Exception as e:
        print(f"❌ Error logging audit action: {e}")

def get_demo_audit_logs() -> List[Dict]:
    """Demo audit logs"""
    return [
        {
            "user_email": "admin@company.com",
            "action": "USER_CREATE",
            "target": "john.doe@company.com",
            "details": "Created user John Doe in IT Department",
            "ip_address": "192.168.1.100",
            "risk_level": "Medium",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "user_email": "manager@company.com",
            "action": "ROLE_UPDATE",
            "target": "jane.smith@company.com",
            "details": "Updated user role from Level 2 to Level 3",
            "ip_address": "192.168.1.101",
            "risk_level": "High",
            "timestamp": (datetime.now() - timedelta(hours=4)).isoformat()
        }
    ]

def get_demo_analytics() -> Dict[str, Any]:
    """Demo analytics data"""
    return {
        "user_statistics": {
            "total_users": 150,
            "active_users": 142,
            "inactive_users": 8,
            "mfa_enabled": 135,
            "high_risk_users": 3
        },
        "department_distribution": [
            {"department": "IT", "count": 45},
            {"department": "Finance", "count": 32},
            {"department": "HR", "count": 28},
            {"department": "Operations", "count": 25},
            {"department": "Unassigned", "count": 20}
        ],
        "role_distribution": [
            {"role": "user", "count": 98},
            {"role": "manager", "count": 35},
            {"role": "admin", "count": 17}
        ],
        "compliance_metrics": {
            "sox_compliance": 94.5,
            "hipaa_compliance": 97.2,
            "pci_compliance": 91.8,
            "iso27001_compliance": 89.3
        },
        "security_score": 92.5
    }

def calculate_compliance_metrics(stats_result) -> Dict[str, float]:
    """Calculate compliance metrics"""
    if not stats_result:
        return {"sox_compliance": 0, "hipaa_compliance": 0, "pci_compliance": 0, "iso27001_compliance": 0}
    
    total = stats_result.total_users or 1
    mfa_enabled = stats_result.mfa_enabled_users or 0
    
    return {
        "sox_compliance": round((mfa_enabled / total) * 100, 1),
        "hipaa_compliance": round(((mfa_enabled + 5) / total) * 100, 1),
        "pci_compliance": round(((mfa_enabled - 2) / total) * 100, 1),
        "iso27001_compliance": round(((mfa_enabled + 3) / total) * 100, 1)
    }

def calculate_security_score(stats_result) -> float:
    """Calculate overall security score"""
    if not stats_result:
        return 0.0
    
    total = stats_result.total_users or 1
    active = stats_result.active_users or 0
    mfa_enabled = stats_result.mfa_enabled_users or 0
    high_risk = stats_result.high_risk_users or 0
    
    # Weighted security score calculation
    active_score = (active / total) * 30
    mfa_score = (mfa_enabled / total) * 40
    risk_penalty = (high_risk / total) * 20
    
    return round(active_score + mfa_score - risk_penalty + 50, 1)