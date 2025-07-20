from fastapi import APIRouter

from app.api.routes.cities import search_cities


router = APIRouter()

router.include_router(search_cities.router)
