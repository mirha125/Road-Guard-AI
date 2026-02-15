from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import certifi
class Database:
    client: AsyncIOMotorClient = None
    db = None
    async def connect_to_database(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI, tlsCAFile=certifi.where())
        self.db = self.client[settings.DB_NAME]
        print("Connected to MongoDB")
    async def close_database_connection(self):
        if self.client:
            self.client.close()
            print("Closed MongoDB connection")
db = Database()
async def get_database():
    return db.db