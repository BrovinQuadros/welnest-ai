from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import users_collection
from app.auth_utils import (
    hash_password,
    is_password_hash,
    verify_and_update_password,
    create_access_token,
)
from app.models import RegisterRequest, RegisterResponse, TokenResponse
from datetime import datetime
import logging
import os
from pymongo.errors import (
    DuplicateKeyError,
    PyMongoError,
    ServerSelectionTimeoutError,
    ConfigurationError,
)

router = APIRouter(tags=["Auth"])
logger = logging.getLogger(__name__)
AUTH_DEBUG_ERRORS = os.getenv("AUTH_DEBUG_ERRORS", "false").lower() == "true"


def _error_detail(default_message: str, exc: Exception) -> str:
    """Return safe production error details, with optional debug expansion."""
    if AUTH_DEBUG_ERRORS:
        return f"{default_message} ({type(exc).__name__}: {exc})"
    return default_message


# ---------------- REGISTER ----------------
@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(data: RegisterRequest):

    username = data.username.strip().lower()

    if not username or not data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    # 1️⃣ Check if user exists
    try:
        existing_user = await users_collection.find_one({"username": username})
        if existing_user:
            raise HTTPException(status_code=409, detail="Username is already taken")
    except HTTPException:
        raise
    except (ServerSelectionTimeoutError, ConfigurationError) as e:
        logger.exception("Database connectivity/config error during registration lookup for '%s'", username)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_error_detail("Database connection error", e)
        )
    except PyMongoError as e:
        logger.exception("Mongo error during registration lookup for '%s'", username)
        raise HTTPException(status_code=500, detail=_error_detail("Database operation error", e))
    except Exception as e:
        logger.exception("Unexpected error while checking existing user '%s'", username)
        raise HTTPException(status_code=500, detail=_error_detail("Registration pre-check failed", e))

    try:
        # 2️⃣ Hash password + Insert user
        hashed_password = hash_password(data.password)
        user_data = {
            "username": username,
            "password": hashed_password,
            "created_at": datetime.utcnow()
        }

        if not is_password_hash(user_data["password"]):
            logger.error("Refusing to store non-hash password for user '%s'", username)
            raise HTTPException(status_code=500, detail="Registration service error. Please try again later.")

        await users_collection.insert_one(user_data)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Username is already taken")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ServerSelectionTimeoutError, ConfigurationError) as e:
        logger.exception("Database connectivity/config error during registration insert for '%s'", username)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_error_detail("Database connection error", e)
        )
    except PyMongoError as e:
        logger.exception("Mongo insert error during registration for '%s'", username)
        raise HTTPException(status_code=500, detail=_error_detail("Database insert error", e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected registration failure for user '%s'", username)
        raise HTTPException(
            status_code=500,
            detail=_error_detail("Registration service error", e)
        )

    return {"message": "User registered successfully", "username": username}


# ---------------- LOGIN ----------------
@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):

    username = form_data.username.strip().lower()

    if not username or not form_data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    if len(username) < 3 or len(username) > 32:
        raise HTTPException(status_code=400, detail="Username must be 3-32 characters long")

    if len(form_data.password) < 8 or len(form_data.password) > 128:
        raise HTTPException(status_code=400, detail="Password must be 8-128 characters long")

    # 1️⃣ Find user
    try:
        user = await users_collection.find_one({"username": username})
    except Exception:
        logger.exception("Login lookup failed for user '%s'", username)
        raise HTTPException(status_code=500, detail="Login service error. Please try again later.")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    stored_password = user.get("password", "")

    # 2️⃣ Verify password and auto-upgrade deprecated hashes if needed.
    is_valid_password, upgraded_hash = verify_and_update_password(form_data.password, stored_password)

    # Legacy plain-text records fallback (one-time migration path)
    legacy_match = (not is_password_hash(stored_password)) and stored_password == form_data.password

    if not (is_valid_password or legacy_match):
        logger.info("Invalid login attempt for user '%s'", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # If hash needs upgrade (e.g., bcrypt -> bcrypt_sha256), persist new hash.
    if upgraded_hash:
        try:
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"password": upgraded_hash}}
            )
            logger.info("Password hash upgraded for user '%s'", username)
        except Exception:
            logger.warning("Could not upgrade password hash for user '%s'", username)

    # If an old plain-text password matched, upgrade it to a secure hash.
    if legacy_match:
        try:
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"password": hash_password(form_data.password)}}
            )
            logger.info("Legacy plain-text password migrated for user '%s'", username)
        except Exception:
            logger.warning("Could not migrate legacy password hash for user '%s'", username)

    # 3️⃣ Create JWT token
    token = create_access_token({"sub": username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }