import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import FUEL_TYPES, TRANSMISSIONS


class VehicleSubmission(BaseModel):
    brand: str = Field(
        min_length=2, max_length=50, description="Vehicle manufacturer brand", examples=["Toyota"]
    )
    model: str = Field(
        min_length=1, max_length=50, description="Vehicle model name", examples=["Camry"]
    )
    variant: str | None = Field(
        default=None, max_length=50, description="Vehicle variant or trim", examples=["Hybrid LE"]
    )
    registration_number: str = Field(
        min_length=4,
        max_length=20,
        description="Vehicle registration / license plate number",
        examples=["TN38AB1234"],
    )
    manufacturing_year: int = Field(
        ge=1980,
        le=datetime.now().year + 1,
        description="Year of vehicle manufacture",
        examples=[2021],
    )
    fuel_type: str = Field(
        description="Fuel type: PETROL, DIESEL, ELECTRIC, HYBRID, CNG, LPG",
        examples=["PETROL"],
    )
    transmission: str = Field(
        description="Transmission type: MANUAL, AUTOMATIC",
        examples=["AUTOMATIC"],
    )
    kilometers_driven: int = Field(
        ge=0, description="Total distance driven in kilometers", examples=[35000]
    )
    ownership_count: int = Field(
        default=1, ge=1, le=10, description="Number of previous owners", examples=[1]
    )
    expected_price: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Seller's expected price in local currency",
        examples=[Decimal("850000.00")],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Detailed condition, accessories, and maintenance notes",
        examples=["Single owner, dealer serviced regularly."],
    )
    seating_capacity: int = Field(ge=1, le=20, description="Total seating capacity", examples=[5])

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
    brand: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Updated brand name",
        examples=["Toyota"],
    )
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Updated model name",
        examples=["Camry"],
    )
    variant: str | None = Field(
        default=None, max_length=50, description="Updated variant", examples=["Hybrid XLE"]
    )
    registration_number: str | None = Field(
        default=None,
        min_length=4,
        max_length=20,
        description="Updated registration number",
        examples=["TN38AB1234"],
    )
    manufacturing_year: int | None = Field(
        default=None,
        ge=1980,
        le=datetime.now().year + 1,
        description="Updated manufacturing year",
        examples=[2021],
    )
    fuel_type: str | None = Field(
        default=None, description="Updated fuel type", examples=["PETROL"]
    )
    transmission: str | None = Field(
        default=None, description="Updated transmission type", examples=["AUTOMATIC"]
    )
    kilometers_driven: int | None = Field(
        default=None, ge=0, description="Updated kilometers driven", examples=[36000]
    )
    ownership_count: int | None = Field(
        default=None, ge=1, le=10, description="Updated ownership count", examples=[1]
    )
    expected_price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
        description="Updated expected price",
        examples=[Decimal("840000.00")],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated description notes",
        examples=["Clean title, new tires."],
    )
    seating_capacity: int | None = Field(
        default=None, ge=1, le=20, description="Updated seating capacity", examples=[5]
    )

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
    id: int = Field(description="Unique vehicle identifier", examples=[1])
    seller_id: int = Field(description="ID of the user who submitted the vehicle", examples=[2])
    brand: str = Field(description="Vehicle manufacturer brand", examples=["Toyota"])
    model: str = Field(description="Vehicle model", examples=["Camry"])
    variant: str | None = Field(default=None, description="Vehicle variant", examples=["Hybrid LE"])
    registration_number: str = Field(
        description="Standardized vehicle registration number", examples=["TN38AB1234"]
    )
    manufacturing_year: int = Field(description="Year of manufacture", examples=[2021])
    fuel_type: str = Field(description="Engine fuel type", examples=["PETROL"])
    transmission: str = Field(description="Transmission type", examples=["AUTOMATIC"])
    kilometers_driven: int = Field(description="Kilometers driven", examples=[35000])
    ownership_count: int = Field(description="Number of owners", examples=[1])
    expected_price: Decimal = Field(description="Expected price", examples=[Decimal("850000.00")])
    description: str | None = Field(
        default=None,
        description="Vehicle notes and description",
        examples=["Single owner, well-kept."],
    )
    seating_capacity: int = Field(description="Seating capacity", examples=[5])

    status: str = Field(
        description="Current vehicle lifecycle status: submitted, approved, rejected, sold, deactivated",
        examples=["submitted"],
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class VehicleFilterParams(BaseModel):
    seller_id: int | None = Field(
        default=None, description="Filter vehicles by seller ID", examples=[2]
    )
    brand: str | None = Field(
        default=None, description="Filter by vehicle brand", examples=["Toyota"]
    )
    model: str | None = Field(default=None, description="Filter by model", examples=["Camry"])
    fuel_type: str | None = Field(
        default=None, description="Filter by fuel type", examples=["PETROL"]
    )
    transmission: str | None = Field(
        default=None, description="Filter by transmission", examples=["AUTOMATIC"]
    )
    min_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="Minimum expected price filter",
        examples=[Decimal("200000.00")],
    )
    max_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="Maximum expected price filter",
        examples=[Decimal("1000000.00")],
    )
    min_year: int | None = Field(
        default=None, ge=1900, description="Minimum manufacturing year filter", examples=[2018]
    )
    max_year: int | None = Field(
        default=None, description="Maximum manufacturing year filter", examples=[2024]
    )
    status: str | None = Field(
        default=None,
        description="Filter by status (submitted, approved, rejected, sold, deactivated)",
        examples=["submitted"],
    )

    page: int = Field(default=1, ge=1, description="Page index (starts at 1)", examples=[1])
    limit: int = Field(default=5, ge=1, le=50, description="Page size limit (max 50)", examples=[5])

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
    vehicles: list[VehicleResponse] = Field(description="List of vehicles on current page")
    page: int = Field(description="Current page index", examples=[1])
    limit: int = Field(description="Vehicles per page", examples=[5])
    total_pages: int = Field(description="Total pages available", examples=[2])
    total_vehicles: int = Field(description="Total matching vehicles count", examples=[8])


class VehicleDecisionRequest(BaseModel):
    action: str = Field(
        description="Must be 'APPROVED', 'REJECTED', or 'RESUBMIT'", examples=["APPROVED"]
    )
    rejection_reason: str | None = Field(
        default=None,
        max_length=500,
        description="Mandatory reason when action is REJECTED",
        examples=["Documentation incomplete"],
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        act = value.upper().strip()
        if act not in ("APPROVED", "REJECTED", "RESUBMIT"):
            raise ValueError("Action must be either 'APPROVED', 'REJECTED', or 'RESUBMIT'")
        return act


class VehicleDecisionResponse(BaseModel):
    vehicle_id: int = Field(description="Vehicle identifier", examples=[1])
    status: str = Field(description="Updated vehicle status", examples=["approved"])
    message: str = Field(description="Outcome message", examples=["Vehicle approved successfully."])
    listing_id: int | None = Field(
        default=None, description="Listing ID created on approval", examples=[1]
    )
    listed_price: Decimal | None = Field(
        default=None, description="Listed resale price", examples=[Decimal("850000.00")]
    )

    model_config = ConfigDict(from_attributes=True)


class VehicleDeleteResponse(BaseModel):
    vehicle_id: int = Field(description="Deactivated vehicle identifier", examples=[1])
    status: str = Field(
        description="Status after deletion ('deactivated')", examples=["deactivated"]
    )
    message: str = Field(
        description="Confirmation message", examples=["Vehicle successfully deactivated."]
    )
