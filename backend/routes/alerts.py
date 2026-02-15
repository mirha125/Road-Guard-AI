from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
from datetime import datetime
from ..database import get_database
from ..models import AlertModel, PyObjectId
from ..services.email_service import email_service
from .users import get_current_user
from bson import ObjectId
router = APIRouter(prefix="/alerts", tags=["Alerts"])
@router.post("/", response_model=AlertModel)
async def create_alert(
    alert: AlertModel, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    db = await get_database()
    hospitals = await db["users"].find({"role": "hospital"}).to_list(1000)
    hospital_emails = [h["email"] for h in hospitals]
    alert.notified_hospitals = hospital_emails
    new_alert = alert.model_dump(by_alias=True, exclude={"id"})
    result = await db["alerts"].insert_one(new_alert)
    created_alert = await db["alerts"].find_one({"_id": result.inserted_id})
    for email in hospital_emails:
        background_tasks.add_task(
            email_service.send_alert_email,
            to_email=email,
            location=alert.location,
            details=alert.details,
            time=alert.time.strftime("%Y-%m-%d %H:%M:%S")
        )
    return created_alert
@router.get("/", response_model=List[AlertModel])
async def list_alerts(current_user: dict = Depends(get_current_user)):
    db = await get_database()
    alerts = await db["alerts"].find().sort("time", -1).to_list(1000)
    return alerts
@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    db = await get_database()
    alert = await db["alerts"].find_one({"_id": ObjectId(alert_id)})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db["alerts"].delete_one({"_id": ObjectId(alert_id)})
    return {"message": "Alert deleted successfully"}