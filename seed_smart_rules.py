#!/usr/bin/env python3
"""
Seed Smart Rules for Local Development

This script populates your local database with enterprise-grade smart rules
that mirror production patterns. Run this to test the AI Rule Engine locally.

Usage:
    python3 seed_smart_rules.py
"""

from database import get_db
from models import SmartRule
from datetime import datetime, UTC
from sqlalchemy import text

def seed_smart_rules():
    """Create enterprise smart rules for local testing"""
    db = next(get_db())

    try:
        # Check if rules already exist
        existing = db.execute(text("SELECT COUNT(*) FROM smart_rules")).scalar()
        if existing > 0:
            print(f"⚠️  Database already has {existing} rules. Clearing and reseeding...")
            db.execute(text("DELETE FROM smart_rules"))
            db.commit()
            print("✅ Cleared existing rules")

        # Enterprise Smart Rules
        rules = [
            {
                "name": "Data Exfiltration Detection",
                "agent_id": "security-ai-001",
                "action_type": "smart_rule",
                "description": "Detects unusual file access patterns that may indicate data theft",
                "condition": "file_access_count > 100 AND access_time BETWEEN '22:00' AND '06:00' AND user_classification = 'standard'",
                "action": "block_and_alert",
                "risk_level": "critical",
                "recommendation": "Immediately investigate user activity and review access logs",
                "justification": "High-volume file access during off-hours by standard users is a primary indicator of data exfiltration attempts. This pattern appears in 87% of confirmed data theft cases.",
                "created_at": datetime.now(UTC)
            },
            {
                "name": "Privilege Escalation Monitor",
                "agent_id": "security-ai-002",
                "action_type": "smart_rule",
                "description": "Monitors for privilege escalation attempts and suspicious sudo usage",
                "condition": "sudo_attempts > 3 AND failed_auth_count > 2 AND time_window = '15_minutes'",
                "action": "quarantine_and_investigate",
                "risk_level": "high",
                "recommendation": "Lock user account and require security review before access restoration",
                "justification": "Multiple failed authentication attempts followed by sudo usage indicates potential credential compromise or privilege escalation attack. 78% of successful breaches follow this pattern.",
                "created_at": datetime.now(UTC)
            },
            {
                "name": "Network Anomaly Detection",
                "agent_id": "security-ai-003",
                "action_type": "smart_rule",
                "description": "Identifies unusual network traffic patterns using ML baseline analysis",
                "condition": "traffic_volume > baseline * 3 AND destination_ports IN (suspicious_ports) AND geo_location = 'untrusted'",
                "action": "monitor_and_escalate",
                "risk_level": "high",
                "recommendation": "Analyze traffic patterns and block if malicious indicators confirmed",
                "justification": "Network traffic 3x above baseline to suspicious ports in untrusted geolocations indicates command & control communication or data exfiltration. ML analysis shows 92% correlation with actual threats.",
                "created_at": datetime.now(UTC)
            },
            {
                "name": "Insider Threat Detection",
                "agent_id": "security-ai-004",
                "action_type": "smart_rule",
                "description": "Detects insider threat patterns during maintenance windows",
                "condition": "database_query_count > 50 AND maintenance_window = true AND query_type = 'SELECT_SENSITIVE'",
                "action": "alert_and_log",
                "risk_level": "medium",
                "recommendation": "Review database audit logs and user access justification",
                "justification": "Unusual database query patterns during maintenance windows when oversight is reduced. Time-series analysis shows 73% of insider threats occur during these periods.",
                "created_at": datetime.now(UTC)
            },
            {
                "name": "Credential Stuffing Prevention",
                "agent_id": "security-ai-005",
                "action_type": "smart_rule",
                "description": "Prevents automated credential stuffing attacks",
                "condition": "failed_login_attempts > 10 AND time_window = '5_minutes' AND source_ip_reputation = 'suspicious'",
                "action": "block_and_alert",
                "risk_level": "high",
                "recommendation": "Block IP address and enable MFA for affected accounts",
                "justification": "Rapid failed login attempts from suspicious IPs indicate automated credential stuffing. 94% of these patterns are confirmed attacks.",
                "created_at": datetime.now(UTC)
            },
            {
                "name": "Lateral Movement Detection",
                "agent_id": "security-ai-006",
                "action_type": "smart_rule",
                "description": "Identifies lateral movement patterns across network segments",
                "condition": "new_host_connections > 5 AND connection_type = 'SMB' AND time_window = '10_minutes'",
                "action": "isolate_and_investigate",
                "risk_level": "critical",
                "recommendation": "Isolate affected systems and conduct forensic analysis",
                "justification": "Rapid connections to multiple hosts via SMB indicates lateral movement after initial compromise. This is a key indicator in 89% of advanced persistent threats.",
                "created_at": datetime.now(UTC)
            },
            {
                "name": "API Abuse Detection",
                "agent_id": "security-ai-007",
                "action_type": "smart_rule",
                "description": "Detects API rate limit abuse and scraping attempts",
                "condition": "api_requests > 1000 AND time_window = '1_minute' AND endpoint_diversity < 3",
                "action": "rate_limit_and_alert",
                "risk_level": "medium",
                "recommendation": "Implement progressive rate limiting and analyze request patterns",
                "justification": "High-volume API requests to limited endpoints suggests automated scraping or API abuse. Pattern recognition shows 85% accuracy in detecting malicious automation.",
                "created_at": datetime.now(UTC)
            },
            {
                "name": "Ransomware Behavior Detection",
                "agent_id": "security-ai-008",
                "action_type": "smart_rule",
                "description": "Early detection of ransomware encryption behavior",
                "condition": "file_modification_rate > 100_per_minute AND file_extension_changes = true AND backup_access_attempts = true",
                "action": "block_and_isolate",
                "risk_level": "critical",
                "recommendation": "Immediately isolate system, kill suspicious processes, restore from backup",
                "justification": "Rapid file modifications with extension changes combined with backup access indicates active ransomware encryption. 96% detection accuracy before significant damage.",
                "created_at": datetime.now(UTC)
            }
        ]

        print(f"\n🌱 Seeding {len(rules)} enterprise smart rules...")

        for rule_data in rules:
            # Insert using raw SQL to avoid model issues
            db.execute(text("""
                INSERT INTO smart_rules
                (name, agent_id, action_type, description, condition, action,
                 risk_level, recommendation, justification, created_at)
                VALUES
                (:name, :agent_id, :action_type, :description, :condition, :action,
                 :risk_level, :recommendation, :justification, :created_at)
            """), rule_data)
            print(f"  ✅ Created: {rule_data['name']}")

        db.commit()

        # Verify
        count = db.execute(text("SELECT COUNT(*) FROM smart_rules")).scalar()
        print(f"\n✅ Successfully seeded {count} smart rules!")

        print("\n📊 Rule Summary:")
        summary = db.execute(text("""
            SELECT risk_level, COUNT(*) as count
            FROM smart_rules
            GROUP BY risk_level
            ORDER BY
                CASE risk_level
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        """)).fetchall()

        for risk_level, count in summary:
            print(f"  {risk_level.upper()}: {count} rules")

        print("\n🎯 Next Steps:")
        print("  1. Start your backend: python3 main.py")
        print("  2. Open AI Rule Engine sidebar in frontend")
        print("  3. View your smart rules in the Smart Rules tab")
        print("  4. Analytics will now show real performance metrics")

    except Exception as e:
        print(f"\n❌ Error seeding rules: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 80)
    print("SMART RULES DATABASE SEEDING")
    print("=" * 80)
    seed_smart_rules()
