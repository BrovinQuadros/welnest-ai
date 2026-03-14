from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# =========================
# AUTH MODELS
# =========================

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# =========================
# MOOD MODELS
# =========================

class MoodCreate(BaseModel):
    mood_score: int
    notes: Optional[str] = None


class MoodOut(BaseModel):
    mood_score: int
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# JOURNAL MODELS
# =========================

class JournalCreate(BaseModel):
    content: str


class JournalOut(BaseModel):
    content: str
    ai_summary: str
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# ANALYTICS MODELS
# =========================

class AnalyticsResponse(BaseModel):
    average: float
    min: int
    max: int


class MoodTrendsResponse(BaseModel):
    labels: List[str]
    values: List[float]


# =========================
# PRIVACY / REPORT SHARING MODELS
# =========================

class ShareReportRequest(BaseModel):
    provider_email: str