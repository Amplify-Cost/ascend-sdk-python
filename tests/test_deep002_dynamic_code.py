"""
DEEP-002: Dynamic Code Wrapper Unit Tests

Tests for governed eval/exec wrapper and AST analyzer.

Author: Enterprise Security Team
"""

import pytest
from unittest.mock import Mock, patch

# Import modules
import sys
sys.path.insert(0, '..')
from ascend.wrappers.ast_analyzer import (
    ASTAnalyzer,
    ASTAnalysisResult,
    ASTFinding,
    analyze_code,
    is_code_safe
)
from ascend.wrappers.dynamic_code import (
    SafeEvaluator,
    safe_eval,
    safe_exec,
    configure,
    DangerousCodeError,
    CodeTooLongError,
    DEFAULT_SAFE_BUILTINS
)


class TestASTAnalyzer:
    """Tests for AST analyzer."""

    def test_detects_import(self):
        """Test import statement detection."""
        result = analyze_code("import os")

        assert result.has_dangerous_constructs
        assert result.max_severity == "critical"
        assert any(f.name == "os" for f in result.findings)

    def test_detects_from_import(self):
        """Test from...import statement detection."""
        result = analyze_code("from subprocess import run")

        assert result.has_dangerous_constructs
        assert any(f.node_type == "ImportFrom" for f in result.findings)

    def test_detects_eval_call(self):
        """Test eval() call detection."""
        result = analyze_code("eval('1+1')")

        assert result.has_dangerous_constructs
        assert any(f.name == "eval" for f in result.findings)

    def test_detects_exec_call(self):
        """Test exec() call detection."""
        result = analyze_code("exec('x = 1')")

        assert result.has_dangerous_constructs
        assert any(f.name == "exec" for f in result.findings)

    def test_detects_dunder_name(self):
        """Test __builtins__ access detection."""
        result = analyze_code("__builtins__")

        assert result.has_dangerous_constructs
        assert result.max_severity == "critical"

    def test_detects_dunder_attribute(self):
        """Test dunder attribute access detection."""
        result = analyze_code("x.__class__.__bases__")

        assert result.has_dangerous_constructs
        assert any(f.name == "__class__" for f in result.findings)
        assert any(f.name == "__bases__" for f in result.findings)

    def test_detects_sandbox_escape_pattern(self):
        """Test common sandbox escape pattern detection."""
        code = "().__class__.__bases__[0].__subclasses__()"
        result = analyze_code(code)

        assert result.has_dangerous_constructs
        assert result.max_severity == "critical"

    def test_detects_open_call(self):
        """Test file open() detection."""
        result = analyze_code("open('/etc/passwd')")

        assert result.has_dangerous_constructs
        assert any(f.category == "file_access" for f in result.findings)

    def test_safe_math_expression(self):
        """Test that safe math expressions pass."""
        result = analyze_code("2 + 2 * 3")

        assert result.is_safe
        assert len(result.findings) == 0

    def test_safe_list_comprehension(self):
        """Test that safe list comprehension passes."""
        result = analyze_code("[x * 2 for x in range(10)]")

        assert result.is_safe

    def test_syntax_error_handling(self):
        """Test syntax error handling."""
        result = analyze_code("def invalid(")

        assert result.parse_error is not None


class TestSafeEvaluator:
    """Tests for SafeEvaluator class."""

    def test_simple_math(self):
        """Test simple math evaluation."""
        evaluator = SafeEvaluator()
        result = evaluator.eval("2 + 2")

        assert result == 4

    def test_with_context(self):
        """Test evaluation with context variables."""
        evaluator = SafeEvaluator()
        result = evaluator.eval("price * quantity", {"price": 10, "quantity": 5})

        assert result == 50

    def test_allowed_builtins(self):
        """Test allowed builtins work."""
        evaluator = SafeEvaluator(allowed_builtins={"sum", "list", "range"})
        result = evaluator.eval("sum(list(range(5)))")

        assert result == 10  # 0+1+2+3+4

    def test_blocks_dangerous_code(self):
        """Test dangerous code is blocked."""
        evaluator = SafeEvaluator()

        with pytest.raises(DangerousCodeError):
            evaluator.eval("__import__('os').system('ls')")

    def test_blocks_sandbox_escape(self):
        """Test sandbox escape is blocked."""
        evaluator = SafeEvaluator()

        with pytest.raises(DangerousCodeError):
            evaluator.eval("().__class__.__bases__[0]")

    def test_max_code_length(self):
        """Test code length limit."""
        evaluator = SafeEvaluator(max_code_length=10)

        with pytest.raises(CodeTooLongError):
            evaluator.eval("x" * 100)

    def test_exec_creates_variables(self):
        """Test exec creates variables in namespace."""
        evaluator = SafeEvaluator()
        namespace = evaluator.exec("x = 10\ny = 20")

        assert namespace["x"] == 10
        assert namespace["y"] == 20

    def test_analyze_without_execute(self):
        """Test analyze method doesn't execute."""
        evaluator = SafeEvaluator()
        result = evaluator.analyze("1 / 0")  # Would raise ZeroDivisionError if executed

        assert result.is_safe  # Just analyzing, not executing


class TestModuleLevelFunctions:
    """Tests for module-level safe_eval and safe_exec."""

    def test_safe_eval_basic(self):
        """Test safe_eval basic usage."""
        configure(client=None, fail_mode="open")
        result = safe_eval("3 * 4")

        assert result == 12

    def test_safe_eval_with_context(self):
        """Test safe_eval with context."""
        configure(client=None, fail_mode="open")
        result = safe_eval("a + b", {"a": 5, "b": 7})

        assert result == 12

    def test_safe_exec_basic(self):
        """Test safe_exec basic usage."""
        configure(client=None, fail_mode="open")
        namespace = safe_exec("result = 10 * 10")

        assert namespace["result"] == 100


class TestComplianceMappings:
    """Tests for compliance mapping in findings."""

    def test_eval_has_cwe_mapping(self):
        """Test eval detection includes CWE mapping."""
        result = analyze_code("eval('1+1')")

        finding = next(f for f in result.findings if f.name == "eval")
        assert "CWE-94" in finding.cwe_ids or "CWE-95" in finding.cwe_ids

    def test_import_has_mitre_mapping(self):
        """Test import detection includes MITRE mapping."""
        result = analyze_code("import os")

        finding = next(f for f in result.findings if f.name == "os")
        assert "T1059.006" in finding.mitre_techniques


class TestIsCodeSafeHelper:
    """Tests for is_code_safe helper function."""

    def test_safe_code_returns_true(self):
        """Test safe code returns True."""
        assert is_code_safe("1 + 1") is True

    def test_dangerous_code_returns_false(self):
        """Test dangerous code returns False."""
        assert is_code_safe("import os") is False

    def test_with_allowed_builtins(self):
        """Test with custom allowed builtins."""
        assert is_code_safe("len([1,2,3])", allowed_builtins={"len"}) is True


# Run with: pytest tests/test_deep002_dynamic_code.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
