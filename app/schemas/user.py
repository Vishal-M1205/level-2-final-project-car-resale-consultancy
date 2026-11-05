from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import GENDERS


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    age: int | None = None
    gender: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserFilterParams(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)

    model_config = ConfigDict(str_strip_whitespace=True)


class PaginatedUsersResponse(BaseModel):
    users: list[UserResponse]
    page: int
    limit: int
    total_pages: int
    total_users: int


class UserDeleteResponse(BaseModel):
    user_id: int
    is_active: bool
    message: str
    deactivated_listings_count: int = 0


class UserPatchRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = None
    age: int | None = Field(default=None, ge=18, le=100)
    gender: str | None = None
    address_line_1: str | None = Field(default=None, min_length=2, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    pincode: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.match(r"^[A-Za-z\s.]+$", value):
                raise ValueError("Name can only contain alphabets, spaces, and dots")
            return value
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.match(r"^[6-9]\d{9}$", value):
                raise ValueError("Phone number must be a valid 10-digit mobile number")
            return value
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        if value is not None:
            gender = value.upper()
            if gender not in GENDERS:
                raise ValueError(f"Gender must be one of {GENDERS}")
            return gender
        return value

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.match(r"^\d{6}$", value):
                raise ValueError("Pincode must be exactly 6 numeric digits")
            return value
        return value

