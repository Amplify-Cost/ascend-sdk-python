"""
DEEP-002: AST Analyzer for Dynamic Code Safety

Analyzes Python code AST (Abstract Syntax Tree) to detect
dangerous constructs before execution.

Features:
- Detects dangerous function calls (eval, exec, __import__)
- Detects sandbox escape attempts via dunder attributes
- Detects import statements
- Detects file/network operations
- Configurable allowed/blocked lists

This provides Layer 1 (local, fast) security checking
before Layer 2 (backend API) governance.

Compliance: CWE-94, CWE-95, MITRE T1059.006
Author: Enterprise Security Team
Version: 1.0.0
"""

import ast
import logging
from dataclasses import dataclass, field
from typing import Set, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Finding Data Classes
# =============================================================================

@dataclass
class ASTFinding:
    """Represents a dangerous construct found in code."""
    category: str  # code_injection, sandbox_escape, file_access, network_access
    severity: str  # critical, high, medium, low
    node_type: str  # Name, Attribute, Call, Import, etc.
    name: str  # The specific name/attribute
    line: int
    col: int
    description: str
    cwe_ids: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "category": self.category,
            "severity": self.severity,
            "node_type": self.node_type,
            "name": self.name,
            "line": self.line,
            "col": self.col,
            "description": self.description,
            "cwe_ids": self.cwe_ids,
            "mitre_techniques": self.mitre_techniques
        }


@dataclass
class ASTAnalysisResult:
    """Result of AST analysis."""
    code_length: int
    findings: List[ASTFinding] = field(default_factory=list)
    parse_error: Optional[str] = None

    @property
    def is_safe(self) -> bool:
        """Code is safe if no critical/high findings."""
        return not any(
            f.severity in ("critical", "high")
            for f in self.findings
        )

    @property
    def has_dangerous_constructs(self) -> bool:
        """Returns True if any dangerous constructs found."""
        return len(self.findings) > 0

    @property
    def max_severity(self) -> Optional[str]:
        """Returns the highest severity found."""
        severities = ["critical", "high", "medium", "low"]
        for sev in severities:
            if any(f.severity == sev for f in self.findings):
                return sev
        return None

    @property
    def reason(self) -> Optional[str]:
        """Returns description of the most severe finding."""
        if not self.findings:
            return None
        # Sort by severity and return first
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(
            self.findings,
            key=lambda f: severity_order.get(f.severity, 99)
        )
        return sorted_findings[0].description

    def to_dict(self):
        return {
            "code_length": self.code_length,
            "is_safe": self.is_safe,
            "has_dangerous_constructs": self.has_dangerous_constructs,
            "max_severity": self.max_severity,
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "parse_error": self.parse_error
        }


# =============================================================================
# AST Analyzer
# =============================================================================

class ASTAnalyzer(ast.NodeVisitor):
    """
    Analyze Python code AST for dangerous constructs.

    This analyzer walks the AST and identifies:
    1. Dangerous function calls (eval, exec, __import__, compile)
    2. Sandbox escape attempts via dunder attributes
    3. Import statements (can load arbitrary code)
    4. File operations (open, io module)
    5. Network operations (socket, requests, etc.)
    """

    # Dangerous function names that allow code execution
    DANGEROUS_FUNCTIONS: Set[str] = {
        "eval", "exec", "compile",
        "__import__", "importlib",
        "getattr", "setattr", "delattr",  # Can access dunders
        "globals", "locals", "vars",  # Namespace access
        "input",  # Can be used for injection
    }

    # Dangerous names that indicate sandbox escape attempts
    DANGEROUS_NAMES: Set[str] = {
        "__import__", "__builtins__", "__globals__",
        "__code__", "__class__", "__bases__", "__mro__",
        "__subclasses__", "__dict__", "__closure__",
        "__self__", "__func__", "__module__",
        "__loader__", "__spec__", "__cached__",
        "__file__", "__name__", "__doc__",
    }

    # Dangerous attribute accesses
    DANGEROUS_ATTRIBUTES: Set[str] = {
        "__class__", "__bases__", "__mro__", "__subclasses__",
        "__globals__", "__code__", "__closure__", "__self__",
        "__func__", "__dict__", "__builtins__",
    }

    # File operation functions
    FILE_OPERATIONS: Set[str] = {
        "open", "file", "read", "write", "readlines", "writelines",
    }

    # Network modules (if accessed as names)
    NETWORK_MODULES: Set[str] = {
        "socket", "urllib", "requests", "httpx", "aiohttp",
        "http", "ftplib", "smtplib", "poplib", "imaplib",
    }

    def __init__(
        self,
        allowed_builtins: Optional[Set[str]] = None,
        blocked_names: Optional[Set[str]] = None,
        allow_imports: bool = False
    ):
        """
        Initialize the AST analyzer.

        Args:
            allowed_builtins: Set of allowed builtin names (whitelist)
            blocked_names: Additional names to block (blacklist)
            allow_imports: Whether to allow import statements
        """
        self.allowed_builtins = allowed_builtins or set()
        self.blocked_names = blocked_names or set()
        self.allow_imports = allow_imports
        self.findings: List[ASTFinding] = []

    def analyze(self, code: str) -> ASTAnalysisResult:
        """
        Analyze Python code for dangerous constructs.

        Args:
            code: Python source code string

        Returns:
            ASTAnalysisResult with findings
        """
        self.findings = []

        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            return ASTAnalysisResult(
                code_length=len(code),
                parse_error=f"Syntax error: {e}"
            )

        return ASTAnalysisResult(
            code_length=len(code),
            findings=self.findings
        )

    def visit_Import(self, node: ast.Import):
        """Detect import statements."""
        if not self.allow_imports:
            for alias in node.names:
                self.findings.append(ASTFinding(
                    category="code_injection",
                    severity="critical",
                    node_type="Import",
                    name=alias.name,
                    line=node.lineno,
                    col=node.col_offset,
                    description=f"Import statement not allowed: {alias.name}",
                    cwe_ids=["CWE-94"],
                    mitre_techniques=["T1059.006"]
                ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Detect from ... import statements."""
        if not self.allow_imports:
            self.findings.append(ASTFinding(
                category="code_injection",
                severity="critical",
                node_type="ImportFrom",
                name=node.module or "*",
                line=node.lineno,
                col=node.col_offset,
                description=f"From import not allowed: from {node.module} import ...",
                cwe_ids=["CWE-94"],
                mitre_techniques=["T1059.006"]
            ))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Detect dangerous function calls."""
        func_name = self._get_call_name(node)

        if func_name:
            # Check dangerous functions
            if func_name in self.DANGEROUS_FUNCTIONS:
                if func_name not in self.allowed_builtins:
                    severity = "critical" if func_name in ("eval", "exec", "__import__", "compile") else "high"
                    self.findings.append(ASTFinding(
                        category="code_injection",
                        severity=severity,
                        node_type="Call",
                        name=func_name,
                        line=node.lineno,
                        col=node.col_offset,
                        description=f"Dangerous function call: {func_name}()",
                        cwe_ids=["CWE-94", "CWE-95"],
                        mitre_techniques=["T1059.006"]
                    ))

            # Check file operations
            if func_name in self.FILE_OPERATIONS:
                self.findings.append(ASTFinding(
                    category="file_access",
                    severity="high",
                    node_type="Call",
                    name=func_name,
                    line=node.lineno,
                    col=node.col_offset,
                    description=f"File operation: {func_name}()",
                    cwe_ids=["CWE-22", "CWE-73"],
                    mitre_techniques=["T1083"]
                ))

            # Check blocked names
            if func_name in self.blocked_names:
                self.findings.append(ASTFinding(
                    category="blocked",
                    severity="high",
                    node_type="Call",
                    name=func_name,
                    line=node.lineno,
                    col=node.col_offset,
                    description=f"Blocked function: {func_name}()",
                    cwe_ids=["CWE-94"],
                    mitre_techniques=["T1059.006"]
                ))

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """Detect dangerous name access."""
        name = node.id

        # Check dunder names (sandbox escape)
        if name in self.DANGEROUS_NAMES:
            self.findings.append(ASTFinding(
                category="sandbox_escape",
                severity="critical",
                node_type="Name",
                name=name,
                line=node.lineno,
                col=node.col_offset,
                description=f"Dangerous name access: {name}",
                cwe_ids=["CWE-94"],
                mitre_techniques=["T1059.006"]
            ))

        # Check network modules
        if name in self.NETWORK_MODULES:
            self.findings.append(ASTFinding(
                category="network_access",
                severity="high",
                node_type="Name",
                name=name,
                line=node.lineno,
                col=node.col_offset,
                description=f"Network module access: {name}",
                cwe_ids=["CWE-918"],
                mitre_techniques=["T1071"]
            ))

        # Check blocked names
        if name in self.blocked_names:
            self.findings.append(ASTFinding(
                category="blocked",
                severity="high",
                node_type="Name",
                name=name,
                line=node.lineno,
                col=node.col_offset,
                description=f"Blocked name: {name}",
                cwe_ids=["CWE-94"],
                mitre_techniques=["T1059.006"]
            ))

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Detect dangerous attribute access."""
        attr = node.attr

        # Check dunder attributes (sandbox escape)
        if attr in self.DANGEROUS_ATTRIBUTES:
            self.findings.append(ASTFinding(
                category="sandbox_escape",
                severity="critical",
                node_type="Attribute",
                name=attr,
                line=node.lineno,
                col=node.col_offset,
                description=f"Dangerous attribute access: .{attr}",
                cwe_ids=["CWE-94"],
                mitre_techniques=["T1059.006"]
            ))

        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract function name from Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


# =============================================================================
# Convenience Functions
# =============================================================================

def analyze_code(
    code: str,
    allowed_builtins: Optional[Set[str]] = None,
    blocked_names: Optional[Set[str]] = None,
    allow_imports: bool = False
) -> ASTAnalysisResult:
    """
    Analyze Python code for dangerous constructs.

    Args:
        code: Python source code
        allowed_builtins: Whitelist of allowed builtins
        blocked_names: Additional names to block
        allow_imports: Whether to allow imports

    Returns:
        ASTAnalysisResult with findings
    """
    analyzer = ASTAnalyzer(
        allowed_builtins=allowed_builtins,
        blocked_names=blocked_names,
        allow_imports=allow_imports
    )
    return analyzer.analyze(code)


def is_code_safe(
    code: str,
    allowed_builtins: Optional[Set[str]] = None
) -> bool:
    """
    Quick check if code is safe to execute.

    Args:
        code: Python source code
        allowed_builtins: Whitelist of allowed builtins

    Returns:
        True if code has no critical/high findings
    """
    result = analyze_code(code, allowed_builtins=allowed_builtins)
    return result.is_safe


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'ASTAnalyzer',
    'ASTAnalysisResult',
    'ASTFinding',
    'analyze_code',
    'is_code_safe',
]
