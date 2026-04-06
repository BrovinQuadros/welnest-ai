from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
logger = logging.getLogger(__name__)

# 🔐 Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if SECRET_KEY == "dev_secret_key":
    logger.warning("SECRET_KEY is not set. Using insecure development fallback key.")

# Password hashing configuration
# - bcrypt_sha256 prevents bcrypt's 72-byte password truncation issue.
# - bcrypt is kept for backwards compatibility and auto-migrated on login.
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


# ---------------- PASSWORD UTILS ----------------
def hash_password(password: str) -> str:
    """Hash a plain password."""
    if not password or not isinstance(password, str):
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)


def is_password_hash(value: str | None) -> bool:
    """Return True if a value looks like a passlib-generated hash."""
    return bool(value and isinstance(value, str) and value.startswith("$"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not plain_password or not hashed_password:
        return False

    # Passlib may throw for malformed / non-hash input.
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def verify_and_update_password(plain_password: str, stored_hash: str) -> Tuple[bool, str | None]:
    """
    Verify password and optionally return upgraded hash when legacy hash is used.
    """
    if not plain_password or not stored_hash:
        return False, None

    try:
        verified, new_hash = pwd_context.verify_and_update(plain_password, stored_hash)
        return bool(verified), new_hash
    except Exception:
        return False, None


# ---------------- JWT UTILS ----------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT access token."""

    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt