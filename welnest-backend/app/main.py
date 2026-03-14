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


# -----------------------------
# CORS CONFIGURATION
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Primary deployed frontend
        "https://welnest-ai-five.vercel.app",
    ],
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
    await init_db()


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