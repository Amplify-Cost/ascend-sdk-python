-- Add missing columns to agent_actions table
ALTER TABLE agent_actions ADD COLUMN IF NOT EXISTS extra_data JSONB;
ALTER TABLE agent_actions ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255);

-- Ensure mcp_policies table has proper constraints
ALTER TABLE mcp_policies ALTER COLUMN created_by DROP NOT NULL;
