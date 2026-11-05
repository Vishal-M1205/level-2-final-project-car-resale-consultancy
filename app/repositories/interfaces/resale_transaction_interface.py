from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from app.models.resale_transaction import ResaleTransaction
from app.schemas.resale_transaction import TransactionFilterParams


class ResaleTransactionInterface(ABC):
    @abstractmethod
    async def create_transaction(
        self,
        listing_id: int,
        buyer_id: int,
        seller_id: int,
        final_price: Decimal,
        consultant_id: int | None = None,
        delivery_date: datetime | None = None,
        delivery_notes: str | None = None,
    ) -> ResaleTransaction:
        pass

    @abstractmethod
    async def get_transactions(
        self,
        filters: TransactionFilterParams,
        user_id: int | None = None,
        role: str | None = None,
    ) -> dict:
        pass

    @abstractmethod
    async def get_transaction_by_id(self, transaction_id: int) -> ResaleTransaction | None:
        pass

    @abstractmethod
    async def update_transaction(
        self, transaction_id: int, update_data: dict
    ) -> ResaleTransaction | None:
        pass
