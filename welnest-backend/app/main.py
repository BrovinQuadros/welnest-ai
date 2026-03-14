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
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",

        # Vercel frontend
        "https://wellnest-ai-five.vercel.app",
    ],
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
app.include_router(mood_router, prefix="/mood", tags=["Mood Tracking"])
app.include_router(journal_router, prefix="/journal", tags=["Journal"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])
app.include_router(privacy_router, prefix="/privacy", tags=["Privacy"])


# -----------------------------
# ROOT ENDPOINT
# -----------------------------
@app.get("/")
async def root():
    return {
        "message": "WellNest AI Backend Running",
        "status": "ok"
    }