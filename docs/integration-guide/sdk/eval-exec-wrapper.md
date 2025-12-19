# eval/exec Wrapper

Governed dynamic code execution for AI agents.

## Overview

The ASCEND eval/exec wrapper provides safe alternatives to Python's `eval()` and `exec()` functions with 4-layer defense: AST analysis, governance check, sandboxed execution, and timeout protection.

## Installation

```python
from ascend.wrappers.dynamic_code import safe_eval, safe_exec, SafeEvaluator
```

## Features

- **4-layer defense** - Length check, AST analysis, governance, sandbox
- **Restricted builtins** - Only safe functions allowed
- **Timeout protection** - Prevents infinite loops (Unix SIGALRM)
- **AST-based analysis** - Detects dangerous constructs before execution
- **Fail-closed by default** - Denies on any error
- **Configurable allow/block lists** - Whitelist approach

## Usage

### Basic Usage

```python
from ascend.wrappers.dynamic_code import safe_eval, safe_exec

# Safe expression evaluation
result = safe_eval("2 + 2")  # Returns 4

# With context variables
result = safe_eval("price * quantity", {"price": 10, "quantity": 5})  # Returns 50

# Safe code execution (returns created variables)
namespace = safe_exec("x = 10; y = x * 2")
print(namespace["y"])  # 20
```

### With SafeEvaluator Class

```python
from ascend.wrappers.dynamic_code import SafeEvaluator

evaluator = SafeEvaluator(
    client=ascend_client,                    # ASCEND client for governance
    allowed_builtins={"sum", "len", "min", "max"},  # Restrict builtins
    max_code_length=10000,                   # Max code size
    timeout_seconds=5                         # Execution timeout
)

result = evaluator.eval("sum([1, 2, 3])")  # Returns 6

# Analyze without executing
analysis = evaluator.analyze("import os; os.system('ls')")
print(analysis.is_safe)  # False
print(analysis.reason)   # "Import statement not allowed: os"
```

## 4-Layer Defense Model

```
User Code Input
      │
      ▼
┌─────────────────────┐
│ Layer 0: Length     │  Code length <= max_code_length (default: 10000)
│ Check               │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Layer 1: AST        │  Parse and analyze syntax tree
│ Analysis (Local)    │  - Detect imports
│                     │  - Detect dangerous calls (eval, exec, __import__)
│                     │  - Detect sandbox escape (__class__, __bases__)
│                     │  - Detect file/network operations
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Layer 2: Governance │  Submit to ASCEND (if client configured)
│ Check (Remote)      │  - action_type="code.eval" or "code.exec"
│                     │  - Include AST findings count
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Layer 3: Sandbox    │  Restricted execution environment
│ Execution           │  - Only allowed builtins
│                     │  - No __builtins__ access
│                     │  - Context variables only
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Layer 4: Timeout    │  Unix SIGALRM timeout protection
│ Protection          │  - Default: 5 seconds
└─────────────────────┘
      │
      ▼
   Result
```

## AST Analysis Categories

The analyzer detects dangerous constructs in these categories:

### Code Injection (Critical)

| Pattern | Description |
|---------|-------------|
| `eval()` | Dynamic evaluation |
| `exec()` | Dynamic execution |
| `compile()` | Code compilation |
| `__import__()` | Dynamic import |
| `import ...` | Import statements |
| `from ... import` | From imports |
| `getattr/setattr/delattr` | Attribute manipulation |
| `globals/locals/vars` | Namespace access |

### Sandbox Escape (Critical)

| Pattern | Description |
|---------|-------------|
| `__class__` | Class access |
| `__bases__` | Base class access |
| `__mro__` | Method resolution order |
| `__subclasses__` | Subclass enumeration |
| `__globals__` | Global namespace |
| `__builtins__` | Builtins access |
| `__code__` | Code object access |
| `__closure__` | Closure access |
| `__dict__` | Dictionary access |

### File Access (High)

| Pattern | Description |
|---------|-------------|
| `open()` | File open |
| `read()` | File read |
| `write()` | File write |

### Network Access (High)

| Pattern | Description |
|---------|-------------|
| `socket` | Socket module |
| `urllib` | URL library |
| `requests` | HTTP library |
| `httpx` | HTTP library |
| `aiohttp` | Async HTTP |

## Default Safe Builtins

The following builtins are allowed by default:

```python
DEFAULT_SAFE_BUILTINS = {
    # Math
    "abs", "round", "min", "max", "sum", "pow", "divmod", "float", "int",

    # Data structures
    "len", "list", "dict", "set", "tuple", "frozenset",
    "str", "bool", "bytes", "bytearray",

    # Iteration
    "range", "enumerate", "zip", "map", "filter", "sorted", "reversed",

    # Type checking
    "type", "isinstance", "issubclass",

    # Other safe operations
    "all", "any", "repr", "hash", "id", "ord", "chr", "bin", "hex", "oct",
}
```

## SafeEvaluator Class

```python
from ascend.wrappers.dynamic_code import SafeEvaluator

evaluator = SafeEvaluator(
    client=None,                       # AscendClient for governance
    fail_mode="closed",                # 'closed' or 'open'
    allowed_builtins={"len", "sum"},   # Override defaults
    blocked_names={"custom_func"},     # Additional blocked names
    max_code_length=10000,             # Max code size
    timeout_seconds=5,                 # Execution timeout
    allow_imports=False                # Allow imports (default: False)
)

# Methods
result = evaluator.eval("2 + 2")                    # Evaluate expression
namespace = evaluator.exec("x = 10")                # Execute code
results = evaluator.eval_many(["1+1", "2+2"])       # Batch evaluation
analysis = evaluator.analyze("import os")           # Analyze only
```

## Error Handling

```python
from ascend.wrappers.dynamic_code import (
    safe_eval,
    SafeEvalError,        # Base exception
    CodeTooLongError,     # Code exceeds max length
    DangerousCodeError,   # Dangerous constructs detected by AST
    GovernanceError,      # Governance check failed
    TimeoutError          # Execution timeout
)

try:
    result = safe_eval("__import__('os').system('rm -rf /')")
except DangerousCodeError as e:
    print(f"Code blocked by AST analysis: {e}")
except GovernanceError as e:
    print(f"Code denied by ASCEND: {e}")
except TimeoutError as e:
    print(f"Execution timeout: {e}")
```

## Configuration

```python
from ascend.wrappers.dynamic_code import configure

configure(
    client=ascend_client,              # AscendClient instance
    fail_mode='closed',                # 'closed' (default) or 'open'
    allowed_builtins={"sum", "len"},   # Override default builtins
    blocked_names={"custom_func"},     # Additional blocked names
    max_code_length=10000,             # Max code length
    timeout_seconds=5                   # Execution timeout
)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASCEND_EVAL_FAIL_MODE` | `closed` | Fail mode when API unavailable |
| `ASCEND_EVAL_MAX_LENGTH` | `10000` | Maximum code length |
| `ASCEND_EVAL_TIMEOUT` | `5` | Execution timeout (seconds) |

## ASTAnalysisResult

The `analyze()` method returns an `ASTAnalysisResult`:

```python
analysis = evaluator.analyze("import os")

print(analysis.is_safe)                  # False (critical/high findings)
print(analysis.has_dangerous_constructs) # True
print(analysis.max_severity)             # "critical"
print(analysis.reason)                   # Description of most severe finding
print(analysis.code_length)              # Code length
print(len(analysis.findings))            # Number of findings
```

## Example: Safe Calculator

```python
from ascend.wrappers.dynamic_code import SafeEvaluator

calculator = SafeEvaluator(
    allowed_builtins={"abs", "round", "min", "max", "sum", "pow", "int", "float"},
    timeout_seconds=1
)

# Safe math operations
calculator.eval("2 + 2")                  # 4
calculator.eval("pow(2, 10)")             # 1024
calculator.eval("sum([1,2,3,4])")         # 10
calculator.eval("round(3.14159, 2)")      # 3.14

# With context
calculator.eval("price * (1 - discount)", {"price": 100, "discount": 0.1})  # 90.0

# Blocked - DangerousCodeError
calculator.eval("__import__('os')")
calculator.eval("open('/etc/passwd')")
calculator.eval("().__class__.__bases__[0].__subclasses__()")
```

## Compliance

- **CWE-94**: Code Injection
- **CWE-95**: Eval Injection
- **CWE-502**: Deserialization of Untrusted Data
- **MITRE ATT&CK**: T1059.006 (Python)
- **NIST 800-53**: SI-10 (Information Input Validation)
- **OWASP**: A03:2021 - Injection

## Best Practices

1. **Prefer safe_eval over eval** - Always use the wrapper
2. **Limit allowed builtins** - Only include what you need
3. **Set timeouts** - Prevent infinite loops
4. **Configure ASCEND client** - Get governance audit trail
5. **Use analyze() first** - Check code before executing
6. **Monitor audit logs** - Review blocked attempts
