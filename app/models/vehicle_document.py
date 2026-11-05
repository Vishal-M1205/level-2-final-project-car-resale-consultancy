from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DOCUMENT_TYPES
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle


class VehicleDocument(Base):
    __tablename__ = "vehicle_documents"

    __table_args__ = (
        CheckConstraint(
            f"document_type IN {DOCUMENT_TYPES}",
            name="vehicle_document_type_check",
        ),
        UniqueConstraint("vehicle_id", "document_type", name="uq_vehicle_document_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_url: Mapped[str] = mapped_column(String(500), nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="documents")
