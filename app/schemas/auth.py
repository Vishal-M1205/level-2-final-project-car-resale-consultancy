import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.constants import GENDERS


class RegisterUser(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Full legal name of the user",
        examples=["John Doe"],
    )
    email: EmailStr = Field(
        description="Unique email address for user login and notifications",
        examples=["user@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=32,
        description="Password containing at least one uppercase, one lowercase, one digit, and one special character",
        examples=["SecurePass123!"],
    )
    phone: str = Field(
        description="Valid 10-digit Indian mobile number starting with 6-9",
        examples=["9876543210"],
    )

    age: int = Field(
        ge=18,
        le=100,
        description="Age of the user (must be between 18 and 100)",
        examples=[28],
    )
    gender: str = Field(
        description="Gender of the user (MALE, FEMALE, or OTHER)",
        examples=["MALE"],
    )
    address_line_1: str = Field(
        min_length=2,
        max_length=255,
        description="Primary street address or building details",
        examples=["123 Gandhi Road"],
    )
    address_line_2: str | None = Field(
        default=None,
        max_length=255,
        description="Secondary address, apartment, or landmark (optional)",
        examples=["Apartment 4B"],
    )
    district: str = Field(
        min_length=2,
        max_length=100,
        description="District or city name",
        examples=["Coimbatore"],
    )
    state: str = Field(
        min_length=2,
        max_length=100,
        description="State name",
        examples=["Tamil Nadu"],
    )
    pincode: str = Field(
        description="6-digit postal pincode",
        examples=["641001"],
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not re.match(r"^[A-Za-z\s]+$", value):
            raise ValueError("Name can only contain alphabets, spaces, dots, and hyphens")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}]", value):
            raise ValueError("Password must contain at least one special character")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.match(r"^[6-9]\d{9}$", value):
            raise ValueError("Phone number must be a valid 10-digit mobile number")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        gender = value.upper()
        if gender not in GENDERS:
            raise ValueError(f"Gender must be one of {GENDERS}")
        return gender

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: str) -> str:
        if not re.match(r"^\d{6}$", value):
            raise ValueError("Pincode must be exactly 6 numeric digits")
        return value


class RegisterResponse(BaseModel):
    id: int = Field(description="Unique identifier of the registered user", examples=[1])
    name: str = Field(description="Full legal name of the user", examples=["John Doe"])
    email: str = Field(
        description="Email address of the registered user", examples=["user@example.com"]
    )
    role: str = Field(description="Assigned role for the user account", examples=["customer"])
    created_at: datetime = Field(description="Timestamp when the user account was created")

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    sub: str = Field(
        description="Subject identifier (user email) encoded in JWT", examples=["user@example.com"]
    )
    role: str = Field(description="User role encoded in JWT", examples=["customer"])
    scopes: list[str] = Field(
        default=[],
        description="Authorized permission scopes granted to user",
        examples=[["user:read_own", "vehicle:create"]],
    )
    exp: int = Field(description="Token expiration epoch timestamp")
    type: str = Field(
        default="access_token", description="Type of token payload", examples=["access_token"]
    )


class Token(BaseModel):
    access_token: str = Field(
        description="JWT Bearer access token used to authenticate API requests",
        examples=["eyJhbGciOi..."],
    )
    refresh_token: str = Field(
        description="Long-lived token used to generate new access tokens",
        examples=["eyJhbGciOi..."],
    )
    type: str = Field(
        default="bearer", description="Token authentication scheme", examples=["bearer"]
    )


class Login(BaseModel):
    email: EmailStr = Field(
        description="Registered user email address", examples=["user@example.com"]
    )
    password: str = Field(description="User account password", examples=["SecurePass123!"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        description="Valid, unexpired refresh token string",
        examples=["eyJhbGciOi..."],
    )
