from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VehicleDocumentResponse(BaseModel):
    """
    Response schema for a single vehicle document.
    """
    id: int
    vehicle_id: int
    document_type: str
    original_filename: str
    document_url: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleDocumentListResponse(BaseModel):
    """
    Response schema for listing all documents attached to a vehicle.
    """
    vehicle_id: int
    documents: list[VehicleDocumentResponse]

    model_config = ConfigDict(from_attributes=True)


class VehicleDocumentDeleteResponse(BaseModel):
    vehicle_id: int
    document_type: str
    message: str

