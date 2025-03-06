from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.authentication import router as auth_router
from app.api.routes.profile import router as profile_router
   
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
    }
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