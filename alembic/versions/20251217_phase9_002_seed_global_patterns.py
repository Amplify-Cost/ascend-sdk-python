"""Phase 9: Seed Global Code Patterns

Seeds the global_code_patterns table with initial 16 enterprise patterns.

These patterns are vendor-managed (ASCEND maintains them).
Customers can override or disable via org_pattern_overrides table.

Pattern Categories:
- SQL: data_destruction, privilege_escalation, injection
- Python: code_execution
- Shell: data_destruction, code_execution, privilege_escalation, data_exfiltration
- Any: credential_exposure

Compliance: SOC 2, PCI-DSS 6.5, HIPAA, NIST 800-53 SI-10

Revision ID: phase9_002_seed_patterns
Revises: phase9_001_code_analysis
Create Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, UTC

# revision identifiers, used by Alembic.
revision = 'phase9_002_seed_patterns'
down_revision = 'phase9_001_code_analysis'
branch_labels = None
depends_on = None

# Global patterns to seed
GLOBAL_PATTERNS = [
    # ========================================================================
    # SQL PATTERNS - Data Destruction
    # ========================================================================
    {
        "pattern_id": "SQL-001",
        "language": "sql",
        "category": "data_destruction",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|PROCEDURE|FUNCTION)\s+\w+",
        "pattern_flags": "IGNORECASE",
        "description": "Destructive SQL operation that permanently removes database objects",
        "recommendation": "Use soft delete (SET deleted_at = NOW()) or require explicit approval workflow",
        "cwe_ids": ["CWE-89", "CWE-1321"],
        "mitre_techniques": ["T1485", "T1565.001"],
        "cvss_base_score": 9.1,
    },
    {
        "pattern_id": "SQL-002",
        "language": "sql",
        "category": "data_destruction",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"\bDELETE\s+FROM\s+\w+\s*($|;|WHERE\s+(1\s*=\s*1|true|'[^']*'\s*=\s*'[^']*'))",
        "pattern_flags": "IGNORECASE",
        "description": "DELETE without WHERE clause or with always-true condition (mass deletion)",
        "recommendation": "Always specify a WHERE clause with specific conditions; use LIMIT for safety",
        "cwe_ids": ["CWE-89"],
        "mitre_techniques": ["T1485"],
        "cvss_base_score": 9.1,
    },
    {
        "pattern_id": "SQL-003",
        "language": "sql",
        "category": "data_destruction",
        "severity": "high",
        "pattern_type": "regex",
        "pattern_value": r"\bUPDATE\s+\w+\s+SET\s+.+($|;|WHERE\s+(1\s*=\s*1|true))",
        "pattern_flags": "IGNORECASE",
        "description": "UPDATE without WHERE clause or with always-true condition (mass update)",
        "recommendation": "Always specify a WHERE clause with specific conditions",
        "cwe_ids": ["CWE-89"],
        "mitre_techniques": ["T1565.001"],
        "cvss_base_score": 7.5,
    },

    # ========================================================================
    # SQL PATTERNS - Privilege Escalation
    # ========================================================================
    {
        "pattern_id": "SQL-004",
        "language": "sql",
        "category": "privilege_escalation",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"\b(GRANT|REVOKE)\s+(ALL|SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|EXECUTE)\s+(PRIVILEGES?\s+)?ON",
        "pattern_flags": "IGNORECASE",
        "description": "Database privilege modification that could escalate access",
        "recommendation": "Privilege changes require approval from database administrator",
        "cwe_ids": ["CWE-269", "CWE-250"],
        "mitre_techniques": ["T1078.004", "T1548"],
        "cvss_base_score": 8.8,
    },
    {
        "pattern_id": "SQL-005",
        "language": "sql",
        "category": "privilege_escalation",
        "severity": "high",
        "pattern_type": "regex",
        "pattern_value": r"\b(CREATE|ALTER|DROP)\s+(USER|ROLE|LOGIN)\b",
        "pattern_flags": "IGNORECASE",
        "description": "User/role management operation that modifies database access",
        "recommendation": "User management requires approval from security administrator",
        "cwe_ids": ["CWE-269"],
        "mitre_techniques": ["T1136.002"],
        "cvss_base_score": 7.2,
    },

    # ========================================================================
    # SQL PATTERNS - Injection
    # ========================================================================
    {
        "pattern_id": "SQL-006",
        "language": "sql",
        "category": "injection",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"('\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d*|--\s*$|;\s*--)",
        "pattern_flags": "IGNORECASE",
        "description": "SQL injection pattern (tautology or comment-based)",
        "recommendation": "Use parameterized queries; never concatenate user input into SQL",
        "cwe_ids": ["CWE-89", "CWE-943"],
        "mitre_techniques": ["T1190", "T1059.007"],
        "cvss_base_score": 9.8,
    },
    {
        "pattern_id": "SQL-007",
        "language": "sql",
        "category": "injection",
        "severity": "high",
        "pattern_type": "regex",
        "pattern_value": r"\bUNION\s+(ALL\s+)?SELECT\b",
        "pattern_flags": "IGNORECASE",
        "description": "UNION-based SQL injection pattern",
        "recommendation": "Use parameterized queries; validate and sanitize all inputs",
        "cwe_ids": ["CWE-89"],
        "mitre_techniques": ["T1190"],
        "cvss_base_score": 8.6,
    },

    # ========================================================================
    # PYTHON PATTERNS - Code Execution
    # ========================================================================
    {
        "pattern_id": "PY-001",
        "language": "python",
        "category": "code_execution",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"\b(eval|exec)\s*\(",
        "pattern_flags": None,
        "description": "Dynamic code execution that can run arbitrary Python code",
        "recommendation": "Use ast.literal_eval() for data parsing; avoid dynamic execution entirely",
        "cwe_ids": ["CWE-94", "CWE-95"],
        "mitre_techniques": ["T1059.006"],
        "cvss_base_score": 9.8,
    },
    {
        "pattern_id": "PY-002",
        "language": "python",
        "category": "code_execution",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"\bsubprocess\s*\.\s*(call|run|Popen|check_output|check_call)\s*\([^)]*shell\s*=\s*True",
        "pattern_flags": None,
        "description": "Shell command execution with shell=True enables command injection",
        "recommendation": "Use subprocess with shell=False and pass arguments as a list",
        "cwe_ids": ["CWE-78", "CWE-77"],
        "mitre_techniques": ["T1059.004"],
        "cvss_base_score": 9.8,
    },
    {
        "pattern_id": "PY-003",
        "language": "python",
        "category": "code_execution",
        "severity": "high",
        "pattern_type": "regex",
        "pattern_value": r"\b(os\.system|os\.popen|commands\.getoutput)\s*\(",
        "pattern_flags": None,
        "description": "Legacy shell command execution functions vulnerable to injection",
        "recommendation": "Use subprocess module with shell=False instead",
        "cwe_ids": ["CWE-78"],
        "mitre_techniques": ["T1059.004"],
        "cvss_base_score": 8.8,
    },

    # ========================================================================
    # SHELL PATTERNS - Dangerous Commands
    # ========================================================================
    {
        "pattern_id": "SH-001",
        "language": "shell",
        "category": "data_destruction",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"\brm\s+(-[rRfF]+\s+)*(/|\*|~|\$HOME|\$\{?HOME\}?)",
        "pattern_flags": None,
        "description": "Recursive file deletion targeting root, home, or wildcards",
        "recommendation": "Use specific paths; implement trash/backup before deletion",
        "cwe_ids": ["CWE-73"],
        "mitre_techniques": ["T1485", "T1070.004"],
        "cvss_base_score": 9.1,
    },
    {
        "pattern_id": "SH-002",
        "language": "shell",
        "category": "code_execution",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"(curl|wget)\s+[^|;]*\|\s*(ba)?sh",
        "pattern_flags": "IGNORECASE",
        "description": "Remote code execution via pipe to shell (curl|sh pattern)",
        "recommendation": "Download scripts first, review, then execute; use verified sources",
        "cwe_ids": ["CWE-94", "CWE-829"],
        "mitre_techniques": ["T1059.004", "T1105"],
        "cvss_base_score": 9.8,
    },
    {
        "pattern_id": "SH-003",
        "language": "shell",
        "category": "privilege_escalation",
        "severity": "high",
        "pattern_type": "regex",
        "pattern_value": r"\b(sudo|doas)\s+(-[\w]+\s+)*\w+",
        "pattern_flags": None,
        "description": "Privilege escalation via sudo/doas command",
        "recommendation": "Audit all privileged commands; use minimal required permissions",
        "cwe_ids": ["CWE-250"],
        "mitre_techniques": ["T1548.003"],
        "cvss_base_score": 7.8,
    },
    {
        "pattern_id": "SH-004",
        "language": "shell",
        "category": "data_exfiltration",
        "severity": "high",
        "pattern_type": "regex",
        "pattern_value": r"\b(nc|netcat|ncat)\s+(-[\w]+\s+)*[\d\.]+\s+\d+",
        "pattern_flags": None,
        "description": "Netcat connection that could be used for data exfiltration",
        "recommendation": "Use approved secure transfer mechanisms; audit network connections",
        "cwe_ids": ["CWE-200"],
        "mitre_techniques": ["T1048", "T1071"],
        "cvss_base_score": 7.5,
    },

    # ========================================================================
    # CREDENTIAL PATTERNS - Secret Detection
    # ========================================================================
    {
        "pattern_id": "CRED-001",
        "language": "any",
        "category": "credential_exposure",
        "severity": "critical",
        "pattern_type": "regex",
        "pattern_value": r"(password|passwd|pwd|secret|api_key|apikey|api-key|auth_token|access_token|private_key)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
        "pattern_flags": "IGNORECASE",
        "description": "Hardcoded credential or secret in code",
        "recommendation": "Use environment variables or secrets manager; never hardcode credentials",
        "cwe_ids": ["CWE-798", "CWE-259"],
        "mitre_techniques": ["T1552.001"],
        "cvss_base_score": 7.5,
    },
    {
        "pattern_id": "CRED-002",
        "language": "any",
        "category": "credential_exposure",
        "severity": "high",
        "pattern_type": "regex",
        "pattern_value": r"\b(AWS|AKIA)[A-Z0-9]{16,}",
        "pattern_flags": None,
        "description": "AWS access key ID pattern detected",
        "recommendation": "Use IAM roles or AWS Secrets Manager; rotate exposed keys immediately",
        "cwe_ids": ["CWE-798"],
        "mitre_techniques": ["T1552.001", "T1078.004"],
        "cvss_base_score": 8.0,
    },
]


def upgrade():
    # Get connection for raw SQL
    conn = op.get_bind()

    for pattern in GLOBAL_PATTERNS:
        # Convert lists to PostgreSQL array format
        cwe_ids = "{" + ",".join(pattern.get("cwe_ids", [])) + "}"
        mitre_techniques = "{" + ",".join(pattern.get("mitre_techniques", [])) + "}"

        conn.execute(
            sa.text("""
                INSERT INTO global_code_patterns (
                    pattern_id, language, category, severity, pattern_type,
                    pattern_value, pattern_flags, description, recommendation,
                    cwe_ids, mitre_techniques, cvss_base_score, is_active, version
                ) VALUES (
                    :pattern_id, :language, :category, :severity, :pattern_type,
                    :pattern_value, :pattern_flags, :description, :recommendation,
                    :cwe_ids, :mitre_techniques, :cvss_base_score, true, 1
                )
                ON CONFLICT (pattern_id) DO UPDATE SET
                    language = EXCLUDED.language,
                    category = EXCLUDED.category,
                    severity = EXCLUDED.severity,
                    pattern_value = EXCLUDED.pattern_value,
                    pattern_flags = EXCLUDED.pattern_flags,
                    description = EXCLUDED.description,
                    recommendation = EXCLUDED.recommendation,
                    cwe_ids = EXCLUDED.cwe_ids,
                    mitre_techniques = EXCLUDED.mitre_techniques,
                    cvss_base_score = EXCLUDED.cvss_base_score,
                    version = global_code_patterns.version + 1,
                    updated_at = NOW()
            """),
            {
                "pattern_id": pattern["pattern_id"],
                "language": pattern["language"],
                "category": pattern["category"],
                "severity": pattern["severity"],
                "pattern_type": pattern["pattern_type"],
                "pattern_value": pattern["pattern_value"],
                "pattern_flags": pattern.get("pattern_flags"),
                "description": pattern["description"],
                "recommendation": pattern.get("recommendation"),
                "cwe_ids": cwe_ids,
                "mitre_techniques": mitre_techniques,
                "cvss_base_score": pattern.get("cvss_base_score"),
            }
        )

    print(f"Seeded {len(GLOBAL_PATTERNS)} global code patterns")


def downgrade():
    # Remove seeded patterns
    conn = op.get_bind()
    pattern_ids = [p["pattern_id"] for p in GLOBAL_PATTERNS]
    placeholders = ",".join([f"'{p}'" for p in pattern_ids])
    conn.execute(sa.text(f"DELETE FROM global_code_patterns WHERE pattern_id IN ({placeholders})"))
