from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.authentication import router as auth_router
   
app = FastAPI(title="My API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])