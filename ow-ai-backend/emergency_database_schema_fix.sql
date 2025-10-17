-- EMERGENCY DATABASE SCHEMA FIX - CRITICAL PRODUCTION BLOCKER
-- Fixing missing columns that are causing 500 errors in API endpoints

-- Connect to the database
\c railway;

BEGIN;

-- Fix agent_actions table - Add missing columns
ALTER TABLE agent_actions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

ALTER TABLE agent_actions 
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- Update existing records to have proper updated_at values
UPDATE agent_actions 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Create trigger for automatic updated_at updates
CREATE OR REPLACE FUNCTION update_agent_actions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_agent_actions_updated_at ON agent_actions;
CREATE TRIGGER trigger_agent_actions_updated_at
    BEFORE UPDATE ON agent_actions
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_actions_updated_at();

-- Fix users table - Add missing columns for enterprise features
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0;

-- Update existing users to have 'active' status
UPDATE users 
SET status = 'active' 
WHERE status IS NULL;

-- Verify critical columns exist
DO $$
BEGIN
    -- Check if agent_actions.updated_at exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' 
        AND column_name = 'updated_at'
    ) THEN
        RAISE EXCEPTION 'CRITICAL: agent_actions.updated_at column was not created';
    END IF;

    -- Check if agent_actions.reviewed_at exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_actions' 
        AND column_name = 'reviewed_at'
    ) THEN
        RAISE EXCEPTION 'CRITICAL: agent_actions.reviewed_at column was not created';
    END IF;

    -- Check if users.status exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'status'
    ) THEN
        RAISE EXCEPTION 'CRITICAL: users.status column was not created';
    END IF;

    RAISE NOTICE 'SUCCESS: All critical database schema fixes applied successfully';
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_actions_updated_at ON agent_actions(updated_at);
CREATE INDEX IF NOT EXISTS idx_agent_actions_reviewed_at ON agent_actions(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_agent_actions_status ON agent_actions(status);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

COMMIT;

-- Verify the fix by running test queries
SELECT 'Testing agent_actions.updated_at' as test_name, COUNT(*) as record_count 
FROM agent_actions WHERE updated_at IS NOT NULL;

SELECT 'Testing agent_actions.reviewed_at availability' as test_name, COUNT(*) as total_records 
FROM agent_actions;

SELECT 'Testing users.status' as test_name, status, COUNT(*) as user_count 
FROM users GROUP BY status;

-- Show table structure to confirm changes
\d agent_actions;
\d users;