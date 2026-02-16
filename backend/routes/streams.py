from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List
import shutil
import os
import uuid
from pathlib import Path
from ..database import get_database
from ..models import StreamModel
from ..services.stream_service import stream_service
from .users import get_current_admin_user, get_current_user
from bson import ObjectId
router = APIRouter(prefix="/streams", tags=["Streams"])

# Use absolute path for cross-platform compatibility (Windows/Mac/Linux)
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
@router.post("/upload", response_model=StreamModel)
async def upload_video(
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_admin_user)
):
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = str(UPLOAD_DIR / filename)  # Use Path for cross-platform path handling
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    stream_entry = StreamModel(
        video_path=file_path,
        stream_url="", 
        is_active=True
    )
    db = await get_database()
    new_stream = stream_entry.model_dump(by_alias=True, exclude={"id"})
    result = await db["streams"].insert_one(new_stream)
    stream_id = str(result.inserted_id)
    stream_url = f"/streams/feed/{stream_id}"
    await db["streams"].update_one(
        {"_id": result.inserted_id},
        {"$set": {"stream_url": stream_url}}
    )
    created_stream = await db["streams"].find_one({"_id": result.inserted_id})
    return created_stream
@router.get("/feed/{stream_id}")
async def video_feed(stream_id: str):
    db = await get_database()
    stream = await db["streams"].find_one({"_id": ObjectId(stream_id)})
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    if not stream.get("is_active", True):
        raise HTTPException(status_code=404, detail="Stream is inactive")
    video_path = stream["video_path"]
    if not os.path.exists(video_path):
         raise HTTPException(status_code=404, detail="Video file not found")
    return StreamingResponse(
        stream_service.generate_frames(video_path),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
@router.get("/", response_model=List[StreamModel])
async def list_streams(current_user: dict = Depends(get_current_user)):
    db = await get_database()
    streams = await db["streams"].find().to_list(1000)
    return streams
@router.patch("/{stream_id}/stop")
async def stop_stream(stream_id: str, current_user: dict = Depends(get_current_user)):

    db = await get_database()
    stream = await db["streams"].find_one({"_id": ObjectId(stream_id)})
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    await db["streams"].update_one(
        {"_id": ObjectId(stream_id)},
        {"$set": {"is_active": False}}
    )
    return {"message": "Stream stopped successfully"}
@router.delete("/{stream_id}")
async def delete_stream(stream_id: str, current_user: dict = Depends(get_current_user)):

    db = await get_database()
    stream = await db["streams"].find_one({"_id": ObjectId(stream_id)})
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    if os.path.exists(stream["video_path"]):
        os.remove(stream["video_path"])
    result = await db["streams"].delete_one({"_id": ObjectId(stream_id)})
    return {"message": "Stream deleted successfully"}

@router.delete("/all/delete")
async def delete_all_streams(current_user: dict = Depends(get_current_admin_user)):
    db = await get_database()
    streams = await db["streams"].find().to_list(1000)
    
    # Delete all files
    for stream in streams:
        if "video_path" in stream and os.path.exists(stream["video_path"]):
            try:
                os.remove(stream["video_path"])
            except Exception as e:
                print(f"Error deleting file {stream['video_path']}: {e}")
                
    # Delete all records
    await db["streams"].delete_many({})
    return {"message": "All streams deleted successfully"}