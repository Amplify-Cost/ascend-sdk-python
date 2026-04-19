"""
ASCEND Governance Wrappers

Drop-in replacements for dangerous Python operations with
ASCEND governance checks built-in.

Modules:
- subprocess: Governed shell/process execution (DEEP-001)
- dynamic_code: Governed eval/exec (DEEP-002)

Usage:
    # Subprocess wrapper
    from ascend.wrappers import subprocess
    result = subprocess.run(["ls", "-la"])

    # Dynamic code wrapper
    from ascend.wrappers.dynamic_code import safe_eval
    result = safe_eval("2 + 2")

Author: Enterprise Security Team
Version: 1.0.0
"""

# DEEP-001: Subprocess wrapper
from ascend.wrappers import subprocess

# Re-export key items for convenience
from ascend.wrappers.subprocess import (
    configure as configure_subprocess,
    governed_run,
    govern_subprocess,
    classify_command_risk,
    GovernanceError,
    ShellNotAllowedError,
)

# DEEP-002: Dynamic code wrapper
from ascend.wrappers.dynamic_code import (
    SafeEvaluator,
    safe_eval,
    safe_exec,
    analyze_expression,
    configure as configure_dynamic_code,
    SafeEvalError,
    DangerousCodeError,
    CodeTooLongError,
)

# DEEP-002: AST analyzer
from ascend.wrappers.ast_analyzer import (
    ASTAnalyzer,
    ASTAnalysisResult,
    ASTFinding,
    analyze_code,
    is_code_safe,
)

__all__ = [
    # Modules
    'subprocess',

    # DEEP-001: Subprocess utilities
    'configure_subprocess',
    'governed_run',
    'govern_subprocess',
    'classify_command_risk',
    'GovernanceError',
    'ShellNotAllowedError',

    # DEEP-002: Dynamic code utilities
    'SafeEvaluator',
    'safe_eval',
    'safe_exec',
    'analyze_expression',
    'configure_dynamic_code',
    'SafeEvalError',
    'DangerousCodeError',
    'CodeTooLongError',

    # DEEP-002: AST analyzer
    'ASTAnalyzer',
    'ASTAnalysisResult',
    'ASTFinding',
    'analyze_code',
    'is_code_safe',
]
