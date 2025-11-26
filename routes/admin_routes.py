from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from dependencies import require_admin, get_current_user, require_csrf, get_organization_filter
from schemas import UserOut
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)  # 🏢 ENTERPRISE: Multi-tenant isolation
):
    """List all users (admin only)"""
    try:
        query = db.query(User)
        # 🏢 ENTERPRISE: Multi-tenant isolation - filter by organization
        if org_id is not None:
            query = query.filter(User.organization_id == org_id)
        users = query.order_by(User.created_at.desc()).all()
        return users
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    _=Depends(require_csrf),
    org_id: int = Depends(get_organization_filter)  # 🏢 ENTERPRISE: Multi-tenant isolation
):
    """Update user role (admin only)"""
    try:
        if new_role not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'user' or 'admin'"
            )

        query = db.query(User).filter(User.id == user_id)
        # 🏢 ENTERPRISE: Multi-tenant isolation - ensure user is in same org
        if org_id is not None:
            query = query.filter(User.organization_id == org_id)
        user = query.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prevent admin from demoting themselves
        if user.id == admin_user["user_id"] and new_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own admin role"
            )

        user.role = new_role
        db.commit()

        logger.info(f"User {user.email} role changed to {new_role} by {admin_user['email']}")
        return {"message": f"User role updated to {new_role}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user role: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    _=Depends(require_csrf),
    org_id: int = Depends(get_organization_filter)  # 🏢 ENTERPRISE: Multi-tenant isolation
):
    """Delete user (admin only)"""
    try:
        query = db.query(User).filter(User.id == user_id)
        # 🏢 ENTERPRISE: Multi-tenant isolation - ensure user is in same org
        if org_id is not None:
            query = query.filter(User.organization_id == org_id)
        user = query.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prevent admin from deleting themselves
        if user.id == admin_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        db.delete(user)
        db.commit()

        logger.info(f"User {user.email} deleted by {admin_user['email']}")
        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )



