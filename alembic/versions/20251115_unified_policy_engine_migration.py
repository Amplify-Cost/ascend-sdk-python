"""Unified Policy Engine Migration - Add policy fusion fields to mcp_actions

Revision ID: 20251115_unified
Revises: 202511121500_merge_heads
Create Date: 2025-11-15 14:00:00.000000

🏢 ENTERPRISE: Unified Policy Engine Architecture
- Adds Option 4 policy fusion fields to mcp_actions table
- Adds MCP-specific fields (namespace, verb)
- Adds user context and approval workflow fields
- Enables both agent and MCP actions to use same policy engine

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251115_unified'
down_revision = '91e6b34f6aea'  # Latest production migration
branch_labels = None
depends_on = None


def upgrade():
    """
    🏢 ENTERPRISE MIGRATION: Unified Policy Engine Support

    Adds all required fields to mcp_actions table to support:
    1. Option 4 Policy Fusion (policy_evaluated, policy_decision, policy_risk_score)
    2. MCP Protocol fields (namespace, verb)
    3. User context (user_email, user_role, created_by)
    4. Approval workflow (approved_by, approved_at, reviewed_by, reviewed_at)
    5. Risk scoring standardization (risk_score as FLOAT)

    All columns are NULLABLE for backward compatibility.
    """

    # ========== OPTION 4 POLICY FUSION FIELDS ==========
    # These enable unified policy engine evaluation for MCP actions

    op.add_column('mcp_actions', sa.Column(
        'policy_evaluated',
        sa.Boolean(),
        server_default=sa.false(),
        nullable=True,
        comment='True if EnterpriseRealTimePolicyEngine evaluated this action'
    ))

    op.add_column('mcp_actions', sa.Column(
        'policy_decision',
        sa.String(50),
        nullable=True,
        comment='Policy engine decision: ALLOW|DENY|REQUIRE_APPROVAL|ESCALATE|CONDITIONAL'
    ))

    op.add_column('mcp_actions', sa.Column(
        'policy_risk_score',
        sa.Integer(),
        nullable=True,
        comment='0-100 policy engine risk score (4-category comprehensive)'
    ))

    op.add_column('mcp_actions', sa.Column(
        'risk_fusion_formula',
        sa.Text(),
        nullable=True,
        comment='Formula used for risk fusion (e.g., hybrid_80_20_policy_75)'
    ))

    # ========== MCP PROTOCOL FIELDS ==========
    # Required for policy engine pattern matching

    op.add_column('mcp_actions', sa.Column(
        'namespace',
        sa.String(100),
        nullable=True,
        comment='MCP namespace (e.g., filesystem, database, tools)'
    ))

    op.add_column('mcp_actions', sa.Column(
        'verb',
        sa.String(100),
        nullable=True,
        comment='MCP verb/action (e.g., read_file, write_file, execute)'
    ))

    # ========== USER CONTEXT FIELDS ==========
    # Required for policy evaluation context

    op.add_column('mcp_actions', sa.Column(
        'user_email',
        sa.String(255),
        nullable=True,
        comment='Email of user who initiated the action'
    ))

    op.add_column('mcp_actions', sa.Column(
        'user_role',
        sa.String(100),
        nullable=True,
        comment='Role of user (for policy condition evaluation)'
    ))

    op.add_column('mcp_actions', sa.Column(
        'created_by',
        sa.String(255),
        nullable=True,
        comment='Email/username of creator (for audit trail)'
    ))

    # ========== APPROVAL WORKFLOW FIELDS ==========
    # Required for unified authorization center

    op.add_column('mcp_actions', sa.Column(
        'approved_by',
        sa.String(255),
        nullable=True,
        comment='Email of approver'
    ))

    op.add_column('mcp_actions', sa.Column(
        'approved_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Timestamp when action was approved'
    ))

    op.add_column('mcp_actions', sa.Column(
        'reviewed_by',
        sa.String(255),
        nullable=True,
        comment='Email of reviewer'
    ))

    op.add_column('mcp_actions', sa.Column(
        'reviewed_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Timestamp when action was reviewed'
    ))

    # ========== RISK SCORING STANDARDIZATION ==========
    # Standardize on FLOAT (0.0-100.0) to match agent_actions

    op.add_column('mcp_actions', sa.Column(
        'risk_score',
        sa.Float(),
        nullable=True,
        comment='0-100 comprehensive risk score (matches agent_actions type)'
    ))

    # ========== DATA BACKFILL ==========
    # Backfill namespace and verb from context JSONB (if available)

    op.execute("""
        UPDATE mcp_actions
        SET
            namespace = COALESCE(context->>'namespace', 'unknown'),
            verb = COALESCE(context->>'verb', action_type),
            created_by = COALESCE(context->>'user_email', 'system')
        WHERE context IS NOT NULL
    """)

    # For rows without context, set sensible defaults
    op.execute("""
        UPDATE mcp_actions
        SET
            namespace = 'unknown',
            verb = action_type,
            created_by = 'system'
        WHERE namespace IS NULL OR verb IS NULL
    """)

    # ========== INDEXES FOR PERFORMANCE ==========
    # Add indexes for common query patterns

    op.create_index(
        'idx_mcp_actions_policy_evaluated',
        'mcp_actions',
        ['policy_evaluated', 'status'],
        unique=False
    )

    op.create_index(
        'idx_mcp_actions_namespace_verb',
        'mcp_actions',
        ['namespace', 'verb'],
        unique=False
    )

    op.create_index(
        'idx_mcp_actions_user_email',
        'mcp_actions',
        ['user_email', 'created_at'],
        unique=False
    )

    print("✅ ENTERPRISE MIGRATION COMPLETE: mcp_actions table now supports unified policy engine")


def downgrade():
    """
    Rollback migration - removes all added columns and indexes.

    WARNING: This will drop policy evaluation data!
    """

    # Drop indexes
    op.drop_index('idx_mcp_actions_user_email', table_name='mcp_actions')
    op.drop_index('idx_mcp_actions_namespace_verb', table_name='mcp_actions')
    op.drop_index('idx_mcp_actions_policy_evaluated', table_name='mcp_actions')

    # Drop policy fusion fields
    op.drop_column('mcp_actions', 'policy_evaluated')
    op.drop_column('mcp_actions', 'policy_decision')
    op.drop_column('mcp_actions', 'policy_risk_score')
    op.drop_column('mcp_actions', 'risk_fusion_formula')

    # Drop MCP protocol fields
    op.drop_column('mcp_actions', 'namespace')
    op.drop_column('mcp_actions', 'verb')

    # Drop user context fields
    op.drop_column('mcp_actions', 'user_email')
    op.drop_column('mcp_actions', 'user_role')
    op.drop_column('mcp_actions', 'created_by')

    # Drop approval workflow fields
    op.drop_column('mcp_actions', 'approved_by')
    op.drop_column('mcp_actions', 'approved_at')
    op.drop_column('mcp_actions', 'reviewed_by')
    op.drop_column('mcp_actions', 'reviewed_at')

    # Drop risk score standardization
    op.drop_column('mcp_actions', 'risk_score')

    print("⚠️  ROLLBACK COMPLETE: mcp_actions table reverted to original schema")
