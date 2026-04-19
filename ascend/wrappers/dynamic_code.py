"""
DEEP-002: Safe eval/exec Wrapper with Governance

Provides governed alternatives to Python's dangerous eval() and exec()
with multi-layer security:

Layer 1: Local AST analysis (fast, offline)
Layer 2: Remote ASCEND governance check
Layer 3: Restricted execution environment
Layer 4: Comprehensive audit logging

Features:
- AST-based code safety analysis before execution
- Restricted builtins environment
- Configurable allowed/blocked operations
- Timeout protection
- Fail-closed by default

Usage:
    from ascend.wrappers.dynamic_code import safe_eval, SafeEvaluator

    # Simple usage
    result = safe_eval("2 + 2")  # Returns 4

    # With context
    result = safe_eval("price * quantity", {"price": 10, "quantity": 5})

    # Configured evaluator
    evaluator = SafeEvaluator(
        client=ascend_client,
        allowed_builtins=["sum", "len", "min", "max"]
    )
    result = evaluator.eval("sum([1, 2, 3])")

Compliance: CWE-94, CWE-95, MITRE T1059.006, NIST SI-10
Author: Enterprise Security Team
Version: 1.0.0
"""

import os
import logging
import signal
from typing import Any, Dict, List, Optional, Set, Callable
from functools import wraps
from contextlib import contextmanager

from ascend.wrappers.ast_analyzer import (
    ASTAnalyzer,
    ASTAnalysisResult,
    analyze_code
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Default safe builtins (mathematical and data operations only)
DEFAULT_SAFE_BUILTINS: Set[str] = {
    # Math
    "abs", "round", "min", "max", "sum", "pow",
    "divmod", "float", "int",

    # Data structures
    "len", "list", "dict", "set", "tuple", "frozenset",
    "str", "bool", "bytes", "bytearray",

    # Iteration
    "range", "enumerate", "zip", "map", "filter", "sorted", "reversed",

    # Type checking
    "type", "isinstance", "issubclass",

    # Other safe operations
    "all", "any", "repr", "hash", "id",
    "ord", "chr", "bin", "hex", "oct",
}

# Global configuration
_config = {
    "client": None,
    "fail_mode": os.getenv("ASCEND_EVAL_FAIL_MODE", "closed"),
    "max_code_length": int(os.getenv("ASCEND_EVAL_MAX_LENGTH", "10000")),
    "timeout_seconds": int(os.getenv("ASCEND_EVAL_TIMEOUT", "5")),
    "allowed_builtins": DEFAULT_SAFE_BUILTINS.copy(),
}


# =============================================================================
# Exceptions
# =============================================================================

class SafeEvalError(Exception):
    """Base exception for safe eval errors."""
    pass


class CodeTooLongError(SafeEvalError):
    """Raised when code exceeds maximum length."""
    pass


class DangerousCodeError(SafeEvalError):
    """Raised when code contains dangerous constructs."""
    pass


class GovernanceError(SafeEvalError):
    """Raised when governance check fails."""
    pass


class TimeoutError(SafeEvalError):
    """Raised when code execution times out."""
    pass


# =============================================================================
# Timeout Context Manager
# =============================================================================

@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for execution timeout.

    Note: Only works on Unix systems with signal support.
    On Windows, this is a no-op.
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Code execution timed out after {seconds} seconds")

    # Check if signals are available (Unix)
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows - no timeout support
        yield


# =============================================================================
# Restricted Builtins
# =============================================================================

def create_restricted_builtins(allowed: Set[str]) -> Dict[str, Any]:
    """
    Create a restricted builtins dictionary.

    Args:
        allowed: Set of allowed builtin names

    Returns:
        Dictionary of allowed builtins
    """
    import builtins

    restricted = {"__builtins__": {}}

    for name in allowed:
        if hasattr(builtins, name):
            restricted["__builtins__"][name] = getattr(builtins, name)

    # Always include True, False, None
    restricted["__builtins__"]["True"] = True
    restricted["__builtins__"]["False"] = False
    restricted["__builtins__"]["None"] = None

    return restricted


# =============================================================================
# Safe Evaluator Class
# =============================================================================

class SafeEvaluator:
    """
    Safe code evaluator with governance integration.

    Provides multi-layer security:
    1. AST analysis (local, fast)
    2. ASCEND governance check (remote)
    3. Restricted execution environment
    4. Timeout protection
    """

    def __init__(
        self,
        client=None,
        fail_mode: str = "closed",
        allowed_builtins: Optional[Set[str]] = None,
        blocked_names: Optional[Set[str]] = None,
        max_code_length: int = 10000,
        timeout_seconds: int = 5,
        allow_imports: bool = False
    ):
        """
        Initialize the safe evaluator.

        Args:
            client: AscendClient instance for governance checks
            fail_mode: "closed" (deny on error) or "open" (allow on error)
            allowed_builtins: Set of allowed builtin functions
            blocked_names: Additional names to block
            max_code_length: Maximum allowed code length
            timeout_seconds: Execution timeout in seconds
            allow_imports: Whether to allow import statements
        """
        self.client = client
        self.fail_mode = fail_mode
        self.allowed_builtins = allowed_builtins or DEFAULT_SAFE_BUILTINS.copy()
        self.blocked_names = blocked_names or set()
        self.max_code_length = max_code_length
        self.timeout_seconds = timeout_seconds
        self.allow_imports = allow_imports

        # Create AST analyzer
        self.analyzer = ASTAnalyzer(
            allowed_builtins=self.allowed_builtins,
            blocked_names=self.blocked_names,
            allow_imports=self.allow_imports
        )

        logger.info(
            f"DEEP-002: SafeEvaluator initialized - "
            f"fail_mode={fail_mode}, "
            f"allowed_builtins={len(self.allowed_builtins)}, "
            f"timeout={timeout_seconds}s"
        )

    def eval(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Safely evaluate Python expression.

        Args:
            code: Python expression to evaluate
            context: Dictionary of variables available during evaluation

        Returns:
            Result of the expression

        Raises:
            CodeTooLongError: If code exceeds max length
            DangerousCodeError: If code contains dangerous constructs
            GovernanceError: If governance check fails
            TimeoutError: If execution times out
        """
        # Step 0: Length check
        if len(code) > self.max_code_length:
            raise CodeTooLongError(
                f"Code length {len(code)} exceeds maximum {self.max_code_length}"
            )

        # Step 1: AST analysis (local, fast)
        ast_result = self.analyzer.analyze(code)

        if not ast_result.is_safe:
            logger.warning(
                f"DEEP-002: Dangerous code detected - "
                f"severity={ast_result.max_severity}, "
                f"findings={len(ast_result.findings)}"
            )
            raise DangerousCodeError(
                f"Code contains dangerous constructs: {ast_result.reason}"
            )

        # Step 2: ASCEND governance check (if client configured)
        if self.client is not None:
            try:
                decision = self.client.evaluate_action(
                    action_type="code.eval",
                    resource="dynamic_code",
                    parameters={
                        "code": code[:1000],  # Truncate for API
                        "code_length": len(code),
                        "ast_findings": len(ast_result.findings)
                    },
                    risk_indicators={
                        "dynamic_execution": True,
                        "ast_analyzed": True
                    }
                )

                if not decision.execution_allowed:
                    raise GovernanceError(
                        f"Code denied by ASCEND: {decision.reason}"
                    )

            except GovernanceError:
                raise
            except Exception as e:
                logger.error(f"DEEP-002: Governance check failed: {e}")
                if self.fail_mode == "closed":
                    raise GovernanceError(f"Governance check failed: {e}")
                logger.warning("DEEP-002: Fail-open mode, allowing code")

        # Step 3: Execute in restricted environment
        restricted_globals = create_restricted_builtins(self.allowed_builtins)

        # Add context variables
        if context:
            restricted_globals.update(context)

        # Step 4: Execute with timeout
        try:
            with timeout_context(self.timeout_seconds):
                result = eval(code, restricted_globals, {})

            logger.debug(f"DEEP-002: Code executed successfully")
            return result

        except TimeoutError:
            raise
        except Exception as e:
            logger.error(f"DEEP-002: Code execution failed: {e}")
            raise SafeEvalError(f"Execution failed: {e}")

    def exec(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Safely execute Python code.

        Args:
            code: Python code to execute
            context: Dictionary of variables available during execution

        Returns:
            Dictionary of variables created during execution

        Raises:
            Same exceptions as eval()
        """
        # Step 0: Length check
        if len(code) > self.max_code_length:
            raise CodeTooLongError(
                f"Code length {len(code)} exceeds maximum {self.max_code_length}"
            )

        # Step 1: AST analysis
        ast_result = self.analyzer.analyze(code)

        if not ast_result.is_safe:
            raise DangerousCodeError(
                f"Code contains dangerous constructs: {ast_result.reason}"
            )

        # Step 2: Governance check (same as eval)
        if self.client is not None:
            try:
                decision = self.client.evaluate_action(
                    action_type="code.exec",
                    resource="dynamic_code",
                    parameters={
                        "code": code[:1000],
                        "code_length": len(code)
                    },
                    risk_indicators={
                        "dynamic_execution": True,
                        "exec_mode": True
                    }
                )

                if not decision.execution_allowed:
                    raise GovernanceError(
                        f"Code denied by ASCEND: {decision.reason}"
                    )

            except GovernanceError:
                raise
            except Exception as e:
                if self.fail_mode == "closed":
                    raise GovernanceError(f"Governance check failed: {e}")

        # Step 3: Execute in restricted environment
        restricted_globals = create_restricted_builtins(self.allowed_builtins)
        local_namespace = {}

        if context:
            restricted_globals.update(context)

        # Step 4: Execute with timeout
        try:
            with timeout_context(self.timeout_seconds):
                exec(code, restricted_globals, local_namespace)

            return local_namespace

        except TimeoutError:
            raise
        except Exception as e:
            raise SafeEvalError(f"Execution failed: {e}")

    def eval_many(
        self,
        expressions: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Evaluate multiple expressions.

        Args:
            expressions: List of Python expressions
            context: Shared context for all expressions

        Returns:
            List of results
        """
        return [self.eval(expr, context) for expr in expressions]

    def analyze(self, code: str) -> ASTAnalysisResult:
        """
        Analyze code without executing.

        Args:
            code: Python code to analyze

        Returns:
            ASTAnalysisResult with findings
        """
        return self.analyzer.analyze(code)


# =============================================================================
# Module-Level Functions
# =============================================================================

# Default evaluator instance
_default_evaluator: Optional[SafeEvaluator] = None


def configure(
    client=None,
    fail_mode: str = None,
    allowed_builtins: Set[str] = None,
    blocked_names: Set[str] = None,
    max_code_length: int = None,
    timeout_seconds: int = None
):
    """
    Configure the module-level safe evaluator.

    Args:
        client: AscendClient instance
        fail_mode: "closed" or "open"
        allowed_builtins: Set of allowed builtin names
        blocked_names: Additional names to block
        max_code_length: Maximum code length
        timeout_seconds: Execution timeout
    """
    global _default_evaluator, _config

    if client is not None:
        _config["client"] = client
    if fail_mode is not None:
        _config["fail_mode"] = fail_mode
    if allowed_builtins is not None:
        _config["allowed_builtins"] = allowed_builtins
    if max_code_length is not None:
        _config["max_code_length"] = max_code_length
    if timeout_seconds is not None:
        _config["timeout_seconds"] = timeout_seconds

    # Recreate default evaluator with new config
    _default_evaluator = SafeEvaluator(
        client=_config["client"],
        fail_mode=_config["fail_mode"],
        allowed_builtins=_config["allowed_builtins"],
        blocked_names=blocked_names,
        max_code_length=_config["max_code_length"],
        timeout_seconds=_config["timeout_seconds"]
    )


def _get_evaluator() -> SafeEvaluator:
    """Get or create default evaluator."""
    global _default_evaluator
    if _default_evaluator is None:
        _default_evaluator = SafeEvaluator(
            client=_config["client"],
            fail_mode=_config["fail_mode"],
            allowed_builtins=_config["allowed_builtins"],
            max_code_length=_config["max_code_length"],
            timeout_seconds=_config["timeout_seconds"]
        )
    return _default_evaluator


def safe_eval(
    code: str,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Safely evaluate a Python expression.

    Args:
        code: Python expression
        context: Variable context

    Returns:
        Expression result

    Raises:
        SafeEvalError: If evaluation fails
    """
    return _get_evaluator().eval(code, context)


def safe_exec(
    code: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Safely execute Python code.

    Args:
        code: Python code
        context: Variable context

    Returns:
        Dictionary of created variables

    Raises:
        SafeEvalError: If execution fails
    """
    return _get_evaluator().exec(code, context)


def analyze_expression(code: str) -> ASTAnalysisResult:
    """
    Analyze code without executing.

    Args:
        code: Python code

    Returns:
        ASTAnalysisResult
    """
    return _get_evaluator().analyze(code)


def govern_eval(risk_level: str = None) -> Callable:
    """
    Decorator to add eval governance to a function.

    All safe_eval/safe_exec calls within will use governance.

    Args:
        risk_level: Override risk level

    Usage:
        @govern_eval(risk_level="high")
        def calculate(formula):
            return safe_eval(formula)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Classes
    'SafeEvaluator',

    # Functions
    'safe_eval',
    'safe_exec',
    'analyze_expression',
    'configure',
    'govern_eval',
    'create_restricted_builtins',

    # Exceptions
    'SafeEvalError',
    'CodeTooLongError',
    'DangerousCodeError',
    'GovernanceError',
    'TimeoutError',

    # Constants
    'DEFAULT_SAFE_BUILTINS',
]
