# File: ow-ai-backend/models_playbook_versioning.py
# Enterprise Playbook Versioning Models
# ============================================================================
"""
🏢 ENTERPRISE PLAYBOOK VERSIONING SYSTEM

Phase 3 Feature: Playbook Version Control & History

Business Value:
- Audit trail for all playbook changes
- Rollback capability for failed updates
- Compliance documentation (SOX, PCI-DSS)
- Team collaboration with change tracking
- A/B testing for playbook optimization

Author: Donald King (OW-kai Enterprise)
Date: 2025-11-18
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database import Base


class PlaybookVersion(Base):
    """
    🏢 ENTERPRISE PLAYBOOK VERSION HISTORY

    Tracks every change to automation playbooks with full audit trail.
    Enables rollback, comparison, and compliance documentation.

    Pattern: GitLab CI/CD Version Control
    Compliance: SOX Section 404 (change management)
    """
    __tablename__ = "playbook_versions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Playbook reference
    playbook_id = Column(String(255), ForeignKey('automation_playbooks.id', ondelete='CASCADE'), nullable=False, index=True)

    # Version metadata
    version_number = Column(Integer, nullable=False)  # Incremental version (1, 2, 3, ...)
    version_tag = Column(String(100), nullable=True)  # Optional: "v1.0", "stable", "beta"
    is_current = Column(Boolean, default=False, index=True)  # Only one current version per playbook

    # Snapshot of playbook configuration at this version
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False)  # active|inactive|disabled
    risk_level = Column(String(50), nullable=False)
    approval_required = Column(Boolean, nullable=False)
    trigger_conditions = Column(JSON, nullable=False)  # Full snapshot
    actions = Column(JSON, nullable=False)  # Full snapshot

    # Change tracking
    change_summary = Column(Text)  # Human-readable change description
    change_type = Column(String(50), default='UPDATE')  # CREATE|UPDATE|ROLLBACK|CLONE
    changed_fields = Column(JSON, default=list)  # List of field names changed
    diff_details = Column(JSON, nullable=True)  # Detailed before/after diff

    # Audit metadata
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Performance tracking for this version
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_execution_time = Column(Float, nullable=True)  # Seconds

    # Rollback tracking
    rolled_back_at = Column(DateTime, nullable=True)
    rolled_back_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    rollback_reason = Column(Text, nullable=True)

    # Relationships
    playbook = relationship("AutomationPlaybook", foreign_keys=[playbook_id])

    # Composite index for fast version lookups
    __table_args__ = (
        Index('ix_playbook_version_lookup', 'playbook_id', 'version_number'),
        Index('ix_playbook_current_version', 'playbook_id', 'is_current'),
    )


class PlaybookExecutionLog(Base):
    """
    🏢 ENTERPRISE EXECUTION ANALYTICS LOG

    Enhanced execution tracking with performance metrics and analytics.
    Extends PlaybookExecution with Phase 3 analytics capabilities.

    Pattern: Splunk SOAR Analytics Dashboard
    """
    __tablename__ = "playbook_execution_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # References
    playbook_id = Column(String(255), ForeignKey('automation_playbooks.id'), nullable=False, index=True)
    playbook_version_id = Column(Integer, ForeignKey('playbook_versions.id'), nullable=True, index=True)
    execution_id = Column(Integer, ForeignKey('playbook_executions.id'), nullable=True, index=True)

    # Execution context
    triggered_by_action_id = Column(Integer, ForeignKey('agent_actions.id'), nullable=True, index=True)
    execution_mode = Column(String(50), default='automatic')  # automatic|manual|scheduled|dry_run

    # Timing metrics
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Milliseconds for precision

    # Step-by-step execution tracking
    steps_executed = Column(JSON, default=list)  # List of action steps with timestamps
    steps_total = Column(Integer, default=0)
    steps_successful = Column(Integer, default=0)
    steps_failed = Column(Integer, default=0)

    # Result tracking
    execution_status = Column(String(50), index=True)  # pending|running|completed|failed|partial
    final_action = Column(String(100))  # What action was ultimately taken (approve|deny|escalate|notify)
    error_message = Column(Text, nullable=True)
    error_stack = Column(Text, nullable=True)

    # Performance metrics
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    api_calls_made = Column(Integer, default=0)

    # Input/Output data
    input_snapshot = Column(JSON)  # Snapshot of trigger data
    output_result = Column(JSON)  # Final result data

    # User context
    executed_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Analytics flags
    was_successful = Column(Boolean, index=True)
    cost_impact = Column(Float, nullable=True)  # Dollar value impact (savings or cost)

    # Indexes for analytics queries
    __table_args__ = (
        Index('ix_execution_analytics', 'playbook_id', 'started_at', 'execution_status'),
        Index('ix_execution_performance', 'playbook_id', 'was_successful', 'duration_ms'),
    )


class PlaybookSchedule(Base):
    """
    🏢 ENTERPRISE PLAYBOOK SCHEDULING

    Phase 3: Time-based and event-based playbook execution scheduling.

    Business Value:
    - Automated maintenance windows
    - Off-hours processing
    - Compliance reporting automation
    - Proactive risk mitigation

    Pattern: Ansible Tower Scheduled Jobs
    """
    __tablename__ = "playbook_schedules"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Playbook reference
    playbook_id = Column(String(255), ForeignKey('automation_playbooks.id'), nullable=False, index=True)

    # Schedule configuration
    schedule_name = Column(String(255), nullable=False)
    schedule_type = Column(String(50), nullable=False, index=True)  # cron|interval|one_time|event_based

    # Cron expression (for cron-based schedules)
    cron_expression = Column(String(100), nullable=True)  # e.g., "0 2 * * *" (daily at 2am)

    # Interval (for interval-based schedules)
    interval_minutes = Column(Integer, nullable=True)  # Run every N minutes

    # One-time execution
    scheduled_for = Column(DateTime, nullable=True)  # Specific datetime for one-time execution

    # Event-based triggers
    event_type = Column(String(100), nullable=True)  # e.g., "high_risk_spike", "after_hours_activity"
    event_conditions = Column(JSON, nullable=True)  # Conditions to trigger execution

    # Status and control
    is_active = Column(Boolean, default=True, index=True)
    is_paused = Column(Boolean, default=False)

    # Execution window
    start_time = Column(String(10), nullable=True)  # HH:MM format for daily window start
    end_time = Column(String(10), nullable=True)  # HH:MM format for daily window end
    timezone = Column(String(50), default='UTC')  # Timezone for schedule

    # Execution limits
    max_executions = Column(Integer, nullable=True)  # Stop after N executions
    executions_remaining = Column(Integer, nullable=True)

    # Last execution tracking
    last_executed_at = Column(DateTime, nullable=True)
    last_execution_status = Column(String(50), nullable=True)
    next_execution_at = Column(DateTime, nullable=True, index=True)

    # Audit fields
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    playbook = relationship("AutomationPlaybook", foreign_keys=[playbook_id])


class PlaybookTemplate(Base):
    """
    🏢 ENTERPRISE PLAYBOOK TEMPLATE LIBRARY

    Phase 3: Shareable playbook templates with import/export capability.

    Business Value:
    - Knowledge sharing across teams
    - Best practice distribution
    - Rapid deployment
    - Consistent governance patterns

    Pattern: Terraform Module Registry
    """
    __tablename__ = "playbook_templates"

    # Primary key
    id = Column(String(255), primary_key=True, index=True)  # e.g., "template-auto-approve-low"

    # Template metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # productivity|security|compliance|cost

    # Template configuration
    trigger_conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)

    # Template properties
    complexity = Column(String(50), default='medium')  # low|medium|high
    estimated_savings_per_month = Column(Float, nullable=True)
    use_case = Column(Text)

    # Usage tracking
    times_used = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)  # From instances created
    average_rating = Column(Float, nullable=True)  # User ratings

    # Visibility and access
    is_public = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Verified by platform team
    industry_tags = Column(JSON, default=list)  # e.g., ["finance", "healthcare"]

    # Version and maintenance
    template_version = Column(String(50), default='1.0')
    last_updated = Column(DateTime, default=lambda: datetime.now(UTC))

    # Audit
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Indexes
    __table_args__ = (
        Index('ix_template_category', 'category', 'is_public'),
        Index('ix_template_usage', 'times_used', 'average_rating'),
    )
