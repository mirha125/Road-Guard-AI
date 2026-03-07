from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File
from typing import Optional
from datetime import datetime
from collections import deque
from pathlib import Path
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
import uuid

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
    detection_threshold = 3  # Number of consecutive predictions before triggering alert
    cooldown_frames = 0
    cooldown_period = 300  # Frames to wait after an alert (~10s at 30fps)
    consecutive_failures = 0
    max_failures = 10

    # Rolling buffer for video snippet capture
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_delay = 1.0 / source_fps
    snippet_buffer = deque(maxlen=int(source_fps * 5))  # ~5 seconds of pre-trigger video

    # Post-capture state
    POST_CAPTURE_FRAMES = int(source_fps * 3)  # ~3 seconds of post-accident footage
    post_capture_remaining = 0
    post_capture_frames = []
    post_capture_confidence = 0.0
    post_capture_time = None

    # Snippets directory
    snippets_dir = Path(__file__).resolve().parent.parent / "uploads" / "snippets"
    snippets_dir.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_event_loop()

    # Non-blocking prediction: fire prediction in background, check result later
    pending_prediction = None  # asyncio.Future or None
    frame_count = 0
    PREDICT_EVERY = 16  # Run prediction every N frames

    # Initialize model frame buffer
    if camera_id not in accident_detection_service.frame_buffers:
        accident_detection_service.frame_buffers[camera_id] = deque(maxlen=accident_detection_service.sequence_length)

    while accident_detection_service.is_detection_active(camera_id):
        try:
            ret, frame = await loop.run_in_executor(None, cap.read)

            if not ret:
                consecutive_failures += 1
                logger.warning(f"Failed to read frame from camera {camera_id} ({consecutive_failures}/{max_failures})")

                if not camera_url.startswith(("http://", "https://", "rtsp://")):
                    logger.info(f"Video file ended for camera {camera_id}, restarting...")
                    cap.release()
                    cap = cv2.VideoCapture(camera_url)
                    consecutive_failures = 0
                    continue

                if consecutive_failures >= max_failures:
                    logger.error(f"Max failures reached for camera {camera_id}, stopping")
                    accident_detection_service.stop_detection(camera_id)
                    db = await get_database()
                    await db["cameras"].update_one(
                        {"_id": ObjectId(camera_id)},
                        {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
                    )
                    break

                await asyncio.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(camera_url)
                continue

            consecutive_failures = 0

            if frame is not None:
                frame_count += 1

                # --- Post-capture phase: collect frames after accident trigger ---
                if post_capture_remaining > 0:
                    post_capture_frames.append(frame.copy())
                    post_capture_remaining -= 1

                    if post_capture_remaining == 0:
                        try:
                            db = await get_database()

                            all_frames = list(snippet_buffer) + post_capture_frames
                            snippet_url = None
                            if len(all_frames) > 0:
                                try:
                                    write_fps = source_fps
                                    snippet_filename = f"{uuid.uuid4()}.mp4"
                                    snippet_path = str(snippets_dir / snippet_filename)
                                    h, w = all_frames[0].shape[:2]
                                    fourcc = cv2.VideoWriter_fourcc(*'avc1')
                                    writer = cv2.VideoWriter(snippet_path, fourcc, write_fps, (w, h))
                                    if not writer.isOpened():
                                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                                        writer = cv2.VideoWriter(snippet_path, fourcc, write_fps, (w, h))
                                    for f in all_frames:
                                        writer.write(f)
                                    writer.release()
                                    snippet_url = f"/alerts/snippet/{snippet_filename}"
                                    logger.info(f"Snippet saved: {snippet_path} ({len(all_frames)} frames at {write_fps:.0f}fps)")
                                except Exception as e:
                                    logger.error(f"Error saving snippet: {e}")

                            alert_data = {
                                "location": camera_location,
                                "time": post_capture_time,
                                "details": f"ACCIDENT DETECTED at {camera_name} with {post_capture_confidence*100:.1f}% confidence. Automatic detection triggered by AI model.",
                                "notified_hospitals": [],
                                "camera_id": camera_id,
                                "camera_name": camera_name,
                                "confidence": post_capture_confidence,
                                "status": "PENDING_ADMIN_REVIEW",
                                "dispatch_type": None,
                                "admin_decision_time": None,
                                "dispatched_at": None,
                                "snippet_url": snippet_url
                            }

                            result = await db["alerts"].insert_one(alert_data)
                            logger.info(f"Alert created with ID: {result.inserted_id} (PENDING_ADMIN_REVIEW)")

                            from .alerts import schedule_auto_dispatch
                            schedule_auto_dispatch(str(result.inserted_id))

                        except Exception as e:
                            logger.error(f"Error creating alert: {e}")

                        post_capture_frames = []
                        snippet_buffer.clear()

                    await asyncio.sleep(frame_delay)
                    continue

                # --- Normal phase: buffer frames for snippets + run detection ---
                snippet_buffer.append(frame.copy())

                if cooldown_frames > 0:
                    cooldown_frames -= 1
                    await asyncio.sleep(frame_delay)
                    continue

                # Preprocess and add to model buffer (fast — no prediction here)
                processed = accident_detection_service.preprocess_frame(frame)
                accident_detection_service.frame_buffers[camera_id].append(processed)

                # Check if a background prediction finished
                if pending_prediction is not None and pending_prediction.done():
                    try:
                        is_accident, confidence = pending_prediction.result()
                        if is_accident:
                            consecutive_detections += 1
                            logger.info(f"Accident detected! Consecutive: {consecutive_detections}, Confidence: {confidence:.4f}")
                            if consecutive_detections >= detection_threshold:
                                logger.warning(f"ACCIDENT CONFIRMED at {camera_name} ({camera_location})")
                                post_capture_remaining = POST_CAPTURE_FRAMES
                                post_capture_frames = []
                                post_capture_confidence = confidence
                                post_capture_time = get_pkt_now()
                                consecutive_detections = 0
                                cooldown_frames = cooldown_period
                        else:
                            consecutive_detections = 0
                    except Exception as e:
                        logger.error(f"Prediction error: {e}")
                    pending_prediction = None

                # Fire off a new prediction if none is running
                if (pending_prediction is None and
                    frame_count % PREDICT_EVERY == 0 and
                    len(accident_detection_service.frame_buffers[camera_id]) >= accident_detection_service.sequence_length):
                    # Snapshot the buffer so the executor thread reads a stable copy
                    buffer_snapshot = deque(list(accident_detection_service.frame_buffers[camera_id]),
                                           maxlen=accident_detection_service.sequence_length)
                    pending_prediction = loop.run_in_executor(
                        None,
                        accident_detection_service.predict_accident,
                        buffer_snapshot
                    )

            await asyncio.sleep(frame_delay)

        except asyncio.CancelledError:
            logger.info(f"Detection task cancelled for camera {camera_id}")
            break
        except Exception as e:
            logger.error(f"Error in detection loop: {e}")
            await asyncio.sleep(1)

    # Cleanup
    cap.release()
    accident_detection_service.stop_detection(camera_id)
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
        # Stop detection service first
        stopped = accident_detection_service.stop_detection(camera_id)

        logger.info(f"Detection service stopped for camera {camera_id}: {stopped}")

        # Cancel background task if exists
        if camera_id in active_detection_tasks:
            task = active_detection_tasks[camera_id]
            task.cancel()

            # Wait for the task to actually finish (with timeout)
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                # Task was cancelled or didn't finish in time, that's okay
                pass
            except Exception as e:
                logger.warning(f"Error while waiting for task cancellation: {e}")

            # Remove from active tasks
            del active_detection_tasks[camera_id]
            logger.info(f"Background task cancelled for camera {camera_id}")

        # Update camera status in database
        db = await get_database()
        await db["cameras"].update_one(
            {"_id": ObjectId(camera_id)},
            {"$set": {"detection_active": False, "detection_stopped_at": get_pkt_now()}}
        )

        logger.info(f"Successfully stopped detection for camera {camera_id}")

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
