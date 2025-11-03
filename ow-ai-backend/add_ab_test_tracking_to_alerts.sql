-- Migration: Add A/B Test Tracking to Alerts
-- Date: 2025-10-30
-- Purpose: Track which A/B test variant evaluated each alert for real metrics

-- Add A/B test tracking columns to alerts table
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS ab_test_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS evaluated_by_variant VARCHAR(20),  -- 'variant_a' or 'variant_b'
ADD COLUMN IF NOT EXISTS variant_rule_id INTEGER,
ADD COLUMN IF NOT EXISTS detected_by_rule_id INTEGER,
ADD COLUMN IF NOT EXISTS detection_time_ms INTEGER,  -- Response time in milliseconds
ADD COLUMN IF NOT EXISTS is_true_positive BOOLEAN DEFAULT NULL,  -- NULL = not yet determined
ADD COLUMN IF NOT EXISTS is_false_positive BOOLEAN DEFAULT FALSE;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_ab_test_id ON alerts(ab_test_id);
CREATE INDEX IF NOT EXISTS idx_alerts_evaluated_by_variant ON alerts(evaluated_by_variant);
CREATE INDEX IF NOT EXISTS idx_alerts_variant_rule_id ON alerts(variant_rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_detected_by_rule_id ON alerts(detected_by_rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_is_true_positive ON alerts(is_true_positive);
CREATE INDEX IF NOT EXISTS idx_alerts_is_false_positive ON alerts(is_false_positive);

-- Add foreign key to ab_tests table
ALTER TABLE alerts
ADD CONSTRAINT fk_alerts_ab_test
FOREIGN KEY (ab_test_id)
REFERENCES ab_tests(test_id)
ON DELETE SET NULL;

-- Comment for documentation
COMMENT ON COLUMN alerts.ab_test_id IS 'UUID of A/B test that evaluated this alert (NULL if not part of test)';
COMMENT ON COLUMN alerts.evaluated_by_variant IS 'Which variant evaluated this alert: variant_a or variant_b';
COMMENT ON COLUMN alerts.variant_rule_id IS 'ID of variant rule that evaluated this alert';
COMMENT ON COLUMN alerts.detected_by_rule_id IS 'ID of rule that detected this alert (may differ from variant_rule_id)';
COMMENT ON COLUMN alerts.detection_time_ms IS 'Time taken to detect and evaluate alert in milliseconds';
COMMENT ON COLUMN alerts.is_true_positive IS 'Whether this alert was a true positive (NULL = not yet determined)';
COMMENT ON COLUMN alerts.is_false_positive IS 'Whether this alert was a false positive';
