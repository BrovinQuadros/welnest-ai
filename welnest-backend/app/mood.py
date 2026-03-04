from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from app.database import get_db
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
    "/",
    response_model=MoodResponse,
    status_code=status.HTTP_201_CREATED
)
def log_mood(
    mood: MoodCreate,
    current_user: str = Depends(get_current_user)
):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO moods (username, mood_score, notes)
            VALUES (?, ?, ?)
            """,
            (current_user, mood.mood_score, mood.notes)
        )

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to log mood"
        )

    finally:
        db.close()

    return {"message": "Mood logged successfully"}


# =========================================================
# GET MOODS
# =========================================================

@router.get(
    "/",
    response_model=List[MoodOut]
)
def get_moods(
    current_user: str = Depends(get_current_user)
):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT mood_score, notes, created_at
            FROM moods
            WHERE username = ?
            ORDER BY created_at DESC
            """,
            (current_user,)
        )

        rows = cursor.fetchall()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch moods"
        )

    finally:
        db.close()

    return [
        MoodOut(
            mood_score=row[0],
            notes=row[1],
            created_at=row[2]
        )
        for row in rows
    ]
