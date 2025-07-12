from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Union
from app.core.database import get_db
from app.services.email_hash_service import process_excel_file
from app.schemas.allowed_emails import AllowedEmailResponse
from app.core.security import get_current_user
from app.models.users import Admin, Alumni

router = APIRouter()

@router.post("/upload-allowed-emails", response_model=AllowedEmailResponse)
async def upload_allowed_emails(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Union[Admin, Alumni] = Depends(get_current_user)
):
    """
    Upload an Excel file with allowed email addresses.
    The first column of the Excel file should contain email addresses.
    """
    print(f"Upload allowed emails request received, file: {file.filename}")
    
    # Check if user is admin
    if not isinstance(current_user, Admin):
        print(f"Access denied: User is not an admin")
        raise HTTPException(status_code=403, detail="Only administrators can upload allowed emails")
    
    print(f"Admin authorized to upload allowed emails")
    
    # Check file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        print(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    print(f"File format valid: {file.filename}")
    
    # Read file content
    file_content = await file.read()
    print(f"File content read, size: {len(file_content)} bytes")
    
    # Process the Excel file
    result = process_excel_file(db, file_content)
    print(f"File processing result: {result}")
    
    if not result["success"]:
        print(f"File processing failed: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    print(f"File processing successful: {result['message']}")
    return result