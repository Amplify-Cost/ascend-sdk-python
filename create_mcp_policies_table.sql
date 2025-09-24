-- Create MCP Policies Table Schema
-- This script creates the mcp_policies table for Policy Management functionality

-- Drop table if exists (for clean recreation)
DROP TABLE IF EXISTS mcp_policies CASCADE;

-- Create mcp_policies table with all enterprise features
CREATE TABLE mcp_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Policy Identity
    policy_name VARCHAR(200) NOT NULL,
    policy_description TEXT,
    policy_version VARCHAR(20) DEFAULT '1.0',
    
    -- Scope
    server_patterns JSONB DEFAULT '[]',
    namespace_patterns JSONB DEFAULT '[]',
    verb_patterns JSONB DEFAULT '[]',
    resource_patterns JSONB DEFAULT '[]',
    
    -- Enterprise Policy Versioning Fields
    policy_status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, testing, approved, deployed, deprecated
    major_version INTEGER NOT NULL DEFAULT 1,
    minor_version INTEGER NOT NULL DEFAULT 0,
    patch_version INTEGER NOT NULL DEFAULT 0,
    version_hash VARCHAR(64),
    parent_policy_id UUID REFERENCES mcp_policies(id),
    deployment_timestamp TIMESTAMP WITH TIME ZONE,
    rollback_target_id UUID REFERENCES mcp_policies(id),
    
    -- Natural Language Policy Support
    natural_language_description TEXT,
    test_results JSONB,
    
    -- Enterprise Approval Workflow
    approval_required BOOLEAN NOT NULL DEFAULT true,
    approved_by VARCHAR(200),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Conditions
    conditions JSONB DEFAULT '{}',
    risk_threshold INTEGER DEFAULT 50,
    
    -- Actions
    action VARCHAR(50) DEFAULT 'EVALUATE', -- ALLOW, DENY, EVALUATE
    required_approval_level INTEGER DEFAULT 1,
    auto_approve_conditions JSONB DEFAULT '{}',
    
    -- Governance
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100,
    created_by VARCHAR(100) NOT NULL,
    
    -- Compliance
    compliance_framework VARCHAR(50), -- SOX, HIPAA, PCI, GDPR
    regulatory_reference VARCHAR(200),
    
    -- Performance
    execution_count INTEGER DEFAULT 0,
    last_triggered TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX idx_mcp_policies_status ON mcp_policies(policy_status, is_active);
CREATE INDEX idx_mcp_policies_created_by ON mcp_policies(created_by);
CREATE INDEX idx_mcp_policies_priority ON mcp_policies(priority DESC);
CREATE INDEX idx_mcp_policies_compliance ON mcp_policies(compliance_framework);
CREATE INDEX idx_mcp_policies_version ON mcp_policies(major_version, minor_version, patch_version);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_mcp_policies_updated_at 
    BEFORE UPDATE ON mcp_policies 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample policy for testing
INSERT INTO mcp_policies (
    policy_name,
    policy_description, 
    natural_language_description,
    created_by,
    policy_status,
    conditions,
    risk_threshold
) VALUES (
    'Database Access Control Policy',
    'Controls access to production databases with mandatory approval workflow',
    'If agent attempts to access production database, require Level 3 approval from database administrator',
    'admin@owkai.com',
    'approved',
    '{"environment": "production", "resource_type": "database", "operation": ["read", "write", "delete"]}',
    80
);

-- Verify table creation
SELECT 'MCP Policies table created successfully!' as result;
SELECT COUNT(*) as policy_count FROM mcp_policies;