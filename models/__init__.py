"""
Models Module
Organized by domain for better maintainability
"""
# Import all models here for backward compatibility
# This allows: from models import AgentAction, Alert, Workflow

# Core models will be split into separate files
# For now, we'll import from the main models.py file

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from parent directory's models.py
from ..models import *

__all__ = [
    'AgentAction',
    'Alert', 
    'Workflow',
    'WorkflowExecution',
    'User',
    'EnterpriseUser',
    # Add other model names as needed
]
