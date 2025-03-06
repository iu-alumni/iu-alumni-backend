from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.user_import import import_graduates_from_excel
import tempfile
import os

router = APIRouter()

@router.post("/import-alumni", status_code=status.HTTP_201_CREATED)
async def import_alumni_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import alumni data from an Excel file.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are supported"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file_path = temp_file.name
        content = await file.read()
        temp_file.write(content)
    
    try:
        # Process the file
        import_graduates_from_excel(db, temp_file_path)
        
        # Return success response
        return {"status": "success", "message": "Alumni data imported successfully"}
    except ValueError as e:
        # Handle validation errors from the import function
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during import: {str(e)}"
        )
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
