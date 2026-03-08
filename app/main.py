import asyncio
import contextlib
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes.admin import router as admin_router
from app.api.routes.authentication import router as auth_router
from app.api.routes.cities import router as cities_router
from app.api.routes.events import router as events_router
from app.api.routes.profile import router as profile_router
from app.api.routes.telegram import router as telegram_router
from app.core.database import SessionLocal
from app.core.logging import app_logger, setup_logging
from app.core.security import get_password_hash, get_random_token
from app.models.users import Admin
from app.services.telegram_polling import start_polling


# Initialize logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create admin user if it doesn't exist
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.email == os.getenv("ADMIN_EMAIL")).first()
        if not admin:
            admin = Admin(
                id=get_random_token(),
                email=os.getenv("ADMIN_EMAIL"),
                hashed_password=get_password_hash(os.getenv("ADMIN_PASSWORD")),
            )
            db.add(admin)
            db.commit()
            app_logger.info("Initial admin user created")
        else:
            app_logger.debug("Admin user already exists")
    finally:
        db.close()

    # Start Telegram long-polling in the background
    stop_polling = asyncio.Event()
    polling_task = asyncio.create_task(start_polling(stop_polling))

    yield  # Server is running and handling requests here

    # Shutdown: stop the polling loop gracefully
    stop_polling.set()
    polling_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await polling_task


# Environment-based documentation control
ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV").upper()
IS_DEVELOPMENT = ENVIRONMENT in ("DEV", "TEST")

app = FastAPI(
    title="Alumni API",
    description="API for the IU Alumni platform",
    version="1.0.0",
    # Enable docs only in development
    docs_url="/docs" if IS_DEVELOPMENT else None,
    redoc_url="/redoc" if IS_DEVELOPMENT else None,
    openapi_url="/openapi.json" if IS_DEVELOPMENT else None,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Operations related to user authentication",
        },
        {
            "name": "Profile",
            "description": "Operations related to user profiles",
        },
    ],
    openapi_extra={
        "components": {
            "securitySchemes": {
                "Bearer": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter JWT token",
                }
            }
        }
    },
    lifespan=lifespan,
)

# CORS configuration
# CORS_ORIGINS is a comma-separated list of allowed origins, e.g.:
#   CORS_ORIGINS=https://alumap.example.com,https://admin.example.com
# Wildcards ("*") cannot be used together with allow_credentials=True per
# the CORS spec, so an explicit origin list is always required in production.
_raw_origins = os.getenv("CORS_ORIGINS", "")
_allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])
app.include_router(events_router, prefix="/events", tags=["Events"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(cities_router, prefix="/cities", tags=["Cities"])
app.include_router(telegram_router, tags=["Telegram"])

Instrumentator().instrument(app).expose(app)
