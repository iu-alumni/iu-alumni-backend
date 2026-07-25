from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.projects import Project
from app.models.users import Admin, Alumni
from app.schemas.project import Project as ProjectResponse, UpdateProjectRequest


router = APIRouter()


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    db: Session = Depends(get_db),
    current_user: Admin | Alumni = Depends(get_current_user),
):
    """Owner-only edit. Editing an approved project drops it back to pending."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this project",
        )

    changed_content = False
    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title cannot be blank",
            )
        if title != project.title:
            project.title = title
            changed_content = True
    if body.description is not None:
        description = body.description.strip()
        if not description:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Description cannot be blank",
            )
        if description != project.description:
            project.description = description
            changed_content = True
    if body.cover is not None:
        # Empty string clears the cover; any other change counts too.
        new_cover = body.cover or None
        if new_cover != project.cover:
            project.cover = new_cover
            changed_content = True
    if body.donation_link is not None:
        # Empty string clears the link; anything else that differs from
        # the stored value counts as an edit for the re-review gate.
        new_link = body.donation_link.strip() or None
        if new_link != project.donation_link:
            project.donation_link = new_link
            changed_content = True
    if body.goal_amount is not None:
        if body.goal_amount < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Goal amount must be zero or positive",
            )
        # 0 clears the goal (owner deciding to drop the target); anything
        # else that differs counts as an edit for the re-review gate.
        new_goal = body.goal_amount if body.goal_amount > 0 else None
        if new_goal != project.goal_amount:
            project.goal_amount = new_goal
            changed_content = True

    # Both fields are mandatory in v1 — every project is a fundraiser,
    # so the row can never end up without a target or without a link.
    if not project.donation_link:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Donation link is required",
        )
    if project.goal_amount is None or project.goal_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fundraising goal is required and must be positive",
        )

    # If the owner touched any content, an approved project goes back to
    # pending so the change goes through admin review again.
    if changed_content and project.approved is True:
        project.approved = None

    db.commit()
    db.refresh(project)
    return project
