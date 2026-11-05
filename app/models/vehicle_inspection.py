from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

from app.core.constants import CONDITIONS, INSPECTION_STATUSES
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle import Vehicle


class VehicleInspection(Base):
    __tablename__ = "vehicle_inspections"

    __table_args__ = (
        CheckConstraint(f"condition IN {CONDITIONS}", name="vehicle_inspection_condition_check"),
        CheckConstraint(
            f"engine_condition IN {CONDITIONS}",
            name="vehicle_inspection_engine_condition_check",
        ),
        CheckConstraint(
            f"exterior_condition IN {CONDITIONS}",
            name="vehicle_inspection_exterior_condition_check",
        ),
        CheckConstraint(
            f"interior_condition IN {CONDITIONS}",
            name="vehicle_inspection_interior_condition_check",
        ),
        CheckConstraint(
            f"status IN {INSPECTION_STATUSES}",
            name="vehicle_inspection_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
    )
    consultant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    condition: Mapped[str | None] = mapped_column(String(20), nullable=True)
    engine_condition: Mapped[str | None] = mapped_column(String(20), nullable=True)
    exterior_condition: Mapped[str | None] = mapped_column(String(20), nullable=True)
    interior_condition: Mapped[str | None] = mapped_column(String(20), nullable=True)

    accident_history: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    estimated_market_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    inspection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    inspection_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

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

    # Relationships: 1-to-1 with Vehicle, N-to-1 with Consultant (User)
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="inspection")
    consultant: Mapped["User | None"] = relationship("User", back_populates="inspections")
