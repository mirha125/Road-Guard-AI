#!/usr/bin/env python3
"""
Test script to verify app startup works correctly
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

async def test_startup():
    print("=" * 60)
    print("Testing App Startup...")
    print("=" * 60)

    try:
        # Import the database module
        print("\n1. Importing database module...")
        from backend.database import db
        print("   ✅ Database module imported")

        # Import the auth module
        print("\n2. Importing auth module...")
        from backend.routes import auth
        print("   ✅ Auth module imported")

        # Test database connection
        print("\n3. Testing database connection...")
        await db.connect_to_database()
        print("   ✅ Database connected")

        # Test admin creation
        print("\n4. Testing admin creation...")
        await auth.create_initial_admin()
        print("   ✅ Admin creation completed")

        # Check if admin exists now
        print("\n5. Verifying admin in database...")
        from backend.config import settings
        database = await db.db["users"].find_one({"email": settings.ADMIN_EMAIL})

        if database:
            print("   ✅ Admin found in database!")
            print(f"      Name: {database.get('name')}")
            print(f"      Email: {database.get('email')}")
            print(f"      Role: {database.get('role')}")
        else:
            print("   ❌ Admin still not in database")

        # Close connection
        await db.close_database_connection()

        print("\n" + "=" * 60)
        print("✅ All startup tests passed!")
        print("=" * 60)

    except Exception as e:
        import traceback
        print(f"\n❌ Error during startup test: {e}")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_startup())
