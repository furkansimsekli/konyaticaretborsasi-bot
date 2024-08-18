import logging

from motor.motor_asyncio import AsyncIOMotorClient

from .config import (
    DB_STRING,
    DB_NAME
)
from .models import User

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger()

# Initialize the MongoDB client and database
client = AsyncIOMotorClient(DB_STRING)
db = client[DB_NAME]
User.initialize_collection(db, "users")
