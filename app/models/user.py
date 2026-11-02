from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import GENDERS
from app.core.scopes import ROLES
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.resale_transaction import ResaleTransaction
    from app.models.vehicle import Vehicle
    from app.models.vehicle_inspection import VehicleInspection


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(f"role IN {tuple(ROLES)}", name="user_role_check"),
        CheckConstraint(f"gender IN {GENDERS}", name="user_gender_check"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    role: Mapped[str] = mapped_column(String(20), default="CUSTOMER", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="seller")
    inspections: Mapped[list["VehicleInspection"]] = relationship(
        "VehicleInspection", back_populates="consultant"
    )
    buyer_transactions: Mapped[list["ResaleTransaction"]] = relationship(
        "ResaleTransaction",
        foreign_keys="ResaleTransaction.buyer_id",
        back_populates="buyer",
    )
    seller_transactions: Mapped[list["ResaleTransaction"]] = relationship(
        "ResaleTransaction",
        foreign_keys="ResaleTransaction.seller_id",
        back_populates="seller",
    )
    consultant_transactions: Mapped[list["ResaleTransaction"]] = relationship(
        "ResaleTransaction",
        foreign_keys="ResaleTransaction.consultant_id",
        back_populates="consultant",
    )
