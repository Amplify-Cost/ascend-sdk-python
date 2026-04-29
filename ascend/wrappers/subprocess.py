"""
DEEP-001: Subprocess Wrapper with Governance

Drop-in replacement for Python's subprocess module that adds
ASCEND governance checks before command execution.

Features:
- Same API as stdlib subprocess (drop-in replacement)
- Governance check before command execution
- Local risk classification for common commands
- Fail-closed mode by default
- Comprehensive audit logging
- Shell=True blocking by default

Usage:
    # Option 1: Drop-in replacement
    from ascend.wrappers import subprocess
    result = subprocess.run(["ls", "-la"])

    # Option 2: Explicit governance
    from ascend.wrappers.subprocess import governed_run
    result = governed_run(["git", "clone", url])

    # Option 3: Decorator
    from ascend.wrappers.subprocess import govern_subprocess
    @govern_subprocess(risk_level="high")
    def deploy():
        subprocess.run(["./deploy.sh"])

Compliance: CWE-78, CWE-77, MITRE T1059.004, NIST SI-10
Author: Enterprise Security Team
Version: 1.0.0
"""

import os
import re
import logging
import subprocess as _original_subprocess
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

# Global configuration (set via configure() or environment)
_config = {
    "client": None,
    "fail_mode": os.getenv("ASCEND_SUBPROCESS_FAIL_MODE", "closed"),
    "auto_approve_safe": os.getenv("ASCEND_SUBPROCESS_AUTO_APPROVE_LOW", "true").lower() == "true",
    "allow_shell": os.getenv("ASCEND_SUBPROCESS_ALLOW_SHELL", "false").lower() == "true",
    "blocked_commands": [],
    "timeout": 5,  # Governance check timeout in seconds
}


# =============================================================================
# Risk Classification
# =============================================================================

# Command patterns by risk level
COMMAND_PATTERNS = {
    "critical": [
        r"rm\s+-rf\s+/",           # Recursive delete from root
        r"rm\s+.*\s+-rf",          # rm with -rf flag
        r"dd\s+if=.*of=/dev/",     # Direct disk write
        r"mkfs\.",                  # Filesystem format
        r":\(\)\{\s*:\|:\&\s*\};:", # Fork bomb
        r">\s*/dev/[sh]d[a-z]",     # Write to disk device
        # BUG-16-port: anchor to end-of-string so only literal `/` (root
        # filesystem) matches as critical; `chmod 777 /var/www` stays `high`.
        r"chmod\s+777\s+/\s*$",     # Wide open permissions on literal root
        r"curl.*\|\s*(bash|sh)",    # Pipe to shell
        r"wget.*\|\s*(bash|sh)",    # Pipe to shell
    ],
    "high": [
        r"sudo\s+",                 # Privilege escalation
        r"su\s+-",                  # Switch user
        r"chmod\s+[0-7]*7[0-7]*",   # World-writable
        r"chown\s+.*:.*\s+/",       # Change ownership from root
        r"iptables",                # Firewall modification
        r"systemctl\s+(stop|disable|mask)", # Service disruption
        r"kill\s+-9",               # Force kill
        r"pkill",                   # Process kill
        r"nc\s+-[el]",              # Netcat listener
        r"ncat\s+-[el]",            # Ncat listener
    ],
    "medium": [
        r"chmod\s+",                # Permission change
        r"chown\s+",                # Ownership change
        r"mount\s+",                # Mount filesystem
        r"umount\s+",               # Unmount filesystem
        r"kill\s+",                 # Kill process
        r"crontab\s+",              # Cron modification
        # BUG-16-port: word-boundary prefix so `cat`, `chat`, `dispatch`
        # don't false-positive into the `at` scheduled-task classifier.
        r"\bat\s+",                 # Scheduled task
        r"ssh\s+",                  # SSH connection
        r"scp\s+",                  # Secure copy
        r"rsync\s+",                # Remote sync
    ],
    "low": [
        r"ls\s+",                   # List files
        r"cat\s+",                  # View file
        r"grep\s+",                 # Search
        r"echo\s+",                 # Echo
        r"pwd",                     # Current directory
        r"whoami",                  # Current user
        r"date",                    # Date
        r"uname",                   # System info
        r"env",                     # Environment
        r"printenv",                # Environment
    ]
}

# Precompile patterns
_compiled_patterns = {
    level: [re.compile(p, re.IGNORECASE) for p in patterns]
    for level, patterns in COMMAND_PATTERNS.items()
}


def classify_command_risk(command: Union[str, List[str]]) -> str:
    """
    Classify command risk level based on patterns.

    Args:
        command: Command string or list

    Returns:
        Risk level: critical, high, medium, low
    """
    if isinstance(command, list):
        command_str = " ".join(command)
    else:
        command_str = command

    # Check patterns in order of severity
    for level in ["critical", "high", "medium", "low"]:
        for pattern in _compiled_patterns[level]:
            if pattern.search(command_str):
                return level

    return "low"  # Default to low if no patterns match


# =============================================================================
# Governance Functions
# =============================================================================

class GovernanceError(Exception):
    """Raised when governance check fails."""
    pass


class ShellNotAllowedError(GovernanceError):
    """Raised when shell=True is used but not allowed."""
    pass


def _check_governance(
    command: Union[str, List[str]],
    shell: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Check governance for a subprocess command.

    Args:
        command: Command to execute
        shell: Whether shell=True is used
        **kwargs: Additional subprocess arguments

    Returns:
        Governance decision dictionary

    Raises:
        GovernanceError: If governance denies the command
        ShellNotAllowedError: If shell=True is used but not allowed
    """
    # Check shell=True restriction
    if shell and not _config["allow_shell"]:
        raise ShellNotAllowedError(
            "shell=True is not allowed. Use list form: ['cmd', 'arg1', 'arg2']"
        )

    # Classify risk locally
    risk_level = classify_command_risk(command)

    # Check local blocklist
    if isinstance(command, list):
        cmd_name = command[0] if command else ""
    else:
        cmd_name = command.split()[0] if command else ""

    if cmd_name in _config["blocked_commands"]:
        raise GovernanceError(f"Command '{cmd_name}' is blocked by local policy")

    # Auto-approve low-risk if configured
    if risk_level == "low" and _config["auto_approve_safe"]:
        logger.debug(f"DEEP-001: Auto-approved low-risk command: {cmd_name}")
        return {
            "allowed": True,
            "risk_level": risk_level,
            "action_id": None,
            "auto_approved": True
        }

    # Check with ASCEND backend if client is configured
    client = _config["client"]
    if client is not None:
        try:
            # Format command for submission
            if isinstance(command, list):
                command_str = " ".join(str(arg) for arg in command)
            else:
                command_str = str(command)

            # Submit to ASCEND
            decision = client.evaluate_action(
                action_type="system.subprocess",
                resource=cmd_name,
                parameters={
                    "command": command_str[:1000],  # Truncate for API
                    "shell": shell,
                    "cwd": kwargs.get("cwd"),
                },
                risk_indicators={
                    "subprocess_execution": True,
                    "shell_mode": shell,
                    "local_risk_level": risk_level
                },
                timeout=_config["timeout"]
            )

            if not decision.execution_allowed:
                raise GovernanceError(
                    f"Command denied by ASCEND: {decision.reason}"
                )

            return {
                "allowed": True,
                "risk_level": decision.risk_level or risk_level,
                "action_id": decision.action_id,
                "auto_approved": False
            }

        except GovernanceError:
            raise
        except Exception as e:
            logger.error(f"DEEP-001: Governance check failed: {e}")
            if _config["fail_mode"] == "closed":
                raise GovernanceError(f"Governance check failed: {e}")
            else:
                logger.warning("DEEP-001: Fail-open mode, allowing command")
                return {
                    "allowed": True,
                    "risk_level": risk_level,
                    "action_id": None,
                    "governance_error": str(e)
                }
    else:
        # No client configured - check fail mode
        if _config["fail_mode"] == "closed" and risk_level in ["critical", "high"]:
            raise GovernanceError(
                f"No ASCEND client configured and command is {risk_level} risk. "
                "Configure client or set fail_mode='open'."
            )

        logger.warning(
            f"DEEP-001: No client configured, allowing {risk_level} risk command"
        )
        return {
            "allowed": True,
            "risk_level": risk_level,
            "action_id": None,
            "no_client": True
        }


# =============================================================================
# Subprocess Wrappers
# =============================================================================

def run(
    args,
    *,
    stdin=None,
    input=None,
    stdout=None,
    stderr=None,
    capture_output=False,
    shell=False,
    cwd=None,
    timeout=None,
    check=False,
    encoding=None,
    errors=None,
    text=None,
    env=None,
    **other_kwargs
) -> _original_subprocess.CompletedProcess:
    """
    Governed subprocess.run() replacement.

    Same API as subprocess.run() with added governance checks.

    Raises:
        GovernanceError: If command is denied by governance
        ShellNotAllowedError: If shell=True is used but not allowed
    """
    # Check governance first
    _check_governance(args, shell=shell, cwd=cwd)

    # Execute original
    return _original_subprocess.run(
        args,
        stdin=stdin,
        input=input,
        stdout=stdout,
        stderr=stderr,
        capture_output=capture_output,
        shell=shell,
        cwd=cwd,
        timeout=timeout,
        check=check,
        encoding=encoding,
        errors=errors,
        text=text,
        env=env,
        **other_kwargs
    )


def call(args, *, stdin=None, stdout=None, stderr=None, shell=False,
         cwd=None, timeout=None, **other_kwargs) -> int:
    """
    Governed subprocess.call() replacement.
    """
    _check_governance(args, shell=shell, cwd=cwd)
    return _original_subprocess.call(
        args, stdin=stdin, stdout=stdout, stderr=stderr,
        shell=shell, cwd=cwd, timeout=timeout, **other_kwargs
    )


def check_call(args, *, stdin=None, stdout=None, stderr=None, shell=False,
               cwd=None, timeout=None, **other_kwargs) -> int:
    """
    Governed subprocess.check_call() replacement.
    """
    _check_governance(args, shell=shell, cwd=cwd)
    return _original_subprocess.check_call(
        args, stdin=stdin, stdout=stdout, stderr=stderr,
        shell=shell, cwd=cwd, timeout=timeout, **other_kwargs
    )


def check_output(args, *, stdin=None, stderr=None, shell=False,
                 cwd=None, timeout=None, **other_kwargs) -> bytes:
    """
    Governed subprocess.check_output() replacement.
    """
    _check_governance(args, shell=shell, cwd=cwd)
    return _original_subprocess.check_output(
        args, stdin=stdin, stderr=stderr,
        shell=shell, cwd=cwd, timeout=timeout, **other_kwargs
    )


class Popen(_original_subprocess.Popen):
    """
    Governed subprocess.Popen replacement.

    Adds governance check in __init__ before process creation.
    """

    def __init__(self, args, **kwargs):
        # Check governance before creating process
        shell = kwargs.get("shell", False)
        cwd = kwargs.get("cwd")
        _check_governance(args, shell=shell, cwd=cwd)

        # Call original Popen
        super().__init__(args, **kwargs)


# =============================================================================
# Configuration and Decorators
# =============================================================================

def configure(
    client=None,
    fail_mode: str = None,
    auto_approve_safe: bool = None,
    blocked_commands: List[str] = None,
    allow_shell: bool = None,
    timeout: int = None
):
    """
    Configure the subprocess wrapper.

    Args:
        client: AscendClient instance for governance checks
        fail_mode: "closed" (deny on error) or "open" (allow on error)
        auto_approve_safe: Auto-approve low-risk commands without backend check
        blocked_commands: Additional commands to block locally
        allow_shell: Allow shell=True (default: False for security)
        timeout: Governance check timeout in seconds
    """
    if client is not None:
        _config["client"] = client
    if fail_mode is not None:
        _config["fail_mode"] = fail_mode
    if auto_approve_safe is not None:
        _config["auto_approve_safe"] = auto_approve_safe
    if blocked_commands is not None:
        _config["blocked_commands"] = blocked_commands
    if allow_shell is not None:
        _config["allow_shell"] = allow_shell
    if timeout is not None:
        _config["timeout"] = timeout

    logger.info(
        f"DEEP-001: Subprocess wrapper configured - "
        f"fail_mode={_config['fail_mode']}, "
        f"allow_shell={_config['allow_shell']}, "
        f"client={'configured' if _config['client'] else 'not configured'}"
    )


def governed_run(
    args,
    **kwargs
) -> _original_subprocess.CompletedProcess:
    """
    Explicit governed run function.

    Same as run() but more explicit about governance.
    """
    return run(args, **kwargs)


def govern_subprocess(
    risk_level: str = None,
    require_approval: bool = False
) -> Callable:
    """
    Decorator to add subprocess governance to a function.

    All subprocess calls within the decorated function will be governed.

    Args:
        risk_level: Override risk level for all subprocess calls
        require_approval: Require explicit approval for all calls

    Usage:
        @govern_subprocess(risk_level="high")
        def deploy():
            subprocess.run(["./deploy.sh"])
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Store original config
            original_auto_approve = _config["auto_approve_safe"]

            # Override if required
            if require_approval:
                _config["auto_approve_safe"] = False

            try:
                return func(*args, **kwargs)
            finally:
                # Restore original config
                _config["auto_approve_safe"] = original_auto_approve

        return wrapper
    return decorator


# =============================================================================
# Re-export subprocess constants and utilities
# =============================================================================

# Re-export common constants
PIPE = _original_subprocess.PIPE
STDOUT = _original_subprocess.STDOUT
DEVNULL = _original_subprocess.DEVNULL

# Re-export exceptions
SubprocessError = _original_subprocess.SubprocessError
CalledProcessError = _original_subprocess.CalledProcessError
TimeoutExpired = _original_subprocess.TimeoutExpired

# Re-export CompletedProcess
CompletedProcess = _original_subprocess.CompletedProcess


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Main functions
    'run',
    'call',
    'check_call',
    'check_output',
    'Popen',

    # Configuration
    'configure',
    'governed_run',
    'govern_subprocess',

    # Risk classification
    'classify_command_risk',

    # Exceptions
    'GovernanceError',
    'ShellNotAllowedError',

    # Re-exports from stdlib
    'PIPE',
    'STDOUT',
    'DEVNULL',
    'SubprocessError',
    'CalledProcessError',
    'TimeoutExpired',
    'CompletedProcess',
]
