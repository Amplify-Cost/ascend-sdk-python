"""SEC-REL-001: write human + machine reports and append the audit log.

Per Evidence A: every echoed field is sanitized before it reaches the
Markdown output. File paths and symbol names go through the allowlist
scrubber; free-text goes through HTML-escape + control-char strip.

Audit log is append-only JSONL; one line per run. Never rewrite prior
lines.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
from typing import Any, Dict, List, Optional

from .sanitizer import sanitize_symbol, sanitize_freetext, sanitize_path


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json_report(path: pathlib.Path, records: List[Dict[str, Any]]) -> None:
    path.write_text(json.dumps(records, indent=2, ensure_ascii=True, sort_keys=True))


def write_markdown_report(path: pathlib.Path, records: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# SEC-REL-001 Contract Test Report")
    lines.append("")
    lines.append(f"- runner_version: `{sanitize_symbol(str(summary.get('runner_version', '')))}`")
    lines.append(f"- sdk_sha: `{sanitize_symbol(str(summary.get('sdk_sha', '')))}`")
    lines.append(f"- timestamp: `{sanitize_symbol(str(summary.get('timestamp', '')))}`")
    lines.append("")
    lines.append(
        f"**{summary.get('total', 0)} total** · "
        f"{summary.get('passed', 0)} passed · "
        f"{summary.get('failed', 0)} failed · "
        f"{summary.get('skipped', 0)} skipped"
    )
    lines.append("")

    failed = [r for r in records if r.get("status") == "fail"]
    if failed:
        lines.append("## Failures")
        lines.append("")
        lines.append("| File | Line | Lang | Missing symbol | Suggestion |")
        lines.append("|---|---|---|---|---|")
        for r in failed:
            f = sanitize_path(r.get("file", ""))
            ln = sanitize_symbol(str(r.get("line", "")))
            lang = sanitize_symbol(str(r.get("lang", "")))
            sym = sanitize_symbol(str(r.get("missing_symbol", "")))
            sug = sanitize_symbol(str(r.get("suggestion", "") or ""))
            lines.append(f"| {f} | {ln} | {lang} | `{sym}` | {sug} |")
        lines.append("")

    skipped = [r for r in records if r.get("status") == "skip"]
    if skipped:
        lines.append("## Skipped (with reason)")
        lines.append("")
        lines.append("| File | Line | Reason |")
        lines.append("|---|---|---|")
        for r in skipped:
            f = sanitize_path(r.get("file", ""))
            ln = sanitize_symbol(str(r.get("line", "")))
            reason = sanitize_freetext(r.get("skip_reason", "") or "")
            lines.append(f"| {f} | {ln} | {reason} |")
        lines.append("")

    path.write_text("\n".join(lines) + "\n")


def append_audit_line(
    audit_file: pathlib.Path,
    *,
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    sdk_sha: str,
    docs_sha: str,
    node_sha: str,
    trigger: str,
    runner_version: str,
) -> None:
    entry = {
        "timestamp": _now_iso(),
        "runner_version": sanitize_symbol(runner_version),
        "sdk_sha": sanitize_symbol(sdk_sha),
        "docs_sha": sanitize_symbol(docs_sha),
        "node_sha": sanitize_symbol(node_sha),
        "total": int(total),
        "passed": int(passed),
        "failed": int(failed),
        "skipped": int(skipped),
        "trigger": sanitize_symbol(trigger),
    }
    line = json.dumps(entry, ensure_ascii=True, sort_keys=True)
    with audit_file.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def summarize(records: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "total": len(records),
        "passed": sum(1 for r in records if r.get("status") == "pass"),
        "failed": sum(1 for r in records if r.get("status") == "fail"),
        "skipped": sum(1 for r in records if r.get("status") == "skip"),
    }
