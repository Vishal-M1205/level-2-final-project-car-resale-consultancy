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

from app.core.constants import VEHICLE_LISTING_STATUSES
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.resale_transaction import ResaleTransaction
    from app.models.vehicle import Vehicle


class VehicleListing(Base):
    __tablename__ = "vehicle_listings"

    __table_args__ = (
        CheckConstraint(
            f"status IN {VEHICLE_LISTING_STATUSES}",
            name="vehicle_listing_status_check",
        ),
        CheckConstraint("listed_price > 0", name="vehicle_listing_price_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    listed_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    listing_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    listed_at: Mapped[datetime] = mapped_column(
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
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="listing")
    transactions: Mapped[list["ResaleTransaction"]] = relationship(
        "ResaleTransaction", back_populates="listing"
    )
