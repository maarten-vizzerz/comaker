"""
User Management API Endpoints
Only accessible by administrators
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
import uuid

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.models.historie_setup import HistorieContext

router = APIRouter()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    role: UserRole
    is_active: bool
    avatar: Optional[str] = None
    leverancier_id: Optional[str] = None
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole
    is_active: bool = True
    leverancier_id: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    leverancier_id: Optional[str] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_admin_rights(user: User):
    """Check if user has admin rights"""
    if user.role != UserRole.BEHEERDER:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage users"
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all users (admin only)
    """
    check_admin_rights(current_user)

    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.order_by(User.name).all()

    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user details (admin only, or own profile)
    """
    # Allow users to see their own profile
    if current_user.id != user_id:
        check_admin_rights(current_user)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.post("/users", response_model=UserResponse, status_code=http_status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new user (admin only)
    """
    check_admin_rights(current_user)

    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{user_data.email}' already exists"
        )

    # Validate leverancier requirement
    if user_data.role == UserRole.LEVERANCIER and not user_data.leverancier_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Leverancier ID is verplicht voor gebruikers met rol 'leverancier'"
        )

    # Validate leverancier exists if provided
    if user_data.leverancier_id:
        from app.models.leverancier import Leverancier
        leverancier = db.query(Leverancier).filter(Leverancier.id == user_data.leverancier_id).first()
        if not leverancier:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Leverancier met ID '{user_data.leverancier_id}' niet gevonden"
            )

    # Set historie context
    HistorieContext.set_user_id(current_user.id)
    HistorieContext.set_opmerking("Nieuwe gebruiker aangemaakt via API")

    try:
        # Create user
        user = User(
            id=f"usr_{uuid.uuid4().hex[:8]}",
            email=user_data.email,
            name=user_data.name,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active,
            leverancier_id=user_data.leverancier_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    finally:
        HistorieContext.clear()


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user (admin only)
    """
    check_admin_rights(current_user)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate leverancier requirement
    new_role = user_data.role if user_data.role is not None else user.role
    new_leverancier_id = user_data.leverancier_id if user_data.leverancier_id is not None else user.leverancier_id

    if new_role == UserRole.LEVERANCIER and not new_leverancier_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Leverancier ID is verplicht voor gebruikers met rol 'leverancier'"
        )

    # Validate leverancier exists if provided
    if user_data.leverancier_id:
        from app.models.leverancier import Leverancier
        leverancier = db.query(Leverancier).filter(Leverancier.id == user_data.leverancier_id).first()
        if not leverancier:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Leverancier met ID '{user_data.leverancier_id}' niet gevonden"
            )

    # Set historie context
    HistorieContext.set_user_id(current_user.id)
    HistorieContext.set_opmerking("Gebruiker bijgewerkt via API")

    try:
        # Update fields
        if user_data.email is not None:
            # Check if new email already exists
            existing = db.query(User).filter(
                User.email == user_data.email,
                User.id != user_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"User with email '{user_data.email}' already exists"
                )
            user.email = user_data.email

        if user_data.name is not None:
            user.name = user_data.name

        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)

        if user_data.role is not None:
            user.role = user_data.role

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        if user_data.leverancier_id is not None:
            user.leverancier_id = user_data.leverancier_id

        db.commit()
        db.refresh(user)

        return user
    finally:
        HistorieContext.clear()


@router.delete("/users/{user_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete user (admin only)
    Cannot delete yourself
    """
    check_admin_rights(current_user)

    if user_id == current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Set historie context
    HistorieContext.set_user_id(current_user.id)
    HistorieContext.set_opmerking(f"Gebruiker verwijderd: {user.name}")

    try:
        db.delete(user)
        db.commit()
    finally:
        HistorieContext.clear()
