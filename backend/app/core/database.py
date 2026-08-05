from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

def connect_db():
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    # the database name is typically extracted from URI or hardcoded. We'll use the default db from URI
    db.db = db.client.get_database()

def close_db():
    if db.client:
        db.client.close()

def get_db():
    return db.db
