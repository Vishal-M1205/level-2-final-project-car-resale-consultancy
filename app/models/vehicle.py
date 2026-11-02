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

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle_inspection import VehicleInspection
    from app.models.vehicle_listing import VehicleListing

VEHICLE_STATUSES = ("submitted", "approved", "rejected", "sold")


class Vehicle(Base):
    __tablename__ = "vehicles"

    __table_args__ = (
        CheckConstraint(
            f"status IN {VEHICLE_STATUSES}",
            name="vehicle_status_check",
        ),
        CheckConstraint("expected_price > 0", name="vehicle_expected_price_check"),
        CheckConstraint("kilometers_driven >= 0", name="vehicle_km_check"),
        CheckConstraint(
            "manufacturing_year >= 1900", name="vehicle_manufacturing_year_check"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    variant: Mapped[str | None] = mapped_column(String(50), nullable=True)
    registration_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    manufacturing_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    transmission: Mapped[str] = mapped_column(String(30), nullable=False)
    kilometers_driven: Mapped[int] = mapped_column(Integer, nullable=False)
    ownership_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expected_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    seating_capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="submitted",
        nullable=False,
    )

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
    seller: Mapped["User"] = relationship("User", back_populates="vehicles")
    inspection: Mapped["VehicleInspection | None"] = relationship(
        "VehicleInspection", back_populates="vehicle", uselist=False
    )
    listing: Mapped["VehicleListing | None"] = relationship(
        "VehicleListing", back_populates="vehicle", uselist=False
    )
