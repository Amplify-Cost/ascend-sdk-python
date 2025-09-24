-- AWS RDS PostgreSQL Schema Fix Script
-- Database: owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com
-- Production Endpoint: pilot.owkai.app
-- 
-- CRITICAL: This script fixes missing columns causing 500 errors
-- Score 4/10 → Target 9/10 enterprise database schema
-- 
-- Author: Enterprise Backend Team
-- Created: 2025-09-11
-- AWS RDS ONLY - NO RAILWAY

-- =============================================================================
-- SAFETY CHECKS
-- =============================================================================
SELECT 'Starting AWS RDS Schema Fix for owkai_pilot database' as status;
SELECT current_database() as connected_database;
SELECT version() as postgresql_version;

-- =============================================================================
-- USER TABLE ENHANCEMENTS - Enterprise Security Features
-- =============================================================================
DO $$ 
BEGIN
    -- Add status column for enterprise user management
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'status'
    ) THEN
        ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
        RAISE NOTICE 'Added status column to users table';
    ELSE
        RAISE NOTICE 'status column already exists in users table';
    END IF;

    -- Add MFA enabled column for enterprise security
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'mfa_enabled'
    ) THEN
        ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT false;
        RAISE NOTICE 'Added mfa_enabled column to users table';
    ELSE
        RAISE NOTICE 'mfa_enabled column already exists in users table';
    END IF;

    -- Add login attempts for security tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'login_attempts'
    ) THEN
        ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0;
        RAISE NOTICE 'Added login_attempts column to users table';
    ELSE
        RAISE NOTICE 'login_attempts column already exists in users table';
    END IF;

    -- Add account locked timestamp
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'locked_until'
    ) THEN
        ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
        RAISE NOTICE 'Added locked_until column to users table';
    ELSE
        RAISE NOTICE 'locked_until column already exists in users table';
    END IF;

    -- Add password changed timestamp for enterprise compliance
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_changed_at'
    ) THEN
        ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added password_changed_at column to users table';
    ELSE
        RAISE NOTICE 'password_changed_at column already exists in users table';
    END IF;
END $$;

-- =============================================================================
-- AGENT_ACTIONS TABLE ENHANCEMENTS - Critical Missing Columns
-- =============================================================================
DO $$ 
BEGIN
    -- Ensure updated_at column exists (CRITICAL - causing governance failures)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE agent_actions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        
        -- Create trigger to auto-update timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS update_agent_actions_updated_at ON agent_actions;
        CREATE TRIGGER update_agent_actions_updated_at 
            BEFORE UPDATE ON agent_actions 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        RAISE NOTICE 'Added updated_at column and trigger to agent_actions table';
    ELSE
        RAISE NOTICE 'updated_at column already exists in agent_actions table';
    END IF;

    -- Ensure reviewed_at column exists (CRITICAL - causing metrics failures)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' AND column_name = 'reviewed_at'
    ) THEN
        ALTER TABLE agent_actions ADD COLUMN reviewed_at TIMESTAMP;
        RAISE NOTICE 'Added reviewed_at column to agent_actions table';
    ELSE
        RAISE NOTICE 'reviewed_at column already exists in agent_actions table';
    END IF;

    -- Add execution timestamp for enterprise tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' AND column_name = 'executed_at'
    ) THEN
        ALTER TABLE agent_actions ADD COLUMN executed_at TIMESTAMP;
        RAISE NOTICE 'Added executed_at column to agent_actions table';
    ELSE
        RAISE NOTICE 'executed_at column already exists in agent_actions table';
    END IF;

    -- Add execution status for workflow tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' AND column_name = 'execution_status'
    ) THEN
        ALTER TABLE agent_actions ADD COLUMN execution_status VARCHAR(50);
        RAISE NOTICE 'Added execution_status column to agent_actions table';
    ELSE
        RAISE NOTICE 'execution_status column already exists in agent_actions table';
    END IF;
END $$;

-- =============================================================================
-- CREATE ENTERPRISE INDEXES FOR PERFORMANCE
-- =============================================================================
-- User management indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status_active 
    ON users(status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login 
    ON users(last_login DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_mfa_enabled 
    ON users(mfa_enabled);

-- Agent actions performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_actions_updated_at 
    ON agent_actions(updated_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_actions_reviewed_at 
    ON agent_actions(reviewed_at DESC) WHERE reviewed_at IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_actions_status_pending 
    ON agent_actions(status) WHERE status = 'pending';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_actions_risk_level 
    ON agent_actions(risk_level);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_actions_execution_status 
    ON agent_actions(execution_status);

-- Composite indexes for enterprise queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_actions_status_risk_created 
    ON agent_actions(status, risk_level, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_actions_user_status 
    ON agent_actions(user_id, status) WHERE user_id IS NOT NULL;

-- =============================================================================
-- UPDATE EXISTING DATA FOR ENTERPRISE COMPLIANCE
-- =============================================================================

-- Set default status for existing users
UPDATE users SET status = 'active' WHERE status IS NULL;

-- Update existing agent_actions with proper timestamps
UPDATE agent_actions 
SET updated_at = COALESCE(reviewed_at, created_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

-- Set execution status for completed actions
UPDATE agent_actions 
SET execution_status = 'completed' 
WHERE status = 'executed' AND execution_status IS NULL;

UPDATE agent_actions 
SET execution_status = 'pending' 
WHERE status = 'approved' AND execution_status IS NULL;

UPDATE agent_actions 
SET execution_status = 'failed' 
WHERE status = 'denied' AND execution_status IS NULL;

-- =============================================================================
-- ENTERPRISE CONSTRAINTS AND VALIDATION
-- =============================================================================

-- Add check constraints for data integrity
DO $$
BEGIN
    -- User status constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_users_status'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT chk_users_status 
        CHECK (status IN ('active', 'inactive', 'suspended', 'locked'));
        RAISE NOTICE 'Added status check constraint to users table';
    END IF;

    -- Login attempts constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_users_login_attempts'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT chk_users_login_attempts 
        CHECK (login_attempts >= 0 AND login_attempts <= 10);
        RAISE NOTICE 'Added login_attempts check constraint to users table';
    END IF;

    -- Agent actions execution status constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_agent_actions_execution_status'
    ) THEN
        ALTER TABLE agent_actions 
        ADD CONSTRAINT chk_agent_actions_execution_status 
        CHECK (execution_status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));
        RAISE NOTICE 'Added execution_status check constraint to agent_actions table';
    END IF;
END $$;

-- =============================================================================
-- CREATE ENTERPRISE VIEWS FOR DASHBOARD
-- =============================================================================

-- User management view for enterprise dashboard
CREATE OR REPLACE VIEW v_enterprise_users AS
SELECT 
    u.id,
    u.email,
    u.role,
    u.status,
    u.is_active,
    u.mfa_enabled,
    u.login_attempts,
    u.last_login,
    u.created_at,
    u.locked_until,
    u.password_changed_at,
    u.approval_level,
    u.is_emergency_approver,
    u.max_risk_approval,
    COUNT(aa.id) as total_actions,
    COUNT(CASE WHEN aa.status = 'pending' THEN 1 END) as pending_approvals
FROM users u
LEFT JOIN agent_actions aa ON u.id = aa.user_id
GROUP BY u.id, u.email, u.role, u.status, u.is_active, u.mfa_enabled, 
         u.login_attempts, u.last_login, u.created_at, u.locked_until,
         u.password_changed_at, u.approval_level, u.is_emergency_approver, u.max_risk_approval;

-- Agent actions enterprise metrics view
CREATE OR REPLACE VIEW v_enterprise_agent_metrics AS
SELECT 
    DATE_TRUNC('day', created_at) as action_date,
    risk_level,
    status,
    execution_status,
    COUNT(*) as action_count,
    AVG(CASE WHEN risk_score IS NOT NULL THEN risk_score END) as avg_risk_score,
    COUNT(CASE WHEN reviewed_at IS NOT NULL THEN 1 END) as reviewed_count,
    AVG(EXTRACT(EPOCH FROM (COALESCE(reviewed_at, updated_at) - created_at))/60) as avg_review_time_minutes
FROM agent_actions
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at), risk_level, status, execution_status
ORDER BY action_date DESC, risk_level;

-- Pending actions summary for enterprise dashboard
CREATE OR REPLACE VIEW v_pending_actions_summary AS
SELECT 
    risk_level,
    COUNT(*) as pending_count,
    MIN(created_at) as oldest_pending,
    AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at))/3600) as avg_pending_hours,
    COUNT(CASE WHEN requires_approval = true THEN 1 END) as requires_approval_count
FROM agent_actions
WHERE status = 'pending'
GROUP BY risk_level
ORDER BY 
    CASE risk_level 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        WHEN 'low' THEN 4 
    END;

-- =============================================================================
-- GRANT PERMISSIONS FOR AWS RDS
-- =============================================================================

-- Grant necessary permissions to application user
-- (Replace 'owkai_admin' with your actual application database user)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO owkai_admin;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO owkai_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO owkai_admin;

-- Grant view permissions
GRANT SELECT ON v_enterprise_users TO owkai_admin;
GRANT SELECT ON v_enterprise_agent_metrics TO owkai_admin;
GRANT SELECT ON v_pending_actions_summary TO owkai_admin;

-- =============================================================================
-- FINAL VALIDATION AND SUMMARY
-- =============================================================================

-- Verify all critical columns exist
SELECT 
    'users.status' as column_check,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'status'
    ) THEN 'EXISTS' ELSE 'MISSING' END as status
UNION ALL
SELECT 
    'users.mfa_enabled',
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'mfa_enabled'
    ) THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 
    'users.login_attempts',
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'login_attempts'
    ) THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 
    'agent_actions.updated_at',
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' AND column_name = 'updated_at'
    ) THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 
    'agent_actions.reviewed_at',
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' AND column_name = 'reviewed_at'
    ) THEN 'EXISTS' ELSE 'MISSING' END;

-- Summary of improvements
SELECT 'AWS RDS Schema Fix Completed Successfully' as status;
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(*) as total_agent_actions FROM agent_actions;
SELECT COUNT(DISTINCT status) as unique_statuses FROM agent_actions;

-- Performance summary
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('users', 'agent_actions')
AND schemaname = 'public'
ORDER BY tablename, indexname;

COMMIT;