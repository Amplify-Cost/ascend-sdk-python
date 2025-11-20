# OW-KAI AI Governance Platform
## Enterprise Client Onboarding Guide

**Document Version**: 1.0
**Last Updated**: November 19, 2025
**Confidentiality**: Enterprise Internal Use Only

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Platform Overview](#platform-overview)
3. [Prerequisites](#prerequisites)
4. [Authentication & Authorization](#authentication--authorization)
5. [API Integration Patterns](#api-integration-patterns)
6. [MCP Server Integration](#mcp-server-integration)
7. [Reference Implementations](#reference-implementations)
8. [Deployment Architectures](#deployment-architectures)
9. [Security & Compliance](#security--compliance)
10. [Monitoring & Observability](#monitoring--observability)
11. [Troubleshooting](#troubleshooting)
12. [Support & Escalation](#support--escalation)

---

## Executive Summary

### What is OW-KAI?

OW-KAI is an **enterprise-grade AI governance platform** that provides:

- **Centralized AI Asset Management**: Inventory and catalog all AI models across your organization
- **Risk Assessment & Management**: Automated CVSS scoring, MITRE ATT&CK mapping, and risk quantification
- **Policy Enforcement**: Multi-level approval workflows with SOC2, GDPR, HIPAA compliance
- **MCP Server Governance**: Control and audit Model Context Protocol (MCP) server actions
- **Immutable Audit Trail**: Comprehensive logging for regulatory compliance
- **Real-Time Monitoring**: Performance tracking, drift detection, and alerting

### Who Should Use This Guide?

- **Enterprise Architects**: Designing integration architecture
- **DevOps Engineers**: Implementing and deploying integrations
- **Security Teams**: Ensuring secure authentication and data handling
- **Compliance Officers**: Understanding audit and compliance features
- **AI/ML Engineers**: Integrating model deployment workflows

### Quick Start Summary

```bash
# 1. Get credentials from OW-KAI team
CLIENT_ID="your-client-id"
CLIENT_SECRET="your-client-secret"

# 2. Authenticate and get token
TOKEN=$(curl -s -X POST "https://pilot.owkai.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"your-email\",\"password\":\"your-password\"}" \
  | jq -r '.access_token')

# 3. Register your first model
curl -X POST "https://pilot.owkai.app/api/governance/unified/action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "model_deployment",
    "model_name": "sentiment-analysis-v1",
    "risk_level": "medium",
    "action_source": "agent"
  }'

# Done! Your model is now under governance.
```

---

## Platform Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  YOUR ENTERPRISE ENVIRONMENT                                    │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Agent 1   │  │   Agent 2   │  │  MCP Server │            │
│  │ (Compliance)│  │   (Risk)    │  │  (Custom)   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                    │
│         └────────────────┴────────────────┘                    │
│                          │                                     │
│                   API Gateway/Client                           │
│                          │                                     │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                    HTTPS/TLS 1.3
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│  OW-KAI PLATFORM (pilot.owkai.app)                             │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  API Layer                                             │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │    │
│  │  │  Unified │  │   MCP    │  │  Auth    │            │    │
│  │  │Governance│  │Governance│  │ Service  │            │    │
│  │  └──────────┘  └──────────┘  └──────────┘            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Core Services                                         │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │    │
│  │  │   Risk   │  │  Policy  │  │  Audit   │            │    │
│  │  │ Scoring  │  │  Engine  │  │  Trail   │            │    │
│  │  └──────────┘  └──────────┘  └──────────┘            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Data Layer                                            │    │
│  │  PostgreSQL + Immutable Audit Logs                     │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Core Capabilities

#### 1. Unified Governance API
- **Endpoint**: `POST /api/governance/unified/action`
- **Purpose**: Single endpoint for all governance actions (agent + MCP)
- **Features**:
  - Automatic risk assessment (CVSS v3.1)
  - Policy evaluation (4-category scoring)
  - Workflow routing
  - Audit logging
  - Alert generation

#### 2. MCP Governance API
- **Endpoint**: `POST /mcp/evaluate`
- **Purpose**: Evaluate MCP server actions before execution
- **Features**:
  - Real-time action evaluation
  - Risk-based approval workflows
  - Policy enforcement
  - Session tracking
  - Immutable audit trail

#### 3. Authorization Center
- **Endpoint**: `GET /api/authorization/workflows`
- **Purpose**: Multi-level approval workflows
- **Features**:
  - Configurable approval levels (1-5)
  - Dynamic approver assignment
  - SLA tracking
  - Escalation policies
  - Emergency override capabilities

#### 4. Enterprise Security
- **Authentication**: JWT-based with OAuth 2.0 support
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: TLS 1.3 for all communications
- **Compliance**: SOC2, GDPR, HIPAA, PCI-DSS ready

---

## Prerequisites

### Technical Requirements

#### Infrastructure
- **AWS Account** (or equivalent cloud provider)
- **Network Connectivity**: HTTPS access to `pilot.owkai.app`
- **DNS Resolution**: Ability to resolve `pilot.owkai.app`
- **Outbound Firewall**: Allow HTTPS (443) to `pilot.owkai.app`

#### Development Environment
- **Python**: 3.9+ (recommended 3.11+)
- **Node.js**: 16+ (if using JavaScript/TypeScript)
- **Docker**: 24+ (for containerized deployments)
- **Git**: For version control

#### Libraries & Dependencies
```python
# Python requirements
requests>=2.31.0
pyjwt>=2.8.0
pydantic>=2.4.0
httpx>=0.25.0  # For async operations
websockets>=12.0  # For real-time events
```

```javascript
// Node.js requirements (package.json)
{
  "dependencies": {
    "axios": "^1.6.0",
    "jsonwebtoken": "^9.0.2",
    "ws": "^8.14.2"
  }
}
```

### Organizational Requirements

#### Credentials
- **OW-KAI Account**: Contact OW-KAI team for provisioning
- **Email/Password**: For initial authentication
- **Client ID/Secret**: (Optional) For OAuth 2.0 client credentials flow

#### Access Control
- **Admin User**: For initial setup and configuration
- **Service Accounts**: For automated agent/MCP integrations
- **Read-Only Users**: For auditors and compliance teams

#### Network Security
- **TLS Certificates**: Valid CA-signed certificates for HTTPS
- **Firewall Rules**: Allow outbound HTTPS to `pilot.owkai.app`
- **Proxy Configuration**: (Optional) If using corporate proxy

---

## Authentication & Authorization

### Authentication Methods

OW-KAI supports two primary authentication methods:

#### Method 1: Email/Password Authentication (Recommended for getting started)

```python
import requests
from datetime import datetime, timedelta

class OWKAIAuthenticator:
    def __init__(self, email: str, password: str, base_url: str = "https://pilot.owkai.app"):
        self.email = email
        self.password = password
        self.base_url = base_url
        self.token = None
        self.token_expiry = None

    def login(self) -> str:
        """
        Authenticate with email/password and get JWT access token

        Returns:
            str: JWT access token

        Raises:
            HTTPException: If authentication fails
        """
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": self.email, "password": self.password},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')

            # Set token expiry (default 30 minutes, with 2-minute buffer)
            self.token_expiry = datetime.now() + timedelta(minutes=28)

            return self.token
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

    def get_access_token(self) -> str:
        """
        Get valid access token, refreshing if needed

        Returns:
            str: Valid JWT access token
        """
        if self.token and datetime.now() < self.token_expiry:
            return self.token

        # Token expired or doesn't exist, get new one
        return self.login()

# Usage
auth = OWKAIAuthenticator("your-email@company.com", "your-password")
token = auth.get_access_token()
print(f"Access token: {token[:20]}...")
```

#### Method 2: OAuth 2.0 Client Credentials (Recommended for production)

```python
import requests
from datetime import datetime, timedelta
import threading

class OWKAIOAuthenticator:
    def __init__(self, client_id: str, client_secret: str,
                 token_url: str = "https://pilot.owkai.app/api/auth/token"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.token = None
        self.token_expiry = None
        self.lock = threading.Lock()

    def get_access_token(self) -> str:
        """
        Get valid OAuth 2.0 access token using client credentials flow

        Returns:
            str: Valid access token

        Features:
            - Thread-safe token caching
            - Automatic token refresh
            - Exponential backoff retry
        """
        with self.lock:
            # Check if cached token is still valid
            if self.token and datetime.now() < self.token_expiry:
                return self.token

            # Fetch new token
            return self._fetch_new_token()

    def _fetch_new_token(self) -> str:
        """Fetch new token from OAuth 2.0 server with retry logic"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.token_url,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'scope': 'api:read api:write governance:manage'
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()
                self.token = data['access_token']

                # Set expiry with 60-second safety margin
                expires_in = data.get('expires_in', 1800)  # Default 30 min
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

                print(f"✅ Token acquired, expires at {self.token_expiry}")
                return self.token

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1  # Exponential backoff
                    print(f"⚠️  Token fetch failed (attempt {attempt+1}/{max_retries}), "
                          f"retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to fetch token after {max_retries} attempts: {e}")

# Usage
oauth_auth = OWKAIOAuthenticator("your-client-id", "your-client-secret")
token = oauth_auth.get_access_token()
```

### JWT Token Structure

The OW-KAI platform uses JWT tokens with the following structure:

```json
{
  "sub": "user-id-7",
  "email": "admin@company.com",
  "role": "admin",
  "user_id": 7,
  "exp": 1763577266,
  "iat": 1763575466,
  "type": "access",
  "iss": "ow-ai-enterprise",
  "aud": "ow-ai-platform",
  "jti": "access-7-1763575466"
}
```

**Key Claims**:
- `sub`: Subject (user identifier)
- `email`: User email address
- `role`: User role (admin, manager, user, viewer)
- `exp`: Expiration timestamp (Unix time)
- `iat`: Issued at timestamp
- `type`: Token type (access or refresh)
- `iss`: Issuer (ow-ai-enterprise)
- `aud`: Audience (ow-ai-platform)
- `jti`: JWT ID (unique identifier)

### Role-Based Access Control (RBAC)

OW-KAI implements RBAC with four primary roles:

| Role | Permissions | Use Case |
|------|------------|----------|
| **admin** | Full platform access, policy creation, user management | Platform administrators |
| **manager** | Approve actions, view analytics, manage policies | Security/compliance managers |
| **user** | Submit actions, view own data, request approvals | AI engineers, data scientists |
| **viewer** | Read-only access to dashboards and reports | Auditors, executives |

---

## API Integration Patterns

### Complete API Client Library

```python
# File: owkai_client.py
"""
OW-KAI AI Governance Platform - Enterprise API Client

Features:
- Automatic authentication and token refresh
- Retry logic with exponential backoff
- Request/response logging
- Error handling
- Type hints for IDE support
"""

import requests
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OWKAIClient:
    """
    Complete OW-KAI API client for enterprise integrations

    Supports all platform endpoints:
    - Authentication
    - Model governance
    - MCP evaluation
    - Risk assessments
    - Policy management
    - Audit trail
    - Workflow management
    """

    def __init__(self, base_url: str, email: str, password: str):
        """
        Initialize OW-KAI client

        Args:
            base_url: OW-KAI platform URL (e.g., "https://pilot.owkai.app")
            email: User email for authentication
            password: User password
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.token = None
        self.token_expiry = None

        # Configure session with retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OWKAIEnterpriseClient/1.0',
            'Accept': 'application/json'
        })

    # ============================================================================
    # AUTHENTICATION
    # ============================================================================

    def _authenticate(self) -> str:
        """Get fresh access token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"email": self.email, "password": self.password},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            self.token = data['access_token']
            self.token_expiry = datetime.now() + timedelta(minutes=28)  # 30min - 2min buffer

            logger.info(f"✅ Authenticated successfully, token expires at {self.token_expiry}")
            return self.token

        except requests.RequestException as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise

    def get_access_token(self) -> str:
        """Get valid access token, refreshing if needed"""
        if self.token and datetime.now() < self.token_expiry:
            return self.token
        return self._authenticate()

    # ============================================================================
    # HTTP REQUEST HANDLER
    # ============================================================================

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., "/api/governance/models")
            **kwargs: Additional arguments passed to requests

        Returns:
            Response JSON as dictionary

        Raises:
            HTTPException: If request fails after retries
        """
        # Prepare headers
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.get_access_token()}'
        headers['X-Request-ID'] = str(uuid.uuid4())
        headers['X-Client-Version'] = '1.0.0'

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    f'{self.base_url}{endpoint}',
                    headers=headers,
                    timeout=30,
                    **kwargs
                )

                # Handle 401 Unauthorized by refreshing token
                if response.status_code == 401 and attempt == 0:
                    logger.warning("⚠️  Token expired, refreshing...")
                    self.token = None  # Force token refresh
                    headers['Authorization'] = f'Bearer {self.get_access_token()}'
                    continue

                response.raise_for_status()

                # Log successful request
                logger.info(f"✅ {method} {endpoint} - {response.status_code}")

                return response.json() if response.content else {}

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"⚠️  Request failed (attempt {attempt+1}/{max_retries}), "
                                 f"retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Request failed after {max_retries} attempts: {method} {endpoint}")
                    raise

    # ============================================================================
    # HEALTH CHECK
    # ============================================================================

    def health_check(self) -> Dict[str, Any]:
        """
        Check platform health status

        Returns:
            Health check response with system status
        """
        return self._request('GET', '/health')

    # ============================================================================
    # MODEL GOVERNANCE
    # ============================================================================

    def register_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register new AI model with governance platform

        Args:
            model_data: Model information (name, type, owner, risk_level, etc.)

        Returns:
            Registered model with governance action ID

        Example:
            client.register_model({
                "model_name": "sentiment-analysis-v1",
                "model_type": "NLP",
                "owner": "data-science-team",
                "risk_level": "medium",
                "action_type": "model_deployment"
            })
        """
        return self._request('POST', '/api/governance/unified/action', json=model_data)

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get model details by ID"""
        return self._request('GET', f'/api/governance/models/{model_id}')

    def list_models(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List all models with optional filters

        Args:
            filters: Optional filters (status, risk_level, owner, etc.)

        Returns:
            List of models matching filters
        """
        return self._request('GET', '/api/governance/models', params=filters or {})

    # ============================================================================
    # UNIFIED GOVERNANCE
    # ============================================================================

    def create_governance_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create unified governance action (agent or MCP)

        This is the primary endpoint for all governance actions.

        Features:
        - Automatic risk assessment (CVSS v3.1)
        - Policy evaluation (4-category scoring)
        - Workflow routing based on risk
        - Audit logging
        - Alert generation for high-risk actions

        Args:
            action_data: Action details
                Required fields:
                - action_type: Type of action
                - action_source: "agent" or "mcp"

                Optional fields:
                - model_name: Model identifier
                - risk_level: "low", "medium", "high", "critical"
                - policy_id: Policy to evaluate against
                - metadata: Additional context

        Returns:
            Action record with:
            - action_id: Unique identifier
            - status: Current status
            - risk_score: Calculated risk (0-100)
            - requires_approval: Whether approval is needed
            - workflow_stage: Current workflow stage

        Example:
            result = client.create_governance_action({
                "action_type": "model_deployment",
                "action_source": "agent",
                "model_name": "fraud-detection-v2",
                "risk_level": "high",
                "metadata": {
                    "deployed_by": "alice@company.com",
                    "environment": "production"
                }
            })

            print(f"Action created: {result['action_id']}")
            print(f"Risk score: {result['risk_score']}")
            print(f"Requires approval: {result['requires_approval']}")
        """
        return self._request('POST', '/api/governance/unified/action', json=action_data)

    def get_governance_action(self, action_id: str) -> Dict[str, Any]:
        """Get governance action details by ID"""
        return self._request('GET', f'/api/governance/actions/{action_id}')

    def list_pending_actions(self) -> List[Dict[str, Any]]:
        """
        List actions pending approval

        Returns:
            List of actions awaiting approval
        """
        return self._request('GET', '/api/governance/pending-actions')

    def list_unified_actions(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List all governance actions (paginated)

        Args:
            limit: Number of results per page (default 100)
            offset: Pagination offset

        Returns:
            Paginated list of actions
        """
        return self._request('GET', '/api/governance/unified-actions',
                           params={'limit': limit, 'offset': offset})

    # ============================================================================
    # MCP GOVERNANCE
    # ============================================================================

    def evaluate_mcp_action(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate MCP server action before execution

        This endpoint evaluates MCP actions using the same risk assessment
        and approval workflows as agent actions.

        Args:
            mcp_request: MCP action details
                Required fields:
                - server_id: MCP server identifier
                - namespace: MCP namespace (e.g., "filesystem", "database")
                - verb: Action verb (e.g., "read_file", "write_file")
                - resource: Target resource path/identifier
                - session_id: MCP session ID
                - client_id: MCP client ID

                Optional fields:
                - parameters: Action parameters (dict)
                - request_id: Unique request ID

        Returns:
            MCP evaluation result:
            - action_id: Governance action ID
            - decision: "ALLOW", "DENY", or "EVALUATE"
            - status: "AUTO_APPROVED", "PENDING_APPROVAL", or "DENIED"
            - risk_score: Calculated risk (0-100)
            - requires_approval: Whether approval is needed
            - approval_level: Required approval level (1-5)
            - reason: Decision rationale

        Example:
            result = client.evaluate_mcp_action({
                "server_id": "filesystem-server-1",
                "namespace": "filesystem",
                "verb": "read_file",
                "resource": "/etc/passwd",
                "session_id": "session-abc-123",
                "client_id": "claude-desktop",
                "parameters": {"encoding": "utf-8"}
            })

            if result['decision'] == 'ALLOW':
                print("Action approved, proceeding...")
            elif result['decision'] == 'EVALUATE':
                print(f"Pending approval (level {result['approval_level']})")
            else:
                print(f"Action denied: {result['reason']}")
        """
        return self._request('POST', '/mcp/evaluate', json=mcp_request)

    def approve_mcp_action(self, action_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Approve or deny MCP action

        Args:
            action_id: Governance action ID
            approval_data: Approval decision
                Required fields:
                - approval_decision: "APPROVE" or "DENY"
                - approval_reason: Rationale for decision

                Optional fields:
                - conditions: Conditional approval parameters

        Returns:
            Updated action status
        """
        return self._request('POST', f'/mcp/approval/{action_id}', json=approval_data)

    def register_mcp_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register new MCP server with platform

        Args:
            server_data: Server configuration
                Required fields:
                - server_id: Unique server identifier
                - server_name: Human-readable name
                - endpoint_url: Server endpoint

                Optional fields:
                - server_description: Description
                - capabilities: Server capabilities (dict)
                - trust_level: "trusted", "restricted", "sandbox"

        Returns:
            Registered server details
        """
        return self._request('POST', '/mcp/register-server', json=server_data)

    def list_mcp_sessions(self) -> List[Dict[str, Any]]:
        """List active MCP sessions"""
        return self._request('GET', '/mcp/sessions')

    # ============================================================================
    # RISK MANAGEMENT
    # ============================================================================

    def create_risk_assessment(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new risk assessment

        Args:
            assessment_data: Risk assessment details
                - model_id: Model to assess
                - assessment_type: Type of assessment
                - risk_factors: List of identified risks

        Returns:
            Risk assessment record
        """
        return self._request('POST', '/api/risk/assessments', json=assessment_data)

    def get_risk_score(self, model_id: str) -> Dict[str, Any]:
        """Get current risk score for model"""
        return self._request('GET', f'/api/risk/models/{model_id}/score')

    def calculate_cvss_score(self, cvss_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate CVSS v3.1 score for vulnerability

        Args:
            cvss_data: CVSS vector components
                Required CVSS v3.1 metrics:
                - attack_vector: "N", "A", "L", or "P"
                - attack_complexity: "L" or "H"
                - privileges_required: "N", "L", or "H"
                - user_interaction: "N" or "R"
                - scope: "U" or "C"
                - confidentiality_impact: "N", "L", or "H"
                - integrity_impact: "N", "L", or "H"
                - availability_impact: "N", "L", or "H"

        Returns:
            CVSS score and severity rating
        """
        return self._request('POST', '/api/risk/cvss-assessments', json=cvss_data)

    # ============================================================================
    # POLICY MANAGEMENT
    # ============================================================================

    def evaluate_policy(self, policy_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate action against specific policy

        Args:
            policy_id: Policy identifier
            context: Evaluation context (action details)

        Returns:
            Policy evaluation result
        """
        return self._request('POST', f'/api/policies/{policy_id}/evaluate', json=context)

    def list_policies(self, policy_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List governance policies

        Args:
            policy_type: Filter by type ("compliance", "security", etc.)

        Returns:
            List of policies
        """
        params = {'type': policy_type} if policy_type else {}
        return self._request('GET', '/api/policies', params=params)

    def create_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new governance policy"""
        return self._request('POST', '/api/policies', json=policy_data)

    # ============================================================================
    # WORKFLOW MANAGEMENT
    # ============================================================================

    def get_workflow_config(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow configuration

        Args:
            workflow_id: Workflow identifier (e.g., "risk_90_100")

        Returns:
            Workflow configuration with approvers, SLA, escalation
        """
        return self._request('GET', f'/api/authorization/workflows/{workflow_id}')

    def list_workflow_configs(self) -> Dict[str, Any]:
        """
        List all workflow configurations

        Returns:
            All configured workflows with metadata
        """
        return self._request('GET', '/api/authorization/workflow-config')

    def update_workflow_config(self, workflow_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update workflow configuration (admin only)

        Args:
            workflow_id: Workflow to update
            config_data: New configuration

        Returns:
            Updated workflow configuration
        """
        return self._request('PUT', f'/api/authorization/workflows/{workflow_id}', json=config_data)

    # ============================================================================
    # AUDIT TRAIL
    # ============================================================================

    def submit_audit_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit audit event

        Args:
            event_data: Audit event details
                - event_type: Type of event
                - action_id: Related action ID
                - user_id: User who performed action
                - event_details: Additional context

        Returns:
            Audit event record
        """
        return self._request('POST', '/api/audit/events', json=event_data)

    def query_audit_trail(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query audit trail with filters

        Args:
            filters: Query filters
                - start_date: Start of date range
                - end_date: End of date range
                - event_type: Filter by event type
                - user_id: Filter by user

        Returns:
            List of audit events matching filters
        """
        return self._request('GET', '/api/audit/events', params=filters)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Initialize client
    client = OWKAIClient(
        base_url="https://pilot.owkai.app",
        email="your-email@company.com",
        password="your-password"
    )

    # Health check
    print("=" * 60)
    print("HEALTH CHECK")
    print("=" * 60)
    health = client.health_check()
    print(f"Status: {health.get('status')}")
    print(f"Enterprise Grade: {health.get('enterprise_grade')}")
    print()

    # Register a model
    print("=" * 60)
    print("MODEL REGISTRATION")
    print("=" * 60)
    model_result = client.register_model({
        "action_type": "model_deployment",
        "action_source": "agent",
        "model_name": "fraud-detection-v3",
        "risk_level": "high",
        "metadata": {
            "deployed_by": "alice@company.com",
            "environment": "production",
            "model_type": "RandomForest",
            "training_data": "customer-transactions-2024"
        }
    })
    print(f"Action ID: {model_result.get('action_id')}")
    print(f"Status: {model_result.get('status')}")
    print(f"Risk Score: {model_result.get('risk_score')}")
    print(f"Requires Approval: {model_result.get('requires_approval')}")
    print()

    # Evaluate MCP action
    print("=" * 60)
    print("MCP ACTION EVALUATION")
    print("=" * 60)
    mcp_result = client.evaluate_mcp_action({
        "server_id": "filesystem-server-1",
        "namespace": "filesystem",
        "verb": "read_file",
        "resource": "/home/user/data/sensitive.csv",
        "session_id": "session-xyz-789",
        "client_id": "claude-desktop",
        "parameters": {"encoding": "utf-8"}
    })
    print(f"Decision: {mcp_result.get('decision')}")
    print(f"Status: {mcp_result.get('status')}")
    print(f"Risk Score: {mcp_result.get('risk_score')}")
    print(f"Reason: {mcp_result.get('reason')}")
    print()

    # List pending actions
    print("=" * 60)
    print("PENDING APPROVALS")
    print("=" * 60)
    pending = client.list_pending_actions()
    print(f"Total pending: {len(pending)}")
    for action in pending[:3]:  # Show first 3
        print(f"  - {action.get('action_id')}: {action.get('model_name')} "
              f"(Risk: {action.get('risk_score')})")
    print()

    print("✅ All tests completed successfully!")
```

---

*This is Page 1 of the Enterprise Onboarding Guide. Continue to next sections for:*
- *MCP Server Integration Guide*
- *Reference Implementation Examples*
- *Deployment Architectures*
- *Security & Compliance*
- *Monitoring & Observability*
- *Troubleshooting Guide*

**Document Status**: Section 1-6 Complete
**Next Update**: Add MCP Server Integration details

---

## Support Contact

**OW-KAI Support Team**
- **Email**: support@ow-kai.com
- **Platform**: https://pilot.owkai.app
- **Documentation**: [Enterprise Portal]
- **Emergency Support**: Available 24/7 for enterprise clients

