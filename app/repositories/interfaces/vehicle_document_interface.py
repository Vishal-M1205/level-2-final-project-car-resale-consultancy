from abc import ABC, abstractmethod

from app.models.vehicle_document import VehicleDocument


class VehicleDocumentInterface(ABC):
    @abstractmethod
    async def get_document_by_type(
        self, vehicle_id: int, document_type: str
    ) -> VehicleDocument | None:
        """
        Retrieve a vehicle document by vehicle ID and document type.
        """
        pass

    @abstractmethod
    async def get_documents_by_vehicle_id(self, vehicle_id: int) -> list[VehicleDocument]:
        """
        Retrieve all documents associated with a specific vehicle.
        """
        pass

    @abstractmethod
    async def upsert_vehicle_document(
        self,
        vehicle_id: int,
        document_type: str,
        original_filename: str,
        document_url: str,
    ) -> tuple[VehicleDocument, str | None]:
        """
        Insert or update a vehicle document.
        Returns a tuple of (VehicleDocument, old_document_url).
        If replacing an existing document, old_document_url will contain its previous path.
        """
        pass

    @abstractmethod
    async def delete_document(self, vehicle_id: int, document_type: str) -> bool:
        """
        Hard delete a vehicle document by vehicle ID and document type.
        Returns True if deleted, False if not found.
        """
        pass
