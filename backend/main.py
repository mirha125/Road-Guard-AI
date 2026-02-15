from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import db
from .config import settings
from .routes import auth, users, cameras, streams, alerts, detection

app = FastAPI(title="Road Safety Monitoring System")
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

@app.on_event("startup")
async def startup_db_client():
    await db.connect_to_database()
    await auth.create_initial_admin()
@app.on_event("shutdown")
async def shutdown_db_client():
    await db.close_database_connection()
@app.get("/")
async def root():
    return {"message": "Road Safety Monitoring System API"}