from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# =========================
# AUTH MODELS
# =========================

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="3-32 chars, letters/numbers/._- only"
    )
    password: str = Field(..., min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    message: str
    username: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)


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
    provider_email: str = Field(
        ...,
        min_length=5,
        max_length=254,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )