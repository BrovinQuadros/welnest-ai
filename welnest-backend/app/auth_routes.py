from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.database import users_collection
from app.auth_utils import hash_password, verify_password, create_access_token
from app.models import RegisterRequest
from datetime import datetime
import logging

router = APIRouter(tags=["Auth"])
logger = logging.getLogger(__name__)


# ---------------- REGISTER ----------------
@router.post("/register")
async def register(data: RegisterRequest):

    username = data.username.strip()

    if not username or not data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    # 1️⃣ Check if user exists
    existing_user = await users_collection.find_one({"username": username})

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    try:
        # 2️⃣ Hash password + Insert user
        user_data = {
            "username": username,
            "password": hash_password(data.password),
            "created_at": datetime.utcnow()
        }

        await users_collection.insert_one(user_data)
    except Exception as e:
        logger.exception("Registration failed for user '%s'", username)
        # Keep response generic for security; details will be in server logs.
        raise HTTPException(
            status_code=500,
            detail="Registration service error. Please try again later."
        )

    return {"message": "User registered successfully"}


# ---------------- LOGIN ----------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):

    username = form_data.username.strip()

    if not username or not form_data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    # 1️⃣ Find user
    user = await users_collection.find_one({"username": username})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_password = user.get("password", "")

    # 2️⃣ Verify password (supports legacy plain-text records and auto-migrates to hash)
    is_valid_password = False
    try:
        is_valid_password = verify_password(form_data.password, stored_password)
    except Exception:
        is_valid_password = form_data.password == stored_password

    if not is_valid_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # If an old plain-text password matched, upgrade it to bcrypt hash.
    if stored_password == form_data.password:
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"password": hash_password(form_data.password)}}
        )

    # 3️⃣ Create JWT token
    token = create_access_token({"sub": username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }