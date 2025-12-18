"""DEEP-002: Add Python Dynamic Code Patterns (PY-004 to PY-007)

Adds new security patterns for detecting dangerous Python constructs:
- PY-004: Dynamic import detection (__import__, importlib, compile)
- PY-005: Sandbox escape detection (dunder attributes)
- PY-006: File access in dynamic code (open, io module)
- PY-007: Network access in dynamic code (socket, requests, etc.)

These patterns complement the existing PY-001 (eval/exec) and PY-002/003
(subprocess/os.system) patterns with more comprehensive detection.

Revision ID: deep002_python_patterns
Revises: behav001_rate_limits
Create Date: 2025-12-18

Compliance: CWE-94, CWE-95, CWE-22, CWE-918, MITRE T1059.006, NIST SI-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'deep002_python_patterns'
down_revision = 'behav001_rate_limits'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # Add new Python patterns (PY-004 to PY-007)
    # ========================================================================
    # These extend the existing Phase 9 patterns with more comprehensive
    # detection for dynamic code execution scenarios

    op.execute("""
        INSERT INTO global_code_patterns (
            pattern_id, language, category, severity, pattern_type, pattern_value,
            pattern_flags, description, recommendation,
            cwe_ids, mitre_techniques, cvss_base_score, cvss_vector,
            is_active, version
        ) VALUES
        -- PY-004: Dynamic import detection
        (
            'PY-004',
            'python',
            'code_injection',
            'critical',
            'regex',
            '(__import__|importlib\\.import_module|compile)\\s*\\(',
            'IGNORECASE',
            'Dynamic import or code compilation detected. These functions can load and execute arbitrary code.',
            'Use explicit imports. If dynamic imports are required, validate module names against an allowlist.',
            ARRAY['CWE-94', 'CWE-95'],
            ARRAY['T1059.006'],
            9.8,
            'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H',
            true,
            1
        ),
        -- PY-005: Sandbox escape detection
        (
            'PY-005',
            'python',
            'sandbox_escape',
            'critical',
            'regex',
            '(__builtins__|__globals__|__code__|__class__|__bases__|__mro__|__subclasses__)',
            'IGNORECASE',
            'Access to Python internal attributes detected. These can be used to escape sandboxes and access restricted functionality.',
            'Never allow access to dunder attributes in user-provided code. Use AST analysis to detect these patterns.',
            ARRAY['CWE-94'],
            ARRAY['T1059.006'],
            9.5,
            'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:N',
            true,
            1
        ),
        -- PY-006: File access in dynamic code
        (
            'PY-006',
            'python',
            'file_access',
            'high',
            'regex',
            '(open\\s*\\(|file\\s*\\(|io\\.(open|BytesIO|StringIO)|pathlib\\.Path)',
            'IGNORECASE',
            'File system access detected in code. This can lead to unauthorized file reads or writes.',
            'Validate file paths against an allowlist. Use chroot or container isolation for file operations.',
            ARRAY['CWE-22', 'CWE-73'],
            ARRAY['T1083'],
            7.5,
            'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N',
            true,
            1
        ),
        -- PY-007: Network access in dynamic code
        (
            'PY-007',
            'python',
            'network_access',
            'high',
            'regex',
            '(socket\\.|urllib\\.|requests\\.|httpx\\.|aiohttp\\.|http\\.client)',
            'IGNORECASE',
            'Network access detected in code. This can be used for data exfiltration or SSRF attacks.',
            'Block network access in evaluated code. If required, use a proxy with strict URL allowlisting.',
            ARRAY['CWE-918', 'CWE-200'],
            ARRAY['T1071', 'T1048'],
            7.0,
            'CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N',
            true,
            1
        )
        ON CONFLICT (pattern_id) DO UPDATE SET
            category = EXCLUDED.category,
            severity = EXCLUDED.severity,
            pattern_value = EXCLUDED.pattern_value,
            description = EXCLUDED.description,
            recommendation = EXCLUDED.recommendation,
            cwe_ids = EXCLUDED.cwe_ids,
            mitre_techniques = EXCLUDED.mitre_techniques,
            cvss_base_score = EXCLUDED.cvss_base_score,
            cvss_vector = EXCLUDED.cvss_vector,
            version = global_code_patterns.version + 1,
            updated_at = NOW();
    """)

    # Log the pattern additions
    op.execute("""
        INSERT INTO code_pattern_audit_log (
            organization_id, user_id, user_email,
            action, resource_type, resource_id,
            new_value, change_reason, created_at
        )
        SELECT
            NULL,  -- System-level change
            NULL,
            'system@ascend.ai',
            'created',
            'global_pattern',
            pattern_id,
            jsonb_build_object(
                'pattern_id', pattern_id,
                'category', category,
                'severity', severity,
                'cvss_base_score', cvss_base_score
            ),
            'DEEP-002: Added Python dynamic code patterns for enhanced security detection',
            NOW()
        FROM global_code_patterns
        WHERE pattern_id IN ('PY-004', 'PY-005', 'PY-006', 'PY-007');
    """)


def downgrade():
    # Deactivate patterns (don't delete, for audit trail)
    op.execute("""
        UPDATE global_code_patterns
        SET is_active = false, updated_at = NOW()
        WHERE pattern_id IN ('PY-004', 'PY-005', 'PY-006', 'PY-007');
    """)

    # Log the deactivation
    op.execute("""
        INSERT INTO code_pattern_audit_log (
            organization_id, user_id, user_email,
            action, resource_type, resource_id,
            old_value, change_reason, created_at
        )
        SELECT
            NULL,
            NULL,
            'system@ascend.ai',
            'disabled',
            'global_pattern',
            pattern_id,
            jsonb_build_object(
                'pattern_id', pattern_id,
                'reason', 'Downgrade: DEEP-002 rollback'
            ),
            'DEEP-002: Rollback - Deactivated Python dynamic code patterns',
            NOW()
        FROM global_code_patterns
        WHERE pattern_id IN ('PY-004', 'PY-005', 'PY-006', 'PY-007');
    """)
