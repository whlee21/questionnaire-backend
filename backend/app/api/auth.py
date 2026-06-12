from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token, verify_password
from app.db.session import get_db
from app.models.admin import AdminUser
from app.schemas.auth import LoginIn, TokenOut

router = APIRouter()
security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """FastAPI dependency: validates JWT bearer token and returns the active AdminUser."""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str | None = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(AdminUser).where(AdminUser.email == email, AdminUser.is_active == True)  # noqa: E712
    )
    admin = result.scalar_one_or_none()
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    """Public endpoint: email + password → JWT access token."""
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == body.email, AdminUser.is_active == True)  # noqa: E712
    )
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(body.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": admin.email})
    return TokenOut(access_token=token)


@router.get("/me")
async def get_me(admin: AdminUser = Depends(get_current_admin)) -> dict:
    """Protected endpoint: returns current admin info."""
    return {"id": str(admin.id), "email": admin.email, "is_active": admin.is_active}
