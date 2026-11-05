import os
from pathlib import Path
import uuid
import aiofiles
from fastapi import UploadFile

from app.exceptions import BadRequestException

UPLOAD_DIR = Path("uploads") / "vehicles"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate that the uploaded file is a non-empty PDF and within the size limit.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise BadRequestException("Only PDF documents are allowed.")

    if file.content_type != "application/pdf":
        raise BadRequestException("Invalid content type,Expected application/pdf.")

    if file.size is None or file.size <= 0:
        raise BadRequestException("Uploaded file is empty.")

    if file.size > MAX_FILE_SIZE:
        raise BadRequestException(
            "File size exceeds the maximum allowed limit of 5MB."
        )


async def save_vehicle_document_file(file: UploadFile, vehicle_id: int) -> str:
    """
    Validate and save the uploaded vehicle document, returns the relative path
    """
    validate_pdf_file(file)

    target_directory = UPLOAD_DIR / str(vehicle_id)
    target_directory.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}.pdf"
    file_path = target_directory / unique_filename

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return str(file_path).replace("\\", "/")


def delete_file(file_path: str) -> bool:
    """
    Utility function to safely delete a file from the filesystem.
    """
    try:
        path = Path(file_path)
        if path.is_file():
            os.remove(path)
            return True
        return False
    except OSError:
        return False
