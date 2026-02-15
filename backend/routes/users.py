from fastapi import APIRouter, HTTPException, status, Depends, Body
from typing import List
from ..database import get_database
from ..models import UserModel, UserCreate, PyObjectId
from .auth import get_password_hash, oauth2_scheme
from ..config import settings
from jose import jwt, JWTError
from bson import ObjectId
router = APIRouter(prefix="/users", tags=["Users"])
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = await get_database()
    user = await db["users"].find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user
async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
@router.post("/", response_model=UserModel)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_admin_user)):
    db = await get_database()
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = UserModel(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role,
        approval_status="approved"
    )
    result = await db["users"].insert_one(new_user.model_dump(by_alias=True, exclude={"id"}))
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    return created_user
@router.get("/", response_model=List[UserModel])
async def list_users(current_user: dict = Depends(get_current_user)):
    db = await get_database()
    users = await db["users"].find().to_list(1000)
    return users
@router.patch("/{user_id}/approval")
async def update_user_approval(
    user_id: str, 
    approval_data: dict = Body(...),
    current_user: dict = Depends(get_current_admin_user)
):
    db = await get_database()
    approval_status = approval_data.get("approval_status")
    if approval_status not in ["approved", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid approval status")
    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"approval_status": approval_status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User approval status updated to {approval_status}"}
@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_admin_user)):
    db = await get_database()
    result = await db["users"].delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}