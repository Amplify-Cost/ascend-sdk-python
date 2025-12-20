# ASCEND MCP Server Integration

Enterprise-grade governance for Model Context Protocol (MCP) servers.

[![npm version](https://badge.fury.io/js/ascend-mcp-server.svg)](https://www.npmjs.com/package/ascend-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

## Overview

Add ASCEND governance to your MCP servers to control AI agent tool execution. Every tool invocation is evaluated against enterprise security policies before execution.

**Security Features:**
- Fail-closed design (deny on errors)
- Sensitive data redaction
- Multi-level approval workflows
- Full audit trail (SOC 2, HIPAA, PCI-DSS compliant)

## Installation

```bash
npm install ascend-mcp-server
```

## Quick Start

### 1. Basic Usage

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { McpGovernance } from "ascend-mcp-server";

// Initialize governance
const governance = new McpGovernance({
  apiKey: process.env.ASCEND_API_KEY,
  agentId: "mcp-database-server",
  agentName: "Database MCP Server"
});

// Create MCP server
const server = new Server({ name: "database-server", version: "1.0.0" });

// Handle tool calls with governance
server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  // Evaluate governance
  const decision = await governance.evaluate(name, args, {
    actionType: `database.${name}`,
    resource: "production_db"
  });

  if (!decision.allowed) {
    return {
      content: [{ type: "text", text: `Denied: ${decision.reason}` }],
      isError: true
    };
  }

  // Execute tool
  const result = await executeQuery(args.sql);
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
});
```

### 2. Using Tool Wrapper

```typescript
import { McpGovernance } from "ascend-mcp-server";

const governance = new McpGovernance({
  apiKey: process.env.ASCEND_API_KEY,
  agentId: "mcp-server",
  agentName: "My MCP Server"
});

// Wrap tool handler with governance
const governedQuery = governance.wrapTool(
  async (request) => {
    const { sql } = request.params.arguments;
    return { content: [{ type: "text", text: await db.execute(sql) }] };
  },
  {
    actionType: "database.query",
    resource: "production_db",
    riskLevel: "medium"
  }
);
```

### 3. Using Higher-Order Functions

```typescript
import { withGovernance, highRiskTool } from "ascend-mcp-server";

// Standard governance
const queryHandler = withGovernance({
  agentId: "mcp-server",
  agentName: "Database Server",
  actionType: "database.query",
  resource: "production_db",
  riskLevel: "low"
})(async (request) => {
  return await executeQuery(request.params.arguments.sql);
});

// High-risk tool (requires human approval)
const deleteHandler = highRiskTool({
  agentId: "mcp-server",
  agentName: "Database Server",
  actionType: "database.delete",
  resource: "production_db"
})(async (request) => {
  return await deleteRecords(request.params.arguments);
});
```

## Configuration

### Environment Variables

```bash
export ASCEND_API_KEY="owkai_your_key_here"
export ASCEND_API_URL="https://api.owkai.app"  # Optional
```

### Full Configuration Options

```typescript
const governance = new McpGovernance({
  // Required
  agentId: "mcp-database-server",
  agentName: "Database MCP Server",

  // Optional - API Configuration
  apiKey: process.env.ASCEND_API_KEY,
  baseUrl: "https://pilot.owkai.app",

  // Optional - Security Configuration
  failMode: "closed",           // 'closed' (default) or 'open'
  waitForApproval: true,        // Wait for pending approvals
  approvalTimeoutMs: 300000,    // 5 minutes
  approvalPollIntervalMs: 5000, // 5 seconds

  // Optional - Tool Configuration
  defaultRiskLevel: "medium",
  toolRiskLevels: {
    "query": "low",
    "execute": "high",
    "delete": "critical"
  },
  toolActionTypes: {
    "query": "database.read",
    "execute": "database.write",
    "delete": "database.delete"
  },

  // Optional - Callbacks
  onApprovalRequired: async (decision, toolName) => {
    console.log(`Tool ${toolName} requires approval`);
    // Send notification to Slack, Teams, etc.
  },
  onDenied: async (decision, toolName) => {
    console.log(`Tool ${toolName} was denied: ${decision.reason}`);
  },
  onApproved: async (decision, toolName) => {
    console.log(`Tool ${toolName} was approved`);
  },
  onTimeout: async (decision, toolName) => {
    console.log(`Approval timeout for ${toolName}`);
  }
});
```

## Risk Levels

| Level | Description | Default Behavior |
|-------|-------------|------------------|
| `low` | Read-only operations | Auto-approve |
| `medium` | Write operations | Evaluate policy |
| `high` | Destructive operations | Require review |
| `critical` | Administrative operations | Require approval |

### Automatic Risk Classification

Tools are automatically classified based on name patterns:

| Pattern | Risk Level |
|---------|------------|
| `read`, `get`, `list`, `query` | low |
| `create`, `update`, `write` | medium |
| `delete`, `remove`, `drop` | high |
| `execute`, `admin`, `transfer` | critical |

## Complete Example

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { McpGovernance } from "ascend-mcp-server";

// Initialize governance
const governance = new McpGovernance({
  apiKey: process.env.ASCEND_API_KEY!,
  agentId: "mcp-database-server",
  agentName: "Production Database Server",
  failMode: "closed",
  toolRiskLevels: {
    "query": "low",
    "execute": "high"
  }
});

// Create server
const server = new Server({
  name: "database-server",
  version: "1.0.0"
}, {
  capabilities: { tools: {} }
});

// List available tools
server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "query",
      description: "Execute read-only SQL query",
      inputSchema: {
        type: "object",
        properties: { sql: { type: "string" } },
        required: ["sql"]
      }
    },
    {
      name: "execute",
      description: "Execute SQL statement (requires approval)",
      inputSchema: {
        type: "object",
        properties: { sql: { type: "string" } },
        required: ["sql"]
      }
    }
  ]
}));

// Handle tool calls
server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  // Determine if read-only
  const isReadOnly = name === "query" && /^SELECT/i.test(args?.sql || "");

  // Evaluate governance
  const decision = await governance.evaluate(name, args || {}, {
    actionType: `mcp.database.${name}`,
    resource: "production_db",
    riskLevel: isReadOnly ? "low" : "high"
  });

  if (!decision.allowed) {
    return {
      content: [{
        type: "text",
        text: `[GOVERNANCE] Operation denied\n` +
              `Reason: ${decision.reason}\n` +
              `Risk Level: ${decision.riskLevel}`
      }],
      isError: true
    };
  }

  // Execute query
  try {
    const result = await executeQuery(args?.sql);
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

## API Reference

### McpGovernance

Main governance class for MCP servers.

#### Constructor

```typescript
new McpGovernance(config: McpGovernanceConfig)
```

#### Methods

| Method | Description |
|--------|-------------|
| `evaluate(toolName, args, options)` | Evaluate a tool call against policies |
| `wrapTool(handler, options)` | Wrap a tool handler with governance |
| `governTool(options)` | Decorator for tool handlers |
| `tools` | Get list of governed tool names |

### Helper Functions

| Function | Description |
|----------|-------------|
| `createGovernedTool(options, handler)` | Create a governed tool handler |
| `withGovernance(options)` | Higher-order function for governance |
| `highRiskTool(options)` | Mark tool as requiring approval |

## Compliance

This package supports enterprise compliance requirements:

- **SOC 2 CC6.1** - Access control
- **HIPAA 164.312(e)** - Transmission security
- **PCI-DSS 8.2** - API key management
- **NIST AI RMF** - AI risk management

## Documentation

- [Full Documentation](https://docs.owkai.app/integration/frameworks/mcp-server)
- [ASCEND Platform](https://owkai.app)
- [API Reference](https://docs.owkai.app/api-reference)

## License

MIT License - see [LICENSE](LICENSE) for details.
