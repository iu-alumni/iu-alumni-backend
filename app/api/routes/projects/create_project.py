from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_random_token
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.project import CreateProjectRequest, CreateProjectResponse


router = APIRouter()


@router.post(
    "/",
    response_model=CreateProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Any alumni can propose a project. Rows start as pending (approved=None)."""
    if isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot create projects",
        )

    if not body.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title is required",
        )
    if not body.description.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Description is required",
        )

    project = Project(
        id=get_random_token(),
        owner_id=current_user.id,
        contributors_ids=[],
        title=body.title.strip(),
        description=body.description.strip(),
        cover=body.cover,
        approved=None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return CreateProjectResponse(id=project.id)
