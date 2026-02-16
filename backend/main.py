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