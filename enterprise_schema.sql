-- Master Prompt Enterprise Database Schema

-- Enterprise sessions table
CREATE TABLE IF NOT EXISTS enterprise_sessions (
    id SERIAL PRIMARY KEY,
    session_token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER,
    email VARCHAR(255),
    role VARCHAR(50),
    tenant_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_activity TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    compliance_logged BOOLEAN DEFAULT TRUE
);

-- Enterprise audit logs
CREATE TABLE IF NOT EXISTS enterprise_audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),
    user_email VARCHAR(255),
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    details JSONB,
    risk_level VARCHAR(20) DEFAULT 'Medium',
    compliance_flags JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced agent_actions table
ALTER TABLE agent_actions 
ADD COLUMN IF NOT EXISTS enterprise_session_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS compliance_reviewed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS audit_trail_id INTEGER;

-- Enhanced alerts table  
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS enterprise_priority VARCHAR(20) DEFAULT 'Medium',
ADD COLUMN IF NOT EXISTS compliance_category VARCHAR(50),
ADD COLUMN IF NOT EXISTS executive_visibility BOOLEAN DEFAULT FALSE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_enterprise_sessions_token ON enterprise_sessions(session_token_hash);
CREATE INDEX IF NOT EXISTS idx_enterprise_sessions_user ON enterprise_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_enterprise_audit_user ON enterprise_audit_logs(user_email);
CREATE INDEX IF NOT EXISTS idx_enterprise_audit_timestamp ON enterprise_audit_logs(timestamp);

-- Insert enterprise roles if not exists
INSERT INTO user_roles (name, description, permissions, level, risk_level) VALUES
('Enterprise Admin', 'Full enterprise system access', '{"all": true}', 5, 'Critical'),
('Security Manager', 'Security operations management', '{"security": true, "audit": true}', 4, 'High'),
('Compliance Officer', 'Compliance and audit access', '{"compliance": true, "audit": true}', 3, 'Medium')
ON CONFLICT DO NOTHING;

