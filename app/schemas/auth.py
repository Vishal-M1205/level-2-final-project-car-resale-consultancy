import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import datetime
from app.core.constants import GENDERS


class RegisterUser(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)
    phone: str

    age: int = Field(ge=18, le=100)
    gender: str
    address_line_1: str = Field(min_length=2, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    district: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not re.match(r"^[A-Za-z\s]+$", value):
            raise ValueError(
                "Name can only contain alphabets, spaces, dots, and hyphens"
            )
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
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    sub: str
    role: str
    scopes: list[str] = []
    exp: int
    type: str = Field(default="access_token")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    type: str = Field(default="bearer")


class Login(BaseModel):
    email: EmailStr
    password: str
