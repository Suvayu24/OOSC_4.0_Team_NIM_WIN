from motor.motor_asyncio import AsyncIOMotorClient

from config import settings

client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
db = client[settings.mongo_db_name]
