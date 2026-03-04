from fastapi import APIRouter, Depends
from app.models import JournalCreate, JournalOut
from app.auth_dependencies import get_current_user
from app.ai_service import summarize_text
from datetime import datetime

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post("/", response_model=JournalOut)
def create_journal(
    journal: JournalCreate,
    user=Depends(get_current_user)
):
    ai_summary = summarize_text(journal.content)

    return {
        "content": journal.content,
        "ai_summary": ai_summary,
        "created_at": datetime.now().isoformat()
    }
