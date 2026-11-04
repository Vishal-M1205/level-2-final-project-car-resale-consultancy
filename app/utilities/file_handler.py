import os
from pathlib import Path
import uuid
import aiofiles
from fastapi import HTTPException, UploadFile, status

UPLOAD_DIR = Path("uploads") / "vehicles"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate that the uploaded file is a non-empty PDF and within the size limit.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are allowed.",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type,Expected application/pdf.",
        )

    if file.size is None or file.size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum allowed limit of 5MB.",
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
        file_content = await file.read()
        await out_file.write(file_content)

    relative_path = f"{UPLOAD_DIR.as_posix()}/{vehicle_id}/{unique_filename}"
    return relative_path


def delete_file(relative_path: str) -> None:
    """
    Safely delete a file from disk given its relative path.
    """
    if not relative_path:
        return

    full_path = Path(relative_path)
    if full_path.is_file():
        try:
            full_path.unlink()
        except OSError:
            pass
