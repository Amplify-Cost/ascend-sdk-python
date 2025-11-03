-- Enterprise A/B Testing Table Schema
-- Created: 2025-10-30
-- Purpose: Store real A/B tests with performance tracking

CREATE TABLE IF NOT EXISTS ab_tests (
    -- Primary identification
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Rule references
    base_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,
    variant_a_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,
    variant_b_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,

    -- Test configuration
    traffic_split INTEGER DEFAULT 50 CHECK (traffic_split >= 0 AND traffic_split <= 100),
    duration_hours INTEGER DEFAULT 168,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'running',
    progress_percentage INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Performance metrics (calculated from alerts)
    variant_a_triggers INTEGER DEFAULT 0,
    variant_a_true_positives INTEGER DEFAULT 0,
    variant_a_false_positives INTEGER DEFAULT 0,
    variant_a_performance DECIMAL(5,2) DEFAULT 75.00,

    variant_b_triggers INTEGER DEFAULT 0,
    variant_b_true_positives INTEGER DEFAULT 0,
    variant_b_false_positives INTEGER DEFAULT 0,
    variant_b_performance DECIMAL(5,2) DEFAULT 80.00,

    -- Results
    winner VARCHAR(20),
    confidence_level INTEGER,
    statistical_significance VARCHAR(20) DEFAULT 'low',
    improvement VARCHAR(100),

    -- Audit trail
    created_by VARCHAR(255),
    tenant_id VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_tests_base_rule ON ab_tests(base_rule_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created_by ON ab_tests(created_by);
CREATE INDEX IF NOT EXISTS idx_ab_tests_test_id ON ab_tests(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created_at ON ab_tests(created_at DESC);

-- Comments for documentation
COMMENT ON TABLE ab_tests IS 'Enterprise A/B testing for security rules with real performance tracking';
COMMENT ON COLUMN ab_tests.test_id IS 'Unique UUID for test identification';
COMMENT ON COLUMN ab_tests.base_rule_id IS 'Original rule being tested';
COMMENT ON COLUMN ab_tests.variant_a_rule_id IS 'Control variant (clone of original)';
COMMENT ON COLUMN ab_tests.variant_b_rule_id IS 'Test variant (optimized version)';
COMMENT ON COLUMN ab_tests.traffic_split IS 'Percentage of traffic to variant A (0-100)';
COMMENT ON COLUMN ab_tests.duration_hours IS 'Planned test duration in hours';
COMMENT ON COLUMN ab_tests.variant_a_performance IS 'Detection accuracy percentage for variant A';
COMMENT ON COLUMN ab_tests.variant_b_performance IS 'Detection accuracy percentage for variant B';
