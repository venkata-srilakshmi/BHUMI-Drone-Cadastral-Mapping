import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database.session import engine, Base, SessionLocal
from app.auth.security import init_demo_users
from app.services.demo_data import seed_demo_dataset

# Import API routers
from app.api.auth import router as auth_router
from app.api.surveys import router as surveys_router
from app.api.parcels import router as parcels_router
from app.api.features import router as features_router
from app.api.change_detection import router as change_detection_router
from app.api.ai_assistant import router as ai_assistant_router
from app.api.analytics import router as analytics_router
from app.api.reports import router as reports_router

app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    description="Drone-Based AI Parcel Mapping & Automated Cadastral Feature Extraction • SIH26012",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local storage directory for static imagery access
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
app.mount("/static/storage", StaticFiles(directory=str(settings.STORAGE_PATH)), name="storage")

# Include Routers under API v1 prefix
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(surveys_router, prefix=settings.API_V1_STR)
app.include_router(parcels_router, prefix=settings.API_V1_STR)
app.include_router(features_router, prefix=settings.API_V1_STR)
app.include_router(change_detection_router, prefix=settings.API_V1_STR)
app.include_router(ai_assistant_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed demo users (Officer, Admin, Viewer)
        init_demo_users(db)
        # Seed full prototype demo dataset
        seed_demo_dataset(db)
        print("[BHOOMI-AI] Database tables verified, demo users and survey dataset initialized.")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "status": "Operational",
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_STR,
        "mandate": "Ministry of Rural Development • Smart India Hackathon SIH26012"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
