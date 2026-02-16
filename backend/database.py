from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import certifi
class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_to_database(self):
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI, tlsCAFile=certifi.where())
            self.db = self.client[settings.DB_NAME]

            # Test the connection
            await self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB - Database: {settings.DB_NAME}")

            # Initialize collections and indexes
            await self.initialize_collections()

        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise

    async def initialize_collections(self):
        """Initialize collections and create indexes"""
        try:
            print("🔧 Initializing database collections...")

            # Get list of existing collections
            existing_collections = await self.db.list_collection_names()
            print(f"   Existing collections: {existing_collections if existing_collections else 'None'}")

            # Users collection with email index
            if "users" not in existing_collections:
                await self.db.create_collection("users")
                print("   ✅ Created 'users' collection")

            await self.db.users.create_index("email", unique=True)
            print("   ✅ Created unique index on users.email")

            # Cameras collection
            if "cameras" not in existing_collections:
                await self.db.create_collection("cameras")
                print("   ✅ Created 'cameras' collection")

            # Streams collection
            if "streams" not in existing_collections:
                await self.db.create_collection("streams")
                print("   ✅ Created 'streams' collection")

            # Alerts collection with time index
            if "alerts" not in existing_collections:
                await self.db.create_collection("alerts")
                print("   ✅ Created 'alerts' collection")

            await self.db.alerts.create_index("time")
            print("   ✅ Created index on alerts.time")

            # Show final collection list
            final_collections = await self.db.list_collection_names()
            print(f"   📚 Available collections: {final_collections}")

        except Exception as e:
            print(f"   ⚠️  Warning during collection initialization: {e}")
            # Don't raise - this is not critical

    async def close_database_connection(self):
        if self.client:
            self.client.close()
            print("Closed MongoDB connection")

db = Database()

async def get_database():
    return db.db