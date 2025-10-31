-- Production Database Schema Fix
-- Fixes missing columns in agent_actions and ab_tests tables
-- Date: 2025-10-30

-- ==========================================
-- Fix 1: Add missing CVSS columns to agent_actions
-- ==========================================

ALTER TABLE agent_actions
ADD COLUMN IF NOT EXISTS cvss_score FLOAT,
ADD COLUMN IF NOT EXISTS cvss_severity VARCHAR(20),
ADD COLUMN IF NOT EXISTS cvss_vector VARCHAR(255);

-- Add index for CVSS score queries
CREATE INDEX IF NOT EXISTS idx_agent_actions_cvss_score ON agent_actions(cvss_score);
CREATE INDEX IF NOT EXISTS idx_agent_actions_cvss_severity ON agent_actions(cvss_severity);

COMMENT ON COLUMN agent_actions.cvss_score IS 'CVSS vulnerability score (0-10)';
COMMENT ON COLUMN agent_actions.cvss_severity IS 'CVSS severity rating (LOW, MEDIUM, HIGH, CRITICAL)';
COMMENT ON COLUMN agent_actions.cvss_vector IS 'CVSS vector string (e.g., CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N)';

-- ==========================================
-- Fix 2: Verify ab_tests table structure
-- ==========================================

-- Check if ab_tests table exists, if not create it
CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    description TEXT,
    base_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,
    variant_a_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,
    variant_b_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,
    traffic_split INTEGER DEFAULT 50 CHECK (traffic_split >= 0 AND traffic_split <= 100),
    duration_hours INTEGER DEFAULT 168,
    status VARCHAR(50) DEFAULT 'running',
    progress_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    variant_a_triggers INTEGER DEFAULT 0,
    variant_a_true_positives INTEGER DEFAULT 0,
    variant_a_false_positives INTEGER DEFAULT 0,
    variant_a_performance DECIMAL(5,2) DEFAULT 75.00,
    variant_b_triggers INTEGER DEFAULT 0,
    variant_b_true_positives INTEGER DEFAULT 0,
    variant_b_false_positives INTEGER DEFAULT 0,
    variant_b_performance DECIMAL(5,2) DEFAULT 80.00,
    winner VARCHAR(20),
    confidence_level INTEGER,
    statistical_significance VARCHAR(20) DEFAULT 'low',
    improvement VARCHAR(100),
    created_by VARCHAR(255),
    tenant_id VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW(),
    sample_size INTEGER DEFAULT 0
);

-- Add indexes for ab_tests
CREATE INDEX IF NOT EXISTS idx_ab_tests_test_id ON ab_tests(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created_by ON ab_tests(created_by);
CREATE INDEX IF NOT EXISTS idx_ab_tests_base_rule ON ab_tests(base_rule_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created_at ON ab_tests(created_at DESC);

-- ==========================================
-- Fix 3: Add A/B test tracking to alerts table
-- ==========================================

ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS ab_test_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS evaluated_by_variant VARCHAR(20),
ADD COLUMN IF NOT EXISTS variant_rule_id INTEGER,
ADD COLUMN IF NOT EXISTS detected_by_rule_id INTEGER,
ADD COLUMN IF NOT EXISTS detection_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS is_true_positive BOOLEAN DEFAULT NULL,
ADD COLUMN IF NOT EXISTS is_false_positive BOOLEAN DEFAULT FALSE;

-- Add indexes for alert AB test tracking
CREATE INDEX IF NOT EXISTS idx_alerts_ab_test_id ON alerts(ab_test_id);
CREATE INDEX IF NOT EXISTS idx_alerts_evaluated_by_variant ON alerts(evaluated_by_variant);
CREATE INDEX IF NOT EXISTS idx_alerts_variant_rule_id ON alerts(variant_rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_detected_by_rule_id ON alerts(detected_by_rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_is_true_positive ON alerts(is_true_positive);
CREATE INDEX IF NOT EXISTS idx_alerts_is_false_positive ON alerts(is_false_positive);

-- Add foreign key to ab_tests (only if ab_tests table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ab_tests') THEN
        ALTER TABLE alerts
        ADD CONSTRAINT fk_alerts_ab_test
        FOREIGN KEY (ab_test_id)
        REFERENCES ab_tests(test_id)
        ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN duplicate_object THEN
        NULL; -- Constraint already exists, ignore
END$$;

-- Add comments
COMMENT ON COLUMN alerts.ab_test_id IS 'UUID of A/B test that evaluated this alert';
COMMENT ON COLUMN alerts.evaluated_by_variant IS 'Which variant evaluated: variant_a or variant_b';
COMMENT ON COLUMN alerts.variant_rule_id IS 'ID of variant rule that evaluated this';
COMMENT ON COLUMN alerts.detection_time_ms IS 'Detection time in milliseconds';

-- ==========================================
-- Verification Queries
-- ==========================================

-- Verify agent_actions columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'agent_actions'
AND column_name IN ('cvss_score', 'cvss_severity', 'cvss_vector')
ORDER BY column_name;

-- Verify ab_tests table exists and has test_id column
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ab_tests'
AND column_name IN ('test_id', 'sample_size', 'tenant_id')
ORDER BY column_name;

-- Verify alerts AB test tracking columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'alerts'
AND column_name IN ('ab_test_id', 'evaluated_by_variant', 'detection_time_ms')
ORDER BY column_name;

-- Show summary
SELECT
    'agent_actions' as table_name,
    COUNT(*) FILTER (WHERE column_name IN ('cvss_score', 'cvss_severity', 'cvss_vector')) as cvss_columns_present
FROM information_schema.columns
WHERE table_name = 'agent_actions'
UNION ALL
SELECT
    'ab_tests' as table_name,
    COUNT(*) FILTER (WHERE column_name IN ('test_id', 'sample_size')) as key_columns_present
FROM information_schema.columns
WHERE table_name = 'ab_tests'
UNION ALL
SELECT
    'alerts' as table_name,
    COUNT(*) FILTER (WHERE column_name IN ('ab_test_id', 'evaluated_by_variant')) as ab_test_columns_present
FROM information_schema.columns
WHERE table_name = 'alerts';
