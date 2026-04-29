# YELLOW — intentional skip (SEC-REL-001 validation case C)

The gate MUST honor the skip directive, log the skip with the reason, and
not execute the block.

<!-- contract-test: skip reason="pedagogical AttributeError example for SDK migration docs" -->
```python
from ascend import AscendClient

client = AscendClient(
    api_key="fake_contract_test_key_do_not_use",
    api_url="https://contract-test.invalid",
)

# This is the pre-2.0 API, intentionally shown as an error example:
result = client.submit_action(action_type="foo", resource="bar")
```
