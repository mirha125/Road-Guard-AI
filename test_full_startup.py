#!/usr/bin/env python3
"""
Test full server startup with lifespan
"""

import asyncio
from contextlib import asynccontextmanager

async def test_lifespan():
    print("\nTesting lifespan startup...")

    # Import after path setup
    from backend.main import app
    from backend.database import db
    from backend.routes import auth
    from backend.config import settings

    # Manually run the lifespan startup
    print("\n" + "=" * 50)
    print("🚀 Starting Road Safety Monitoring System")
    print("=" * 50)
    try:
        print("📡 Connecting to database...")
        await db.connect_to_database()
        print("✅ Database connected successfully")

        print("👤 Creating initial admin user...")
        await auth.create_initial_admin()
        print("✅ Admin setup completed")
        print("=" * 50)

        # Verify
        print("\n✅ Startup completed successfully!")
        print(f"   Admin email: {settings.ADMIN_EMAIL}")
        print(f"   Server ready to start")

        await db.close_database_connection()

    except Exception as e:
        import traceback
        print(f"❌ Startup error: {e}")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    asyncio.run(test_lifespan())
