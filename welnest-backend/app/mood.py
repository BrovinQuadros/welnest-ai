from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.database import moods_collection
from app.auth_dependencies import get_current_user

router = APIRouter(
    prefix="/mood",
    tags=["Mood"]
)

# =========================================================
# REQUEST MODEL
# =========================================================

class MoodCreate(BaseModel):
    mood_score: int = Field(..., ge=1, le=10)
    notes: Optional[str] = None


# =========================================================
# RESPONSE MODEL
# =========================================================

class MoodOut(BaseModel):
    mood_score: int
    notes: Optional[str]
    created_at: str


class MoodResponse(BaseModel):
    message: str


# =========================================================
# ADD MOOD
# =========================================================

@router.post(
    "",
    response_model=MoodResponse,
    status_code=status.HTTP_201_CREATED
)
async def log_mood(
    mood: MoodCreate,
    current_user: str = Depends(get_current_user)
):

    try:
        mood_data = {
            "username": current_user,
            "mood_score": mood.mood_score,
            "notes": mood.notes,
            "created_at": datetime.utcnow()
        }

        await moods_collection.insert_one(mood_data)

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to log mood"
        )

    return {"message": "Mood logged successfully"}


# =========================================================
# GET MOODS
# =========================================================

@router.get(
    "",
    response_model=List[MoodOut]
)
async def get_moods(
    current_user: str = Depends(get_current_user)
):

    try:
        moods = await moods_collection.find(
            {"username": current_user}
        ).sort("created_at", -1).to_list(1000)

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch moods"
        )

    return [
        MoodOut(
            mood_score=m["mood_score"],
            notes=m.get("notes"),
            created_at=m["created_at"].isoformat()
        )
        for m in moods
    ]