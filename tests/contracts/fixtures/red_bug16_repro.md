# RED — BUG-16 reproduction (SEC-REL-001 validation case A)

The gate MUST flag this block: `submit_action` does not exist on
`AscendClient` in SDK 2.3.0; the canonical method is `evaluate_action`.

```python
from ascend import AscendClient

client = AscendClient(
    api_key="fake_contract_test_key_do_not_use",
    api_url="https://contract-test.invalid",
    agent_id="test-alan-001",
)

result = client.submit_action(
    action_type="database.read",
    resource="reports_db",
)
print(result.decision, result.risk_score)
```
