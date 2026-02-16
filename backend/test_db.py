#!/usr/bin/env python3
"""
Test script to verify MongoDB connection and admin user creation
Run this with: python -m backend.test_db
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import certifi


async def test_connection():
    print("=" * 60)
    print("🧪 Testing MongoDB Connection")
    print("=" * 60)

    try:
        # Test 1: Basic connection
        print("\n1️⃣  Testing basic connection...")
        print(f"   MongoDB URI: {settings.MONGO_URI[:50]}...")
        print(f"   Database Name: {settings.DB_NAME}")

        client = AsyncIOMotorClient(settings.MONGO_URI, tlsCAFile=certifi.where())
        db = client[settings.DB_NAME]

        # Ping the database
        await client.admin.command('ping')
        print("   ✅ Successfully connected to MongoDB!")

        # Test 2: List collections
        print("\n2️⃣  Listing existing collections...")
        collections = await db.list_collection_names()
        if collections:
            print(f"   📚 Found {len(collections)} collection(s):")
            for col in collections:
                count = await db[col].count_documents({})
                print(f"      - {col}: {count} document(s)")
        else:
            print("   📭 No collections found (this is normal for a new database)")

        # Test 3: Check for admin user
        print("\n3️⃣  Checking for admin user...")
        print(f"   Looking for: {settings.ADMIN_EMAIL}")

        if "users" in collections:
            admin = await db["users"].find_one({"email": settings.ADMIN_EMAIL})
            if admin:
                print("   ✅ Admin user found!")
                print(f"      Name: {admin.get('name')}")
                print(f"      Email: {admin.get('email')}")
                print(f"      Role: {admin.get('role')}")
                print(f"      Status: {admin.get('approval_status')}")
                print(f"      ID: {admin.get('_id')}")
            else:
                print("   ⚠️  Admin user NOT found in database")
                print("   This means the admin was not created during startup")

            # List all users
            users_count = await db["users"].count_documents({})
            print(f"\n   Total users in database: {users_count}")

        else:
            print("   ⚠️  'users' collection does not exist yet")
            print("   The admin user should be created on first startup")

        # Test 4: Test write permission
        print("\n4️⃣  Testing write permissions...")
        try:
            test_collection = db["_test_connection"]
            result = await test_collection.insert_one({"test": "data"})
            print(f"   ✅ Write permission verified (inserted ID: {result.inserted_id})")

            # Clean up test document
            await test_collection.delete_one({"_id": result.inserted_id})
            print("   ✅ Cleanup successful")
        except Exception as write_error:
            print(f"   ❌ Write permission test failed: {write_error}")

        # Test 5: Connection info
        print("\n5️⃣  Connection information...")
        server_info = await client.server_info()
        print(f"   MongoDB Version: {server_info.get('version')}")
        print(f"   Server: Atlas (Cloud)")

        client.close()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("   1. Start your FastAPI server: uvicorn backend.main:app --reload")
        print("   2. Check the startup logs for admin creation")
        print("   3. Try logging in with your admin credentials")
        print("=" * 60)

    except Exception as e:
        import traceback
        print(f"\n❌ Error during testing: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nFull traceback:")
        print(traceback.format_exc())
        print("\n" + "=" * 60)
        print("🔧 Troubleshooting tips:")
        print("   1. Check your .env file has correct MONGO_URI")
        print("   2. Verify your MongoDB Atlas cluster is running")
        print("   3. Check network/firewall settings")
        print("   4. Verify database user has read/write permissions")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_connection())
