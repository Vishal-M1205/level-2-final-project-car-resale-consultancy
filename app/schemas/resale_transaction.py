from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.vehicle_listing import ListingResponse


class CreateResaleTransactionRequest(BaseModel):
    listing_id: int
    buyer_id: int
    final_price: Decimal = Field(gt=0, decimal_places=2)
    consultant_id: int | None = None
    delivery_date: datetime | None = None
    delivery_notes: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(str_strip_whitespace=True)


class TransactionUserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str

    model_config = ConfigDict(from_attributes=True)


class ResaleTransactionResponse(BaseModel):
    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    consultant_id: int | None
    final_price: Decimal
    status: str
    delivery_date: datetime | None
    delivery_notes: str | None
    created_at: datetime
    updated_at: datetime
    buyer: TransactionUserResponse | None = None
    seller: TransactionUserResponse | None = None
    consultant: TransactionUserResponse | None = None
    listing: ListingResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class TransactionFilterParams(BaseModel):
    status: str | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)

    model_config = ConfigDict(str_strip_whitespace=True)


class PaginatedTransactionsResponse(BaseModel):
    transactions: list[ResaleTransactionResponse]
    page: int
    limit: int
    total_pages: int
    total_transactions: int

