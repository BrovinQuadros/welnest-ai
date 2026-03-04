from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.auth_utils import hash_password, verify_password, create_access_token
from app.models import RegisterRequest
import sqlite3

router = APIRouter(prefix="/auth", tags=["Auth"])

# ---------------- REGISTER ----------------
@router.post("/register")
def register(data: RegisterRequest):
    db = get_db()
    cursor = db.cursor()

    # 1️⃣ Explicitly check if user exists
    cursor.execute(
        "SELECT 1 FROM users WHERE username = ?",
        (data.username,)
    )
    if cursor.fetchone():
        db.close()
        raise HTTPException(status_code=400, detail="User already exists")

    # 2️⃣ Insert user
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (data.username, hash_password(data.password))
        )
        db.commit()
    except sqlite3.Error as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

    db.close()
    return {"message": "User registered successfully"}

# ---------------- LOGIN ----------------
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE username = ?",
        (form_data.username,)
    )
    row = cursor.fetchone()
    db.close()

    # 3️⃣ Correct password verification
    if not row or not verify_password(form_data.password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": form_data.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }
