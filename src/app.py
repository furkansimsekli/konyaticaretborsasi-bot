import logging

from motor.motor_asyncio import AsyncIOMotorClient

from .config import (
    MONGODB_URI,
    DATABASE_NAME
)
from .models import User

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger()

# Initialize the MongoDB client and database
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
User.initialize_collection(db, "users")
