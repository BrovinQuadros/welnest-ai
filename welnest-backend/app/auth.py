from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime

from app.database import users_collection
from app.auth_utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------- REGISTER ----------------
@router.post("/register")
async def register(username: str, password: str):

    # Check if user already exists
    existing_user = await users_collection.find_one({"username": username})

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user_data = {
        "username": username,
        "password": hash_password(password),
        "created_at": datetime.utcnow()
    }

    try:
        await users_collection.insert_one(user_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "User registered successfully"}


# ---------------- LOGIN ----------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):

    user = await users_collection.find_one({"username": form_data.username})

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": form_data.username})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }