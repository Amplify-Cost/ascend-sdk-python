"""SEC-REL-001: Doc/SDK Contract Test — orchestrator / CLI entry point.

Exit codes:
  0 = all blocks pass (or skipped with valid reason)
  1 = contract violation (missing symbol, malformed skip, unexpected failure)
  2 = infrastructure failure (missing canonical source, credential leak,
      runner crash) — wrapping CI must treat this as failure, never pass.

The runner is fail-closed. Any uncaught exception in main() exits 2.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import traceback
from typing import Any, Dict, List

from . import config
from . import credential_scanner
from . import surface_py
from . import surface_node
from . import extractor
from . import executor
from . import reporter


def _find_suggestion(missing: str, class_method_index: Dict[str, Dict[str, Any]]) -> str:
    if "." not in missing:
        return ""
    cls, method = missing.split(".", 1)
    methods = list(class_method_index.get(cls, {}).keys())
    if not methods:
        return ""
    tokens = [t for t in method.replace("_", " ").split() if t]
    for m in methods:
        mt = set(m.replace("_", " ").split())
        if tokens and any(t in mt for t in tokens):
            return f"did you mean {cls}.{m}?"
    return f"available: {', '.join(sorted(methods)[:5])}"


def _collect_docs_sources(
    extra_paths: List[pathlib.Path], *, isolated: bool = False
) -> List[pathlib.Path]:
    sources: List[pathlib.Path] = []
    if not isolated:
        if config.PUBLIC_DOCS_ROOT.exists():
            sources.append(config.PUBLIC_DOCS_ROOT)
        for f in config.README_FILES:
            if f.exists():
                sources.append(f)
    for p in extra_paths:
        if p.exists():
            sources.append(p)
    return sources


def _docs_sha(sources: List[pathlib.Path]) -> str:
    h = hashlib.sha256()
    for src in sources:
        if src.is_file():
            h.update(src.read_bytes())
        else:
            for f in sorted(src.rglob("*.md")):
                if "node_modules" in f.parts or ".vercel" in f.parts:
                    continue
                h.update(f.read_bytes())
            for f in sorted(src.rglob("*.mdx")):
                if "node_modules" in f.parts or ".vercel" in f.parts:
                    continue
                h.update(f.read_bytes())
    return h.hexdigest()[:16]


def run(
    extra_paths: List[pathlib.Path],
    json_out: pathlib.Path,
    md_out: pathlib.Path,
    *,
    trigger: str = "manual",
    append_audit: bool = True,
    force_crash: bool = False,
    isolated: bool = False,
) -> int:
    config.validate_environment()

    if force_crash:
        raise RuntimeError("SEC-REL-001 crash-test harness tripped intentionally")

    leaked = credential_scanner.scan_env()
    if leaked:
        sys.stderr.write(
            "SEC-REL-001 infra failure: real-shape API key detected in environment\n"
        )
        return config.EXIT_INFRA_FAILURE

    sources = _collect_docs_sources(extra_paths, isolated=isolated)

    fixture_hits = credential_scanner.scan_paths(sources)
    if fixture_hits:
        sys.stderr.write(
            f"SEC-REL-001 infra failure: real-shape API key found in "
            f"{len(fixture_hits)} doc source(s); first: {fixture_hits[0][0]}\n"
        )
        return config.EXIT_INFRA_FAILURE

    py_surface = surface_py.build_surface(config.PYTHON_SDK_ROOT)
    node_surface = surface_node.build_surface(config.NODE_SDK_ROOT)

    blocks = extractor.extract_from_paths(sources)

    records: List[Dict[str, Any]] = []

    for b in blocks:
        if b.skip_malformed:
            records.append({
                "file": b.file, "line": b.line, "lang": b.lang, "hash": b.hash,
                "status": "fail",
                "missing_symbol": f"skip-directive/{b.skip_malformed}",
                "suggestion": "skip reasons must be >=10 chars and may not contain TODO/FIXME",
            })
            continue

        if b.skip:
            records.append({
                "file": b.file, "line": b.line, "lang": b.lang, "hash": b.hash,
                "status": "skip", "skip_reason": b.skip_reason,
            })
            continue

        if b.lang == "py":
            r = executor.execute_python_block(b.content, py_surface["class_method_index"])
        elif b.lang in ("js", "ts"):
            r = executor.check_node_block(b.content, node_surface.get("class_method_index", {}))
        else:
            records.append({
                "file": b.file, "line": b.line, "lang": b.lang, "hash": b.hash,
                "status": "skip", "skip_reason": "lang-not-supported",
            })
            continue

        if r.passed:
            records.append({
                "file": b.file, "line": b.line, "lang": b.lang, "hash": b.hash,
                "status": "pass",
                "executed": r.executed, "ast_fallback": r.used_ast_fallback,
            })
        else:
            index = (
                py_surface["class_method_index"] if b.lang == "py"
                else node_surface.get("class_method_index", {})
            )
            records.append({
                "file": b.file, "line": b.line, "lang": b.lang, "hash": b.hash,
                "status": "fail",
                "missing_symbol": r.missing_symbol or "unknown",
                "suggestion": _find_suggestion(r.missing_symbol or "", index),
                "error_type": r.error_type,
                "error_detail": r.error_detail,
                "executed": r.executed,
                "ast_fallback": r.used_ast_fallback,
            })

    summary = reporter.summarize(records)
    docs_sha_val = _docs_sha(sources)
    summary.update({
        "runner_version": config.RUNNER_VERSION,
        "sdk_sha": py_surface.get("sha", ""),
        "node_sha": node_surface.get("sha", ""),
        "docs_sha": docs_sha_val,
        "timestamp": reporter._now_iso(),
    })

    reporter.write_json_report(json_out, records)
    reporter.write_markdown_report(md_out, records, summary)

    if append_audit:
        reporter.append_audit_line(
            config.AUDIT_LOG_FILE,
            total=summary["total"], passed=summary["passed"],
            failed=summary["failed"], skipped=summary["skipped"],
            sdk_sha=py_surface.get("sha", ""),
            docs_sha=docs_sha_val,
            node_sha=node_surface.get("sha", ""),
            trigger=trigger,
            runner_version=config.RUNNER_VERSION,
        )

    if summary["failed"] > 0:
        return config.EXIT_CONTRACT_VIOLATION
    return config.EXIT_OK


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="contract-test", description="SEC-REL-001 Doc/SDK Contract Test")
    ap.add_argument("--path", type=pathlib.Path, action="append", default=[],
                    help="additional doc path to include (repeatable)")
    ap.add_argument("--json-out", type=pathlib.Path, default=pathlib.Path("/tmp/contract-report.json"))
    ap.add_argument("--md-out", type=pathlib.Path, default=pathlib.Path("/tmp/contract-report.md"))
    ap.add_argument("--trigger", default="manual")
    ap.add_argument("--no-audit", action="store_true", help="skip audit-log append")
    ap.add_argument("--force-crash", action="store_true", help="deliberate-crash test harness")
    ap.add_argument("--isolated", action="store_true",
                    help="scan only --path arguments, skip repo-wide defaults (self-test mode)")
    args = ap.parse_args(argv)

    try:
        return run(
            extra_paths=list(args.path),
            json_out=args.json_out,
            md_out=args.md_out,
            trigger=args.trigger,
            append_audit=not args.no_audit,
            force_crash=args.force_crash,
            isolated=args.isolated,
        )
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(
            "SEC-REL-001 infra failure: runner crashed — "
            f"{type(e).__name__}: {str(e)[:200]}\n"
        )
        traceback.print_exc(file=sys.stderr)
        return config.EXIT_INFRA_FAILURE


if __name__ == "__main__":
    sys.exit(main())
