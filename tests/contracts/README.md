# SEC-REL-001 — Doc/SDK Contract Test

The gate that catches BUG-16-class drift between customer-visible docs and
the SDK surface. Four-layer defense: pre-commit, PR check, Vercel build,
PyPI publish handoff.

## Quick start

```bash
# Run against the real docs (appends to the audit ledger)
python -m tests.contracts.runner \
  --json-out /tmp/report.json \
  --md-out /tmp/report.md \
  --trigger manual

# Self-tests (isolated, no audit append)
pytest tests/contracts/tests/ -v
```

Exit codes:
- `0` — no violations
- `1` — contract violation(s) detected
- `2` — infrastructure failure (missing source, leaked credential, runner crash)

Any non-zero exit in CI is a build failure. There is no silent-pass.

## Authoring docs

Write code blocks the way you always have. The gate runs them against a
mock HTTP transport — no real network, no real credentials.

To skip a block intentionally (e.g., showing a deliberate error):

```md
<!-- contract-test: skip reason="pedagogical example of the pre-2.0 API" -->
```python
client.submit_action(...)  # OLD API
```
```

Rules: reason ≥ 10 chars, no TODO/FIXME tokens, each skip is audit-logged.

## Layout

```
tests/contracts/
  runner.py              # orchestrator / CLI
  config.py              # canonical paths, exit-code constants
  surface_py.py          # Python SDK AST inventory
  surface_node.py        # Node SDK d.ts parser
  extractor.py           # MDX/MD fenced-code extractor
  executor.py            # execute or AST-check a block
  mock_transport.py      # network-isolated stub
  credential_scanner.py  # pre-flight key-shape detector
  sanitizer.py           # allowlist scrubbers for report output
  reporter.py            # JSON + MD + JSONL audit writers
  fixtures/              # RED/GREEN/YELLOW validation fixtures
  tests/                 # self-tests for the gate itself
```

## Related

- [`ascend-audit/`](../../ascend-audit/) — append-only audit ledger
- [`ascend-audit/BOT_IDENTITY.md`](../../ascend-audit/BOT_IDENTITY.md) — bot spec
- [`.github/workflows/contract-docs.yml`](../../.github/workflows/contract-docs.yml) — L2 CI
- [`owkai-pilot-frontend/ascend-docs/scripts/contract-gate.sh`](../../owkai-pilot-frontend/ascend-docs/scripts/contract-gate.sh) — L3 Vercel
