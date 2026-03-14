from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =====================================================
# MONGODB CONNECTION
# =====================================================
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

# Create MongoDB async client
client = AsyncIOMotorClient(MONGO_URL)


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

    print("✅ MongoDB connected successfully")