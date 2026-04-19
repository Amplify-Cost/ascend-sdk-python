# RED — missing-method reproduction (SEC-REL-001 validation case A)

The gate MUST flag this block: `nonexistent_fictitious_method` does not
exist on `AscendClient` and was never part of any published SDK surface.

Originally this fixture referenced `submit_action` (the BUG-16 symbol).
After SDK 2.4.0 landed the BUG-16 cohort fix, `submit_action` is a
deprecated compat shim that forwards to `evaluate_action`, so it no
longer triggers a contract violation. The fixture was updated to use a
name that is guaranteed to remain absent, so the RED self-test keeps
exercising the gate's missing-symbol detection.

```python
from ascend import AscendClient

client = AscendClient(
    api_key="fake_contract_test_key_do_not_use",
    api_url="https://contract-test.invalid",
    agent_id="test-alan-001",
)

# Intentionally-missing method — must trigger a contract violation.
result = client.nonexistent_fictitious_method(
    action_type="database.read",
    resource="reports_db",
)
print(result.decision, result.risk_score)
```
