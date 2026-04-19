"""SEC-REL-001: Python SDK public-surface inventory via AST.

Produces a JSON-serializable shape:
  {
    "sha": "<source hash>",
    "modules": {"client.py": {"classes": {"AscendClient": {"methods": {...}}}, ...}},
    "exports": ["AscendClient", "FailMode", ...],
    "class_method_index": {"AscendClient": {"evaluate_action": {...}, ...}, ...}
  }
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
from typing import Any, Dict, List


def _method_record(node) -> Dict[str, Any]:
    args = [a.arg for a in node.args.args]
    kwonly = [a.arg for a in node.args.kwonlyargs]
    return {
        "name": node.name,
        "args": args,
        "kwonly": kwonly,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
    }


def _parse_module(path: pathlib.Path) -> Dict[str, Any]:
    tree = ast.parse(path.read_text())
    mod: Dict[str, Any] = {"classes": {}, "functions": {}, "exports_all": None}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods: Dict[str, Any] = {}
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if sub.name == "__init__" or not sub.name.startswith("_"):
                        methods[sub.name] = _method_record(sub)
            mod["classes"][node.name] = {"methods": methods}
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            mod["functions"][node.name] = _method_record(node)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                    mod["exports_all"] = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
    return mod


def build_surface(sdk_root: pathlib.Path) -> Dict[str, Any]:
    modules: Dict[str, Any] = {}
    hasher = hashlib.sha256()
    for p in sorted(sdk_root.glob("*.py")):
        modules[p.name] = _parse_module(p)
        hasher.update(p.read_bytes())

    init = modules.get("__init__.py", {})
    exports = init.get("exports_all") or []

    class_method_index: Dict[str, Dict[str, Any]] = {}
    for mod_name, mod in modules.items():
        for cls_name, cls in mod.get("classes", {}).items():
            class_method_index.setdefault(cls_name, {}).update(cls.get("methods", {}))

    return {
        "sha": hasher.hexdigest()[:16],
        "modules": modules,
        "exports": exports,
        "class_method_index": class_method_index,
    }


def class_has_method(surface: Dict[str, Any], class_name: str, method: str) -> bool:
    return method in surface.get("class_method_index", {}).get(class_name, {})


def save(surface: Dict[str, Any], path: pathlib.Path) -> None:
    path.write_text(json.dumps(surface, indent=2, sort_keys=True))
