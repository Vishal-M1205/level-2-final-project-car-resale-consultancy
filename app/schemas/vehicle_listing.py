from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import VEHICLE_LISTING_STATUSES
from app.schemas.vehicle import VehicleResponse


class ListingFilterParams(BaseModel):
    status: str | None = Field(
        default=None,
        description="Filter listings by status (ACTIVE, SOLD, INACTIVE)",
        examples=["ACTIVE"],
    )
    min_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="Minimum listed price filter",
        examples=[Decimal("200000.00")],
    )
    max_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="Maximum listed price filter",
        examples=[Decimal("900000.00")],
    )
    brand: str | None = Field(
        default=None,
        description="Filter listings by vehicle brand name",
        examples=["Toyota"],
    )
    page: int = Field(default=1, ge=1, description="Page index (starts at 1)", examples=[1])
    limit: int = Field(default=10, ge=1, le=50, description="Page size limit", examples=[10])

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
    status: str | None = Field(
        default=None,
        description="Update status ('ACTIVE' or 'INACTIVE')",
        examples=["INACTIVE"],
    )
    listed_price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
        description="Updated listing resale price",
        examples=[Decimal("830000.00")],
    )
    listing_description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated public marketing description",
        examples=["Certified pre-owned with warranty."],
    )

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
    id: int = Field(description="Listing unique identifier", examples=[1])
    vehicle_id: int = Field(description="Vehicle ID tied to this listing", examples=[1])
    listed_price: Decimal = Field(
        description="Published resale price", examples=[Decimal("850000.00")]
    )
    listing_description: str | None = Field(
        default=None,
        description="Public listing description",
        examples=["Pristine condition."],
    )
    status: str = Field(description="Listing status (ACTIVE, SOLD, INACTIVE)", examples=["ACTIVE"])
    listed_at: datetime = Field(description="Timestamp when listing was created and published")
    updated_at: datetime = Field(description="Timestamp when listing was last updated")
    vehicle: VehicleResponse = Field(description="Complete vehicle specifications")

    model_config = ConfigDict(from_attributes=True)


class PaginatedListingsResponse(BaseModel):
    listings: list[ListingResponse] = Field(description="Listings on the current page")
    page: int = Field(description="Current page index", examples=[1])
    limit: int = Field(description="Listing items per page", examples=[10])
    total_pages: int = Field(description="Total pages available", examples=[2])
    total_listings: int = Field(description="Total matching listings count", examples=[15])
