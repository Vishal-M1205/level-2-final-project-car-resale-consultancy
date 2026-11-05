from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import VEHICLE_LISTING_STATUSES
from app.schemas.vehicle import VehicleResponse


class ListingFilterParams(BaseModel):
    status: str | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    brand: str | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None:
            val = value.upper().strip()
            if val not in VEHICLE_LISTING_STATUSES:
                raise ValueError(f"Status must be one of {VEHICLE_LISTING_STATUSES}")
            return val
        return value


class ListingPatchRequest(BaseModel):
    status: str | None = None
    listed_price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    listing_description: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None:
            val = value.upper().strip()
            if val == "SOLD":
                raise ValueError(
                    "Cannot manually set status to 'SOLD'. Listings automatically transition to 'SOLD' when a resale transaction is completed."
                )
            if val not in ("ACTIVE", "INACTIVE"):
                raise ValueError("Status must be either 'ACTIVE' or 'INACTIVE'")
            return val
        return value


class ListingResponse(BaseModel):
    id: int
    vehicle_id: int
    listed_price: Decimal
    listing_description: str | None
    status: str
    listed_at: datetime
    updated_at: datetime
    vehicle: VehicleResponse

    model_config = ConfigDict(from_attributes=True)


class PaginatedListingsResponse(BaseModel):
    listings: list[ListingResponse]
    page: int
    limit: int
    total_pages: int
    total_listings: int

