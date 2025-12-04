---
sidebar_position: 10
title: Governance Integration
description: Integrate Ascend governance features into your AI agents using the Python or Node.js SDK
---

# SDK Governance Integration

This guide explains how to integrate Ascend's enterprise governance features into your AI agents using the Python or Node.js SDK.

## Prerequisites

- Ascend SDK v2.0 or later
- API key with governance permissions
- Registered agent in [Ascend Dashboard](https://pilot.owkai.app)

## Installation

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
<TabItem value="python" label="Python" default>

```bash
pip install ascend-sdk
```

</TabItem>
<TabItem value="nodejs" label="Node.js">

```bash
npm install @ascend/sdk
```

</TabItem>
</Tabs>

---

## Circuit Breaker Integration

The SDK automatically handles circuit breaker states for MCP server calls.

<Tabs>
<TabItem value="python" label="Python" default>

```python
from ascend_sdk import AscendClient, FailMode
from ascend_sdk.exceptions import CircuitBreakerOpen

client = AscendClient(
    api_key="owkai_your_api_key",
    agent_id="production-agent-001",
    agent_name="Production Data Agent",
    fail_mode=FailMode.CLOSED,
)

async def query_with_circuit_breaker(query: str):
    """Execute query with automatic circuit breaker handling."""
    try:
        decision = await client.evaluate_action(
            action_type="database.query",
            resource="production_db",
            parameters={"query": query}
        )

        if decision.decision == "allowed":
            result = execute_query(query)
            await client.log_action_completed(decision.action_id, result)
            return result

    except CircuitBreakerOpen as e:
        # MCP server is unhealthy - circuit is open
        logger.warning(f"Circuit open for {e.server_id}")
        logger.warning(f"Recovery in {e.recovery_time}s")
        raise ServiceUnavailableError("Service temporarily unavailable")
```

</TabItem>
<TabItem value="nodejs" label="Node.js">

```typescript
import { AscendClient, FailMode, CircuitBreakerOpenError } from '@ascend/sdk';

const client = new AscendClient({
    apiKey: 'owkai_your_api_key',
    agentId: 'production-agent-001',
    agentName: 'Production Data Agent',
    failMode: FailMode.CLOSED,
});

async function queryWithCircuitBreaker(query: string) {
    try {
        const decision = await client.evaluateAction({
            actionType: 'database.query',
            resource: 'production_db',
            parameters: { query },
        });

        if (decision.decision === 'allowed') {
            const result = await executeQuery(query);
            await client.logActionCompleted(decision.actionId, result);
            return result;
        }
    } catch (error) {
        if (error instanceof CircuitBreakerOpenError) {
            console.warn(`Circuit open, recovery in ${error.recoveryTimeSeconds}s`);
            throw new ServiceUnavailableError();
        }
        throw error;
    }
}
```

</TabItem>
</Tabs>

### Circuit Breaker Status

Check circuit state programmatically:

<Tabs>
<TabItem value="python" label="Python" default>

```python
# Check circuit state
status = await client.get_circuit_status("mcp-server-001")
print(f"State: {status['state']}")
print(f"Failures: {status['failure_count']}")

# Force reset (admin only)
await client.reset_circuit("mcp-server-001")
```

</TabItem>
<TabItem value="nodejs" label="Node.js">

```typescript
// Check circuit state
const status = await client.getCircuitStatus('mcp-server-001');
console.log(`State: ${status.state}`);
console.log(`Failures: ${status.failureCount}`);

// Force reset (admin only)
await client.resetCircuit('mcp-server-001');
```

</TabItem>
</Tabs>

---

## Anomaly-Aware Actions

Incorporate anomaly detection into your agent's decision making.

<Tabs>
<TabItem value="python" label="Python" default>

```python
async def execute_with_anomaly_check(action_type: str, resource: str, params: dict):
    """Execute action with pre-flight anomaly check."""

    # Check if agent is in anomaly state
    health = await client.get_agent_health()

    if health.get("consecutive_anomalies", 0) >= 2:
        logger.warning("Agent showing anomalous behavior")
        params["require_human_approval"] = True

    decision = await client.evaluate_action(
        action_type=action_type,
        resource=resource,
        parameters=params,
        context={
            "anomaly_status": health.get("last_anomaly_severity"),
            "consecutive_anomalies": health.get("consecutive_anomalies", 0),
        }
    )

    return decision
```

</TabItem>
<TabItem value="nodejs" label="Node.js">

```typescript
async function executeWithAnomalyCheck(
    actionType: string,
    resource: string,
    params: Record<string, unknown>
) {
    // Check if agent is in anomaly state
    const health = await client.getAgentHealth();

    if ((health.consecutiveAnomalies ?? 0) >= 2) {
        console.warn('Agent showing anomalous behavior');
        params.requireHumanApproval = true;
    }

    const decision = await client.evaluateAction({
        actionType,
        resource,
        parameters: params,
        context: {
            anomalyStatus: health.lastAnomalySeverity,
            consecutiveAnomalies: health.consecutiveAnomalies ?? 0,
        },
    });

    return decision;
}
```

</TabItem>
</Tabs>

### Webhook Handler for Anomaly Alerts

```python
# Webhook handler for anomaly alerts
@app.post("/webhooks/ascend")
async def handle_ascend_webhook(request: Request):
    payload = await request.json()

    if payload["event"] == "anomaly.detected":
        agent_id = payload["data"]["agent_id"]
        severity = payload["data"]["severity"]

        if severity == "critical":
            await pause_agent_operations(agent_id)
            await notify_security_team(payload["data"])
        elif severity == "high":
            await enable_enhanced_approval(agent_id)
```

---

## Policy-Aware Decisions

Handle policy decisions including conflicts and priorities.

<Tabs>
<TabItem value="python" label="Python" default>

```python
from ascend_sdk import AscendClient, Decision

async def execute_with_policy_handling(action_type: str, resource: str):
    """Execute action with comprehensive policy handling."""

    decision = await client.evaluate_action(
        action_type=action_type,
        resource=resource,
        parameters={"include_policy_details": True}
    )

    if decision.decision == Decision.ALLOWED:
        if decision.metadata.get("policy_conflicts"):
            logger.info(f"Allowed with conflicts: {decision.metadata['policy_conflicts']}")
        return await execute_action()

    elif decision.decision == Decision.DENIED:
        logger.warning(
            f"Denied by policy: {decision.policy_violations}",
            extra={
                "risk_score": decision.risk_score,
                "resolution_strategy": decision.metadata.get("resolution_strategy"),
            }
        )
        raise PolicyDenialError(decision.reason)

    elif decision.decision == Decision.PENDING:
        return await wait_for_approval(decision.approval_request_id)
```

</TabItem>
<TabItem value="nodejs" label="Node.js">

```typescript
import { Decision } from '@ascend/sdk';

async function executeWithPolicyHandling(actionType: string, resource: string) {
    const decision = await client.evaluateAction({
        actionType,
        resource,
        parameters: { includePolicyDetails: true },
    });

    if (decision.decision === Decision.ALLOWED) {
        if (decision.metadata?.policyConflicts) {
            console.info(`Allowed with conflicts: ${decision.metadata.policyConflicts}`);
        }
        return await executeAction();
    }

    if (decision.decision === Decision.DENIED) {
        console.warn(`Denied by policy: ${decision.policyViolations}`);
        throw new PolicyDenialError(decision.reason);
    }

    if (decision.decision === Decision.PENDING) {
        return await waitForApproval(decision.approvalRequestId!);
    }
}
```

</TabItem>
</Tabs>

---

## MCP Server Governance

Wrap MCP tools with Ascend governance using decorators.

<Tabs>
<TabItem value="python" label="Python" default>

```python
from ascend_sdk.mcp import mcp_governance, MCPGovernanceConfig

config = MCPGovernanceConfig(
    wait_for_approval=True,
    approval_timeout_seconds=300,
    log_all_decisions=True,
    respect_circuit_breaker=True,
    anomaly_context=True,
)

@mcp_server.tool()
@mcp_governance(client, "file.read", "/var/data/*", config=config)
async def read_data_file(path: str) -> str:
    """Read a data file with governance."""
    with open(path) as f:
        return f.read()

@mcp_server.tool()
@mcp_governance(client, "file.write", "/var/data/*", config=config)
async def write_data_file(path: str, content: str) -> bool:
    """Write a data file with governance."""
    with open(path, "w") as f:
        f.write(content)
    return True
```

</TabItem>
<TabItem value="nodejs" label="Node.js">

```typescript
import { mcpGovernance, MCPGovernanceConfig } from '@ascend/sdk/mcp';

const config: MCPGovernanceConfig = {
    waitForApproval: true,
    approvalTimeoutMs: 300000,
    logAllDecisions: true,
    respectCircuitBreaker: true,
    anomalyContext: true,
};

const readFile = mcpGovernance(client, {
    actionType: 'file.read',
    resource: '/var/data/*',
    config,
})(async (path: string): Promise<string> => {
    return await fs.readFile(path, 'utf-8');
});
```

</TabItem>
</Tabs>

---

## Error Handling

### Comprehensive Error Handler

```python
from ascend_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CircuitBreakerOpen,
    ConnectionError,
    TimeoutError,
    RateLimitError,
)

async def governed_action(action_type: str, resource: str, params: dict):
    """Execute action with comprehensive error handling."""
    try:
        return await client.evaluate_action(action_type, resource, params)

    except AuthenticationError:
        logger.error("API key invalid or expired")
        raise

    except AuthorizationError as e:
        logger.warning(f"Action denied: {e.policy_violations}")
        await audit_log.record_denial(e)
        raise

    except CircuitBreakerOpen as e:
        logger.warning(f"Service {e.server_id} unavailable")
        await retry_queue.add(action_type, resource, params)
        raise ServiceUnavailableError()

    except RateLimitError as e:
        logger.info(f"Rate limited, retry after {e.retry_after}s")
        await asyncio.sleep(e.retry_after)
        return await governed_action(action_type, resource, params)

    except TimeoutError:
        logger.error("Request timed out")
        raise

    except ConnectionError:
        if client.fail_mode == FailMode.OPEN:
            logger.warning("Connection failed, proceeding in fail-open mode")
            return Decision(decision="allowed", conditions=["fail_open_mode"])
        raise
```

---

## Monitoring Integration

### Datadog Metrics

```python
from datadog import statsd

class MetricsClient:
    def __init__(self, client: AscendClient):
        self.client = client

    async def evaluate_action(self, *args, **kwargs):
        start = time.time()
        try:
            result = await self.client.evaluate_action(*args, **kwargs)
            statsd.increment('ascend.action.evaluated', tags=[
                f'decision:{result.decision}',
                f'agent:{self.client.agent_id}',
            ])
            return result
        except CircuitBreakerOpen:
            statsd.increment('ascend.circuit_breaker.blocked')
            raise
        finally:
            statsd.timing('ascend.action.latency', time.time() - start)
```

---

## Next Steps

<div className="row">
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>Python SDK Reference</h3>
      </div>
      <div className="card__body">
        <p>Complete API reference for the Python SDK.</p>
      </div>
      <div className="card__footer">
        <a className="button button--primary button--block" href="/sdk/python/api-reference">View Reference</a>
      </div>
    </div>
  </div>
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>Node.js SDK Reference</h3>
      </div>
      <div className="card__body">
        <p>Complete API reference for the Node.js SDK.</p>
      </div>
      <div className="card__footer">
        <a className="button button--secondary button--block" href="/sdk/nodejs/installation">View Reference</a>
      </div>
    </div>
  </div>
</div>

## Get Help

- **SDK Issues**: [github.com/anthropics/ascend-sdk-python](https://github.com/anthropics/ascend-sdk-python/issues)
- **Support**: [support@ascendowkai.com](mailto:support@ascendowkai.com)
- **Status**: [status.ascendowkai.com](https://status.ascendowkai.com)
