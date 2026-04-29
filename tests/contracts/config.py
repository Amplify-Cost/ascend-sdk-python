"""SEC-REL-001: Doc/SDK Contract Test — runtime configuration and canonical paths.

All paths are resolved once at import. A missing canonical path is a hard
error at import time — the gate cannot fail open by defaulting to an empty
source of truth.
"""
from __future__ import annotations

import os
import pathlib
import sys

RUNNER_VERSION = "1.0.0"

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

PYTHON_SDK_ROOT = _PROJECT_ROOT / "ascend"
NODE_SDK_ROOT = _PROJECT_ROOT / "ow-ai-backend" / "sdk" / "nodejs"
PUBLIC_DOCS_ROOT = _PROJECT_ROOT / "owkai-pilot-frontend" / "ascend-docs" / "docs"
README_FILES = [
    _PROJECT_ROOT / "README.md",
    _PROJECT_ROOT / "CHANGELOG.md",
    NODE_SDK_ROOT / "README.md",
    NODE_SDK_ROOT / "CHANGELOG.md",
]

AUDIT_LOG_FILE = _PROJECT_ROOT / "ascend-audit" / "contract-tests.jsonl"

EXIT_OK = 0
EXIT_CONTRACT_VIOLATION = 1
EXIT_INFRA_FAILURE = 2

def _required_paths():
    return [
        ("python sdk", PYTHON_SDK_ROOT / "client.py"),
        ("python sdk init", PYTHON_SDK_ROOT / "__init__.py"),
        ("node sdk index", NODE_SDK_ROOT / "dist" / "index.d.ts"),
        ("public docs", PUBLIC_DOCS_ROOT),
        ("audit log file", AUDIT_LOG_FILE),
    ]


def validate_environment() -> None:
    """Fail closed on any missing source-of-truth. Exit 2 on any miss."""
    missing = [name for name, p in _required_paths() if not p.exists()]
    if missing:
        sys.stderr.write(
            "SEC-REL-001 infra failure: missing canonical paths: "
            + ", ".join(missing)
            + "\n"
        )
        sys.exit(EXIT_INFRA_FAILURE)
