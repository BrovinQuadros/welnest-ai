from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.auth_dependencies import get_current_user
from app.ai_service import summarize_text

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

# =====================================================
# RESPONSE MODELS
# =====================================================

class MoodTrendsResponse(BaseModel):
    labels: List[str]
    values: List[float]


class MoodSummaryResponse(BaseModel):
    average: float
    minimum: int
    maximum: int
    total_entries: int


class MoodStreakResponse(BaseModel):
    streak: int


class WeeklyInsightResponse(BaseModel):
    weekly_average: float
    insight: str


# =====================================================
# MOOD TRENDS (Daily Average)
# =====================================================

@router.get("/mood-trends", response_model=MoodTrendsResponse)
def mood_trends(current_user: str = Depends(get_current_user)):

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT DATE(created_at), AVG(mood_score)
            FROM moods
            WHERE username = ?
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
            """,
            (current_user,)
        )

        rows = cursor.fetchall()

        if not rows:
            return {"labels": [], "values": []}

        return {
            "labels": [row[0] for row in rows],
            "values": [round(row[1], 2) for row in rows]
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch mood trends")

    finally:
        db.close()


# =====================================================
# MOOD SUMMARY
# =====================================================

@router.get("/summary", response_model=MoodSummaryResponse)
def mood_summary(current_user: str = Depends(get_current_user)):

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT AVG(mood_score),
                   MIN(mood_score),
                   MAX(mood_score),
                   COUNT(*)
            FROM moods
            WHERE username = ?
            """,
            (current_user,)
        )

        result = cursor.fetchone()

        if not result or result[3] == 0:
            return {
                "average": 0,
                "minimum": 0,
                "maximum": 0,
                "total_entries": 0
            }

        return {
            "average": round(result[0], 2),
            "minimum": result[1],
            "maximum": result[2],
            "total_entries": result[3]
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch mood summary")

    finally:
        db.close()


# =====================================================
# MOOD STREAK
# =====================================================

@router.get("/streak", response_model=MoodStreakResponse)
def mood_streak(current_user: str = Depends(get_current_user)):

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT DISTINCT DATE(created_at)
            FROM moods
            WHERE username = ?
            ORDER BY DATE(created_at) DESC
            """,
            (current_user,)
        )

        rows = cursor.fetchall()

        if not rows:
            return {"streak": 0}

        dates = [
            datetime.strptime(row[0], "%Y-%m-%d").date()
            for row in rows
        ]

        streak = 0
        today = datetime.today().date()

        for i, date in enumerate(dates):

            if i == 0:
                if date == today or date == today - timedelta(days=1):
                    streak = 1
                else:
                    break
            else:
                if date == dates[i - 1] - timedelta(days=1):
                    streak += 1
                else:
                    break

        return {"streak": streak}

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to calculate streak")

    finally:
        db.close()


# =====================================================
# WEEKLY AI INSIGHT
# =====================================================

@router.get("/weekly-ai-insight", response_model=WeeklyInsightResponse)
def weekly_ai_insight(current_user: str = Depends(get_current_user)):

    db = get_db()
    cursor = db.cursor()

    try:
        seven_days_ago = datetime.now() - timedelta(days=7)

        cursor.execute(
            """
            SELECT AVG(mood_score)
            FROM moods
            WHERE username = ?
            AND created_at >= ?
            """,
            (current_user, seven_days_ago)
        )

        result = cursor.fetchone()

        if not result or result[0] is None:
            return {
                "weekly_average": 0,
                "insight": "Not enough data for weekly insight."
            }

        weekly_avg = round(result[0], 2)

        prompt = (
            f"The user's average mood this week is {weekly_avg} out of 10. "
            "Provide a short emotional insight in 2–3 supportive sentences."
        )

        ai_response = summarize_text(prompt)

        return {
            "weekly_average": weekly_avg,
            "insight": ai_response
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate weekly AI insight")

    finally:
        db.close()
