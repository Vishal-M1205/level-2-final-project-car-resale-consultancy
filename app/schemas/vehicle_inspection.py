from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.constants import CONDITIONS
from app.schemas.vehicle import VehicleResponse


class VehicleInspectionClaim(BaseModel):
    consultant_id: int
    consultant_name: str
    vehicle_id: int


class PendingInspectionResponse(BaseModel):
    id: int
    vehicle_id: int
    status: str
    created_at: datetime
    vehicle: VehicleResponse

    model_config = ConfigDict(from_attributes=True)


class PaginatedPendingInspectionsResponse(BaseModel):
    inspections: list[PendingInspectionResponse]
    page: int
    limit: int
    total_pages: int
    total_inspections: int


class ConsultantInspectionFilterParams(BaseModel):
    status: str | None = None
    inspection_date: date | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)

    model_config = ConfigDict(str_strip_whitespace=True)


class VehicleInspectionDetailResponse(BaseModel):
    id: int
    vehicle_id: int
    consultant_id: int | None
    condition: str | None
    engine_condition: str | None
    exterior_condition: str | None
    interior_condition: str | None
    accident_history: bool | None
    estimated_market_value: Decimal | None
    inspection_notes: str | None
    inspection_date: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime
    vehicle: VehicleResponse

    model_config = ConfigDict(from_attributes=True)


class MyInspectionListResponse(BaseModel):
    consultant_id: int
    consultant_name: str
    inspections: list[VehicleInspectionDetailResponse]
    page: int
    limit: int
    total_pages: int
    total_inspections: int


class VehicleInspectionDetailSubmission(BaseModel):
    condition: str
    engine_condition: str
    exterior_condition: str
    interior_condition: str
    accident_history: bool
    estimated_market_value: Decimal = Field(gt=0, decimal_places=2)
    inspection_notes: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator(
        "condition", "engine_condition", "exterior_condition", "interior_condition"
    )
    @classmethod
    def validate_conditions(cls, value: str) -> str:
        val = value.lower()
        if val not in CONDITIONS:
            raise ValueError(f"Value must be one of {CONDITIONS}")
        return val
