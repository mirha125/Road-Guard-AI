from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File
from typing import Optional
from datetime import datetime
from ..database import get_database
from ..models import CameraModel, AlertModel, get_pkt_now
from ..services.accident_detection_service import accident_detection_service
from .users import get_current_user
from .alerts import create_alert
from bson import ObjectId
import numpy as np
import cv2
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection", tags=["Accident Detection"])

# Store background tasks for active detections
active_detection_tasks = {}

async def detection_loop(camera_id: str, camera_url: str, camera_name: str, camera_location: str):
    """Background task that continuously monitors a camera for accidents"""
    from pathlib import Path
    import os
    
    logger.info(f"Starting detection loop for camera {camera_id}")
    logger.info(f"Original camera URL: {camera_url}")
    
    original_url = camera_url
    
    # Extract stream ID from various URL formats and resolve to file path
    stream_id = None
    
    # Check for stream feed URL patterns
    if "/streams/feed/" in camera_url:
        # Extract stream_id from URL (works for both relative and absolute URLs)
        stream_id = camera_url.split("/streams/feed/")[-1].split("?")[0].split("#")[0]
        logger.info(f"Extracted stream_id: {stream_id}")
    
    # If we have a stream_id, look up the actual file path
    if stream_id:
        try:
            db = await get_database()
            stream = await db["streams"].find_one({"_id": ObjectId(stream_id)})
            if stream and "video_path" in stream:
                camera_url = stream["video_path"]
                logger.info(f"Resolved stream to video_path: {camera_url}")
            else:
                logger.error(f"Stream not found in database: {stream_id}")
                accident_detection_service.stop_detection(camera_id)
                db = await get_database()
                await db["cameras"].update_one(
                    {"_id": ObjectId(camera_id)},
                    {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
                )
                return
        except Exception as e:
            logger.error(f"Error looking up stream {stream_id}: {e}")
            accident_detection_service.stop_detection(camera_id)
            return
    
    # Now handle the resolved path (could be relative or absolute file path, or external URL)
    if not camera_url.startswith(("http://", "https://", "rtsp://")):
        # It's a file path - normalize for cross-platform compatibility
        path = Path(camera_url)
        
        logger.info(f"Processing as file path: {camera_url}")
        logger.info(f"Is absolute: {path.is_absolute()}")
        
        # If it's a relative path, try to find the actual file
        if not path.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent
            
            # Try multiple possible locations
            possible_paths = [
                Path(camera_url),  # Current working directory
                backend_dir.parent / camera_url,  # Project root
                backend_dir / "uploads" / path.name,  # Direct uploads folder
            ]
            
            found = False
            for p in possible_paths:
                logger.info(f"Checking path: {p}")
                if p.exists():
                    camera_url = str(p.resolve())
                    logger.info(f"Found file at: {camera_url}")
                    found = True
                    break
            
            if not found:
                logger.error(f"Video file not found. Tried: {[str(p) for p in possible_paths]}")
                accident_detection_service.stop_detection(camera_id)
                db = await get_database()
                await db["cameras"].update_one(
                    {"_id": ObjectId(camera_id)},
                    {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
                )
                return
        
        # Normalize path separators for the current OS
        camera_url = os.path.normpath(camera_url)
        
        # Final existence check
        if not os.path.exists(camera_url):
            logger.error(f"Video file does not exist: {camera_url}")
            accident_detection_service.stop_detection(camera_id)
            db = await get_database()
            await db["cameras"].update_one(
                {"_id": ObjectId(camera_id)},
                {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
            )
            return
    
    logger.info(f"Opening stream: {camera_url}")
    cap = cv2.VideoCapture(camera_url)
    
    if not cap.isOpened():
        logger.error(f"Failed to open stream for camera {camera_id}: {camera_url}")
        accident_detection_service.stop_detection(camera_id)
        # Update camera status in database
        db = await get_database()
        await db["cameras"].update_one(
            {"_id": ObjectId(camera_id)},
            {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
        )
        return

    consecutive_detections = 0
    detection_threshold = 3  # Number of consecutive detections before triggering alert
    cooldown_frames = 0
    cooldown_period = 150  # Frames to wait after an alert
    consecutive_failures = 0
    max_failures = 10  # Stop detection after this many consecutive failures

    loop = asyncio.get_event_loop()

    while accident_detection_service.is_detection_active(camera_id):
        try:
            # Read frame in a separate thread to avoid blocking the event loop
            ret, frame = await loop.run_in_executor(None, cap.read)

            if not ret:
                consecutive_failures += 1
                logger.warning(f"Failed to read frame from camera {camera_id} ({consecutive_failures}/{max_failures}), retrying...")

                # Check if video ended (for file-based streams, loop it)
                if not camera_url.startswith(("http://", "https://", "rtsp://")):
                    logger.info(f"Video file ended for camera {camera_id}, restarting from beginning...")
                    cap.release()
                    cap = cv2.VideoCapture(camera_url)
                    consecutive_failures = 0  # Reset counter for looped videos
                    continue

                if consecutive_failures >= max_failures:
                    logger.error(f"Max consecutive failures reached for camera {camera_id}, stopping detection")
                    accident_detection_service.stop_detection(camera_id)
                    db = await get_database()
                    await db["cameras"].update_one(
                        {"_id": ObjectId(camera_id)},
                        {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
                    )
                    break

                await asyncio.sleep(1)
                # Try to reopen
                cap.release()
                cap = cv2.VideoCapture(camera_url)
                continue

            # Reset failure counter on successful read
            consecutive_failures = 0
            
            if frame is not None:
                # Process frame for accident detection
                is_accident, confidence = await accident_detection_service.process_frame(camera_id, frame)
                
                # Handle cooldown
                if cooldown_frames > 0:
                    cooldown_frames -= 1
                    consecutive_detections = 0
                    await asyncio.sleep(0.05)
                    continue
                
                # Track consecutive detections
                if is_accident:
                    consecutive_detections += 1
                    logger.info(f"Accident detected! Consecutive: {consecutive_detections}, Confidence: {confidence:.4f}")
                    
                    # Trigger alert if we have enough consecutive detections
                    if consecutive_detections >= detection_threshold:
                        logger.warning(f"ACCIDENT CONFIRMED at {camera_name} ({camera_location})")
                        
                        # Create alert
                        try:
                            db = await get_database()
                            
                            # Get hospital emails
                            hospitals = await db["users"].find({"role": "hospital"}).to_list(1000)
                            hospital_emails = [h["email"] for h in hospitals]
                            
                            # Create alert document
                            alert_data = {
                                "location": camera_location,
                                "time": get_pkt_now(),
                                "details": f"🚨 ACCIDENT DETECTED at {camera_name} with {confidence*100:.1f}% confidence. Automatic detection triggered by AI model.",
                                "notified_hospitals": hospital_emails,
                                "camera_id": camera_id,
                                "camera_name": camera_name,
                                "confidence": confidence
                            }
                            
                            result = await db["alerts"].insert_one(alert_data)
                            logger.info(f"Alert created with ID: {result.inserted_id}")
                            
                            # Send emails in background
                            from ..services.email_service import email_service
                            for email in hospital_emails:
                                try:
                                    await asyncio.create_task(
                                        email_service.send_alert_email(
                                            to_email=email,
                                            location=camera_location,
                                            details=alert_data["details"],
                                            time=alert_data["time"].strftime("%Y-%m-%d %H:%M:%S")
                                        )
                                    )
                                except Exception as e:
                                    logger.error(f"Error sending email to {email}: {e}")
                            
                        except Exception as e:
                            logger.error(f"Error creating alert: {e}")
                        
                        # Reset and start cooldown
                        consecutive_detections = 0
                        cooldown_frames = cooldown_period
                else:
                    # Reset counter if no accident detected
                    consecutive_detections = 0
            
            # Control frame rate (approx 10-15 fps processing)
            await asyncio.sleep(0.05)
            
        except Exception as e:
            logger.error(f"Error in detection loop: {e}")
            await asyncio.sleep(1)
    
    cap.release()
    logger.info(f"Detection loop ended for camera {camera_id}")

@router.post("/start/{camera_id}")
async def start_detection(
    camera_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start accident detection for a specific camera"""
    try:
        # Get camera details from database
        db = await get_database()
        camera = await db["cameras"].find_one({"_id": ObjectId(camera_id)})
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Check if detection is already running
        if accident_detection_service.is_detection_active(camera_id):
            return {"message": "Detection already active", "camera_id": camera_id}
        
        # Start detection service
        started = await accident_detection_service.start_detection(camera_id, camera["url"])
        
        if not started:
            raise HTTPException(status_code=400, detail="Failed to start detection")
        
        # Start background detection loop
        task = asyncio.create_task(
            detection_loop(
                camera_id, 
                camera["url"],
                camera["name"],
                camera["location"]
            )
        )
        active_detection_tasks[camera_id] = task
        
        # Update camera status in database
        await db["cameras"].update_one(
            {"_id": ObjectId(camera_id)},
            {"$set": {"detection_active": True, "detection_started_at": get_pkt_now()}}
        )
        
        logger.info(f"Started detection for camera {camera_id}")
        
        return {
            "message": "Detection started successfully",
            "camera_id": camera_id,
            "camera_name": camera["name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop/{camera_id}")
async def stop_detection(
    camera_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Stop accident detection for a specific camera"""
    try:
        # Stop detection service
        stopped = accident_detection_service.stop_detection(camera_id)
        
        if not stopped:
            return {"message": "Detection was not active", "camera_id": camera_id}
        
        # Cancel background task if exists
        if camera_id in active_detection_tasks:
            task = active_detection_tasks[camera_id]
            task.cancel()
            del active_detection_tasks[camera_id]
        
        # Update camera status in database
        db = await get_database()
        await db["cameras"].update_one(
            {"_id": ObjectId(camera_id)},
            {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
        )
        
        logger.info(f"Stopped detection for camera {camera_id}")
        
        return {
            "message": "Detection stopped successfully",
            "camera_id": camera_id
        }
        
    except Exception as e:
        logger.error(f"Error stopping detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{camera_id}")
async def get_detection_status(
    camera_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the current detection status for a camera"""
    is_active = accident_detection_service.is_detection_active(camera_id)
    
    # Get camera info
    db = await get_database()
    camera = await db["cameras"].find_one({"_id": ObjectId(camera_id)})
    
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return {
        "camera_id": camera_id,
        "detection_active": is_active,
        "camera_name": camera.get("name"),
        "camera_location": camera.get("location")
    }
