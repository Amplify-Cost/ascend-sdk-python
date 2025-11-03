# Models Directory

## Structure
```
models/
├── __init__.py          # Imports all models for backward compatibility
├── action.py            # AgentAction model (future)
├── alert.py             # Alert model (future)
├── workflow.py          # Workflow, WorkflowExecution models (future)
├── user.py              # User, EnterpriseUser models (future)
└── assessment.py        # CVSS, MITRE, NIST models (future)
```

## Migration Plan

Currently, all models remain in the root `models.py` file for compatibility.
Future refactoring will move models into their respective domain files.

### Benefits of Domain Organization:
- ✅ Easier to find models by domain
- ✅ Smaller, more maintainable files
- ✅ Clear separation of concerns
- ✅ Backward compatible via __init__.py

### Next Steps:
1. Extract models from models.py into domain files
2. Update imports across codebase
3. Remove old models.py once migration complete
