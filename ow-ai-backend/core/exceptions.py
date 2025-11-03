"""
Custom Exception Hierarchy
Provides clear, consistent error handling across the application
"""
from fastapi import HTTPException, status


class OWAIException(Exception):
    """Base exception for all OWAI errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundError(OWAIException):
    """Resource not found (404)"""
    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationError(OWAIException):
    """Validation failed (422)"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationError(OWAIException):
    """Authentication failed (401)"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(OWAIException):
    """Authorization failed (403)"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class OrchestrationError(OWAIException):
    """Orchestration process failed (500)"""
    def __init__(self, message: str):
        super().__init__(
            message=f"Orchestration failed: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class WorkflowError(OWAIException):
    """Workflow processing failed (500)"""
    def __init__(self, message: str):
        super().__init__(
            message=f"Workflow error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
