from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleDocumentResponse(BaseModel):
    """
    Response schema for a single vehicle document.
    """

    id: int = Field(description="Unique document identifier", examples=[1])
    vehicle_id: int = Field(
        description="Vehicle identifier to which the document belongs", examples=[1]
    )
    document_type: str = Field(
        description="Type of uploaded document (RC, INSURANCE, PUC)", examples=["RC"]
    )
    original_filename: str = Field(
        description="Original filename uploaded by user", examples=["vehicle_rc.pdf"]
    )
    document_url: str = Field(
        description="File access path or URL", examples=["/uploads/documents/vehicle_rc.pdf"]
    )
    uploaded_at: datetime = Field(description="Timestamp when the document was uploaded")

    model_config = ConfigDict(from_attributes=True)


class VehicleDocumentListResponse(BaseModel):
    """
    Response schema for listing all documents attached to a vehicle.
    """

    vehicle_id: int = Field(description="Vehicle identifier", examples=[1])
    documents: list[VehicleDocumentResponse] = Field(
        description="List of documents attached to the vehicle"
    )

    model_config = ConfigDict(from_attributes=True)


class VehicleDocumentDeleteResponse(BaseModel):
    vehicle_id: int = Field(description="Vehicle identifier", examples=[1])
    document_type: str = Field(
        description="Document type that was deleted (RC, INSURANCE, PUC)", examples=["RC"]
    )
    message: str = Field(description="Outcome message", examples=["Document deleted successfully."])
