from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.auth_routes import router as auth_router
from app.mood import router as mood_router
from app.journal import router as journal_router
from app.analytics import router as analytics_router
from app.reports import router as reports_router

app = FastAPI(title="WellNest AI")

# ---------- Startup ----------
@app.on_event("startup")
def startup_event():
    init_db()   # creates tables if not exist


# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Routers ----------
app.include_router(auth_router)
app.include_router(mood_router)
app.include_router(journal_router)
app.include_router(analytics_router)
app.include_router(reports_router)
