#!/bin/bash

echo "🗄️ Setting up production-identical PostgreSQL database..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not installed. Installing via Homebrew..."
    brew install postgresql
    brew services start postgresql
fi

# Create enterprise database and user
echo "🔐 Creating enterprise database and user..."

psql postgres -c "DROP DATABASE IF EXISTS owai_enterprise_db;"
psql postgres -c "DROP USER IF EXISTS owai_user;"
psql postgres -c "CREATE USER owai_user WITH REDACTED-CREDENTIAL 'owai_enterprise_password';"
psql postgres -c "CREATE DATABASE owai_enterprise_db OWNER owai_user;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE owai_enterprise_db TO owai_user;"

# Create enterprise tables with production schema
echo "🏢 Creating enterprise tables with production schema..."

psql owai_enterprise_db -c "
-- Production-identical enterprise schema
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";

-- Users table (production-identical)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    department VARCHAR(100),
    permissions JSONB DEFAULT '[]',
    mfa_enabled BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

-- Smart Rules table (production-identical)
CREATE TABLE IF NOT EXISTS smart_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    conditions JSONB NOT NULL,
    actions JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_count INTEGER DEFAULT 0,
    last_executed TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Analytics Events table (production-identical)
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'
);

-- Governance Actions table (production-identical)
CREATE TABLE IF NOT EXISTS governance_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    requested_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    request_data JSONB NOT NULL,
    approval_data JSONB,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Alerts table (production-identical)
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(100),
    affected_resource VARCHAR(255),
    triggered_by UUID REFERENCES users(id),
    acknowledged_by UUID REFERENCES users(id),
    resolved_by UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'active',
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Audit Logs table (production-identical)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    outcome VARCHAR(50),
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for performance (production-identical)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_smart_rules_active ON smart_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_governance_actions_status ON governance_actions(status);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Insert enterprise test data (production-identical)
INSERT INTO users (email, password_hash, role, department, permissions) VALUES
('shug@gmail.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxWD4xSu', 'admin', 'Engineering', '[\"all\"]'),
('admin@company.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxWD4xSu', 'admin', 'IT', '[\"user_management\", \"system_admin\"]'),
('manager@company.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxWD4xSu', 'manager', 'Operations', '[\"approve_rules\", \"view_analytics\"]'),
('analyst@company.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxWD4xSu', 'analyst', 'Analytics', '[\"view_analytics\", \"create_reports\"]'),
('user@company.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxWD4xSu', 'user', 'Sales', '[\"view_own_data\"]')
ON CONFLICT (email) DO NOTHING;

-- Grant proper permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO owai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO owai_user;
"

echo "✅ Production-identical PostgreSQL database setup complete"
