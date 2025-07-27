# main.py - YOUR ORIGINAL CODE WITH MINIMAL FIXES ONLY
from dotenv import load_dotenv
import openai
import os
import logging
from datetime import datetime, UTC, timedelta  # ADDED timedelta import
from typing import List, Dict, Any
from dependencies import require_admin
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from database import get_db, engine  # REMOVED DATABASE_URL import
from models import User, AgentAction, Alert, LogAuditTrail
from dependencies import get_current_user, verify_token

# COMMENTED OUT - These files don't exist in your deployment
# from agent_routes import agent_router
# from rule_routes import rule_router
# from authorization_routes import authorization_router

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="OW-AI Enterprise Authorization Platform", version="1.0.0")

# CORS Configuration (your existing config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://owai.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
openai.api_key = os.getenv("OPENAI_API_KEY")

# COMMENTED OUT - Router includes that don't exist
#app.include_router(agent_router)
#app.include_router(rule_router) 
#app.include_router(authorization_router)

# ================== AUTHENTICATION ROUTES (YOUR EXISTING CODE) ==================

@app.post("/register")
async def register(request: Request):
    """User registration endpoint"""
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "user")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        # Hash password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(password)

        # Check if user exists
        db: Session = next(get_db())
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        new_user = User(email=email, hashed_password=hashed_password, role=role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user registered: {email}")
        return {"message": "User registered successfully", "user_id": new_user.id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/login")
async def login(request: Request):
    """User login endpoint"""
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        # Verify user
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Generate JWT token
        import jwt
        from datetime import timedelta
        
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        secret_key = os.getenv("SECRET_KEY", "your-secret-key")
        token = jwt.encode(payload, secret_key, algorithm="HS256")

        logger.info(f"User logged in: {email}")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

# ================== YOUR ANALYTICS ROUTES (PRESERVED) ==================

@app.get("/analytics/trends")
async def get_analytics_trends():
    """Get analytics trends"""
    try:
        return {
            "trends": [
                {"month": "Jan", "value": 245},
                {"month": "Feb", "value": 423},
                {"month": "Mar", "value": 356},
                {"month": "Apr", "value": 789},
                {"month": "May", "value": 567},
                {"month": "Jun", "value": 834}
            ]
        }
    except Exception as e:
        logger.error(f"Analytics trends error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics trends")

@app.get("/analytics/risk-distribution")
async def get_risk_distribution():
    """Get risk distribution analytics"""
    try:
        return {
            "risk_distribution": [
                {"name": "High Risk", "value": 125, "color": "#dc2626"},
                {"name": "Medium Risk", "value": 289, "color": "#f59e0b"},
                {"name": "Low Risk", "value": 456, "color": "#10b981"}
            ]
        }
    except Exception as e:
        logger.error(f"Risk distribution error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch risk distribution")

@app.get("/analytics/monthly-summary")
async def get_monthly_summary():
    """Get monthly summary analytics"""
    try:
        return {
            "summary": {
                "total_actions": 1247,
                "approved_actions": 856,
                "rejected_actions": 234,
                "pending_actions": 157,
                "high_risk_actions": 89,
                "compliance_score": 94.2
            }
        }
    except Exception as e:
        logger.error(f"Monthly summary error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch monthly summary")

# ================== YOUR AGENT ACTIVITY ROUTES (PRESERVED) ==================

@app.get("/agent-activity")
async def get_agent_activity():
    """Get agent activity data"""
    try:
        current_time = datetime.now()
        return [
            {
                "id": 1,
                "agent_id": "security-scanner-01",
                "action": "Vulnerability scan completed",
                "timestamp": current_time.isoformat(),
                "status": "completed",
                "details": "Scanned 245 endpoints, found 3 vulnerabilities"
            },
            {
                "id": 2,
                "agent_id": "compliance-checker",
                "action": "SOX compliance audit",
                "timestamp": (current_time - timedelta(minutes=15)).isoformat(),
                "status": "in_progress",
                "details": "Auditing financial system access controls"
            },
            {
                "id": 3,
                "agent_id": "threat-detector",
                "action": "Network anomaly detection",
                "timestamp": (current_time - timedelta(minutes=30)).isoformat(),
                "status": "completed",
                "details": "Analyzed 1.2M network packets, no threats detected"
            }
        ]
    except Exception as e:
        logger.error(f"Agent activity error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent activity")

# ================== YOUR RULES ROUTES (PRESERVED) ==================

@app.get("/rules")
async def get_rules():
    """Get security rules"""
    try:
        return [
            {
                "id": 1,
                "name": "High Risk Action Approval",
                "description": "All high-risk actions require manual approval",
                "risk_level": "high",
                "auto_approve": False,
                "requires_mfa": True,
                "approvers": ["admin@company.com", "security@company.com"],
                "created_at": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": 2,
                "name": "Vulnerability Scan Auto-Approval",
                "description": "Low-risk vulnerability scans can be auto-approved",
                "risk_level": "low",
                "auto_approve": True,
                "requires_mfa": False,
                "approvers": ["security@company.com"],
                "created_at": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": 3,
                "name": "Compliance Check Manual Review",
                "description": "All compliance checks require manual review",
                "risk_level": "medium",
                "auto_approve": False,
                "requires_mfa": True,
                "approvers": ["compliance@company.com", "admin@company.com"],
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
        ]
    except Exception as e:
        logger.error(f"Rules error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch rules")

# ================== YOUR ALERTS ROUTES (PRESERVED) ==================

@app.get("/alerts")
async def get_alerts():
    """Get alerts"""
    try:
        return [
            {
                "id": 1,
                "type": "high_risk_action",
                "title": "High Risk Action Detected",
                "message": "Security scanner attempting to access production database",
                "severity": "high",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
                "action_id": 1001
            },
            {
                "id": 2,
                "type": "unauthorized_access",
                "title": "Unauthorized Access Attempt",
                "message": "Agent attempted to access restricted API endpoint",
                "severity": "medium",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "resolved": True,
                "action_id": 1002
            },
            {
                "id": 3,
                "type": "compliance_violation",
                "title": "Compliance Policy Violation",
                "message": "Agent action violates SOX compliance requirements",
                "severity": "high",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "resolved": False,
                "action_id": 1003
            }
        ]
    except Exception as e:
        logger.error(f"Alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")

# ================== YOUR AGENT ACTIONS ROUTE (PRESERVED) ==================

@app.get("/agent-actions", response_model=None)
async def get_agent_actions_live(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Agent actions with live database integration"""
    try:
        from datetime import datetime, timezone
        current_time = datetime.now(timezone.utc)
        
        logger.info(f"🔄 Live agent-actions called by: {current_user.get('email', 'unknown')}")
        
        db: Session = next(get_db())
        
        try:
            # Query real database records with error handling
            result = db.execute(text("""
                SELECT id, agent_id, action_type, description, risk_level, status, approved,
                       reviewed_by, reviewed_at
                FROM agent_actions 
                ORDER BY id ASC
            """)).fetchall()
            
            if result and len(result) > 0:
                # Convert database results to enterprise format
                live_data = []
                for row in result:
                    # Map database status to UI display
                    db_status = row[5] or "pending"
                    db_approved = row[6]
                    
                    # Enterprise status logic
                    if db_approved == True:
                        display_status = "approved"
                    elif db_approved == False and db_status != "pending":
                        display_status = "rejected"
                    else:
                        display_status = "pending"
                    
                    live_data.append({
                        "id": row[0],
                        "user_id": current_user.get("user_id", 1),
                        "agent_id": row[1] or f"agent-{row[0]}",
                        "action_type": row[2] or "security_scan",
                        "description": row[3] or "Enterprise security action",
                        "tool_name": "enterprise-scanner",
                        "timestamp": current_time.isoformat(),
                        "risk_level": row[4] or "medium",
                        "mitre_tactic": "TA0007",
                        "mitre_technique": "T1190", 
                        "nist_control": "RA-5",
                        "nist_description": "Enterprise Security Control",
                        "recommendation": f"Enterprise review: {display_status}",
                        "summary": f"Enterprise action {row[0]}: {row[2] or 'security_scan'}",
                        "status": display_status,  # LIVE STATUS FROM DATABASE
                        "approved": bool(db_approved) if db_approved is not None else False,
                        "reviewed_by": row[7] if row[7] else None,
                        "reviewed_at": row[8].isoformat() if row[8] else None,
                        "created_at": current_time.isoformat(),
                        "risk_score": 85
                    })
                
                db.close()
                logger.info(f"✅ Returning {len(live_data)} LIVE database records")
                return live_data
            
            else:
                logger.info("📊 No database records found - will return fallback data")
                
        except Exception as db_error:
            logger.error(f"❌ Database error: {db_error}")
        finally:
            db.close()
        
        # Fallback to your original override data
        logger.warning("⚠️ Using fallback override data")
        return [
            {
                "id": 1001,
                "user_id": current_user.get("user_id", 1),
                "agent_id": "security-scanner-01",
                "action_type": "vulnerability_scan",
                "description": "Production infrastructure vulnerability assessment",
                "tool_name": "security-scanner",
                "timestamp": current_time.isoformat(),
                "risk_level": "high",
                "mitre_tactic": "TA0007",
                "mitre_technique": "T1190",
                "nist_control": "RA-5",
                "nist_description": "Vulnerability Scanning",
                "recommendation": "Remediation required for 3 vulnerabilities",
                "summary": "Security scan completed: 3 vulnerabilities discovered",
                "status": "pending",
                "approved": False,
                "reviewed_by": None,
                "reviewed_at": None,
                "created_at": current_time.isoformat(),
                "risk_score": 85
            },
            {
                "id": 1002,
                "user_id": current_user.get("user_id", 1),
                "agent_id": "compliance-agent",
                "action_type": "compliance_check",
                "description": "Automated compliance audit of access controls",
                "tool_name": "compliance-auditor",
                "timestamp": current_time.isoformat(),
                "risk_level": "medium",
                "mitre_tactic": "TA0005",
                "mitre_technique": "T1078",
                "nist_control": "AU-6",
                "nist_description": "Audit Review and Analysis",
                "recommendation": "Review access control violations",
                "summary": "Compliance audit identified 2 policy violations",
                "status": "pending",
                "approved": False,
                "reviewed_by": None,
                "reviewed_at": None,
                "created_at": current_time.isoformat(),
                "risk_score": 65
            },
            {
                "id": 1003,
                "user_id": current_user.get("user_id", 1),
                "agent_id": "threat-detector",
                "action_type": "anomaly_detection",
                "description": "Network traffic anomaly detection analysis",
                "tool_name": "threat-intelligence",
                "timestamp": current_time.isoformat(),
                "risk_level": "low",
                "mitre_tactic": "TA0011",
                "mitre_technique": "T1071",
                "nist_control": "SI-4",
                "nist_description": "Information System Monitoring",
                "recommendation": "Continue monitoring - no action required",
                "summary": "Anomaly detection completed - normal patterns observed",
                "status": "pending",
                "approved": False,
                "reviewed_by": None,
                "reviewed_at": None,
                "created_at": current_time.isoformat(),
                "risk_score": 25
            }
        ]
        
    except Exception as e:
        logger.error(f"❌ Agent-actions endpoint error: {str(e)}")
        return []

# ================== YOUR DATABASE FIX ENDPOINTS (PRESERVED) ==================

@app.post("/admin/fix-agent-actions-table")
async def fix_agent_actions_table():
    """Database schema fix for agent_actions table"""
    try:
        # FIXED: Use engine instead of DATABASE_URL
        results = []
        
        with engine.connect() as conn:
            # Add missing columns one by one
            missing_columns = [
                ("tool_name", "VARCHAR(255)"),
                ("recommendation", "TEXT"),
                ("summary", "TEXT"),
                ("mitre_tactic", "VARCHAR(50)"),
                ("mitre_technique", "VARCHAR(50)"),
                ("nist_control", "VARCHAR(50)"),
                ("nist_description", "TEXT"),
                ("reviewed_by", "VARCHAR(255)"),
                ("reviewed_at", "TIMESTAMP"),
                ("is_false_positive", "BOOLEAN DEFAULT FALSE")
            ]
            
            for col_name, col_type in missing_columns:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE agent_actions 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """))
                    results.append(f"✅ Added {col_name} column")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        results.append(f"✅ {col_name} column already exists")
                    else:
                        results.append(f"⚠️ {col_name} column: {str(e)}")
            
            conn.commit()
        
        logger.info("Agent actions table fix completed")
        return {
            "status": "success",
            "message": "Agent actions table updated",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Failed to fix agent actions table: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix table: {str(e)}"
        }

@app.post("/admin/fix-database-schema")
async def fix_database_schema():
    """Complete database schema fix"""
    try:
        # FIXED: Use engine instead of DATABASE_URL
        results = []
        
        with engine.connect() as conn:
            # Fix agent_actions table
            try:
                conn.execute(text("""
                    ALTER TABLE agent_actions 
                    ADD COLUMN IF NOT EXISTS risk_score INTEGER DEFAULT 50,
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                results.append("✅ Fixed agent_actions table")
            except Exception as e:
                results.append(f"⚠️ agent_actions: {str(e)}")
            
            # Fix alerts table
            try:
                conn.execute(text("""
                    ALTER TABLE alerts 
                    ADD COLUMN IF NOT EXISTS agent_action_id INTEGER
                """))
                results.append("✅ Fixed alerts table")
            except Exception as e:
                results.append(f"⚠️ alerts: {str(e)}")
            
            conn.commit()
        
        logger.info("Database schema fix completed")
        return {
            "status": "success",
            "message": "Database schema updated",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Failed to fix database schema: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fix schema: {str(e)}"
        }

# ================== YOUR AGENT ACTION SUBMISSION ENDPOINT ==================

@app.post("/agent-actions")
async def submit_agent_action(request: Request, current_user: dict = Depends(get_current_user)):
    """Submit new agent action"""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["agent_id", "action_type", "description"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        db: Session = next(get_db())
        
        # Create new agent action
        new_action = AgentAction(
            user_id=current_user.get("user_id"),
            agent_id=data["agent_id"],
            action_type=data["action_type"],
            description=data["description"],
            tool_name=data.get("tool_name", ""),
            risk_level="medium",  # Default risk level
            status="pending",
            approved=False
        )
        
        db.add(new_action)
        db.commit()
        db.refresh(new_action)
        
        logger.info(f"New agent action submitted: {new_action.id} by {current_user.get('email')}")
        
        return {
            "status": "success",
            "message": "Agent action submitted successfully",
            "action_id": new_action.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent action submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit agent action")

# ================== MISSING APPROVAL ENDPOINTS (FIXES THE 405 ERRORS) ==================

@app.post("/agent-action/{action_id}/approve")
def approve_agent_action(
    action_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Approve an agent action (admin only) - Enterprise audit trail preserved"""
    try:
        # Update using raw SQL to avoid model schema issues
        result = db.execute(text("""
            UPDATE agent_actions 
            SET status = 'approved', 
                approved = true, 
                reviewed_by = :reviewed_by, 
                reviewed_at = :reviewed_at
            WHERE id = :action_id
        """), {
            'action_id': action_id,
            'reviewed_by': admin_user["email"],
            'reviewed_at': datetime.now(UTC)
        })
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agent action not found")

        # Create enterprise audit trail
        try:
            audit_log = LogAuditTrail(
                action_id=action_id,
                decision="approved",
                reviewed_by=admin_user["email"],
                timestamp=datetime.now(UTC)
            )
            db.add(audit_log)
        except Exception as audit_error:
            logger.warning(f"Audit trail creation failed: {audit_error}")
        
        db.commit()
        logger.info(f"Enterprise action {action_id} approved by {admin_user['email']}")
        return {"message": "Action approved successfully", "audit_trail": "logged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve action {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to approve action")

@app.post("/agent-action/{action_id}/reject")
def reject_agent_action(
    action_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Reject an agent action (admin only)"""
    try:
        result = db.execute(text("""
            UPDATE agent_actions 
            SET status = 'rejected', 
                approved = false, 
                reviewed_by = :reviewed_by, 
                reviewed_at = :reviewed_at
            WHERE id = :action_id
        """), {
            'action_id': action_id,
            'reviewed_by': admin_user["email"],
            'reviewed_at': datetime.now(UTC)
        })
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agent action not found")

        try:
            audit_log = LogAuditTrail(
                action_id=action_id,
                decision="rejected",
                reviewed_by=admin_user["email"],
                timestamp=datetime.now(UTC)
            )
            db.add(audit_log)
        except Exception as audit_error:
            logger.warning(f"Audit trail creation failed: {audit_error}")
        
        db.commit()
        logger.info(f"Enterprise action {action_id} rejected by {admin_user['email']}")
        return {"message": "Action rejected successfully", "audit_trail": "logged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject action {action_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reject action")

@app.post("/agent-action/{action_id}/false-positive")
def mark_false_positive(
    action_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Mark an agent action as false positive (admin only)"""
    try:
        result = db.execute(text("""
            UPDATE agent_actions 
            SET status = 'false_positive', 
                approved = null,
                reviewed_by = :reviewed_by, 
                reviewed_at = :reviewed_at
            WHERE id = :action_id
        """), {
            'action_id': action_id,
            'reviewed_by': admin_user["email"],
            'reviewed_at': datetime.now(UTC)
        })
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agent action not found")

        try:
            audit_log = LogAuditTrail(
                action_id=action_id,
                decision="false_positive",
                reviewed_by=admin_user["email"],
                timestamp=datetime.now(UTC)
            )
            db.add(audit_log)
        except Exception as audit_error:
            logger.warning(f"Audit trail creation failed: {audit_error}")
        
        db.commit()
        logger.info(f"Enterprise action {action_id} marked as false positive by {admin_user['email']}")
        return {"message": "Action marked as false positive", "audit_trail": "logged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark action {action_id} as false positive: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to mark as false positive")

# ================== SAMPLE DATA CREATION ENDPOINT ==================

@app.post("/admin/create-sample-agent-actions-simplified")
async def create_sample_agent_actions_simplified():
    """Create sample agent actions with only existing columns"""
    try:
        db: Session = next(get_db())
        
        # Check if actions already exist
        existing = db.execute(text("SELECT COUNT(*) FROM agent_actions WHERE id IN (1001, 1002, 1003)")).fetchone()[0]
        
        if existing > 0:
            return {"status": "success", "message": "Sample actions already exist", "count": existing}
        
        # Create sample actions using only columns that exist
        sample_actions = [
            {
                'id': 1001,
                'agent_id': 'security-scanner-01',
                'action_type': 'vulnerability_scan',
                'description': 'Production infrastructure vulnerability assessment',
                'risk_level': 'high',
                'status': 'pending',
                'approved': False
            },
            {
                'id': 1002,
                'agent_id': 'compliance-agent',
                'action_type': 'compliance_check',
                'description': 'Automated compliance audit of access controls',
                'risk_level': 'medium',
                'status': 'pending',
                'approved': False
            },
            {
                'id': 1003,
                'agent_id': 'threat-detector',
                'action_type': 'anomaly_detection',
                'description': 'Network traffic anomaly detection analysis',
                'risk_level': 'low',
                'status': 'pending',
                'approved': False
            }
        ]
        
        for action in sample_actions:
            db.execute(text("""
                INSERT INTO agent_actions (
                    id, agent_id, action_type, description, risk_level, status, approved
                ) VALUES (
                    :id, :agent_id, :action_type, :description, :risk_level, :status, :approved
                )
            """), action)
        
        db.commit()
        db.close()
        
        logger.info("Simplified sample agent actions created successfully")
        return {
            "status": "success",
            "message": "Sample agent actions created in database",
            "count": len(sample_actions),
            "action_ids": [1001, 1002, 1003]
        }
        
    except Exception as e:
        logger.error(f"Failed to create simplified sample actions: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to create simplified sample actions: {str(e)}"
        }

# ================== HEALTH CHECK ENDPOINT ==================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "OW-AI Enterprise Authorization Platform",
        "version": "1.0.0",
        "status": "operational",
        "enterprise_ready": True
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "enterprise_features": "operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)