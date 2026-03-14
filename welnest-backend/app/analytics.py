from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from app.database import moods_collection
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
async def mood_trends(current_user: str = Depends(get_current_user)):

    try:
        moods = await moods_collection.find({"username": current_user}).to_list(1000)

        if not moods:
            return {"labels": [], "values": []}

        daily = {}

        for m in moods:
            date = m["created_at"].strftime("%Y-%m-%d")

            if date not in daily:
                daily[date] = []

            daily[date].append(m["mood_score"])

        labels = sorted(daily.keys())
        values = [
            round(sum(daily[d]) / len(daily[d]), 2)
            for d in labels
        ]

        return {
            "labels": labels,
            "values": values
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch mood trends")


# =====================================================
# MOOD SUMMARY
# =====================================================

@router.get("/summary", response_model=MoodSummaryResponse)
async def mood_summary(current_user: str = Depends(get_current_user)):

    try:
        moods = await moods_collection.find({"username": current_user}).to_list(1000)

        if not moods:
            return {
                "average": 0,
                "minimum": 0,
                "maximum": 0,
                "total_entries": 0
            }

        scores = [m["mood_score"] for m in moods]

        return {
            "average": round(sum(scores) / len(scores), 2),
            "minimum": min(scores),
            "maximum": max(scores),
            "total_entries": len(scores)
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch mood summary")


# =====================================================
# MOOD STREAK
# =====================================================

@router.get("/streak", response_model=MoodStreakResponse)
async def mood_streak(current_user: str = Depends(get_current_user)):

    try:
        moods = await moods_collection.find({"username": current_user}).to_list(1000)

        if not moods:
            return {"streak": 0}

        dates = sorted(
            {m["created_at"].date() for m in moods},
            reverse=True
        )

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


# =====================================================
# WEEKLY AI INSIGHT
# =====================================================

@router.get("/weekly-ai-insight", response_model=WeeklyInsightResponse)
async def weekly_ai_insight(current_user: str = Depends(get_current_user)):

    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        moods = await moods_collection.find({
            "username": current_user,
            "created_at": {"$gte": seven_days_ago}
        }).to_list(1000)

        if not moods:
            return {
                "weekly_average": 0,
                "insight": "Not enough data for weekly insight."
            }

        scores = [m["mood_score"] for m in moods]
        weekly_avg = round(sum(scores) / len(scores), 2)

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