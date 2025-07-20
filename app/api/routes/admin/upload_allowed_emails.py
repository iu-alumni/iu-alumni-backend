import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import Admin, Alumni
from app.services.email_hash_service import process_excel_file


# Get logger for this module
logger = logging.getLogger("iu_alumni.admin.upload_allowed_emails")

router = APIRouter()


@router.post("/upload-allowed-emails")
async def upload_allowed_emails(
    file: UploadFile = File(...),
    current_user: Annotated[Alumni | Admin, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """
    Upload an Excel file containing allowed email addresses.

    The first column of the Excel file should contain email addresses.
    """
    logger.info(f"Upload allowed emails request received, file: {file.filename}")

    # Check if user is admin
    if not isinstance(current_user, Admin):
        logger.warning("Access denied: User is not an admin")
        raise HTTPException(
            status_code=403, detail="Only administrators can upload allowed emails"
        )

    logger.info("Admin authorized to upload allowed emails")

    # Check file extension
    if not file.filename.endswith((".xlsx", ".xls")):
        logger.error(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are supported",
        )

    logger.info(f"File format valid: {file.filename}")

    # Read file content
    file_content = await file.read()
    logger.info(f"File content read, size: {len(file_content)} bytes")

    # Process the Excel file
    result = process_excel_file(db, file_content)
    logger.info(f"File processing result: {result}")

    if not result["success"]:
        logger.error(f"File processing failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
        )

    logger.info(f"File processing successful: {result['message']}")
    return result
