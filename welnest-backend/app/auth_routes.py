from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.database import users_collection
from app.auth_utils import hash_password, verify_password, create_access_token
from app.models import RegisterRequest
from datetime import datetime

router = APIRouter(tags=["Auth"])


# ---------------- REGISTER ----------------
@router.post("/register")
async def register(data: RegisterRequest):

    # 1️⃣ Check if user exists
    existing_user = await users_collection.find_one({"username": data.username})

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # 2️⃣ Insert user
    user_data = {
        "username": data.username,
        "password": hash_password(data.password),
        "created_at": datetime.utcnow()
    }

    try:
        await users_collection.insert_one(user_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

    return {"message": "User registered successfully"}


# ---------------- LOGIN ----------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):

    # 1️⃣ Find user
    user = await users_collection.find_one({"username": form_data.username})

    # 2️⃣ Verify password
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3️⃣ Create JWT token
    token = create_access_token({"sub": form_data.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }