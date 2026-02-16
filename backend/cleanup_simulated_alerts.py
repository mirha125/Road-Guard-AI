#!/usr/bin/env python3
"""
Script to remove simulated alerts from the database
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import db
from backend.config import settings

async def cleanup_simulated_alerts():
    print("🧹 Cleaning up simulated alerts...")

    try:
        await db.connect_to_database()

        # Delete all alerts with "Simulated Stream Location"
        result = await db.db["alerts"].delete_many({
            "location": "Simulated Stream Location"
        })

        print(f"✅ Deleted {result.deleted_count} simulated alert(s)")

        await db.close_database_connection()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(cleanup_simulated_alerts())
