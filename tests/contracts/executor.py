"""SEC-REL-001: execute a Python doc block under the mock-transport sandbox.

Directive 1 (Gate 1 approval): executable blocks default to execution, NOT
AST-only. Authors cannot silently downgrade a block to parse-only.

Classification rules:
  - Block has `from ascend` or `import ascend` → attempt execution.
    AttributeError on AscendClient.* → CONTRACT VIOLATION (emit missing_symbol).
    Other exceptions → degrade to AST symbol check.
  - No ascend import, or Node/TS lang → AST-only symbol check.
"""
from __future__ import annotations

import ast
import contextlib
import io
import pathlib
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .mock_transport import network_sandbox

SDK_NAMES = frozenset({"AscendClient", "OWKAIClient", "AuthorizedAgent"})


@dataclass
class ExecResult:
    executed: bool
    passed: bool
    missing_symbol: Optional[str] = None
    error_type: Optional[str] = None
    error_detail: Optional[str] = None
    used_ast_fallback: bool = False


def _python_imports_ascend(tree: ast.AST) -> bool:
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                if alias.name == "ascend" or alias.name.startswith("ascend."):
                    return True
        elif isinstance(n, ast.ImportFrom):
            if n.module and (n.module == "ascend" or n.module.startswith("ascend.")):
                return True
    return False


def _is_sdk_constructor(call: ast.AST) -> Optional[str]:
    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
        if call.func.id in SDK_NAMES:
            return call.func.id
    return None


def _python_ast_symbol_check(
    content: str, class_method_index: Dict[str, Dict[str, Any]]
) -> Optional[str]:
    """Parse block; for every `<obj>.<attr>` where obj is a known SDK class
    (or an identifier we've seen assigned from one), return the first
    missing method name. Returns None if surface-clean.

    Tracked assignment forms (SEC-REL-001 C1 fixes for live-fire FNs):
      - module / function-scope:  `x = AscendClient(...)`
      - context manager:          `with AscendClient(...) as x:`
      - instance attribute:       `self.x = AscendClient(...)`
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None

    var_to_class: Dict[str, str] = {}
    self_attr_to_class: Dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            cls = _is_sdk_constructor(node.value)
            if cls is None:
                continue
            for t in node.targets:
                if isinstance(t, ast.Name):
                    var_to_class[t.id] = cls
                elif (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                      and t.value.id == "self"):
                    self_attr_to_class[t.attr] = cls

        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                cls = _is_sdk_constructor(item.context_expr)
                if cls is None:
                    continue
                v = item.optional_vars
                if isinstance(v, ast.Name):
                    var_to_class[v.id] = cls
                elif (isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name)
                      and v.value.id == "self"):
                    self_attr_to_class[v.attr] = cls

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue

        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            cls = var_to_class.get(var_name)
            if cls is None and var_name in SDK_NAMES:
                cls = var_name
            if cls and cls in class_method_index:
                if node.attr not in class_method_index[cls]:
                    return f"{cls}.{node.attr}"

        elif (isinstance(node.value, ast.Attribute)
              and isinstance(node.value.value, ast.Name)
              and node.value.value.id == "self"):
            cls = self_attr_to_class.get(node.value.attr)
            if cls and cls in class_method_index:
                if node.attr not in class_method_index[cls]:
                    return f"{cls}.{node.attr}"

    return None


def execute_python_block(
    content: str, class_method_index: Dict[str, Dict[str, Any]]
) -> ExecResult:
    """Try execute; fall back to AST check on non-SDK-related failure."""
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        missing = _python_ast_symbol_check(content, class_method_index)
        return ExecResult(
            executed=False, passed=missing is None,
            missing_symbol=missing, error_type="SyntaxError",
            error_detail=str(e)[:200], used_ast_fallback=True,
        )

    if not _python_imports_ascend(tree):
        missing = _python_ast_symbol_check(content, class_method_index)
        return ExecResult(
            executed=False, passed=missing is None,
            missing_symbol=missing, used_ast_fallback=True,
        )

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    with network_sandbox():
        ns: Dict[str, Any] = {"__name__": "__contract_exec__"}
        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                exec(compile(tree, "<contract-block>", "exec"), ns)
            return ExecResult(executed=True, passed=True)

        except AttributeError as e:
            msg = str(e)
            missing = None
            for cls in SDK_NAMES:
                if cls in msg:
                    for part in msg.split("'"):
                        if part and part.isidentifier() and part not in SDK_NAMES and not part.startswith("_"):
                            if part not in class_method_index.get(cls, {}):
                                missing = f"{cls}.{part}"
                                break
                    if missing:
                        break
            if missing is None:
                missing = _python_ast_symbol_check(content, class_method_index)
            return ExecResult(
                executed=True, passed=missing is None,
                missing_symbol=missing, error_type="AttributeError",
                error_detail=msg[:200],
            )

        except (ImportError, ModuleNotFoundError) as e:
            msg = str(e)
            if "ascend" in msg:
                return ExecResult(
                    executed=True, passed=False,
                    missing_symbol=msg[:200], error_type="ImportError",
                    error_detail=msg[:200],
                )
            missing = _python_ast_symbol_check(content, class_method_index)
            return ExecResult(
                executed=True, passed=missing is None,
                missing_symbol=missing, error_type="ImportError",
                error_detail=msg[:200], used_ast_fallback=True,
            )

        except Exception as e:
            missing = _python_ast_symbol_check(content, class_method_index)
            return ExecResult(
                executed=True, passed=missing is None,
                missing_symbol=missing, error_type=type(e).__name__,
                error_detail=str(e)[:200], used_ast_fallback=True,
            )


_JS_METHOD_CALL = __import__("re").compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)\s*\("
)
_JS_CLIENT_ASSIGN = __import__("re").compile(
    r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Z][A-Za-z0-9_]*)"
)


def check_node_block(
    content: str, class_method_index: Dict[str, Dict[str, Any]]
) -> ExecResult:
    """Regex-based symbol check for JS/TS blocks.

    Identify `new ClassName(...)` → var binding; then any `var.method(` where
    the class is in the Node surface gets checked against its method index.
    """
    var_to_class: Dict[str, str] = {}
    for m in _JS_CLIENT_ASSIGN.finditer(content):
        var_to_class[m.group(1)] = m.group(2)

    for m in _JS_METHOD_CALL.finditer(content):
        obj, method = m.group(1), m.group(2)
        cls = var_to_class.get(obj)
        if cls and cls in class_method_index:
            if method not in class_method_index[cls]:
                return ExecResult(
                    executed=False, passed=False,
                    missing_symbol=f"{cls}.{method}",
                    used_ast_fallback=True,
                )
    return ExecResult(executed=False, passed=True, used_ast_fallback=True)
