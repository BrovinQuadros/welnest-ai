import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -----------------------------
# IMPORT ROUTERS
# -----------------------------
from app.database import init_db
from app.auth_routes import router as auth_router
from app.mood import router as mood_router
from app.journal import router as journal_router
from app.analytics import router as analytics_router
from app.reports import router as reports_router
from app.privacy import router as privacy_router


# -----------------------------
# CREATE FASTAPI APP
# -----------------------------
app = FastAPI(
    title="WellNest AI",
    description="AI powered mental wellness assistant",
    version="1.0.0"
)

logger = logging.getLogger(__name__)


# -----------------------------
# CORS CONFIGURATION
# -----------------------------
configured_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]

default_origins = [
    # Primary deployed frontend
    "https://wellnest-ba120me9u-brovinquadros-projects.vercel.app",
    "https://welnest-ai-five.vercel.app",
]

allow_origins = list(dict.fromkeys(default_origins + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    # Allow local Vite dev servers on any port and Vercel preview deployments.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$|https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
    except Exception:
        logger.exception("Database initialization failed during startup")
        raise


# -----------------------------
# INCLUDE ROUTES
# -----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(mood_router, tags=["Mood Tracking"])
app.include_router(journal_router, tags=["Journal"])
app.include_router(analytics_router, tags=["Analytics"])
app.include_router(reports_router, tags=["Reports"])
app.include_router(privacy_router, tags=["Privacy"])


# -----------------------------
# ROOT ENDPOINT
# -----------------------------
@app.get("/")
async def root():
    return {
        "message": "WellNest AI Backend Running",
        "status": "ok"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}