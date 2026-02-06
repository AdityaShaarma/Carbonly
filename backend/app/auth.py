"""Authentication utilities: JWT, password hashing, dependencies."""
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.company import Company
from app.models.user import User
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

settings = get_settings()
_argon2 = PasswordHasher()
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _argon2.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using argon2."""
    return _argon2.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency: get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> User | None:
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_current_company(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Company:
    """Dependency: get current user's company."""
    result = await db.execute(select(Company).where(Company.id == user.company_id))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


async def require_not_demo_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "demo_read_only", "message": "Demo accounts are read-only."}},
        )
    return user


async def require_paid_plan(
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
) -> Company:
    if user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": {"code": "payment_required", "message": "Upgrade to export reports."}},
        )
    if company.plan in {"starter", "pro"} and company.billing_status in {"active", "trialing"}:
        return company
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={"error": {"code": "payment_required", "message": "Upgrade to export reports."}},
    )


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentCompany = Annotated[Company, Depends(get_current_company)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
NonDemoUser = Annotated[User, Depends(require_not_demo_user)]
PaidCompany = Annotated[Company, Depends(require_paid_plan)]
