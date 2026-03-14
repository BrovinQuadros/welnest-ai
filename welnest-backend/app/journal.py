from fastapi import APIRouter, Depends
from app.models import JournalCreate, JournalOut
from app.auth_dependencies import get_current_user
from app.ai_service import summarize_text
from app.database import journals_collection
from datetime import datetime

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post("", response_model=JournalOut)
async def create_journal(
    journal: JournalCreate,
    user: str = Depends(get_current_user)
):

    # Generate AI summary
    ai_summary = summarize_text(journal.content)

    journal_data = {
        "username": user,
        "content": journal.content,
        "ai_summary": ai_summary,
        "created_at": datetime.utcnow()
    }

    # Insert into MongoDB
    await journals_collection.insert_one(journal_data)

    return JournalOut(
        content=journal.content,
        ai_summary=ai_summary,
        created_at=journal_data["created_at"]
    )