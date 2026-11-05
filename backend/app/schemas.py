from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Display name must have at least 2 characters")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class PasswordResetRequest(TokenRequest):
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetEmailRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    display_name: str
    email: EmailStr


class MessageResponse(BaseModel):
    message: str
