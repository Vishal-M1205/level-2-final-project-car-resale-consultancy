from datetime import datetime
from decimal import Decimal
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.constants import FUEL_TYPES, TRANSMISSIONS


class VehicleSubmission(BaseModel):
    brand: str = Field(min_length=2, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    variant: str | None = Field(default=None, max_length=50)
    registration_number: str = Field(min_length=4, max_length=20)
    manufacturing_year: int = Field(ge=1980, le=datetime.now().year + 1)
    fuel_type: str
    transmission: str
    kilometers_driven: int = Field(ge=0)
    ownership_count: int = Field(default=1, ge=1, le=10)
    expected_price: Decimal = Field(gt=0, decimal_places=2)
    description: str | None = Field(default=None, max_length=1000)
    seating_capacity: int = Field(ge=1, le=20)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("registration_number")
    @classmethod
    def validate_registration_number(cls, value: str) -> str:
        reg_number = re.sub(r"[\s\-]", "", value).upper()
        if not re.match(r"^[A-Z0-9]{10}$", reg_number):
            raise ValueError("Invalid registration number format")
        return reg_number

    @field_validator("fuel_type")
    @classmethod
    def validate_fuel_type(cls, value: str) -> str:
        fuel = value.upper()
        if fuel not in FUEL_TYPES:
            raise ValueError(f"Fuel type must be one of {FUEL_TYPES}")
        return fuel

    @field_validator("transmission")
    @classmethod
    def validate_transmission(cls, value: str) -> str:
        transmission = value.upper()
        if transmission not in TRANSMISSIONS:
            raise ValueError(f"Transmission must be one of {TRANSMISSIONS}")
        return transmission


class VehicleUpdate(BaseModel):
    brand: str | None = Field(default=None, min_length=2, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=50)
    variant: str | None = Field(default=None, max_length=50)
    registration_number: str | None = Field(default=None, min_length=4, max_length=20)
    manufacturing_year: int | None = Field(
        default=None, ge=1980, le=datetime.now().year + 1
    )
    fuel_type: str | None = None
    transmission: str | None = None
    kilometers_driven: int | None = Field(default=None, ge=0)
    ownership_count: int | None = Field(default=None, ge=1, le=10)
    expected_price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    description: str | None = Field(default=None, max_length=1000)
    seating_capacity: int | None = Field(default=None, ge=1, le=20)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("registration_number")
    @classmethod
    def validate_registration_number(cls, value: str | None) -> str | None:
        if value is not None:
            reg_number = re.sub(r"[\s\-]", "", value).upper()
            if not re.match(r"^[A-Z0-9]{4,15}$", reg_number):
                raise ValueError("Invalid registration number format")
            return reg_number
        return value

    @field_validator("fuel_type")
    @classmethod
    def validate_fuel_type(cls, value: str | None) -> str | None:
        if value is not None:
            fuel = value.upper()
            if fuel not in FUEL_TYPES:
                raise ValueError(f"Fuel type must be one of {FUEL_TYPES}")
            return fuel
        return value

    @field_validator("transmission")
    @classmethod
    def validate_transmission(cls, value: str | None) -> str | None:
        if value is not None:
            transmission = value.upper()
            if transmission not in TRANSMISSIONS:
                raise ValueError(f"Transmission must be one of {TRANSMISSIONS}")
            return transmission
        return value


class VehicleResponse(BaseModel):
    id: int
    seller_id: int
    brand: str
    model: str
    variant: str | None
    registration_number: str
    manufacturing_year: int
    fuel_type: str
    transmission: str
    kilometers_driven: int
    ownership_count: int
    expected_price: Decimal
    description: str | None
    seating_capacity: int

    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleFilterParams(BaseModel):
    seller_id: int | None = None
    brand: str | None = None
    model: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    min_year: int | None = Field(default=None, ge=1900)
    max_year: int | None = None
    status: str | None = None

    page: int = Field(default=1, ge=1)
    limit: int = Field(default=5, ge=1, le=50)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("fuel_type", mode="before")
    @classmethod
    def uppercase_fuel_type(cls, value: str | None) -> str | None:
        return value.upper() if isinstance(value, str) else value

    @field_validator("transmission", mode="before")
    @classmethod
    def uppercase_transmission(cls, value: str | None) -> str | None:
        return value.upper() if isinstance(value, str) else value


class VehicleListResponse(BaseModel):
    vehicles: list[VehicleResponse]
    page: int
    limit: int
    total_pages: int
    total_vehicles: int


class VehicleDecisionRequest(BaseModel):
    action: str = Field(description="Must be 'APPROVED', 'REJECTED', or 'RESUBMIT'")
    rejection_reason: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        act = value.upper().strip()
        if act not in ("APPROVED", "REJECTED", "RESUBMIT"):
            raise ValueError(
                "Action must be either 'APPROVED', 'REJECTED', or 'RESUBMIT'"
            )
        return act


class VehicleDecisionResponse(BaseModel):
    vehicle_id: int
    status: str
    message: str
    listing_id: int | None = None
    listed_price: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)


class VehicleDeleteResponse(BaseModel):
    vehicle_id: int
    status: str
    message: str
