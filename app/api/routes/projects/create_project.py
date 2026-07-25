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

    donation_link = body.donation_link.strip() if body.donation_link else None
    goal_amount = body.goal_amount
    # Both fields are mandatory: every project is a fundraiser in v1,
    # so we need somewhere for the money to go and a target to fill.
    if not donation_link:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Donation link is required",
        )
    if goal_amount is None or goal_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fundraising goal is required and must be positive",
        )
    project = Project(
        id=get_random_token(),
        owner_id=current_user.id,
        contributors_ids=[],
        title=body.title.strip(),
        description=body.description.strip(),
        cover=body.cover,
        donation_link=donation_link,
        goal_amount=goal_amount,
        raised_amount=0,
        approved=None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return CreateProjectResponse(id=project.id)
