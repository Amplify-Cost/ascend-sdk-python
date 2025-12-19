# subprocess Wrapper

Governed subprocess execution for AI agents.

## Overview

The ASCEND subprocess wrapper provides a drop-in replacement for Python's `subprocess` module that automatically governs shell command execution through the ASCEND platform.

## Installation

```python
from ascend.wrappers import subprocess
```

## Features

- **Drop-in replacement** - Same API as stdlib subprocess
- **Shell=True blocked by default** - Prevents shell injection attacks
- **Local risk classification** - Critical/high/medium/low patterns
- **Governance integration** - Commands submitted to ASCEND for approval
- **Auto-approve safe commands** - Low-risk commands approved locally
- **Configurable fail modes** - Choose fail-closed or fail-open behavior
- **Decorator support** - Add governance to existing functions

## Usage

### Basic Usage

```python
from ascend.wrappers import subprocess

# Same API as stdlib - but governed!
result = subprocess.run(['ls', '-la'], capture_output=True)

# Shell commands require explicit approval
# This will raise ShellNotAllowedError by default:
subprocess.run('echo hello', shell=True)  # BLOCKED
```

### With Governance Client

```python
from ascend import AscendClient
from ascend.wrappers import subprocess
from ascend.wrappers.subprocess import configure

# Configure with ASCEND client
client = AscendClient(api_key="your_key")
configure(client=client, fail_mode='closed')

# Now all risky commands go through ASCEND approval
result = subprocess.run(['rm', '-rf', '/tmp/cache'])  # Requires approval
```

### Decorator Pattern

```python
from ascend.wrappers.subprocess import govern_subprocess

@govern_subprocess(risk_level="high")
def deploy():
    subprocess.run(["./deploy.sh"])
```

## Configuration

```python
from ascend.wrappers.subprocess import configure

configure(
    client=ascend_client,        # AscendClient instance
    fail_mode='closed',          # 'closed' (default) or 'open'
    allow_shell=False,           # Block shell=True by default
    auto_approve_safe=True,      # Auto-approve low-risk commands
    blocked_commands=['rm'],     # Additional commands to block locally
    timeout=5                    # Governance check timeout in seconds
)
```

## Risk Classification

Commands are classified into four risk levels based on pattern matching:

### Critical Risk

| Pattern | Description |
|---------|-------------|
| `rm -rf /` | Recursive delete from root |
| `dd if=...of=/dev/` | Direct disk write |
| `mkfs.` | Filesystem format |
| `curl \| bash` | Pipe to shell (RCE) |
| `wget \| sh` | Pipe to shell (RCE) |
| `chmod 777 /` | Wide open permissions from root |
| Fork bomb pattern | Resource exhaustion |

### High Risk

| Pattern | Description |
|---------|-------------|
| `sudo` | Privilege escalation |
| `su -` | Switch user |
| `chmod [0-7]*7[0-7]*` | World-writable permissions |
| `chown` on root paths | Ownership change from root |
| `iptables` | Firewall modification |
| `systemctl stop/disable` | Service disruption |
| `kill -9` | Force kill |
| `nc -e/-l` | Netcat listener |

### Medium Risk

| Pattern | Description |
|---------|-------------|
| `chmod` | Permission change |
| `chown` | Ownership change |
| `mount/umount` | Filesystem mount |
| `kill` | Process kill |
| `crontab` | Cron modification |
| `ssh/scp/rsync` | Remote operations |

### Low Risk (Auto-approved)

| Pattern | Description |
|---------|-------------|
| `ls` | List files |
| `cat` | View file |
| `grep` | Search |
| `echo` | Echo |
| `pwd` | Current directory |
| `whoami` | Current user |
| `date` | Date |
| `uname` | System info |

## API Reference

### Functions

```python
# Drop-in replacements (same API as stdlib)
run(args, *, stdin=None, input=None, stdout=None, ...)
call(args, *, stdin=None, stdout=None, ...)
check_call(args, *, stdin=None, stdout=None, ...)
check_output(args, *, stdin=None, ...)
Popen(args, **kwargs)  # Class

# Governance utilities
configure(client=None, fail_mode=None, ...)
governed_run(args, **kwargs)
classify_command_risk(command) -> str  # Returns: critical/high/medium/low
```

### Exceptions

```python
from ascend.wrappers.subprocess import (
    GovernanceError,      # Base exception for governance failures
    ShellNotAllowedError  # Raised when shell=True is used but not allowed
)
```

## Error Handling

```python
from ascend.wrappers.subprocess import GovernanceError, ShellNotAllowedError

try:
    result = subprocess.run(['rm', '-rf', '/'])
except GovernanceError as e:
    print(f"Command denied: {e}")
except ShellNotAllowedError as e:
    print(f"Shell not allowed: {e}")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASCEND_SUBPROCESS_FAIL_MODE` | `closed` | Fail mode when API unavailable |
| `ASCEND_SUBPROCESS_ALLOW_SHELL` | `false` | Allow shell=True commands |
| `ASCEND_SUBPROCESS_AUTO_APPROVE_LOW` | `true` | Auto-approve low-risk commands |

## Governance Flow

```
subprocess.run(['rm', '-rf', '/tmp/cache'])
         │
         ▼
┌─────────────────────────┐
│ 1. Check shell=True     │ → ShellNotAllowedError if shell and not allowed
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 2. Classify risk        │ → critical/high/medium/low
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 3. Check local blocklist│ → GovernanceError if blocked
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 4. Low risk + auto?     │ → Auto-approve, skip backend
└─────────────────────────┘
         │ No
         ▼
┌─────────────────────────┐
│ 5. Submit to ASCEND     │ → action_type="system.subprocess"
└─────────────────────────┘
         │
         ▼
    Approved? ─── No ──→ GovernanceError
         │
        Yes
         │
         ▼
    Execute & Return
```

## Re-exported Constants

The wrapper re-exports stdlib subprocess constants:

```python
from ascend.wrappers import subprocess

subprocess.PIPE      # Pipe constant
subprocess.STDOUT    # Stdout constant
subprocess.DEVNULL   # Devnull constant
subprocess.CalledProcessError
subprocess.TimeoutExpired
subprocess.CompletedProcess
```

## Compliance

- **CWE-78**: OS Command Injection
- **CWE-77**: Command Injection
- **MITRE ATT&CK**: T1059.004 (Unix Shell)
- **NIST 800-53**: SI-10 (Information Input Validation)

## Example: Safe File Operations

```python
from ascend.wrappers import subprocess

# Safe: List directory contents (auto-approved)
result = subprocess.run(['ls', '-la', '/tmp'], capture_output=True)
print(result.stdout)

# Safe: Copy file (low risk, auto-approved)
subprocess.run(['cp', 'source.txt', 'dest.txt'])

# Governed: Delete file (requires ASCEND approval)
subprocess.run(['rm', 'important_file.txt'])

# Blocked: Recursive delete (critical risk)
try:
    subprocess.run(['rm', '-rf', '/'])  # GovernanceError
except subprocess.GovernanceError as e:
    print(f"Blocked: {e}")
```

## Integration with Existing Code

Replace your imports to enable governance:

```python
# Before
import subprocess

# After
from ascend.wrappers import subprocess

# All existing code works unchanged!
# Low-risk commands auto-approved, high-risk go through governance
```
