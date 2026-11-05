from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import RESALE_TRANSACTION_STATUSES
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle_listing import VehicleListing


class ResaleTransaction(Base):
    __tablename__ = "resale_transactions"

    __table_args__ = (
        CheckConstraint("final_price > 0", name="final_price_check"),
        CheckConstraint(
            f"status IN {RESALE_TRANSACTION_STATUSES}",
            name="resale_transaction_status_check",
        ),
        CheckConstraint("buyer_id != seller_id", name="resale_buyer_not_seller_check"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicle_listings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    buyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    consultant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    final_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CONFIRMED")

    delivery_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivery_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    listing: Mapped["VehicleListing"] = relationship(
        "VehicleListing", back_populates="transactions"
    )
    buyer: Mapped["User"] = relationship(
        "User", foreign_keys=[buyer_id], back_populates="buyer_transactions"
    )
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], back_populates="seller_transactions"
    )
    consultant: Mapped["User | None"] = relationship(
        "User", foreign_keys=[consultant_id], back_populates="consultant_transactions"
    )
