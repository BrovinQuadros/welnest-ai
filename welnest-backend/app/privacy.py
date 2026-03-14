from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.auth_dependencies import get_current_user
from app.database import (
    analytics_collection,
    journals_collection,
    moods_collection,
    report_shares_collection,
    reports_collection,
    users_collection,
)


router = APIRouter(tags=["Privacy"])


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"


async def _delete_user_related_data(username: str):
    await moods_collection.delete_many({"username": username})
    await journals_collection.delete_many({"username": username})
    await analytics_collection.delete_many({"username": username})
    await reports_collection.delete_many({"username": username})
    await report_shares_collection.delete_many({"username": username})

    if REPORTS_DIR.exists():
        for file_path in REPORTS_DIR.glob(f"{username}_*"):
            if file_path.is_file():
                file_path.unlink(missing_ok=True)


@router.delete("/api/user/delete-data")
async def delete_my_data(current_user: str = Depends(get_current_user)):
    try:
        await _delete_user_related_data(current_user)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete user data")

    return {"message": "All personal data deleted successfully"}


@router.delete("/api/user/delete-account")
async def delete_account(current_user: str = Depends(get_current_user)):
    try:
        await _delete_user_related_data(current_user)
        await users_collection.delete_one({"username": current_user})
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete account")

    return {"message": "Account deleted successfully"}