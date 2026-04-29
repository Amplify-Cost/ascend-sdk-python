"""SEC-REL-001: Node SDK public-surface inventory.

Parses the compiled `dist/index.d.ts` to extract exported class names and
method names. We avoid adding a TypeScript compiler dependency — the .d.ts
is declaration-only and regex-tractable for "class X" and "methodName(…)"
at top-level indentation.

Scope: exported classes and their public method names. Good enough to catch
"docs reference SubmitAction but SDK provides EvaluateAction" drift. Full
signature parity (arg names / types) is a v1.1 enhancement.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
from typing import Any, Dict, List

_CLASS_DECL = re.compile(r"^(?:export\s+)?declare\s+class\s+([A-Z][A-Za-z0-9_]*)")
_CLASS_DECL_EXPORT = re.compile(r"^export\s+(?:declare\s+)?class\s+([A-Z][A-Za-z0-9_]*)")
# SEC-REL-001 v1.1 (BUG-16 cohort): accept `async` modifier, getter/setter
# keywords, and generic parameters `<...>` between the method name and `(`.
# We intentionally accept name-followed-by-`<`-or-`(` so methods whose
# generic body contains `>` (e.g. `wrap<T extends (...args: any[]) => any>(...)`)
# still match. Without this, generic methods on MCPGovernanceMiddleware
# were falsely reported missing even though they shipped in dist/.
_METHOD_DECL = re.compile(
    r"^\s{4}(?:(?:async|get|set)\s+)?([a-zA-Z_][A-Za-z0-9_]*)\s*(?:<|\()"
)


def build_surface(sdk_root: pathlib.Path) -> Dict[str, Any]:
    dts = sdk_root / "dist" / "index.d.ts"
    if not dts.exists():
        return {"sha": "", "classes": {}, "exports": []}

    text = dts.read_text(errors="replace")
    sha = hashlib.sha256(text.encode()).hexdigest()[:16]

    classes: Dict[str, Dict[str, Any]] = {}
    current_class: str | None = None
    depth = 0

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        m = _CLASS_DECL.match(line) or _CLASS_DECL_EXPORT.match(line)
        if m and "{" in line:
            current_class = m.group(1)
            classes.setdefault(current_class, {"methods": {}})
            depth = line.count("{") - line.count("}")
            continue

        if current_class:
            if "{" in stripped:
                depth += stripped.count("{")
            if "}" in stripped:
                depth -= stripped.count("}")
                if depth <= 0:
                    current_class = None
                    depth = 0
                    continue

            mm = _METHOD_DECL.match(raw_line)
            if mm and current_class:
                name = mm.group(1)
                if name.startswith("_") or name in ("constructor",):
                    continue
                classes[current_class]["methods"][name] = {"name": name}

    return {
        "sha": sha,
        "classes": classes,
        "exports": sorted(classes.keys()),
        "class_method_index": {c: cls["methods"] for c, cls in classes.items()},
    }


def class_has_method(surface: Dict[str, Any], class_name: str, method: str) -> bool:
    return method in surface.get("class_method_index", {}).get(class_name, {})
