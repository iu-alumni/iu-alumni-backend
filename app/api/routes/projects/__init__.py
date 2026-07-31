from fastapi import APIRouter

from app.api.routes.projects import (
    contribute,
    create_project,
    delete_project,
    donate,
    get_cover,
    get_project,
    list_contributed_projects,
    list_owner_projects,
    list_projects,
    update_project,
)


router = APIRouter()

# Order matters — specific paths before dynamic {project_id}.
router.include_router(create_project.router)
router.include_router(list_projects.router)
router.include_router(list_owner_projects.router)
router.include_router(list_contributed_projects.router)
router.include_router(get_cover.router)
router.include_router(get_project.router)
router.include_router(update_project.router)
router.include_router(delete_project.router)
router.include_router(contribute.router)
router.include_router(donate.router)
