from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import db
from .config import settings
from .routes import auth, users, cameras, streams, alerts, detection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 50)
    print("🚀 Starting Road Safety Monitoring System")
    print("=" * 50)
    try:
        print("📡 Connecting to database...")
        await db.connect_to_database()
        print("✅ Database connected successfully")

        print("👤 Creating initial admin user...")
        await auth.create_initial_admin()
        print("✅ Admin setup completed")

        # Migrate old alerts
        from .database import get_database
        from .models import get_pkt_now
        from datetime import timedelta
        db_inst = await get_database()

        # 1) Alerts without status field (pre-migration)
        r1 = await db_inst["alerts"].update_many(
            {"status": {"$exists": False}},
            {"$set": {"status": "EMERGENCY_DISPATCHED", "dispatch_type": "legacy", "admin_decision_time": None, "dispatched_at": None}}
        )
        if r1.modified_count > 0:
            print(f"Migrated {r1.modified_count} old alerts (no status field)")

        # 2) Stuck PENDING_ADMIN_REVIEW alerts older than 20s (no timer running after restart)
        cutoff = get_pkt_now() - timedelta(seconds=20)
        r2 = await db_inst["alerts"].update_many(
            {"status": "PENDING_ADMIN_REVIEW", "time": {"$lt": cutoff}},
            {"$set": {"status": "AUTO_DISPATCHED", "dispatch_type": "auto_timeout", "dispatched_at": get_pkt_now()}}
        )
        if r2.modified_count > 0:
            print(f"Auto-dispatched {r2.modified_count} stale pending alerts")
        print("=" * 50)
    except Exception as e:
        import traceback
        print(f"❌ Startup error: {e}")
        print(traceback.format_exc())
        print("=" * 50)
        raise  # Re-raise to prevent app from starting with errors

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await db.close_database_connection()
    print("✅ Shutdown complete")

app = FastAPI(title="Road Safety Monitoring System", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router)
app.include_router(cameras.router)
app.include_router(streams.router)
app.include_router(alerts.router)
app.include_router(detection.router)

@app.get("/")
async def root():
    return {"message": "Road Safety Monitoring System API"}