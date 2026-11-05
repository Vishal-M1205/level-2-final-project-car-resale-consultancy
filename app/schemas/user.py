import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import GENDERS


class UserResponse(BaseModel):
    id: int = Field(description="Unique identifier of the user", examples=[1])
    name: str = Field(description="Full legal name of the user", examples=["John Doe"])
    email: str = Field(description="User email address", examples=["user@example.com"])
    phone: str = Field(description="User 10-digit mobile phone number", examples=["9876543210"])
    age: int | None = Field(default=None, description="Age in years", examples=[28])
    gender: str | None = Field(
        default=None, description="Gender (MALE, FEMALE, OTHER)", examples=["MALE"]
    )
    address_line_1: str | None = Field(
        default=None, description="Primary address", examples=["123 Gandhi Road"]
    )
    address_line_2: str | None = Field(
        default=None, description="Secondary address/apartment", examples=["Apartment 4B"]
    )
    district: str | None = Field(
        default=None, description="District or city name", examples=["Coimbatore"]
    )
    state: str | None = Field(default=None, description="State name", examples=["Tamil Nadu"])
    pincode: str | None = Field(
        default=None, description="6-digit postal code", examples=["641001"]
    )
    role: str = Field(
        description="Role assigned to user account (admin, customer, consultant)",
        examples=["customer"],
    )
    is_active: bool = Field(description="Account active status flag", examples=[True])
    created_at: datetime = Field(description="Timestamp when the user account was created")
    updated_at: datetime = Field(description="Timestamp when the user account was last updated")

    model_config = ConfigDict(from_attributes=True)


class UserFilterParams(BaseModel):
    search: str | None = Field(
        default=None,
        description="Search keyword matching against name, email, or phone",
        examples=["John"],
    )
    name: str | None = Field(
        default=None,
        description="Filter by user name (partial match)",
        examples=["John"],
    )
    email: str | None = Field(
        default=None,
        description="Filter by user email address (partial match)",
        examples=["john@example.com"],
    )
    phone: str | None = Field(
        default=None,
        description="Filter by user phone number (partial match)",
        examples=["9876543210"],
    )
    role: str | None = Field(
        default=None,
        description="Filter users by role: customer, consultant, admin",
        examples=["customer"],
    )
    is_active: bool | None = Field(
        default=None, description="Filter users by active status", examples=[True]
    )
    district: str | None = Field(
        default=None,
        description="Filter users by district",
        examples=["Coimbatore"],
    )
    state: str | None = Field(
        default=None,
        description="Filter users by state",
        examples=["Tamil Nadu"],
    )
    gender: str | None = Field(
        default=None,
        description="Filter users by gender (MALE, FEMALE, OTHER)",
        examples=["MALE"],
    )
    sort_by: str = Field(
        default="created_at",
        description="Field to sort users by: 'created_at', 'name', 'email', 'role'",
        examples=["created_at"],
    )
    order: str = Field(
        default="desc",
        description="Sort direction: 'asc' or 'desc'",
        examples=["desc"],
    )
    page: int = Field(
        default=1, ge=1, description="Page number for pagination (starts at 1)", examples=[1]
    )
    limit: int = Field(
        default=10, ge=1, le=50, description="Number of users per page (max 50)", examples=[10]
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str) -> str:
        allowed = {"created_at", "name", "email", "role"}
        val = value.lower().strip()
        if val not in allowed:
            raise ValueError(f"sort_by must be one of {allowed}")
        return val

    @field_validator("order")
    @classmethod
    def validate_order(cls, value: str) -> str:
        val = value.lower().strip()
        if val not in {"asc", "desc"}:
            raise ValueError("order must be 'asc' or 'desc'")
        return val


class PaginatedUsersResponse(BaseModel):
    users: list[UserResponse] = Field(description="List of user profiles for the current page")
    page: int = Field(description="Current page index", examples=[1])
    limit: int = Field(description="Configured page limit", examples=[10])
    total_pages: int = Field(description="Total calculated pages available", examples=[3])
    total_users: int = Field(description="Total matching users count", examples=[25])


class UserDeleteResponse(BaseModel):
    user_id: int = Field(description="ID of the deactivated user", examples=[2])
    is_active: bool = Field(description="Updated active status (False)", examples=[False])
    message: str = Field(
        description="Confirmation message", examples=["User successfully deactivated."]
    )
    deactivated_listings_count: int = Field(
        default=0,
        description="Total active listings deactivated as a result of user deactivation",
        examples=[1],
    )


class UserPatchRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated full legal name",
        examples=["John Updated"],
    )
    phone: str | None = Field(
        default=None,
        description="Updated 10-digit mobile number",
        examples=["9123456780"],
    )
    age: int | None = Field(
        default=None,
        ge=18,
        le=100,
        description="Updated age (18 to 100)",
        examples=[30],
    )
    gender: str | None = Field(
        default=None,
        description="Updated gender (MALE, FEMALE, OTHER)",
        examples=["MALE"],
    )
    address_line_1: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Updated primary street address",
        examples=["456 Cross Cut Rd"],
    )
    address_line_2: str | None = Field(
        default=None,
        max_length=255,
        description="Updated secondary address details",
        examples=["Suite 101"],
    )
    district: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated district name",
        examples=["Coimbatore"],
    )
    state: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated state name",
        examples=["Tamil Nadu"],
    )
    pincode: str | None = Field(
        default=None,
        description="Updated 6-digit postal code",
        examples=["641002"],
    )

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
