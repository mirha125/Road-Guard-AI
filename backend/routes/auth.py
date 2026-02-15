from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from ..database import get_database
from ..models import UserModel, UserLogin, UserCreate, UserRegister
from ..config import settings
from bson import ObjectId
router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
async def create_initial_admin():
    db = await get_database()
    admin = await db["users"].find_one({"email": settings.ADMIN_EMAIL})
    if not admin:
        hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
        admin_user = UserModel(
            name="System Admin",
            email=settings.ADMIN_EMAIL,
            password=hashed_password,
            role="admin",
            approval_status="approved"
        )
        await db["users"].insert_one(admin_user.model_dump(by_alias=True, exclude={"id"}))
        print(f"Admin user created: {settings.ADMIN_EMAIL}")
    else:
        print("Admin user already exists")
@router.post("/register", response_model=dict)
async def register(user_data: UserRegister):
    db = await get_database()
    existing_user = await db["users"].find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    hashed_password = get_password_hash(user_data.password)
    new_user = UserModel(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role,
        approval_status="pending"
    )
    await db["users"].insert_one(new_user.model_dump(by_alias=True, exclude={"id"}))
    return {"message": "Registration successful. Please wait for admin approval."}
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = await get_database()
    user = await db["users"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.get("approval_status", "approved") != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an administrator"
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}
@router.post("/login", response_model=dict)
async def login(user_login: UserLogin):
    db = await get_database()
    user = await db["users"].find_one({"email": user_login.email})
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if user.get("approval_status", "approved") != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an administrator"
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}