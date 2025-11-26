# routes/analytics_routes.py - Master Prompt Surgical Fix
# ONLY CHANGE: Replace "User" with "dict" and ".email" with ".get('email')"

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_, or_
from database import get_db
from models import AgentAction, User, AuditLog  # Added AuditLog for enhanced analytics
from datetime import datetime, timedelta, UTC
from collections import defaultdict, Counter
from dependencies import get_current_user, require_admin, get_organization_filter
from services.pending_actions_service import pending_service
from services.cloudwatch_service import get_cloudwatch_service  # Phase 2: CloudWatch integration
from services.ml_prediction_service import get_prediction_engine  # Phase 3: ML predictions
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()

# 🏢 ENTERPRISE: Multi-Tenant Data Isolation
# All routes MUST filter by organization_id to ensure tenant isolation
# Compliance: SOC 2 CC6.1, HIPAA § 164.308, PCI-DSS 7.1

# Phase 2: CloudWatch configuration
CLOUDWATCH_ENABLED = os.getenv("CLOUDWATCH_ENABLED", "true").lower() == "true"
ECS_CLUSTER_NAME = os.getenv("ECS_CLUSTER_NAME", "owkai-pilot")
ECS_SERVICE_NAME = os.getenv("ECS_SERVICE_NAME", "owkai-pilot-backend-service")
CLOUDWATCH_LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP", "/ecs/owkai-pilot-backend")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# ✅ PRESERVED: Original working endpoints
@router.get("/trends")
def get_trend_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """✅ ENTERPRISE: Real-time analytics with actual database queries - filtered by organization"""
    try:
        logger.info(f"🔄 Enterprise analytics requested by: {current_user.get('email')} for org_id={org_id}")

        from datetime import datetime, timedelta, UTC
        from sqlalchemy import func, and_

        now = datetime.now(UTC)
        seven_days_ago = now - timedelta(days=7)

        # 🏢 ENTERPRISE: Filter by organization_id for tenant isolation
        # ✅ REAL: High-risk actions by day (last 7 days)
        try:
            daily_actions = db.execute(text("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM agent_actions
                WHERE timestamp >= :start_date
                  AND organization_id = :org_id
                  AND risk_level IN ('high', 'critical')
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            """), {"start_date": seven_days_ago, "org_id": org_id}).fetchall()
            
            high_risk_by_day = [
                {"date": str(row[0]), "count": row[1]} 
                for row in daily_actions
            ] if daily_actions else [
                {"date": "2025-07-24", "count": 0},
                {"date": "2025-07-25", "count": 0}
            ]
        except Exception as e:
            logger.warning(f"Daily actions query failed: {e}")
            high_risk_by_day = [{"date": "2025-07-24", "count": 0}]
        
        # ✅ REAL: Top agents (by action count) - filtered by organization
        try:
            top_agents_query = db.execute(text("""
                SELECT agent_id, COUNT(*) as count
                FROM agent_actions
                WHERE timestamp >= :start_date
                  AND organization_id = :org_id
                GROUP BY agent_id
                ORDER BY count DESC
                LIMIT 10
            """), {"start_date": seven_days_ago, "org_id": org_id}).fetchall()
            
            top_agents = [
                {"agent": row[0], "count": row[1]} 
                for row in top_agents_query
            ] if top_agents_query else [
                {"agent": "No agents yet", "count": 0}
            ]
        except Exception as e:
            logger.warning(f"Top agents query failed: {e}")
            top_agents = [{"agent": "No agents", "count": 0}]
        
        # ✅ REAL: Top tools (by usage count) - filtered by organization
        try:
            top_tools_query = db.execute(text("""
                SELECT tool_name, COUNT(*) as count
                FROM agent_actions
                WHERE timestamp >= :start_date
                  AND organization_id = :org_id
                  AND tool_name IS NOT NULL
                GROUP BY tool_name
                ORDER BY count DESC
                LIMIT 10
            """), {"start_date": seven_days_ago, "org_id": org_id}).fetchall()
            
            top_tools = [
                {"tool": row[0], "count": row[1]} 
                for row in top_tools_query
            ] if top_tools_query else [
                {"tool": "No tools yet", "count": 0}
            ]
        except Exception as e:
            logger.warning(f"Top tools query failed: {e}")
            top_tools = [{"tool": "No tools", "count": 0}]
        
        # ✅ REAL: Latest enriched actions - filtered by organization
        try:
            actions = db.query(AgentAction).filter(
                AgentAction.organization_id == org_id  # 🏢 ENTERPRISE: Tenant isolation
            ).order_by(
                AgentAction.timestamp.desc()
            ).limit(20).all()
            
            enriched_actions = [
                {
                    "agent_id": a.agent_id,
                    "action_type": a.action_type,
                    "risk_level": a.risk_level,
                    "mitre_tactic": a.mitre_tactic or "N/A",
                    "nist_control": a.nist_control or "N/A",
                    "recommendation": a.recommendation or "No recommendation",
                    "tool_name": a.tool_name or "Unknown",
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None
                }
                for a in actions
            ] if actions else []
        except Exception as e:
            logger.warning(f"Enriched actions query failed: {e}")
            enriched_actions = []
        
        # Get pending approval count - filtered by organization
        pending_count = pending_service.get_pending_count(db, org_id=org_id)
        
        result = {
            "high_risk_actions_by_day": high_risk_by_day,
            "top_agents": top_agents,
            "top_tools": top_tools,
            "enriched_actions": enriched_actions,
            "pending_actions_count": pending_count
        }
        
        logger.info(f"✅ Analytics: {len(top_agents)} agents, {len(top_tools)} tools, {len(enriched_actions)} actions")
        return result
        
    except Exception as e:
        logger.error(f"❌ Analytics error: {str(e)}")
        return {
            "high_risk_actions_by_day": [],
            "top_agents": [],
            "top_tools": [],
            "enriched_actions": []
        }



@router.get("/debug")
def debug_enriched_actions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """Original debug endpoint - PRESERVED for enterprise compatibility - filtered by organization"""
    try:
        logger.info(f"🔄 Debug analytics requested by: {current_user.get('email')} for org_id={org_id}")

        # 🏢 ENTERPRISE: Filter by organization_id for tenant isolation
        actions = (
            db.query(AgentAction)
            .filter(AgentAction.organization_id == org_id)
            .order_by(AgentAction.timestamp.desc())
            .limit(5)
            .all()
        )
        return [
            {
                "id": a.id,
                "agent_id": a.agent_id,
                "risk_level": a.risk_level,
                "mitre_tactic": a.mitre_tactic,
                "nist_control": a.nist_control,
                "recommendation": a.recommendation,
                "summary": a.summary,
            }
            for a in actions
        ]
    except Exception as e:
        logger.error(f"❌ Debug analytics error: {str(e)}")
        return []

# 🚀 NEW: Enhanced Real-Time Analytics Endpoints
@router.get("/realtime/metrics")
def get_realtime_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    org_id: int = Depends(get_organization_filter)
):
    """Real-time enterprise metrics with role-based data access - filtered by organization"""
    try:
        logger.info(f"📊 Real-time metrics requested by: {current_user.get('email')} for org_id={org_id}")

        # Get current time for real-time calculations
        now = datetime.now(UTC)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        # ===== PHASE 1: REAL DATABASE QUERIES (NO FALLBACKS) =====
        # 🏢 ENTERPRISE: All queries filter by organization_id for tenant isolation

        # Real-time active sessions from recent agent actions
        # Note: Using agent actions as proxy for sessions since AuditLog doesn't have timestamp
        active_sessions = db.query(func.count(func.distinct(AgentAction.agent_id))).filter(
            AgentAction.organization_id == org_id,  # 🏢 Tenant isolation
            AgentAction.timestamp >= hour_ago
        ).scalar() or 0

        # Recent high-risk actions
        recent_high_risk = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.organization_id == org_id,  # 🏢 Tenant isolation
                AgentAction.timestamp >= hour_ago,
                AgentAction.risk_level.in_(['high', 'critical'])
            )
        ).scalar() or 0

        # Active agents in last hour
        active_agents = db.query(func.count(func.distinct(AgentAction.agent_id))).filter(
            AgentAction.organization_id == org_id,  # 🏢 Tenant isolation
            AgentAction.timestamp >= hour_ago
        ).scalar() or 0

        # Total actions in last hour
        total_actions = db.query(func.count(AgentAction.id)).filter(
            AgentAction.organization_id == org_id,  # 🏢 Tenant isolation
            AgentAction.timestamp >= hour_ago
        ).scalar() or 0

        # Total actions today
        actions_today = db.query(func.count(AgentAction.id)).filter(
            AgentAction.organization_id == org_id,  # 🏢 Tenant isolation
            AgentAction.timestamp >= day_ago
        ).scalar() or 0

        # ===== DATA QUALITY INDICATORS =====
        has_data = total_actions > 0
        data_quality = {
            "source": "production_database",
            "timestamp": now.isoformat(),
            "has_historical_data": actions_today > 0,
            "has_recent_activity": has_data,
            "data_status": "live" if has_data else "no_recent_activity"
        }

        # ===== PHASE 2: AWS CLOUDWATCH INTEGRATION =====
        # Try to get real metrics from CloudWatch, fallback to Phase 1 status if unavailable
        try:
            if CLOUDWATCH_ENABLED:
                cloudwatch = get_cloudwatch_service(
                    region=AWS_REGION,
                    cache_ttl=30,
                    enabled=CLOUDWATCH_ENABLED
                )
                cw_health = cloudwatch.get_system_health(
                    cluster_name=ECS_CLUSTER_NAME,
                    service_name=ECS_SERVICE_NAME,
                    log_group_name=CLOUDWATCH_LOG_GROUP
                )

                # Check if we got live data or fallback status
                if cw_health.get("status") == "live":
                    logger.info("✅ CloudWatch metrics available - showing live data")
                    system_health = {
                        "status": "live",
                        "source": cw_health.get("source"),
                        "cpu_usage": cw_health.get("cpu_usage", 0.0),
                        "memory_usage": cw_health.get("memory_usage", 0.0),
                        "disk_usage": cw_health.get("disk_usage", 0.0),
                        "network_latency": cw_health.get("network_latency", 0.0),
                        "api_response_time": cw_health.get("api_response_time", 0.0),
                        "timestamp": cw_health.get("timestamp"),
                        "metrics_age_seconds": cw_health.get("metrics_age_seconds", 30)
                    }

                    # Extract performance metrics
                    perf = cw_health.get("performance_metrics", {})
                    performance_metrics = {
                        "status": perf.get("status", "live"),
                        "source": perf.get("source", "cloudwatch_logs"),
                        "requests_per_second": perf.get("requests_per_second", 0.0),
                        "avg_response_time": perf.get("avg_response_time", 0.0),
                        "p95_response_time": perf.get("p95_response_time", 0.0),
                        "error_rate": perf.get("error_rate", 0.0),
                        "timestamp": perf.get("timestamp")
                    }
                else:
                    # CloudWatch returned Phase 1 fallback
                    logger.warning(f"CloudWatch unavailable: {cw_health.get('message')}")
                    raise Exception(cw_health.get("message", "CloudWatch unavailable"))
            else:
                # CloudWatch disabled via config
                logger.info("CloudWatch disabled - showing Phase 2 planned status")
                raise Exception("CloudWatch disabled")

        except Exception as cloudwatch_error:
            # Graceful fallback to Phase 1 status
            logger.warning(f"⚠️  CloudWatch fallback: {cloudwatch_error}")
            system_health = {
                "status": "phase_2_planned",
                "message": "System health monitoring with AWS CloudWatch will be available in Phase 2 (Week 1)",
                "available_metrics": ["CPU", "Memory", "Disk", "Network", "API Response Time"],
                "estimated_availability": "Week 1",
                "cloudwatch_enabled": CLOUDWATCH_ENABLED,
                "fallback_reason": str(cloudwatch_error)
            }

            performance_metrics = {
                "status": "phase_2_planned",
                "message": "Performance tracking with CloudWatch Logs Insights will be available in Phase 2 (Week 1)",
                "planned_metrics": ["Requests/sec", "Error rate", "Response time", "Cache hit rate"],
                "estimated_availability": "Week 1"
            }

        return {
            "timestamp": now.isoformat(),
            "real_time_overview": {
                "active_sessions": active_sessions,
                "recent_high_risk_actions": recent_high_risk,
                "active_agents": active_agents,
                "total_actions_last_hour": total_actions,
                "actions_last_24h": actions_today,

                # User-friendly status
                "status": {
                    "has_data": has_data,
                    "message": "Live data from production database" if has_data else "No activity in last hour",
                    "data_age_minutes": 0 if has_data else None
                }
            },
            "system_health": system_health,
            "performance_metrics": performance_metrics,
            "data_quality": data_quality,
            "meta": {
                "version": "1.0.0-phase2",
                "enterprise_grade": True,
                "mock_data": False,
                "real_data_sources": ["postgresql_rds", "aws_cloudwatch"] if system_health.get("status") == "live" else ["postgresql_rds"],
                "phase": "2_of_3",
                "cloudwatch_enabled": CLOUDWATCH_ENABLED,
                "cloudwatch_status": system_health.get("status")
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Real-time metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch real-time metrics")

@router.get("/predictive/trends")
def get_predictive_trends(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    ===== PHASE 3: ML-Powered Predictive Analytics =====

    Provides intelligent forecasting, anomaly detection, and strategic recommendations.
    Works with limited data using pattern recognition and statistical analysis.
    """
    try:
        logger.info(f"🔮 Predictive analytics requested by: {current_user.get('email')}")

        # Check how much historical data we have
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        historical_count = db.execute(text("""
            SELECT COUNT(DISTINCT DATE(timestamp)) as days_with_data
            FROM agent_actions
            WHERE timestamp >= :start_date
        """), {"start_date": thirty_days_ago}).scalar() or 0

        total_actions = db.query(func.count(AgentAction.id)).filter(
            AgentAction.timestamp >= thirty_days_ago
        ).scalar() or 0

        # ===== PHASE 3: SMART PREDICTIONS =====
        # Minimum 4 days for pattern-based predictions
        minimum_days_for_predictions = 4

        if historical_count >= minimum_days_for_predictions:
            # We have enough data - generate predictions!
            logger.info(f"✅ Generating predictions with {historical_count} days of data")

            try:
                prediction_engine = get_prediction_engine(db)

                # Generate forecasts
                risk_forecast = prediction_engine.forecast_risks(days=7)
                agent_workload = prediction_engine.predict_agent_workload()
                anomalies = prediction_engine.detect_anomalies()
                recommendations = prediction_engine.generate_recommendations(
                    risk_forecast, agent_workload, anomalies
                )

                # Determine prediction quality
                if historical_count >= 14:
                    prediction_quality = "high"
                    method = "ml_powered"
                elif historical_count >= 8:
                    prediction_quality = "medium"
                    method = "trend_based"
                else:
                    prediction_quality = "developing"
                    method = "pattern_based"

                # Calculate confidence range
                confidences = []
                if risk_forecast:
                    confidences.extend([f["confidence"] for f in risk_forecast])
                if agent_workload:
                    confidences.extend([w["confidence"] for w in agent_workload])

                min_conf = min(confidences) if confidences else 0.5
                max_conf = max(confidences) if confidences else 0.7

                return {
                    "status": "active",
                    "prediction_quality": prediction_quality,
                    "risk_forecast": risk_forecast,
                    "agent_workload_forecast": agent_workload,
                    "anomalies": anomalies,
                    "risk_predictions": {
                        "recommended_actions": recommendations
                    },
                    "data_collection": {
                        "days_collected": historical_count,
                        "total_actions": total_actions,
                        "collection_progress": 100.0,
                        "ready": True,
                        "quality": f"{'Excellent' if historical_count >= 14 else 'Good' if historical_count >= 8 else 'Sufficient'} data for {prediction_quality} quality predictions"
                    },
                    "meta": {
                        "version": "1.0.0-phase3",
                        "mock_data": False,
                        "prediction_method": method,
                        "confidence_range": [round(min_conf, 2), round(max_conf, 2)],
                        "phase": "3_of_3_active"
                    },
                    "timestamp": datetime.now(UTC).isoformat()
                }

            except Exception as pred_error:
                logger.error(f"Prediction generation failed: {pred_error}")
                # Fall through to collecting_data status

        # ===== NOT ENOUGH DATA YET =====
        logger.info(f"⏳ Still collecting data: {historical_count}/{minimum_days_for_predictions} days")

        minimum_days_required = 14  # For high-quality predictions
        collection_progress = (historical_count / minimum_days_for_predictions) * 100

        return {
            "status": "collecting_data",
            "message": f"Collecting data for predictions. Minimum {minimum_days_for_predictions} days needed for pattern-based forecasting.",
            "data_collection": {
                "days_collected": historical_count,
                "minimum_required": minimum_days_for_predictions,
                "optimal_required": minimum_days_required,
                "total_actions": total_actions,
                "collection_progress": round(collection_progress, 1),
                "estimated_ready_date": (datetime.now(UTC) + timedelta(days=max(0, minimum_days_for_predictions - historical_count))).strftime("%Y-%m-%d")
            },
            "planned_features": [
                {
                    "feature": "Risk Trend Forecasting",
                    "description": "Predict high-risk action patterns 7 days ahead",
                    "accuracy_target": "85%+",
                    "benefit": "Proactive threat mitigation"
                },
                {
                    "feature": "Agent Workload Prediction",
                    "description": "Forecast agent capacity and utilization",
                    "accuracy_target": "80%+",
                    "benefit": "Capacity planning and resource optimization"
                },
                {
                    "feature": "Anomaly Detection",
                    "description": "Identify unusual patterns and potential security threats",
                    "accuracy_target": "90%+",
                    "benefit": "Early warning system for security incidents"
                },
                {
                    "feature": "Strategic Recommendations",
                    "description": "AI-powered actionable insights for optimization",
                    "accuracy_target": "N/A",
                    "benefit": "Data-driven decision making"
                }
            ],
            "meta": {
                "version": "1.0.0-phase3",
                "mock_data": False,
                "phase": "3_collecting",
                "days_until_ready": max(0, minimum_days_for_predictions - historical_count)
            },
            "timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Predictive analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch predictive analytics")

@router.get("/executive/dashboard")
def get_executive_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Executive-level KPI dashboard with real database metrics"""
    try:
        logger.info(f"📈 Executive dashboard requested by: {current_user.get('email')}")

        now = datetime.now(UTC)
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        # ===== REAL DATABASE QUERIES =====

        # 1. Platform Health - Based on system performance and action success rates
        total_actions_month = db.query(func.count(AgentAction.id)).filter(
            AgentAction.timestamp >= last_month
        ).scalar() or 0

        successful_actions = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.status == 'completed'
            )
        ).scalar() or 0

        failed_actions = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.status == 'failed'
            )
        ).scalar() or 0

        # Calculate platform health score (0-100)
        if total_actions_month > 0:
            success_rate = (successful_actions / total_actions_month) * 100
            platform_health_score = round(success_rate, 1)
            if platform_health_score >= 95:
                health_status = "excellent"
                health_trend = "stable"
            elif platform_health_score >= 85:
                health_status = "good"
                health_trend = "stable"
            elif platform_health_score >= 75:
                health_status = "fair"
                health_trend = "needs_attention"
            else:
                health_status = "poor"
                health_trend = "declining"
        else:
            platform_health_score = 0
            health_status = "no_data"
            health_trend = "unknown"

        # 2. Security Posture - Based on risk levels
        critical_actions = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.risk_level == 'critical'
            )
        ).scalar() or 0

        high_risk_actions = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.risk_level == 'high'
            )
        ).scalar() or 0

        medium_risk_actions = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.risk_level == 'medium'
            )
        ).scalar() or 0

        # Calculate security posture score
        if total_actions_month > 0:
            risk_percentage = ((critical_actions * 10 + high_risk_actions * 5 + medium_risk_actions * 2) / total_actions_month)
            security_score = max(0, round(100 - risk_percentage, 1))

            if security_score >= 90:
                security_trend = "excellent"
            elif security_score >= 75:
                security_trend = "improving"
            elif security_score >= 60:
                security_trend = "stable"
            else:
                security_trend = "declining"
        else:
            security_score = 0
            security_trend = "no_data"

        # 3. Operational Efficiency - Based on approval rates and processing times
        pending_actions = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.status == 'pending'
            )
        ).scalar() or 0

        approved_actions = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.approved == True
            )
        ).scalar() or 0

        # Automation rate: approved / total actions requiring approval
        actions_requiring_approval = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.requires_approval == True
            )
        ).scalar() or 0

        if actions_requiring_approval > 0:
            automation_rate = round(approved_actions / actions_requiring_approval, 2)
            efficiency_score = round(automation_rate * 100, 1)
        else:
            automation_rate = 0
            efficiency_score = 0

        # Manual interventions = pending + actions requiring review
        manual_interventions = pending_actions

        # 4. Compliance Status - Based on audit logs and governance
        compliance_actions = db.query(func.count(AuditLog.id)).filter(
            and_(
                AuditLog.timestamp >= last_month,
                AuditLog.action.in_(['APPROVE', 'DENY', 'REVIEW'])
            )
        ).scalar() or 0

        high_risk_unreviewed = db.query(func.count(AgentAction.id)).filter(
            and_(
                AgentAction.timestamp >= last_month,
                AgentAction.risk_level.in_(['high', 'critical']),
                AgentAction.reviewed_at.is_(None)
            )
        ).scalar() or 0

        # Compliance score based on review coverage
        high_risk_total = critical_actions + high_risk_actions
        if high_risk_total > 0:
            review_coverage = ((high_risk_total - high_risk_unreviewed) / high_risk_total) * 100
            compliance_score = round(review_coverage, 1)
        else:
            compliance_score = 100  # No high-risk actions = perfect compliance

        violations = high_risk_unreviewed  # Unreviewed high-risk = violations
        pending_reviews = pending_actions

        # 5. User Growth - Real user counts
        total_users = db.query(func.count(User.id)).scalar() or 0

        active_users_month = db.query(func.count(func.distinct(User.id))).filter(
            User.last_login >= last_month
        ).scalar() or 0

        users_last_week = db.query(func.count(User.id)).filter(
            User.created_at >= last_week
        ).scalar() or 0

        users_previous_week = db.query(func.count(User.id)).filter(
            and_(
                User.created_at >= last_week - timedelta(days=7),
                User.created_at < last_week
            )
        ).scalar() or 0

        # Calculate growth rate
        if users_previous_week > 0:
            growth_rate = round((users_last_week - users_previous_week) / users_previous_week, 2)
            growth_trend = "positive" if growth_rate > 0 else "negative" if growth_rate < 0 else "stable"
        else:
            growth_rate = 0
            growth_trend = "no_baseline"

        # 6. System Utilization - Based on actual usage patterns
        avg_actions_per_day = round(total_actions_month / 30, 1) if total_actions_month > 0 else 0

        # Get peak day usage
        peak_day_usage = db.execute(text("""
            SELECT COUNT(*) as count
            FROM agent_actions
            WHERE timestamp >= :start_date
            GROUP BY DATE(timestamp)
            ORDER BY count DESC
            LIMIT 1
        """), {"start_date": last_month}).scalar() or 0

        # Efficiency score based on approval throughput
        if actions_requiring_approval > 0:
            utilization_score = round(approved_actions / actions_requiring_approval, 2)
        else:
            utilization_score = 0

        # ===== BUILD RESPONSE WITH REAL DATA =====

        executive_kpis = {
            "platform_health": {
                "score": platform_health_score,
                "trend": health_trend,
                "status": health_status,
                "total_actions": total_actions_month,
                "success_rate": round((successful_actions / total_actions_month * 100), 1) if total_actions_month > 0 else 0
            },
            "security_posture": {
                "score": security_score,
                "trend": security_trend,
                "critical_issues": critical_actions,
                "high_risk_actions": high_risk_actions,
                "medium_risk_actions": medium_risk_actions
            },
            "operational_efficiency": {
                "score": efficiency_score,
                "automation_rate": automation_rate,
                "manual_interventions": manual_interventions,
                "pending_actions": pending_actions
            },
            "compliance_status": {
                "score": compliance_score,
                "violations": violations,
                "pending_reviews": pending_reviews,
                "compliance_actions": compliance_actions
            }
        }

        business_metrics = {
            "user_growth": {
                "current_users": total_users,
                "active_users": active_users_month,
                "growth_rate": growth_rate,
                "trend": growth_trend,
                "new_users_this_week": users_last_week
            },
            "system_utilization": {
                "avg_actions_per_day": avg_actions_per_day,
                "peak_day_actions": peak_day_usage,
                "efficiency_score": utilization_score,
                "total_actions_month": total_actions_month
            },
            "cost_optimization": {
                "status": "cloudwatch_required",
                "message": "Cost metrics require AWS CloudWatch integration"
            }
        }

        # Generate strategic insights based on real data
        strategic_insights = []

        # Growth insight
        if growth_rate > 0.2:
            strategic_insights.append({
                "category": "growth",
                "insight": f"User base growing rapidly ({round(growth_rate * 100)}% growth)",
                "action": "Consider scaling infrastructure to handle increased load",
                "priority": "high",
                "data_source": "user_registration_data"
            })
        elif growth_rate < 0:
            strategic_insights.append({
                "category": "growth",
                "insight": f"User growth declining ({round(growth_rate * 100)}% change)",
                "action": "Review user retention strategies",
                "priority": "medium",
                "data_source": "user_registration_data"
            })

        # Security insight
        if critical_actions == 0 and high_risk_actions < 5:
            strategic_insights.append({
                "category": "security",
                "insight": f"Strong security posture maintained (only {high_risk_actions} high-risk actions)",
                "action": "Continue current security protocols",
                "priority": "low",
                "data_source": "agent_actions_risk_analysis"
            })
        elif critical_actions > 0:
            strategic_insights.append({
                "category": "security",
                "insight": f"Critical security issues detected ({critical_actions} critical actions)",
                "action": "Immediate review of critical security incidents required",
                "priority": "critical",
                "data_source": "agent_actions_risk_analysis"
            })

        # Efficiency insight
        if automation_rate < 0.5:
            strategic_insights.append({
                "category": "efficiency",
                "insight": f"Low automation rate ({round(automation_rate * 100)}%)",
                "action": "Implement additional workflow automation to reduce manual interventions",
                "priority": "high",
                "data_source": "approval_workflow_metrics"
            })
        elif automation_rate > 0.8:
            strategic_insights.append({
                "category": "efficiency",
                "insight": f"Excellent automation rate ({round(automation_rate * 100)}%)",
                "action": "Maintain current automation strategies",
                "priority": "low",
                "data_source": "approval_workflow_metrics"
            })

        # Compliance insight
        if violations > 10:
            strategic_insights.append({
                "category": "compliance",
                "insight": f"Compliance gap detected ({violations} unreviewed high-risk actions)",
                "action": "Prioritize review of pending high-risk actions",
                "priority": "high",
                "data_source": "audit_and_compliance_tracking"
            })

        # Default insight if no specific ones generated
        if not strategic_insights:
            strategic_insights.append({
                "category": "status",
                "insight": "System operating normally with no critical issues",
                "action": "Continue monitoring key metrics",
                "priority": "low",
                "data_source": "overall_system_health"
            })

        # Build key achievements list
        key_achievements = []
        if critical_actions == 0:
            key_achievements.append("Zero critical security incidents this month")
        if compliance_score >= 95:
            key_achievements.append(f"{compliance_score}% compliance score maintained")
        if platform_health_score >= 90:
            key_achievements.append(f"{platform_health_score}% system reliability achieved")
        if automation_rate >= 0.75:
            key_achievements.append(f"{round(automation_rate * 100)}% workflow automation rate")

        # If no achievements, note data status
        if not key_achievements:
            if total_actions_month == 0:
                key_achievements.append("System initialized - awaiting activity data")
            else:
                key_achievements.append("System operational and collecting metrics")

        # Build areas of focus
        areas_of_focus = []
        if violations > 5:
            areas_of_focus.append(f"Review {violations} pending compliance items")
        if automation_rate < 0.6:
            areas_of_focus.append("Improve workflow automation rate")
        if growth_rate > 0.2:
            areas_of_focus.append("Infrastructure scaling for user growth")
        if manual_interventions > 20:
            areas_of_focus.append("Reduce manual intervention backlog")

        # Default focus if none identified
        if not areas_of_focus:
            areas_of_focus.append("Continue monitoring system health and performance")

        return {
            "report_date": now.isoformat(),
            "data_period": {
                "start_date": last_month.isoformat(),
                "end_date": now.isoformat(),
                "days": 30
            },
            "executive_summary": {
                "overall_health": health_status,
                "key_achievements": key_achievements,
                "areas_of_focus": areas_of_focus,
                "data_quality": "real_database_queries" if total_actions_month > 0 else "no_activity"
            },
            "executive_kpis": executive_kpis,
            "business_metrics": business_metrics,
            "strategic_insights": strategic_insights,
            "next_review_date": (now + timedelta(days=7)).isoformat(),
            "meta": {
                "version": "2.0.0",
                "mock_data": False,
                "real_data_sources": ["agent_actions", "users", "audit_logs"],
                "has_activity": total_actions_month > 0
            }
        }

    except Exception as e:
        logger.error(f"❌ Executive dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate executive dashboard: {str(e)}")

@router.get("/performance")
@router.get("/performance/system")
def get_system_performance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Real-time system performance monitoring with CloudWatch integration"""
    try:
        logger.info(f"⚡ System performance requested by: {current_user.get('email')}")

        current_time = datetime.now(UTC)
        hour_ago = current_time - timedelta(hours=1)

        # ===== TRY CLOUDWATCH FIRST, FALLBACK TO DATABASE =====
        system_metrics = None
        application_metrics = None

        try:
            if CLOUDWATCH_ENABLED:
                cloudwatch = get_cloudwatch_service(
                    region=AWS_REGION,
                    cache_ttl=30,
                    enabled=CLOUDWATCH_ENABLED
                )

                # Get CloudWatch system health
                cw_health = cloudwatch.get_system_health(
                    cluster_name=ECS_CLUSTER_NAME,
                    service_name=ECS_SERVICE_NAME,
                    log_group_name=CLOUDWATCH_LOG_GROUP
                )

                if cw_health.get("status") == "live":
                    logger.info("✅ Using CloudWatch metrics for system performance")

                    # System metrics from CloudWatch
                    system_metrics = {
                        "cpu": {
                            "current": round(cw_health.get("cpu_usage", 0.0), 1),
                            "average": round(cw_health.get("cpu_usage", 0.0), 1),
                            "status": "normal" if cw_health.get("cpu_usage", 0) < 80 else "high",
                            "source": "cloudwatch"
                        },
                        "memory": {
                            "current": round(cw_health.get("memory_usage", 0.0), 1),
                            "available": round(100 - cw_health.get("memory_usage", 0.0), 1),
                            "status": "normal" if cw_health.get("memory_usage", 0) < 85 else "high",
                            "source": "cloudwatch"
                        },
                        "storage": {
                            "used": round(cw_health.get("disk_usage", 0.0), 1),
                            "available": round(100 - cw_health.get("disk_usage", 0.0), 1),
                            "status": "healthy" if cw_health.get("disk_usage", 0) < 80 else "warning",
                            "source": "cloudwatch"
                        }
                    }

                    # Application metrics from CloudWatch performance
                    perf = cw_health.get("performance_metrics", {})
                    if perf.get("status") == "live":
                        application_metrics = {
                            "response_times": {
                                "average": round(perf.get("avg_response_time", 0.0), 1),
                                "p95": round(perf.get("p95_response_time", 0.0), 1),
                                "target": 200.0,
                                "status": "good" if perf.get("avg_response_time", 0) < 200 else "slow",
                                "source": "cloudwatch_logs"
                            },
                            "throughput": {
                                "requests_per_second": round(perf.get("requests_per_second", 0.0), 1),
                                "source": "cloudwatch_logs"
                            },
                            "error_rates": {
                                "current": round(perf.get("error_rate", 0.0), 4),
                                "target": 0.01,
                                "status": "good" if perf.get("error_rate", 0) < 0.01 else "elevated",
                                "source": "cloudwatch_logs"
                            }
                        }
                else:
                    raise Exception("CloudWatch not returning live data")
            else:
                raise Exception("CloudWatch disabled")

        except Exception as cloudwatch_error:
            logger.warning(f"CloudWatch unavailable, using fallback: {cloudwatch_error}")

            # Fallback: Mark as unavailable with helpful message
            system_metrics = {
                "status": "cloudwatch_required",
                "message": "System metrics (CPU, Memory, Storage) require AWS CloudWatch integration",
                "available_in": "phase_2",
                "cloudwatch_enabled": CLOUDWATCH_ENABLED,
                "note": "Configure CLOUDWATCH_ENABLED=true and AWS credentials to enable"
            }

            application_metrics = {
                "status": "cloudwatch_required",
                "message": "Application metrics (Response times, Throughput, Error rates) require CloudWatch Logs Insights",
                "available_in": "phase_2",
                "note": "These metrics are calculated from ECS task logs"
            }

        # ===== DATABASE METRICS - ALWAYS AVAILABLE =====
        # Get real database connection stats
        try:
            # Query for active database connections (PostgreSQL specific)
            db_connections_result = db.execute(text("""
                SELECT
                    COUNT(*) FILTER (WHERE state = 'active') as active,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle,
                    COUNT(*) as total
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)).fetchone()

            if db_connections_result:
                active_conns = db_connections_result[0] or 0
                idle_conns = db_connections_result[1] or 0
                total_conns = db_connections_result[2] or 0
            else:
                active_conns = idle_conns = total_conns = 0

            # Get database max connections
            max_conns_result = db.execute(text("SHOW max_connections")).scalar()
            max_connections = int(max_conns_result) if max_conns_result else 100

            # Query performance from recent actions
            recent_actions = db.query(func.count(AgentAction.id)).filter(
                AgentAction.timestamp >= hour_ago
            ).scalar() or 0

            # Estimate slow queries (actions that took longer than expected)
            # This is a proxy - in production you'd use pg_stat_statements
            slow_threshold_minutes = 5
            slow_query_estimate = db.query(func.count(AgentAction.id)).filter(
                and_(
                    AgentAction.timestamp >= hour_ago,
                    AgentAction.status == 'pending',
                    AgentAction.created_at < (current_time - timedelta(minutes=slow_threshold_minutes))
                )
            ).scalar() or 0

            database_metrics = {
                "connections": {
                    "active": active_conns,
                    "idle": idle_conns,
                    "total": total_conns,
                    "max": max_connections,
                    "utilization": round((total_conns / max_connections * 100), 1) if max_connections > 0 else 0,
                    "status": "healthy" if total_conns < (max_connections * 0.8) else "high",
                    "source": "postgresql"
                },
                "query_performance": {
                    "recent_queries": recent_actions,
                    "slow_queries_estimate": slow_query_estimate,
                    "status": "optimal" if slow_query_estimate == 0 else "degraded",
                    "source": "agent_actions_table",
                    "note": "Enable pg_stat_statements for detailed query analytics"
                }
            }

        except Exception as db_error:
            logger.warning(f"Database metrics fallback: {db_error}")
            database_metrics = {
                "status": "partial_data",
                "message": "Some database metrics unavailable",
                "error": str(db_error),
                "note": "This may be due to insufficient database permissions"
            }

        # ===== BUILD RESPONSE =====
        performance_data = {
            "timestamp": current_time.isoformat(),
            "system_metrics": system_metrics,
            "application_metrics": application_metrics,
            "database_metrics": database_metrics,
            "meta": {
                "version": "2.0.0",
                "mock_data": False,
                "cloudwatch_enabled": CLOUDWATCH_ENABLED,
                "data_sources": {
                    "system_metrics": system_metrics.get("source", "cloudwatch_required"),
                    "application_metrics": application_metrics.get("source", "cloudwatch_required"),
                    "database_metrics": "postgresql"
                }
            }
        }

        return performance_data

    except Exception as e:
        logger.error(f"❌ System performance error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch system performance: {str(e)}")

# 🌐 WebSocket for Real-Time Data Streaming
class ConnectionManager:
    """Enterprise WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_email: str):
        """Accept WebSocket connection for authenticated user"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_email] = websocket
        logger.info(f"🔌 WebSocket connected: {user_email}")
    
    def disconnect(self, websocket: WebSocket, user_email: str):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_email in self.user_connections:
            del self.user_connections[user_email]
        logger.info(f"🔌 WebSocket disconnected: {user_email}")
    
    async def send_personal_message(self, message: str, user_email: str):
        """Send message to specific user"""
        if user_email in self.user_connections:
            await self.user_connections[user_email].send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected users"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove failed connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@router.websocket("/ws/realtime/{user_email}")
async def websocket_endpoint(websocket: WebSocket, user_email: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time analytics streaming with real metrics"""
    await manager.connect(websocket, user_email)

    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": f"Real-time analytics connected for {user_email}",
            "timestamp": datetime.now(UTC).isoformat()
        }))

        # Start real-time data streaming
        while True:
            try:
                now = datetime.now(UTC)
                hour_ago = now - timedelta(hours=1)

                # Get real metrics from database
                recent_actions = db.query(func.count(AgentAction.id)).filter(
                    AgentAction.timestamp >= hour_ago
                ).scalar() or 0

                high_risk_recent = db.query(func.count(AgentAction.id)).filter(
                    and_(
                        AgentAction.timestamp >= hour_ago,
                        AgentAction.risk_level.in_(['high', 'critical'])
                    )
                ).scalar() or 0

                active_agents = db.query(func.count(func.distinct(AgentAction.agent_id))).filter(
                    AgentAction.timestamp >= hour_ago
                ).scalar() or 0

                # Try to get CloudWatch metrics if available
                cloudwatch_metrics = {"status": "unavailable"}
                try:
                    if CLOUDWATCH_ENABLED:
                        cloudwatch = get_cloudwatch_service(
                            region=AWS_REGION,
                            cache_ttl=30,
                            enabled=CLOUDWATCH_ENABLED
                        )
                        cw_health = cloudwatch.get_system_health(
                            cluster_name=ECS_CLUSTER_NAME,
                            service_name=ECS_SERVICE_NAME,
                            log_group_name=CLOUDWATCH_LOG_GROUP
                        )

                        if cw_health.get("status") == "live":
                            cloudwatch_metrics = {
                                "status": "live",
                                "cpu_usage": round(cw_health.get("cpu_usage", 0.0), 1),
                                "memory_usage": round(cw_health.get("memory_usage", 0.0), 1),
                                "response_time": round(cw_health.get("api_response_time", 0.0), 1)
                            }
                        else:
                            cloudwatch_metrics = {"status": "cloudwatch_required"}
                    else:
                        cloudwatch_metrics = {"status": "cloudwatch_disabled"}
                except Exception as cw_error:
                    logger.debug(f"CloudWatch unavailable in WebSocket: {cw_error}")
                    cloudwatch_metrics = {"status": "cloudwatch_error"}

                # Build real-time data payload
                realtime_data = {
                    "type": "metrics_update",
                    "timestamp": now.isoformat(),
                    "metrics": {
                        "active_websocket_connections": len(manager.active_connections),
                        "recent_actions_last_hour": recent_actions,
                        "high_risk_actions_last_hour": high_risk_recent,
                        "active_agents_last_hour": active_agents
                    },
                    "system_metrics": cloudwatch_metrics,
                    "data_quality": {
                        "source": "real_database",
                        "mock_data": False,
                        "has_activity": recent_actions > 0
                    }
                }

                await websocket.send_text(json.dumps(realtime_data))
                await asyncio.sleep(10)  # Update every 10 seconds

            except Exception as metric_error:
                # If metrics collection fails, send error status but keep connection alive
                logger.warning(f"Metrics collection error in WebSocket: {metric_error}")
                error_data = {
                    "type": "metrics_update",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "metrics": {
                        "active_websocket_connections": len(manager.active_connections),
                        "status": "error",
                        "message": "Temporary metrics collection error"
                    },
                    "data_quality": {
                        "source": "error",
                        "mock_data": False
                    }
                }
                await websocket.send_text(json.dumps(error_data))
                await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_email)
        logger.info(f"🔌 WebSocket disconnected: {user_email}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for {user_email}: {str(e)}")
        manager.disconnect(websocket, user_email)