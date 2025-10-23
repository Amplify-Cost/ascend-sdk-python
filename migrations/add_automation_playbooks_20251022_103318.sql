-- ================================================================
-- ENTERPRISE MIGRATION: Automation Playbooks System
-- Purpose: Add automation_playbooks and playbook_executions tables
-- Author: Enterprise Security Team
-- Date: 2025-10-22
-- Version: 1.0.0
-- Compliance: SOX, PCI-DSS, HIPAA, GDPR
-- ================================================================

-- ============================================================
-- TABLE: automation_playbooks
-- Purpose: Store automated response playbooks with audit trail
-- ============================================================
CREATE TABLE IF NOT EXISTS automation_playbooks (
    -- Primary identification
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Status and risk management
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    risk_level VARCHAR(50) DEFAULT 'medium' NOT NULL,
    approval_required BOOLEAN DEFAULT FALSE,
    
    -- Playbook configuration (JSONB for PostgreSQL performance)
    trigger_conditions JSONB,
    actions JSONB,
    
    -- Execution tracking
    last_executed TIMESTAMP,
    execution_count INTEGER DEFAULT 0,
    success_rate DOUBLE PRECISION DEFAULT 0.0,
    
    -- Audit fields
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'disabled', 'maintenance')),
    CONSTRAINT valid_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_playbooks_name ON automation_playbooks(name);
CREATE INDEX IF NOT EXISTS idx_playbooks_status ON automation_playbooks(status);
CREATE INDEX IF NOT EXISTS idx_playbooks_risk_level ON automation_playbooks(risk_level);
CREATE INDEX IF NOT EXISTS idx_playbooks_created_by ON automation_playbooks(created_by);
CREATE INDEX IF NOT EXISTS idx_playbooks_created_at ON automation_playbooks(created_at);

-- ============================================================
-- TABLE: playbook_executions
-- Purpose: Audit trail and execution history for playbooks
-- ============================================================
CREATE TABLE IF NOT EXISTS playbook_executions (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Playbook reference
    playbook_id VARCHAR(255) NOT NULL REFERENCES automation_playbooks(id) ON DELETE CASCADE,
    
    -- Execution context
    executed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    execution_context VARCHAR(50) DEFAULT 'manual',
    input_data JSONB,
    
    -- Execution results
    execution_status VARCHAR(50) NOT NULL,
    execution_details JSONB,
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Constraints
    CONSTRAINT valid_execution_status CHECK (
        execution_status IN ('pending', 'running', 'completed', 'failed', 'cancelled')
    ),
    CONSTRAINT valid_execution_context CHECK (
        execution_context IN ('manual', 'automatic', 'scheduled', 'trigger')
    )
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_executions_playbook_id ON playbook_executions(playbook_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON playbook_executions(execution_status);
CREATE INDEX IF NOT EXISTS idx_executions_started_at ON playbook_executions(started_at);
CREATE INDEX IF NOT EXISTS idx_executions_executed_by ON playbook_executions(executed_by);

-- ============================================================
-- SEED DATA: Migrate existing demo playbook to database
-- ============================================================
INSERT INTO automation_playbooks (
    id, 
    name, 
    description, 
    status, 
    risk_level,
    approval_required,
    trigger_conditions,
    actions,
    last_executed,
    execution_count,
    success_rate,
    created_by,
    created_at,
    updated_at
) VALUES (
    'pb-001',
    'High-Risk Action Auto-Review',
    'Automatically review and escalate high-risk agent actions',
    'active',
    'high',
    false,
    '{"risk_score": {"min": 80}, "action_type": ["file_access", "network_scan", "database_query"], "environment": ["production"]}'::jsonb,
    '[
        {"type": "risk_assessment", "parameters": {"deep_scan": true}},
        {"type": "stakeholder_notification", "recipients": ["security-team@company.com"]},
        {"type": "temporary_quarantine", "duration_minutes": 30},
        {"type": "escalate_approval", "level": "L4"}
    ]'::jsonb,
    CURRENT_TIMESTAMP - INTERVAL '2 hours',
    156,
    97.4,
    (SELECT id FROM users WHERE email = 'admin@owkai.com' LIMIT 1),
    CURRENT_TIMESTAMP - INTERVAL '30 days',
    CURRENT_TIMESTAMP - INTERVAL '30 days'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================
-- Verify tables created
SELECT 'automation_playbooks table' as check_name, 
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'automation_playbooks') 
       THEN '✅ EXISTS' ELSE '❌ MISSING' END as status
UNION ALL
SELECT 'playbook_executions table' as check_name,
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'playbook_executions')
       THEN '✅ EXISTS' ELSE '❌ MISSING' END as status;

-- Verify seed data
SELECT 'Seed playbook count' as check_name, COUNT(*)::text as status FROM automation_playbooks;

-- Show table structure
SELECT 'Column count in automation_playbooks' as check_name, COUNT(*)::text as status 
FROM information_schema.columns 
WHERE table_name = 'automation_playbooks';

