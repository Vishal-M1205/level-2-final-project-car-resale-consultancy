from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


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

