-- Database Schema Fix for OW-AI Enterprise Platform
-- Master Prompt Compliant: Adding missing columns for enterprise features

-- Fix agent_actions table
ALTER TABLE agent_actions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Fix alerts table  
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS agent_id VARCHAR(255);

-- Fix workflows table (remove space from description column name)
ALTER TABLE workflows 
RENAME COLUMN "description " TO description;

-- Fix smart_rules table
ALTER TABLE smart_rules
ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.85,
ADD COLUMN IF NOT EXISTS training_data_size INTEGER DEFAULT 1000;

-- Update timestamps for existing records
UPDATE agent_actions SET updated_at = created_at WHERE updated_at IS NULL;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_agent_id ON alerts(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_updated_at ON agent_actions(updated_at);

-- Verify schema fixes
SELECT 'Schema migration completed successfully' as status;
