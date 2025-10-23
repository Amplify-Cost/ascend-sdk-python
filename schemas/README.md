# Schemas Directory

Pydantic schemas for request validation and response serialization.

## Structure
```
schemas/
├── __init__.py       # Export all schemas
├── action.py         # Action validation schemas
├── alert.py          # Alert validation schemas
└── workflow.py       # Workflow validation schemas
```

## Schema Types

### Request Schemas (Input Validation)
- `ActionCreate`: Validate new action creation
- `AlertCreate`: Validate new alert creation
- `ApprovalDecision`: Validate approval decisions

### Update Schemas
- `ActionUpdate`: Validate action updates
- `AlertUpdate`: Validate alert updates

### Response Schemas (Output Serialization)
- `ActionResponse`: Serialize action data
- `AlertResponse`: Serialize alert data
- `WorkflowExecutionResponse`: Serialize workflow execution

## Usage
```python
from fastapi import APIRouter
from schemas import ActionCreate, ActionResponse

@router.post("/actions", response_model=ActionResponse)
async def create_action(data: ActionCreate):
    # data is automatically validated
    # response is automatically serialized
    pass
```

## Benefits

- ✅ Automatic request validation
- ✅ Clear API contracts
- ✅ Type hints for IDE support
- ✅ Automatic OpenAPI/Swagger docs
- ✅ SQL injection prevention
- ✅ Input sanitization
