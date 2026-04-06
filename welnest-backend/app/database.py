import os
from pathlib import Path
from dotenv import load_dotenv
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Force PyMongo to use Python's built-in SSL instead of pyOpenSSL
# (avoids compatibility issues with some OpenSSL/pyOpenSSL builds on Windows)
os.environ.setdefault("PYMONGO_DISABLE_PYOPENSSL", "1")

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
logger = logging.getLogger(__name__)


# =====================================================
# MONGODB CONNECTION
# =====================================================
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

if not MONGO_URL:
    logger.warning("MONGO_URL is empty. Falling back to mongodb://localhost:27017")
    MONGO_URL = "mongodb://localhost:27017"


def _build_mongo_client() -> AsyncIOMotorClient:
    """
    Build MongoDB client with safe defaults for both local and cloud setups.

    - Local mongodb://localhost typically does NOT use TLS.
    - Atlas / mongodb+srv usually requires TLS and CA certs.
    """
    url = (MONGO_URL or "").strip()
    lowered = url.lower()

    use_tls_ca = (
        lowered.startswith("mongodb+srv://")
        or "tls=true" in lowered
        or "ssl=true" in lowered
    )

    client_kwargs = {
        "serverSelectionTimeoutMS": int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "10000"))
    }
    if use_tls_ca:
        client_kwargs["tlsCAFile"] = certifi.where()

    return AsyncIOMotorClient(url, **client_kwargs)

# Create MongoDB async client
client = _build_mongo_client()


# =====================================================
# DATABASE
# =====================================================
database = client["welnest_db"]


# =====================================================
# COLLECTIONS
# =====================================================
users_collection = database["users"]
moods_collection = database["moods"]
journals_collection = database["journals"]
analytics_collection = database["analytics"]
reports_collection = database["reports"]
report_shares_collection = database["report_shares"]


# =====================================================
# INITIALIZE DATABASE INDEXES
# =====================================================
async def init_db():
    """
    Initialize MongoDB indexes.
    Collections are created automatically when data is inserted.
    """

    # Verify connectivity early (helps fail-fast on bad Render env configuration).
    await client.admin.command("ping")

    # Unique username
    await users_collection.create_index("username", unique=True)

    # Index for faster queries
    await moods_collection.create_index([("username", 1)])
    await journals_collection.create_index([("username", 1)])
    await analytics_collection.create_index([("username", 1)])
    await reports_collection.create_index([("username", 1)])
    await report_shares_collection.create_index([("username", 1)])

    # Index for analytics sorting
    await moods_collection.create_index([("created_at", 1)])
    await journals_collection.create_index([("created_at", 1)])
    await analytics_collection.create_index([("created_at", 1)])
    await reports_collection.create_index([("created_at", 1)])
    await report_shares_collection.create_index([("shared_at", 1)])

    logger.info("✅ MongoDB connected and indexes initialized successfully")