from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database.session import get_db
from app.models.models import User
from app.schemas.schemas import Token, LoginRequest, UserResponse
from app.auth.security import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticates user via JSON payload or application/x-www-form-urlencoded (OAuth2 form).
    Supports email or username, case-insensitively with leading/trailing whitespace trimmed.
    """
    content_type = request.headers.get("content-type", "")
    identifier = ""
    password = ""

    if "application/json" in content_type:
        try:
            body = await request.json()
            identifier = (body.get("email") or body.get("username") or "").strip()
            password = body.get("password") or ""
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
    else:
        # Form-urlencoded data (e.g. Swagger /docs Authorize button)
        form = await request.form()
        identifier = (form.get("username") or form.get("email") or "").strip()
        password = form.get("password") or ""

    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email and password are required. Please verify credentials."
        )

    user = db.query(User).filter(func.lower(User.email) == identifier.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify credentials."
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "name": user.name})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department
        }
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
