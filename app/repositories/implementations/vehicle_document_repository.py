from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle_document import VehicleDocument
from app.repositories.interfaces.vehicle_document_interface import (
    VehicleDocumentInterface,
)


class VehicleDocumentRepository(VehicleDocumentInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_document_by_type(
        self, vehicle_id: int, document_type: str
    ) -> VehicleDocument | None:
        stmnt = select(VehicleDocument).where(
            VehicleDocument.vehicle_id == vehicle_id,
            VehicleDocument.document_type == document_type,
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def get_documents_by_vehicle_id(
        self, vehicle_id: int
    ) -> list[VehicleDocument]:
        stmnt = (
            select(VehicleDocument)
            .where(VehicleDocument.vehicle_id == vehicle_id)
            .order_by(VehicleDocument.uploaded_at.asc())
        )
        result = await self.session.execute(stmnt)
        return list(result.scalars().all())

    async def upsert_vehicle_document(
        self,
        vehicle_id: int,
        document_type: str,
        original_filename: str,
        document_url: str,
    ) -> tuple[VehicleDocument, str | None]:
        existing = await self.get_document_by_type(vehicle_id, document_type)

        if existing:
            old_document_url = existing.document_url
            existing.original_filename = original_filename
            existing.document_url = document_url
            existing.uploaded_at = func.now()
            await self.session.flush()
            await self.session.refresh(existing)
            return existing, old_document_url

        new_doc = VehicleDocument(
            vehicle_id=vehicle_id,
            document_type=document_type,
            original_filename=original_filename,
            document_url=document_url,
        )
        self.session.add(new_doc)
        await self.session.flush()
        await self.session.refresh(new_doc)
        return new_doc, None

    async def delete_document(
        self, vehicle_id: int, document_type: str
    ) -> bool:
        doc = await self.get_document_by_type(vehicle_id, document_type)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.flush()
        return True

