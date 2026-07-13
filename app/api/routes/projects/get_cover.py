from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.project import CoverResponse


router = APIRouter()

_IMAGE_CACHE_SECONDS = 3600


@router.get("/{project_id}/cover", response_model=CoverResponse)
def get_project_cover(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Alumni | Admin = Depends(get_current_user),
):
    """Cover blob split into its own endpoint so list responses stay small."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return JSONResponse(
        content={"cover": project.cover},
        headers={"Cache-Control": f"private, max-age={_IMAGE_CACHE_SECONDS}"},
    )
