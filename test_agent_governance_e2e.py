#!/usr/bin/env python3
"""
OW-AI Agent Governance E2E Test
================================
Simulates how a REAL customer's AI agent would interact with OW-AI governance.

This demonstrates the complete flow:
1. Agent wants to perform an action (e.g., write a file)
2. Agent calls OW-AI SDK to request permission
3. OW-AI evaluates risk and policies
4. Returns: approved (proceed), pending (wait), or denied (blocked)

Usage:
    python test_agent_governance_e2e.py --api-key "owkai_xxx"
"""

import requests
import json
import time
import argparse
from datetime import datetime

BASE_URL = "https://pilot.owkai.app"


class AgentGovernanceClient:
    """
    This simulates what the OW-AI SDK does inside a customer's AI agent.

    In a real deployment, customers install our SDK which wraps these API calls.
    """

    def __init__(self, api_key: str, agent_id: str):
        self.api_key = api_key
        self.agent_id = agent_id
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        print(f"\n[SDK] Initialized OW-AI Governance Client")
        print(f"[SDK] Agent ID: {agent_id}")
        print(f"[SDK] Governance Endpoint: {BASE_URL}")

    def request_permission(self, tool_name: str, action_type: str,
                          description: str, target_resource: str = None,
                          risk_score: int = None) -> dict:
        """
        REQUEST PERMISSION BEFORE ACTING

        This is the core governance flow:
        - Agent wants to do something (write file, call API, query DB)
        - BEFORE executing, agent asks OW-AI: "Can I do this?"
        - OW-AI evaluates and returns decision

        Args:
            tool_name: The MCP tool/capability (e.g., "filesystem", "database", "api-gateway")
            action_type: What the tool will do (e.g., "write", "read", "execute")
            description: Human-readable explanation of why
            target_resource: The specific resource being accessed
            risk_score: Optional risk override (normally calculated by OW-AI)
        """

        payload = {
            "agent_id": self.agent_id,
            "tool_name": tool_name,
            "action_type": action_type,
            "description": description,
            "target_resource": target_resource or "unspecified",
            "parameters": {
                "requested_at": datetime.now().isoformat(),
                "sdk_version": "1.0.0"
            }
        }

        if risk_score is not None:
            payload["risk_score"] = risk_score

        print(f"\n{'─'*60}")
        print(f"[AGENT] Requesting permission from OW-AI Governance")
        print(f"{'─'*60}")
        print(f"  Tool:        {tool_name}")
        print(f"  Action:      {action_type}")
        print(f"  Resource:    {target_resource}")
        print(f"  Reason:      {description}")
        if risk_score:
            print(f"  Risk Hint:   {risk_score}")
        print(f"{'─'*60}")

        response = requests.post(
            f"{BASE_URL}/api/sdk/agent-action",
            headers=self.headers,
            json=payload
        )

        if response.status_code in [200, 201]:
            result = response.json()
            status = result.get('status', 'unknown')

            # Color-coded status for visibility
            status_display = {
                'approved': '✅ APPROVED',
                'auto-approved': '✅ AUTO-APPROVED',
                'pending': '⏳ PENDING REVIEW',
                'denied': '❌ DENIED',
                'rejected': '❌ REJECTED'
            }.get(status, f'❓ {status.upper()}')

            print(f"\n[OW-AI RESPONSE]")
            print(f"  Decision:    {status_display}")
            print(f"  Action ID:   {result.get('action_id', 'N/A')}")
            print(f"  Risk Level:  {result.get('risk_level', 'N/A')}")
            if result.get('message'):
                print(f"  Message:     {result.get('message')}")

            return {
                "success": True,
                "status": status,
                "action_id": result.get('action_id'),
                "risk_level": result.get('risk_level'),
                "can_proceed": status in ['approved', 'auto-approved'],
                "needs_review": status == 'pending',
                "blocked": status in ['denied', 'rejected']
            }
        else:
            print(f"\n[ERROR] HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

    def wait_for_approval(self, action_id: int, timeout: int = 30) -> dict:
        """
        Poll for approval status (when action is pending)

        In real usage, the agent would either:
        - Wait and poll until approved/denied
        - Notify user that action is pending
        - Continue with other tasks while waiting
        """
        print(f"\n[SDK] Waiting for human approval (action_id={action_id})...")

        start = time.time()
        while time.time() - start < timeout:
            response = requests.get(
                f"{BASE_URL}/api/agent-action/status/{action_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                status = result.get('status')

                if status != 'pending':
                    print(f"[SDK] Decision received: {status}")
                    return result

            time.sleep(3)
            print(f"[SDK] Still pending... ({int(time.time() - start)}s)")

        print(f"[SDK] Timeout - action still pending")
        return {"status": "pending", "timeout": True}


def simulate_customer_agent():
    """
    SIMULATION: A Customer's AI Agent Using OW-AI Governance

    This shows EXACTLY how a customer's agent would integrate:

    1. Customer's agent is running (e.g., Claude, GPT, custom LLM)
    2. Agent receives a user request that requires sensitive action
    3. Agent calls OW-AI SDK BEFORE executing
    4. Based on response, agent either proceeds or waits
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', required=True)
    args = parser.parse_args()

    print("\n" + "="*70)
    print("  SIMULATION: Customer's AI Agent with OW-AI Governance")
    print("="*70)
    print("""
    This simulates what happens inside a customer's AI agent:

    ┌─────────────────────────────────────────────────────────────────┐
    │  CUSTOMER'S AI AGENT (e.g., Claude, GPT-4, Custom LLM)         │
    │                                                                 │
    │  User Request: "Generate Q4 financial report"                  │
    │                                                                 │
    │  Agent thinks: "I need to write to /reports/financial.csv"     │
    │                                                                 │
    │  BEFORE writing, agent calls OW-AI SDK:                        │
    │  ─────────────────────────────────────────────────────────     │
    │    sdk.request_permission(                                     │
    │        tool="filesystem",                                      │
    │        action="write",                                         │
    │        resource="/reports/financial.csv"                       │
    │    )                                                           │
    │  ─────────────────────────────────────────────────────────     │
    │                                                                 │
    │  IF approved → Execute the action                              │
    │  IF pending  → Wait or notify user                             │
    │  IF denied   → Explain to user why action was blocked          │
    └─────────────────────────────────────────────────────────────────┘
    """)

    # Initialize the SDK (like a customer would)
    sdk = AgentGovernanceClient(
        api_key=args.api_key,
        agent_id="test-agent-001"  # The agent registered in Agent Registry
    )

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 1: Low-Risk Read Operation
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  SCENARIO 1: Agent wants to READ a public file")
    print("  Expected: AUTO-APPROVED (low risk, read-only)")
    print("="*70)

    result1 = sdk.request_permission(
        tool_name="filesystem",
        action_type="read",
        description="Reading public documentation to answer user question",
        target_resource="/docs/public/user-guide.md",
        risk_score=15  # Low risk
    )

    if result1.get('can_proceed'):
        print("\n[AGENT] ✅ Permission granted - executing read operation...")
        print("[AGENT] (In real code, agent would now read the file)")

    time.sleep(1)

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 2: Medium-Risk Database Query
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  SCENARIO 2: Agent wants to QUERY customer database")
    print("  Expected: PENDING (needs human review)")
    print("="*70)

    result2 = sdk.request_permission(
        tool_name="database",
        action_type="query",
        description="Querying customer records to generate support report",
        target_resource="customers.orders",
        risk_score=45  # Medium risk
    )

    if result2.get('needs_review'):
        print("\n[AGENT] ⏳ Action requires human approval")
        print("[AGENT] Notifying user: 'Your request is pending security review'")
        print("[AGENT] (Agent could continue other tasks while waiting)")

    time.sleep(1)

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 3: High-Risk File Write
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  SCENARIO 3: Agent wants to WRITE financial data")
    print("  Expected: PENDING + ALERT (high risk)")
    print("="*70)

    result3 = sdk.request_permission(
        tool_name="filesystem",
        action_type="write",
        description="Writing Q4 financial report with sensitive revenue data",
        target_resource="/data/financial/q4_report.csv",
        risk_score=65  # High risk
    )

    if result3.get('needs_review'):
        print("\n[AGENT] ⚠️ High-risk action flagged for review")
        print("[AGENT] Security team will be alerted")

    time.sleep(1)

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 4: Critical External API Call
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  SCENARIO 4: Agent wants to call EXTERNAL PAYMENT API")
    print("  Expected: CRITICAL ALERT (very high risk)")
    print("="*70)

    result4 = sdk.request_permission(
        tool_name="api-gateway",
        action_type="execute",
        description="Processing refund via Stripe payment gateway",
        target_resource="stripe.com/api/refunds",
        risk_score=85  # Critical risk
    )

    if result4.get('blocked'):
        print("\n[AGENT] 🛑 Action BLOCKED by governance policy")
        print("[AGENT] Informing user: 'This action requires additional approval'")
    elif result4.get('needs_review'):
        print("\n[AGENT] ⚠️ Critical action requires immediate security review")

    # ─────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  TEST COMPLETE - Summary")
    print("="*70)
    print("""
    What happened:
    ─────────────
    1. Scenario 1 (read, risk=15):   Should be AUTO-APPROVED
    2. Scenario 2 (query, risk=45):  Should be PENDING (needs review)
    3. Scenario 3 (write, risk=65):  Should be PENDING + HIGH ALERT
    4. Scenario 4 (API, risk=85):    Should be PENDING + CRITICAL ALERT

    What to check in OW-AI Dashboard:
    ─────────────────────────────────
    • Authorization Center → See pending actions (scenarios 2, 3, 4)
    • AI Alert Management → See alerts for high-risk actions (scenarios 3, 4)
    • Activity Feed → See all 4 actions logged with status

    Try approving/denying:
    ──────────────────────
    1. Go to Authorization Center
    2. Find the pending actions
    3. Click Approve or Deny
    4. The agent would receive this decision via polling
    """)


if __name__ == "__main__":
    simulate_customer_agent()
