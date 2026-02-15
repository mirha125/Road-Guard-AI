from pydantic import BaseModel, EmailStr, Field, field_serializer
from typing import Optional, List, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema
class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ], serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")
class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    password: str
    role: str  
    approval_status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
class UserLogin(BaseModel):
    email: EmailStr
    password: str
class CameraModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    location: str
    url: str
    status: str = "active"
    detection_active: bool = False
    detection_started_at: Optional[datetime] = None
    detection_stopped_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class StreamModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    video_path: str
    stream_url: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
class AlertModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    location: str
    time: datetime = Field(default_factory=datetime.utcnow)
    details: str
    notified_hospitals: List[EmailStr] = []
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }