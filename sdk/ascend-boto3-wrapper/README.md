# ASCEND Boto3 Governance Wrapper

Transparent AI governance for AWS SDK operations. This package automatically adds policy-based access control to boto3 without requiring code changes.

## Installation

```bash
pip install ascend-boto3-wrapper
```

## Quick Start

```python
from ascend_boto3 import enable_governance

# Enable governance (patches boto3 globally)
enable_governance(api_key="ascend_prod_xxx")

# Use boto3 as normal - governance is automatic
import boto3
s3 = boto3.client('s3')

# Low risk - auto-approved
s3.list_buckets()

# High risk - requires approval
s3.delete_bucket(Bucket='production-backup')  # Blocks until approved
```

## Features

- **Zero code changes** - Works with existing boto3 code
- **Automatic risk classification** - Operations classified by impact
- **Policy-based approval** - High-risk operations require human approval
- **Full audit trail** - All operations logged for compliance
- **Configurable bypass** - Skip governance for trusted services

## Risk Levels

| Level | Score | Examples | Default Behavior |
|-------|-------|----------|------------------|
| LOW | 0-44 | `list_*`, `get_*`, `describe_*` | Auto-approve |
| MEDIUM | 45-69 | `put_*`, `create_*`, `start_*` | Evaluate policy |
| HIGH | 70-84 | `delete_*`, `terminate_*` | Require approval |
| CRITICAL | 85-100 | `delete_bucket`, IAM admin ops | Executive approval |

## Configuration

```python
from ascend_boto3 import enable_governance

enable_governance(
    api_key="ascend_prod_xxx",           # Required
    base_url="https://pilot.owkai.app",  # API URL
    agent_id="my-data-pipeline",         # Unique identifier
    agent_name="Data Pipeline Agent",    # Display name
    auto_approve_low_risk=True,          # Auto-approve low risk
    auto_approve_medium_risk=False,      # Require review for medium
    bypass_services={"cloudwatch"},      # Skip governance for these
    bypass_operations={"s3.list_buckets"},  # Skip specific operations
    dry_run=False,                       # Log only, don't enforce
)
```

## Environment Variables

```bash
export ASCEND_API_KEY="ascend_prod_xxx"
export ASCEND_API_URL="https://pilot.owkai.app"
```

## AWS Lambda Example

```python
from ascend_boto3 import enable_governance

# Enable at cold start
enable_governance(api_key=os.environ["ASCEND_API_KEY"])

import boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')

    # Low risk - proceeds immediately
    objects = s3.list_objects_v2(Bucket='data')

    # High risk - waits for approval
    s3.delete_objects(
        Bucket='data',
        Delete={'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}
    )

    return {'statusCode': 200}
```

## Supported Services

Full risk mappings for:
- S3
- EC2
- IAM
- RDS
- Lambda
- DynamoDB
- SQS
- SNS
- CloudFormation
- Secrets Manager
- KMS

Unknown operations default to MEDIUM risk.

## Error Handling

```python
from ascend_boto3 import enable_governance

enable_governance(api_key="ascend_prod_xxx")

import boto3

try:
    s3 = boto3.client('s3')
    s3.delete_bucket(Bucket='critical-production')
except PermissionError as e:
    print(f"Operation denied: {e}")
    # Handle denied operation gracefully
```

## License

MIT License - OW-kai Corporation
