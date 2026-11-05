from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import CONDITIONS
from app.schemas.vehicle import VehicleResponse
from app.schemas.vehicle_document import VehicleDocumentResponse


class VehicleInspectionClaim(BaseModel):
    consultant_id: int = Field(description="ID of claiming consultant", examples=[2])
    consultant_name: str = Field(
        description="Name of claiming consultant", examples=["Consultant Jane"]
    )
    vehicle_id: int = Field(description="Vehicle ID claimed for inspection", examples=[1])


class UserBasicResponse(BaseModel):
    id: int = Field(description="User ID", examples=[2])
    name: str = Field(description="User full name", examples=["Jane Consultant"])
    email: str = Field(description="User email address", examples=["consultant@example.com"])
    phone: str = Field(description="User contact phone", examples=["9876543210"])

    model_config = ConfigDict(from_attributes=True)


class InspectionFilterParams(BaseModel):
    vehicle_id: int | None = Field(default=None, description="Filter by vehicle ID", examples=[1])
    status: str | None = Field(
        default=None,
        description="Filter by inspection status (PENDING, COMPLETED, CANCELLED)",
        examples=["PENDING"],
    )
    is_claimed: bool | None = Field(
        default=None,
        description="Filter by claim status (false = unassigned pool, true = claimed queue)",
        examples=[False],
    )
    consultant_id: int | None = Field(
        default=None, description="Filter by assigned consultant ID (Admin only)", examples=[2]
    )
    mine: bool = Field(
        default=False,
        description="Filter inspections claimed by current authenticated consultant",
        examples=[False],
    )
    inspection_date: date | None = Field(
        default=None,
        description="Filter by inspection date (YYYY-MM-DD)",
        examples=[date(2026, 11, 5)],
    )
    vehicle_status: str | None = Field(
        default=None, description="Filter by vehicle status", examples=["submitted"]
    )
    page: int = Field(default=1, ge=1, description="Page number", examples=[1])
    limit: int = Field(default=10, ge=1, le=50, description="Page size limit", examples=[10])

    model_config = ConfigDict(str_strip_whitespace=True)


class CustomerInspectionFilterParams(BaseModel):
    vehicle_id: int | None = Field(default=None, description="Filter by vehicle ID", examples=[1])
    status: str | None = Field(
        default=None,
        description="Filter by inspection status (PENDING, COMPLETED, CANCELLED)",
        examples=["PENDING"],
    )
    inspection_date: date | None = Field(
        default=None,
        description="Filter by inspection date (YYYY-MM-DD)",
        examples=[date(2026, 11, 5)],
    )
    vehicle_status: str | None = Field(
        default=None, description="Filter by vehicle status", examples=["submitted"]
    )
    page: int = Field(default=1, ge=1, description="Page number", examples=[1])
    limit: int = Field(default=10, ge=1, le=50, description="Page size limit", examples=[10])

    model_config = ConfigDict(str_strip_whitespace=True)


class VehicleInspectionDetailResponse(BaseModel):
    id: int = Field(description="Inspection record ID", examples=[1])
    vehicle_id: int = Field(description="Vehicle ID", examples=[1])
    consultant_id: int | None = Field(
        default=None, description="Assigned consultant user ID", examples=[2]
    )
    condition: str | None = Field(
        default=None,
        description="Overall vehicle condition (excellent, good, fair, poor)",
        examples=["good"],
    )
    engine_condition: str | None = Field(
        default=None, description="Engine rating", examples=["good"]
    )
    exterior_condition: str | None = Field(
        default=None, description="Exterior body rating", examples=["good"]
    )
    interior_condition: str | None = Field(
        default=None, description="Interior cabin rating", examples=["excellent"]
    )
    accident_history: bool | None = Field(
        default=None, description="Whether major accident damage was reported", examples=[False]
    )
    estimated_market_value: Decimal | None = Field(
        default=None,
        description="Consultant estimated market valuation",
        examples=[Decimal("820000.00")],
    )
    inspection_notes: str | None = Field(
        default=None,
        description="Detailed observations and defects report",
        examples=["Vehicle mechanically sound."],
    )
    inspection_date: datetime | None = Field(
        default=None, description="Timestamp when inspection took place"
    )
    status: str = Field(
        description="Inspection status (PENDING, COMPLETED, CANCELLED)", examples=["COMPLETED"]
    )
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Record update timestamp")
    vehicle: VehicleResponse = Field(description="Associated vehicle details")
    consultant: UserBasicResponse | None = Field(
        default=None, description="Assigned consultant details"
    )

    model_config = ConfigDict(from_attributes=True)


class PaginatedInspectionsResponse(BaseModel):
    inspections: list[VehicleInspectionDetailResponse] = Field(
        description="Inspections list on current page"
    )
    page: int = Field(description="Current page index", examples=[1])
    limit: int = Field(description="Items per page", examples=[10])
    total_pages: int = Field(description="Total page count", examples=[1])
    total_inspections: int = Field(description="Total matching inspections count", examples=[5])


class VehicleInspectionDetailSubmission(BaseModel):
    condition: str = Field(
        description="Overall condition rating: excellent, good, fair, poor", examples=["good"]
    )
    engine_condition: str = Field(
        description="Engine rating: excellent, good, fair, poor", examples=["good"]
    )
    exterior_condition: str = Field(
        description="Exterior rating: excellent, good, fair, poor", examples=["good"]
    )
    interior_condition: str = Field(
        description="Interior rating: excellent, good, fair, poor", examples=["excellent"]
    )
    accident_history: bool = Field(
        description="Whether vehicle has an accident history", examples=[False]
    )
    estimated_market_value: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Estimated fair market value in local currency",
        examples=[Decimal("820000.00")],
    )
    inspection_notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Detailed physical inspection findings and observations",
        examples=["Engine runs smooth, brake pads at 80%."],
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("condition", "engine_condition", "exterior_condition", "interior_condition")
    @classmethod
    def validate_conditions(cls, value: str) -> str:
        val = value.lower()
        if val not in CONDITIONS:
            raise ValueError(f"Value must be one of {CONDITIONS}")
        return val


class AdminInspectionDetailResponse(BaseModel):
    id: int = Field(description="Inspection record ID", examples=[1])
    vehicle_id: int = Field(description="Vehicle ID", examples=[1])
    consultant_id: int | None = Field(
        default=None, description="Assigned consultant user ID", examples=[2]
    )
    condition: str | None = Field(
        default=None, description="Overall vehicle condition", examples=["good"]
    )
    engine_condition: str | None = Field(
        default=None, description="Engine condition", examples=["good"]
    )
    exterior_condition: str | None = Field(
        default=None, description="Exterior condition", examples=["good"]
    )
    interior_condition: str | None = Field(
        default=None, description="Interior condition", examples=["excellent"]
    )
    accident_history: bool | None = Field(
        default=None, description="Whether accident history exists", examples=[False]
    )
    estimated_market_value: Decimal | None = Field(
        default=None, description="Consultant valuation", examples=[Decimal("820000.00")]
    )
    inspection_notes: str | None = Field(
        default=None, description="Consultant notes", examples=["Vehicle in good shape."]
    )
    inspection_date: datetime | None = Field(default=None, description="Timestamp of inspection")
    status: str = Field(description="Inspection status", examples=["COMPLETED"])
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    vehicle: VehicleResponse = Field(description="Associated vehicle details")
    consultant: UserBasicResponse | None = Field(
        default=None, description="Assigned consultant details"
    )
    documents: list[VehicleDocumentResponse] = Field(
        default=[], description="Uploaded documents associated with vehicle"
    )

    model_config = ConfigDict(from_attributes=True)


class InspectionUnclaimResponse(BaseModel):
    inspection_id: int = Field(description="Inspection identifier", examples=[1])
    vehicle_id: int = Field(description="Vehicle identifier", examples=[1])
    status: str = Field(description="New status ('PENDING')", examples=["PENDING"])
    message: str = Field(
        description="Confirmation message", examples=["Inspection successfully unclaimed."]
    )


class InspectionCancelResponse(BaseModel):
    inspection_id: int = Field(description="Inspection identifier", examples=[1])
    vehicle_id: int = Field(description="Vehicle identifier", examples=[1])
    inspection_status: str = Field(
        description="Updated inspection status ('CANCELLED')", examples=["CANCELLED"]
    )
    vehicle_status: str = Field(
        description="Updated vehicle status ('rejected')", examples=["rejected"]
    )
    message: str = Field(
        description="Confirmation message", examples=["Inspection cancelled and vehicle rejected."]
    )
