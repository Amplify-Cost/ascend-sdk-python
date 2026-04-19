"""SEC-REL-001: fenced-code-block extractor for Markdown / MDX docs.

Per-block record:
  {
    "file": str, "line": int, "lang": "py"|"js"|"ts",
    "content": str, "hash": str,
    "skip": bool, "skip_reason": Optional[str]
  }

Skip annotation (§6.5 of Gate 1 design):
  <!-- contract-test: skip reason="..." -->
  ```python
  ...
  ```

Reason string is required, >= 10 chars, must not contain TODO/FIXME. A
malformed or missing reason on a skip directive is itself a contract
violation — see runner.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

LANG_MAP = {
    "python": "py", "py": "py",
    "javascript": "js", "js": "js",
    "typescript": "ts", "ts": "ts", "tsx": "ts", "jsx": "js",
}

FENCE_OPEN = re.compile(r"^```([a-zA-Z]+)\s*(.*)$")
SKIP_DIRECTIVE = re.compile(
    r"<!--\s*contract-test:\s*skip\s+reason=\"([^\"]*)\"\s*-->"
)
BAD_REASON_TOKENS = re.compile(r"\b(TODO|FIXME|todo|fixme)\b")


@dataclass
class Block:
    file: str
    line: int
    lang: str
    content: str
    hash: str
    skip: bool = False
    skip_reason: Optional[str] = None
    skip_malformed: Optional[str] = None


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def extract_from_file(path: pathlib.Path) -> List[Block]:
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return []
    lines = text.splitlines()
    blocks: List[Block] = []

    pending_skip: Optional[str] = None
    pending_skip_malformed: Optional[str] = None

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        m_skip = SKIP_DIRECTIVE.search(line)
        if m_skip:
            reason = m_skip.group(1).strip()
            pending_skip_malformed = None
            if len(reason) < 10:
                pending_skip_malformed = "reason-too-short"
            elif BAD_REASON_TOKENS.search(reason):
                pending_skip_malformed = "reason-contains-todo-or-fixme"
            pending_skip = reason
            i += 1
            continue

        if line.strip() == "" or line.lstrip().startswith("<!--"):
            i += 1
            continue

        m = FENCE_OPEN.match(line)
        if m:
            lang_raw = m.group(1).lower()
            if lang_raw not in LANG_MAP:
                pending_skip = None
                pending_skip_malformed = None
                i += 1
                continue
            lang = LANG_MAP[lang_raw]
            start_line = i + 1
            buf: List[str] = []
            j = i + 1
            while j < n and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            content = "\n".join(buf)
            blocks.append(Block(
                file=str(path),
                line=start_line,
                lang=lang,
                content=content,
                hash=_hash(content),
                skip=bool(pending_skip) and pending_skip_malformed is None,
                skip_reason=pending_skip,
                skip_malformed=pending_skip_malformed,
            ))
            pending_skip = None
            pending_skip_malformed = None
            i = j + 1
            continue

        pending_skip = None
        pending_skip_malformed = None
        i += 1

    return blocks


def extract_from_paths(paths: Iterable[pathlib.Path], suffixes=(".md", ".mdx")) -> List[Block]:
    out: List[Block] = []
    for p in paths:
        if p.is_file() and p.suffix in suffixes:
            out.extend(extract_from_file(p))
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.suffix in suffixes and "node_modules" not in f.parts and ".vercel" not in f.parts and ".docusaurus" not in f.parts:
                    out.extend(extract_from_file(f))
    return out
