from fastapi import FastAPI
from app.database.database import engine, Base
from app.models.user import User
from app.models.profile import Profile
from app.api.profiles import router as profile_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.matches import router as matches_router

import app.models.profile

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AlumniConnect API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "AlumniConnect API is running",
        "database_configured": True
    }


app.include_router(profile_router)
app.include_router(matches_router)
