from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import RESALE_TRANSACTION_STATUSES
from app.schemas.vehicle_listing import ListingResponse


class CreateResaleTransactionRequest(BaseModel):
    listing_id: int = Field(
        description="Active listing ID of the vehicle being purchased", examples=[1]
    )
    buyer_id: int = Field(description="Customer user ID of the buyer", examples=[3])
    final_price: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Final agreed transaction price",
        examples=[Decimal("840000.00")],
    )
    consultant_id: int | None = Field(
        default=None,
        description="Optional consultant ID facilitating resale",
        examples=[2],
    )
    delivery_date: datetime | None = Field(
        default=None, description="Scheduled or actual vehicle delivery timestamp"
    )
    delivery_notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Delivery or handover remarks",
        examples=["Vehicle inspected and keys handed over."],
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("delivery_date")
    @classmethod
    def normalize_delivery_date(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class TransactionUserResponse(BaseModel):
    id: int = Field(description="User identifier", examples=[3])
    name: str = Field(description="Full user name", examples=["Buyer Bob"])
    email: str = Field(description="Email address", examples=["buyer@example.com"])
    phone: str = Field(description="Contact mobile phone number", examples=["9876543210"])

    model_config = ConfigDict(from_attributes=True)


class ResaleTransactionResponse(BaseModel):
    id: int = Field(description="Transaction identifier", examples=[1])
    listing_id: int = Field(description="Associated listing ID", examples=[1])
    buyer_id: int = Field(description="Buyer user ID", examples=[3])
    seller_id: int = Field(description="Seller user ID", examples=[2])
    consultant_id: int | None = Field(default=None, description="Consultant user ID", examples=[4])
    final_price: Decimal = Field(description="Final sale price", examples=[Decimal("840000.00")])
    status: str = Field(
        description="Transaction status: PENDING, COMPLETED, DELIVERED, CANCELLED",
        examples=["COMPLETED"],
    )
    delivery_date: datetime | None = Field(default=None, description="Delivery timestamp")
    delivery_notes: str | None = Field(
        default=None,
        description="Delivery remarks",
        examples=["Handed over with all docs."],
    )
    created_at: datetime = Field(description="Transaction logged timestamp")
    updated_at: datetime = Field(description="Transaction last updated timestamp")
    buyer: TransactionUserResponse | None = Field(default=None, description="Buyer profile summary")
    seller: TransactionUserResponse | None = Field(
        default=None, description="Seller profile summary"
    )
    consultant: TransactionUserResponse | None = Field(
        default=None, description="Consultant profile summary"
    )
    listing: ListingResponse | None = Field(default=None, description="Vehicle listing details")

    model_config = ConfigDict(from_attributes=True)


class TransactionFilterParams(BaseModel):
    status: str | None = Field(
        default=None,
        description="Filter transactions by status: PENDING, COMPLETED, DELIVERED, CANCELLED",
        examples=["COMPLETED"],
    )
    page: int = Field(default=1, ge=1, description="Page index (starts at 1)", examples=[1])
    limit: int = Field(default=10, ge=1, le=50, description="Page size limit", examples=[10])

    model_config = ConfigDict(str_strip_whitespace=True)


class PaginatedTransactionsResponse(BaseModel):
    transactions: list[ResaleTransactionResponse] = Field(
        description="List of transactions on current page"
    )
    page: int = Field(description="Current page index", examples=[1])
    limit: int = Field(description="Transaction items per page", examples=[10])
    total_pages: int = Field(description="Total pages available", examples=[1])
    total_transactions: int = Field(description="Total matching transactions count", examples=[5])


class ResaleTransactionPatchRequest(BaseModel):
    status: str | None = Field(
        default=None,
        description="Updated status: DELIVERED or CANCELLED",
        examples=["DELIVERED"],
    )
    delivery_date: datetime | None = Field(
        default=None, description="Updated vehicle handover timestamp"
    )
    delivery_notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated delivery notes",
        examples=["Delivered to buyer residence."],
    )
    final_price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
        description="Updated final sale price",
        examples=[Decimal("835000.00")],
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("delivery_date")
    @classmethod
    def normalize_delivery_date(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None:
            val = value.upper().strip()
            if val not in RESALE_TRANSACTION_STATUSES:
                raise ValueError(f"Status must be one of {RESALE_TRANSACTION_STATUSES}")
            return val
        return value
