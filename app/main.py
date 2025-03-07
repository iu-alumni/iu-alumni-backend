from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.authentication import router as auth_router
from app.api.routes.profile import router as profile_router
from app.api.routes.events import router as events_router
from app.models.users import Admin
from app.core.security import get_password_hash, get_random_token
from app.core.database import SessionLocal
import os
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create admin user if it doesn't exist
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.email == "admin@admin.com").first()
        if not admin:
            admin = Admin(
                id=get_random_token(),
                email=os.getenv("ADMIN_EMAIL"),
                hashed_password=get_password_hash(os.getenv("ADMIN_PASSWORD"))
            )
            db.add(admin)
            db.commit()
            print("Initial admin user created with email: admin and password: admin")
    finally:
        db.close()
    
    yield  # Server is running and handling requests here
    
    # Shutdown: Any cleanup code would go here

app = FastAPI(
    title="Alumni API",
    description="API for the IU Alumni platform",
    version="1.0.0",
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
                    "description": "Enter JWT token"
                }
            }
        }
    },
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])
app.include_router(events_router, prefix="/events", tags=["Events"])