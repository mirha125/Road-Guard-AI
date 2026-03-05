from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from typing import List
from datetime import datetime
from pathlib import Path
from ..database import get_database
from ..models import AlertModel, PyObjectId, get_pkt_now
from ..services.email_service import email_service
from .users import get_current_user
from bson import ObjectId
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# Track pending auto-dispatch timers: alert_id -> asyncio.Task
_auto_dispatch_tasks = {}

AUTO_DISPATCH_DELAY = 15  # seconds


async def _dispatch_alert(alert_id: str, alert_doc: dict):
    """Send emails to all hospitals for a confirmed/auto-dispatched alert."""
    db = await get_database()
    hospitals = await db["users"].find({"role": "hospital"}).to_list(1000)
    hospital_emails = [h["email"] for h in hospitals]

    # Update notified_hospitals list
    await db["alerts"].update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"notified_hospitals": hospital_emails}}
    )

    for email_addr in hospital_emails:
        try:
            asyncio.create_task(
                email_service.send_alert_email(
                    to_email=email_addr,
                    location=alert_doc["location"],
                    details=alert_doc["details"],
                    time=alert_doc["time"].strftime("%Y-%m-%d %H:%M:%S")
                )
            )
        except Exception as e:
            logger.error(f"Error creating email task for {email_addr}: {e}")


async def _auto_dispatch_timer(alert_id: str):
    """Wait AUTO_DISPATCH_DELAY seconds, then auto-dispatch if still pending."""
    try:
        await asyncio.sleep(AUTO_DISPATCH_DELAY)

        db = await get_database()
        # Atomic update: only transition if still PENDING_ADMIN_REVIEW
        result = await db["alerts"].find_one_and_update(
            {"_id": ObjectId(alert_id), "$or": [
                {"status": "PENDING_ADMIN_REVIEW"},
                {"status": {"$exists": False}}
            ]},
            {"$set": {
                "status": "AUTO_DISPATCHED",
                "dispatch_type": "auto_timeout",
                "dispatched_at": get_pkt_now(),
            }},
            return_document=True
        )

        if result:
            logger.info(f"Auto-dispatching alert {alert_id} due to admin timeout")
            await _dispatch_alert(alert_id, result)
        else:
            logger.info(f"Auto-dispatch skipped for {alert_id} (already handled)")

    except asyncio.CancelledError:
        logger.info(f"Auto-dispatch timer cancelled for {alert_id}")
    except Exception as e:
        logger.error(f"Error in auto-dispatch timer for {alert_id}: {e}")
    finally:
        _auto_dispatch_tasks.pop(alert_id, None)


def schedule_auto_dispatch(alert_id: str):
    """Schedule an auto-dispatch timer for a new pending alert."""
    task = asyncio.create_task(_auto_dispatch_timer(alert_id))
    _auto_dispatch_tasks[alert_id] = task


@router.post("/", response_model=AlertModel)
async def create_alert(
    alert: AlertModel,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    db = await get_database()
    alert.status = "PENDING_ADMIN_REVIEW"
    alert.dispatch_type = None
    alert.dispatched_at = None
    alert.admin_decision_time = None
    new_alert = alert.model_dump(by_alias=True, exclude={"id"})
    result = await db["alerts"].insert_one(new_alert)
    created_alert = await db["alerts"].find_one({"_id": result.inserted_id})

    # Schedule auto-dispatch after 15 seconds
    schedule_auto_dispatch(str(result.inserted_id))

    return created_alert


@router.post("/{alert_id}/confirm")
async def confirm_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Admin confirms the alert - dispatch to emergency services."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can confirm alerts")

    db = await get_database()

    # Atomic update: only transition if still PENDING_ADMIN_REVIEW (or old alerts without status field)
    result = await db["alerts"].find_one_and_update(
        {"_id": ObjectId(alert_id), "$or": [
            {"status": "PENDING_ADMIN_REVIEW"},
            {"status": {"$exists": False}}
        ]},
        {"$set": {
            "status": "EMERGENCY_DISPATCHED",
            "dispatch_type": "admin_confirmed",
            "admin_decision_time": get_pkt_now(),
            "dispatched_at": get_pkt_now(),
        }},
        return_document=True
    )

    if not result:
        # Check if alert exists but was already handled
        existing = await db["alerts"].find_one({"_id": ObjectId(alert_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Alert not found")
        raise HTTPException(status_code=409, detail=f"Alert already handled with status: {existing.get('status', 'unknown')}")

    # Cancel the auto-dispatch timer
    timer_task = _auto_dispatch_tasks.pop(alert_id, None)
    if timer_task:
        timer_task.cancel()

    # Dispatch emails
    await _dispatch_alert(alert_id, result)

    return {"message": "Alert confirmed and dispatched to emergency services", "status": "EMERGENCY_DISPATCHED"}


@router.post("/{alert_id}/reject")
async def reject_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Admin rejects the alert - mark as false alarm."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reject alerts")

    db = await get_database()

    # Atomic update: only transition if still PENDING_ADMIN_REVIEW (or old alerts without status field)
    result = await db["alerts"].find_one_and_update(
        {"_id": ObjectId(alert_id), "$or": [
            {"status": "PENDING_ADMIN_REVIEW"},
            {"status": {"$exists": False}}
        ]},
        {"$set": {
            "status": "FALSE_ALARM",
            "admin_decision_time": get_pkt_now(),
        }},
        return_document=True
    )

    if not result:
        existing = await db["alerts"].find_one({"_id": ObjectId(alert_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Alert not found")
        raise HTTPException(status_code=409, detail=f"Alert already handled with status: {existing.get('status', 'unknown')}")

    # Cancel the auto-dispatch timer
    timer_task = _auto_dispatch_tasks.pop(alert_id, None)
    if timer_task:
        timer_task.cancel()

    return {"message": "Alert rejected as false alarm", "status": "FALSE_ALARM"}


@router.get("/", response_model=List[AlertModel])
async def list_alerts(current_user: dict = Depends(get_current_user)):
    db = await get_database()
    alerts = await db["alerts"].find().sort("time", -1).to_list(1000)
    return alerts


SNIPPETS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "snippets"
SNIPPETS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/snippet/{filename}")
async def serve_snippet(filename: str):
    """Serve an accident video snippet."""
    file_path = SNIPPETS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Snippet not found")
    return FileResponse(str(file_path), media_type="video/mp4")


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    db = await get_database()
    alert = await db["alerts"].find_one({"_id": ObjectId(alert_id)})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Cancel any pending timer
    timer_task = _auto_dispatch_tasks.pop(alert_id, None)
    if timer_task:
        timer_task.cancel()

    await db["alerts"].delete_one({"_id": ObjectId(alert_id)})
    return {"message": "Alert deleted successfully"}


@router.delete("/all/delete")
async def delete_all_alerts(current_user: dict = Depends(get_current_user)):
    db = await get_database()

    # Cancel all pending timers
    for aid, task in list(_auto_dispatch_tasks.items()):
        task.cancel()
    _auto_dispatch_tasks.clear()

    await db["alerts"].delete_many({})
    return {"message": "All alerts deleted successfully"}
