# Insert this code after line 1225 (after the alerts table fix, before conn.commit())

            # Create smart_rules table
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS smart_rules (
                        id SERIAL PRIMARY KEY,
                        agent_id VARCHAR(255),
                        action_type VARCHAR(255),
                        description TEXT,
                        condition TEXT,
                        action VARCHAR(100),
                        risk_level VARCHAR(50),
                        recommendation TEXT,
                        justification TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Insert sample data if table is empty
                count_result = conn.execute(text("SELECT COUNT(*) FROM smart_rules"))
                if count_result.fetchone()[0] == 0:
                    conn.execute(text("""
                        INSERT INTO smart_rules (agent_id, action_type, description, condition, action, risk_level, recommendation, justification) 
                        VALUES 
                        ('security-scanner-01', 'vulnerability_scan', 'High-risk scan approval', 'risk_level = high', 'require_approval', 'high', 'Manual approval required', 'Security'),
                        ('compliance-agent', 'compliance_check', 'Auto-approve compliance', 'risk_level = low', 'auto_approve', 'low', 'Automated checks', 'Routine'),
                        ('threat-detector', 'anomaly_detection', 'Alert on anomalies', 'action_type = anomaly', 'alert', 'medium', 'Monitor activity', 'Detection')
                    """))
                
                results.append("✅ Created smart_rules table with sample data")
            except Exception as e:
                results.append(f"⚠️ smart_rules: {str(e)}")
