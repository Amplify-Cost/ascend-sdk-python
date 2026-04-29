# GREEN — correct usage (SEC-REL-001 validation case B)

The gate MUST pass silently on this block: `evaluate_action` exists.

```python
from ascend import AscendClient

client = AscendClient(
    api_key="fake_contract_test_key_do_not_use",
    api_url="https://contract-test.invalid",
    agent_id="test-green-001",
)

result = client.evaluate_action(
    action_type="database.read",
    resource="reports_db",
)
print(result.decision, result.risk_score)
```
