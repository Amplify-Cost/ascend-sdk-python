"""BUG-44 regression — ensure get_action_status uses the correct v1 endpoint.

SDK 2.4.0 shipped with a hardcoded legacy path
(/api/agent-action/status/{action_id}) that rejects X-API-Key auth,
causing every evaluate_action(wait_for_decision=True) call to raise
AuthenticationError even on valid keys. This file locks in the 2.4.1
fix so the defect cannot silently return.
"""
import inspect

from ascend import client
from ascend.constants import API_ENDPOINTS


def test_action_status_constant_is_v1():
    assert API_ENDPOINTS["action_status"] == "/api/v1/actions/{action_id}/status"


def test_get_action_status_uses_v1_endpoint():
    source = inspect.getsource(client.AscendClient.get_action_status)
    assert "/api/agent-action/status/" not in source, (
        "BUG-44 regression: hardcoded legacy path returned to get_action_status"
    )
    assert (
        'API_ENDPOINTS["action_status"]' in source
        or "API_ENDPOINTS['action_status']" in source
    ), "BUG-44: get_action_status must use API_ENDPOINTS constant"
