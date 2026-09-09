import datetime
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.database.session import get_db
from app.models.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if user is None:
        raise credentials_exception
    return user

def require_roles(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of {allowed_roles} roles. Your role is {current_user.role}."
            )
        return current_user
    return role_checker

def init_demo_users(db: Session):
    """Seed demo accounts if not present, and ensure password hashes are strictly up to date."""
    demo_users = [
        {
            "name": "K. Rajeshwar Rao (Survey Officer)",
            "email": "officer@bhoomi.gov.in",
            "password": "Officer@2026",
            "role": UserRole.SURVEY_OFFICER.value,
            "department": "Directorate of Survey & Land Records"
        },
        {
            "name": "Smt. Sunita Sharma (Admin)",
            "email": "admin@bhoomi.gov.in",
            "password": "Admin@2026",
            "role": UserRole.ADMIN.value,
            "department": "Ministry of Rural Development"
        },
        {
            "name": "Arun Verma (Public Viewer)",
            "email": "viewer@bhoomi.gov.in",
            "password": "Viewer@2026",
            "role": UserRole.VIEWER.value,
            "department": "Panchayati Raj Department"
        }
    ]
    for u in demo_users:
        existing = db.query(User).filter(func.lower(User.email) == u["email"].lower()).first()
        if not existing:
            new_user = User(
                name=u["name"],
                email=u["email"].lower(),
                password_hash=get_password_hash(u["password"]),
                role=u["role"],
                department=u["department"]
            )
            db.add(new_user)
        elif not verify_password(u["password"], existing.password_hash):
            existing.password_hash = get_password_hash(u["password"])
            existing.role = u["role"]
            existing.name = u["name"]
    db.commit()
