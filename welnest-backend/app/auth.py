from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.auth_utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(username: str, password: str):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        db.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        db.close()

    return {"message": "User registered successfully"}


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

    if not row or not verify_password(form_data.password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": form_data.username})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
