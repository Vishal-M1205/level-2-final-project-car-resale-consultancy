from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DOCUMENT_TYPES
from app.models.user import User
from app.models.vehicle_document import VehicleDocument
from app.repositories.interfaces.vehicle_document_interface import (
    VehicleDocumentInterface,
)
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.utilities.file_handler import (
    delete_file,
    save_vehicle_document_file,
    validate_pdf_file,
)


class VehicleDocumentService:
    def __init__(
        self,
        session: AsyncSession,
        vehicle_repository: VehicleInterface,
        vehicle_document_repository: VehicleDocumentInterface,
    ):
        self.session = session
        self.vehicle_repository = vehicle_repository
        self.vehicle_document_repository = vehicle_document_repository

    async def upload_document(
        self,
        vehicle_id: int,
        document_type: str,
        file: UploadFile,
        user: User,
    ) -> VehicleDocument:
        doc_type = document_type.upper().strip()

        # Validate document type in allowed types
        if doc_type not in DOCUMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type '{document_type}'. Allowed types: {DOCUMENT_TYPES}",
            )

        # Validate the file to check it is empty or greater than the max size, whether .pdf or not
        validate_pdf_file(file)
        saved_path: str | None = None
        try:
            async with self.session.begin():

                vehicle = await self.vehicle_repository.get_vehicle_by_id(vehicle_id)
                if not vehicle:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Vehicle not found.",
                    )

                if user.role != "ADMIN" and vehicle.seller_id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You do not have permission to upload documents for this vehicle.",
                    )

                # Documents can only be uploaded/updated while vehicle is in submitted or rejected status
                if vehicle.status not in ("submitted", "rejected"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot upload documents. Vehicle status is '{vehicle.status}', documents can only be submitted while 'submitted' or 'rejected'.",
                    )

                saved_path = await save_vehicle_document_file(file, vehicle_id)

                document, old_document_url = (
                    await self.vehicle_document_repository.upsert_vehicle_document(
                        vehicle_id=vehicle_id,
                        document_type=doc_type,
                        original_filename=file.filename or f"{doc_type}.pdf",
                        document_url=saved_path,
                    )
                )

            # Clean up the previous physical file if this was an update/replacement
            if old_document_url and old_document_url != saved_path:
                delete_file(old_document_url)

            return document

        except Exception:
            # Clean up newly written file if database transaction fails
            if saved_path:
                delete_file(saved_path)
            raise

    async def get_vehicle_documents(
        self,
        vehicle_id: int,
        user: User,
    ) -> list[VehicleDocument]:
        async with self.session.begin():
            vehicle = await self.vehicle_repository.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vehicle not found.",
                )

            # Customers can only view documents of their own vehicles
            if user.role == "CUSTOMER" and vehicle.seller_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view documents for this vehicle.",
                )

            return await self.vehicle_document_repository.get_documents_by_vehicle_id(
                vehicle_id
            )

    async def delete_vehicle_document(
        self,
        vehicle_id: int,
        document_type: str,
        user: User,
    ) -> dict:
        doc_type = document_type.upper().strip()
        if doc_type not in DOCUMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type '{document_type}'. Allowed types: {DOCUMENT_TYPES}",
            )

        file_to_delete: str | None = None
        async with self.session.begin():
            vehicle = await self.vehicle_repository.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vehicle not found.",
                )

            if user.role != "ADMIN" and vehicle.seller_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to delete documents for this vehicle.",
                )

            if vehicle.status != "submitted":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete document. Documents can only be deleted when vehicle status is 'submitted' (current status: '{vehicle.status}').",
                )

            doc = await self.vehicle_document_repository.get_document_by_type(
                vehicle_id, doc_type
            )
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document of type '{doc_type}' not found for this vehicle.",
                )

            file_to_delete = doc.document_url
            await self.vehicle_document_repository.delete_document(vehicle_id, doc_type)

        if file_to_delete:
            delete_file(file_to_delete)

        return {
            "vehicle_id": vehicle_id,
            "document_type": doc_type,
            "message": f"Document '{doc_type}' deleted successfully.",
        }
