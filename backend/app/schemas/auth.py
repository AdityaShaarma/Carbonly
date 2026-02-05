"""Auth request/response schemas."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    company_id: str

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    user: UserResponse
    company: "CompanyResponse"

    class Config:
        from_attributes = True


from app.schemas.company import CompanyResponse  # noqa: E402


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    company: CompanyResponse


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    token: str
    new_password: str
