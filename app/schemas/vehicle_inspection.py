from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.constants import CONDITIONS
from app.schemas.vehicle import VehicleResponse
from app.schemas.vehicle_document import VehicleDocumentResponse


class VehicleInspectionClaim(BaseModel):
    consultant_id: int
    consultant_name: str
    vehicle_id: int


class UserBasicResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str

    model_config = ConfigDict(from_attributes=True)


class InspectionFilterParams(BaseModel):
    vehicle_id: int | None = None
    status: str | None = None
    is_claimed: bool | None = None
    consultant_id: int | None = None
    mine: bool = False
    inspection_date: date | None = None
    vehicle_status: str | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)

    model_config = ConfigDict(str_strip_whitespace=True)


class CustomerInspectionFilterParams(BaseModel):
    vehicle_id: int | None = None
    status: str | None = None
    inspection_date: date | None = None
    vehicle_status: str | None = None
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
    consultant: UserBasicResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedInspectionsResponse(BaseModel):
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


class AdminInspectionDetailResponse(BaseModel):
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
    consultant: UserBasicResponse | None = None
    documents: list[VehicleDocumentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InspectionUnclaimResponse(BaseModel):
    inspection_id: int
    vehicle_id: int
    status: str
    message: str


class InspectionCancelResponse(BaseModel):
    inspection_id: int
    vehicle_id: int
    inspection_status: str
    vehicle_status: str
    message: str
