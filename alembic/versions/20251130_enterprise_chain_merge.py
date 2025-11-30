"""SEC-022: Enterprise Migration Chain Consolidation

Revision ID: 20251130_enterprise_merge
Revises: 20251128_integration_suite, 20251127_email_audit
Create Date: 2025-11-30

This merge migration consolidates two parallel branches that both
originated from 20251126_tenant_isolation:

Branch A (Main Integration Chain):
  20251126_tenant_isolation
    → 20251128_webhooks (Phase 1)
    → 20251128_notifications (Phase 2)
    → 20251128_servicenow (Phase 3)
    → 20251128_compliance_export (Phase 4)
    → 20251128_integration_suite (Phase 5)

Branch B (Email Audit):
  20251126_tenant_isolation
    → 20251127_email_audit

This migration merges both branches into a single head, ensuring
proper migration ordering in production deployments.

Banking-Level Security:
- Consolidates all enterprise migrations under single head
- Ensures deterministic migration ordering
- Supports rollback capability

Compliance: SOC 2 CC6.1 (Change Management), SOX (Audit Controls)
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20251130_enterprise_merge'
down_revision: Union[str, Sequence[str], None] = ('20251128_integration_suite', '20251127_email_audit')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Merge migration - no schema changes required.
    This migration exists solely to consolidate multiple heads.
    """
    pass


def downgrade() -> None:
    """
    Merge migration - no schema changes to revert.
    """
    pass
