from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from ..database import get_database
from ..models import CameraModel, PyObjectId
from .users import get_current_admin_user, get_current_user
from bson import ObjectId
router = APIRouter(prefix="/cameras", tags=["Cameras"])
@router.post("/", response_model=CameraModel)
async def add_camera(camera: CameraModel, current_user: dict = Depends(get_current_admin_user)):
    db = await get_database()
    new_camera = camera.model_dump(by_alias=True, exclude={"id"})
    result = await db["cameras"].insert_one(new_camera)
    created_camera = await db["cameras"].find_one({"_id": result.inserted_id})
    return created_camera
@router.get("/", response_model=List[CameraModel])
async def list_cameras(current_user: dict = Depends(get_current_user)):
    db = await get_database()
    cameras = await db["cameras"].find().to_list(1000)
    return cameras
@router.delete("/{camera_id}")
async def delete_camera(camera_id: str, current_user: dict = Depends(get_current_admin_user)):
    db = await get_database()
    result = await db["cameras"].delete_one({"_id": ObjectId(camera_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": "Camera deleted successfully"}