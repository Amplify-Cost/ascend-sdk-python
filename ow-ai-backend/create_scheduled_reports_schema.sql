-- ============================================================================
-- SCHEDULED REPORTS SCHEMA
-- Enterprise-grade report scheduling system with execution tracking
-- ============================================================================

-- Main scheduled reports table
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    classification VARCHAR(100) DEFAULT 'Internal',

    -- Scheduling configuration
    frequency VARCHAR(50) NOT NULL,  -- Daily, Weekly, Bi-weekly, Monthly, Quarterly, Annual
    cron_expression VARCHAR(100),    -- For advanced scheduling (optional)
    day_of_week INTEGER,             -- 0-6 (0=Sunday) for weekly schedules
    day_of_month INTEGER,            -- 1-31 for monthly schedules
    time_of_day TIME NOT NULL,       -- HH:MM:SS execution time
    timezone VARCHAR(50) DEFAULT 'America/New_York',

    -- Distribution configuration
    recipients JSON NOT NULL,         -- Array of email addresses
    distribution_groups JSON,         -- Array of group names (optional)

    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,

    -- Metrics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,

    -- Notes and description
    description TEXT,

    CONSTRAINT valid_frequency CHECK (frequency IN ('Daily', 'Weekly', 'Bi-weekly', 'Monthly', 'Quarterly', 'Annual')),
    CONSTRAINT valid_day_of_week CHECK (day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)),
    CONSTRAINT valid_day_of_month CHECK (day_of_month IS NULL OR (day_of_month >= 1 AND day_of_month <= 31))
);

-- Execution history table
CREATE TABLE IF NOT EXISTS schedule_execution_history (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES scheduled_reports(id) ON DELETE CASCADE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,     -- Success, Failed, Retrying, Cancelled

    -- Generated report information
    report_id VARCHAR(255),           -- Link to enterprise_reports table
    file_size VARCHAR(50),
    page_count INTEGER,

    -- Execution details
    execution_duration_ms INTEGER,    -- Milliseconds to generate report
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    error_stack TEXT,

    -- Email delivery tracking
    emails_sent INTEGER DEFAULT 0,
    emails_failed INTEGER DEFAULT 0,
    delivery_status JSON,             -- Detailed email delivery status

    CONSTRAINT valid_status CHECK (status IN ('Success', 'Failed', 'Retrying', 'Cancelled'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_next_run ON scheduled_reports(next_run_at) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_created_by ON scheduled_reports(created_by);
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_template ON scheduled_reports(template_name);
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_active ON scheduled_reports(is_active);

CREATE INDEX IF NOT EXISTS idx_execution_history_schedule ON schedule_execution_history(schedule_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_executed_at ON schedule_execution_history(executed_at);
CREATE INDEX IF NOT EXISTS idx_execution_history_status ON schedule_execution_history(status);

-- Function to update next_run_at based on frequency
CREATE OR REPLACE FUNCTION calculate_next_run(
    p_frequency VARCHAR,
    p_last_run TIMESTAMP,
    p_day_of_week INTEGER,
    p_day_of_month INTEGER,
    p_time_of_day TIME
) RETURNS TIMESTAMP AS $$
DECLARE
    v_next_run TIMESTAMP;
    v_base_date TIMESTAMP;
BEGIN
    -- Use last run or current time as base
    v_base_date := COALESCE(p_last_run, NOW());

    CASE p_frequency
        WHEN 'Daily' THEN
            v_next_run := v_base_date + INTERVAL '1 day';

        WHEN 'Weekly' THEN
            v_next_run := v_base_date + INTERVAL '7 days';

        WHEN 'Bi-weekly' THEN
            v_next_run := v_base_date + INTERVAL '14 days';

        WHEN 'Monthly' THEN
            v_next_run := v_base_date + INTERVAL '1 month';

        WHEN 'Quarterly' THEN
            v_next_run := v_base_date + INTERVAL '3 months';

        WHEN 'Annual' THEN
            v_next_run := v_base_date + INTERVAL '1 year';

        ELSE
            v_next_run := v_base_date + INTERVAL '1 day';
    END CASE;

    -- Set time of day
    v_next_run := DATE_TRUNC('day', v_next_run) + p_time_of_day;

    RETURN v_next_run;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_scheduled_reports_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_scheduled_reports_timestamp
    BEFORE UPDATE ON scheduled_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduled_reports_timestamp();

-- Insert sample scheduled reports for demo
INSERT INTO scheduled_reports (
    name, template_name, report_type, classification,
    frequency, day_of_week, time_of_day, timezone,
    recipients, is_active, created_by, description,
    next_run_at
) VALUES
(
    'SOX Compliance Weekly Review',
    'SOX Compliance Report',
    'compliance',
    'Confidential',
    'Weekly',
    1,  -- Monday
    '09:00:00',
    'America/New_York',
    '["compliance@company.com", "cfo@company.com"]'::json,
    true,
    'admin@owkai.com',
    'Weekly SOX compliance status report for executive review',
    NOW() + INTERVAL '1 day'
),
(
    'User Risk Assessment Monthly',
    'Risk Assessment Report',
    'security',
    'Internal',
    'Monthly',
    NULL,
    '08:00:00',
    'America/New_York',
    '["security@company.com", "ciso@company.com"]'::json,
    true,
    'admin@owkai.com',
    'Monthly comprehensive user risk assessment and threat analysis',
    NOW() + INTERVAL '30 days'
),
(
    'HIPAA Compliance Quarterly',
    'HIPAA Security Assessment',
    'compliance',
    'Highly Confidential',
    'Quarterly',
    NULL,
    '10:00:00',
    'America/New_York',
    '["privacy@company.com", "compliance@company.com", "legal@company.com"]'::json,
    true,
    'admin@owkai.com',
    'Quarterly HIPAA security and privacy compliance assessment',
    NOW() + INTERVAL '90 days'
),
(
    'Executive Security Summary Daily',
    'Executive Summary Report',
    'executive',
    'Internal',
    'Daily',
    NULL,
    '07:00:00',
    'America/New_York',
    '["ceo@company.com", "ciso@company.com", "board@company.com"]'::json,
    true,
    'admin@owkai.com',
    'Daily executive security posture summary',
    NOW() + INTERVAL '1 day'
),
(
    'PCI DSS Annual Audit',
    'PCI DSS Compliance Report',
    'compliance',
    'Highly Confidential',
    'Annual',
    NULL,
    '09:00:00',
    'America/New_York',
    '["qsa@company.com", "compliance@company.com", "cfo@company.com"]'::json,
    true,
    'admin@owkai.com',
    'Annual PCI DSS compliance audit report for QSA review',
    NOW() + INTERVAL '365 days'
),
(
    'Threat Intelligence Brief Bi-weekly',
    'Threat Intelligence Brief',
    'security',
    'Confidential',
    'Bi-weekly',
    3,  -- Wednesday
    '11:00:00',
    'America/New_York',
    '["security-team@company.com", "soc@company.com"]'::json,
    true,
    'admin@owkai.com',
    'Bi-weekly threat intelligence and incident response briefing',
    NOW() + INTERVAL '14 days'
);

-- Insert sample execution history for demo
INSERT INTO schedule_execution_history (
    schedule_id, executed_at, status, report_id, file_size,
    page_count, execution_duration_ms, emails_sent
) VALUES
(1, NOW() - INTERVAL '7 days', 'Success', 'RPT-SOX-20251124-12345', '2.4 MB', 12, 3450, 2),
(1, NOW() - INTERVAL '14 days', 'Success', 'RPT-SOX-20251117-12344', '2.3 MB', 12, 3320, 2),
(1, NOW() - INTERVAL '21 days', 'Failed', NULL, NULL, NULL, 1250, 0),
(2, NOW() - INTERVAL '30 days', 'Success', 'RPT-RIS-20251031-12346', '3.1 MB', 10, 4120, 2),
(3, NOW() - INTERVAL '90 days', 'Success', 'RPT-HIP-20250901-12347', '4.5 MB', 15, 6230, 3),
(4, NOW() - INTERVAL '1 day', 'Success', 'RPT-EXE-20251130-12348', '1.2 MB', 3, 1890, 3),
(4, NOW() - INTERVAL '2 days', 'Success', 'RPT-EXE-20251129-12349', '1.2 MB', 3, 1920, 3);

COMMENT ON TABLE scheduled_reports IS 'Enterprise scheduled report configurations with CRUD operations';
COMMENT ON TABLE schedule_execution_history IS 'Execution history and audit trail for scheduled reports';
