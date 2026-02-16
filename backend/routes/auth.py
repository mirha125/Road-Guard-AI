from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from ..database import get_database
from ..models import UserModel, UserLogin, UserCreate, UserRegister, get_pkt_now
from ..config import settings
from bson import ObjectId
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = get_pkt_now() + expires_delta
    else:
        expire = get_pkt_now() + timedelta(minutes=15)
    # Convert to timestamp for JWT (JWT expects Unix timestamp)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
async def create_initial_admin():
    try:
        if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
            print(f"   ❌ Admin credentials not configured in .env file")
            print(f"   ADMIN_EMAIL: {settings.ADMIN_EMAIL or 'NOT SET'}")
            print(f"   ADMIN_PASSWORD: {'SET' if settings.ADMIN_PASSWORD else 'NOT SET'}")
            return

        print(f"   Checking for admin with email: {settings.ADMIN_EMAIL}")
        db = await get_database()

        if db is None:
            print("   ❌ Database is None!")
            return

        print(f"   Database obtained: {db.name}")

        # Check if admin already exists
        admin = await db["users"].find_one({"email": settings.ADMIN_EMAIL})

        if not admin:
            print(f"   No existing admin found. Creating new admin...")
            print(f"   Admin email: {settings.ADMIN_EMAIL}")

            hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            print(f"   Password hashed successfully")

            admin_user = UserModel(
                name="System Admin",
                email=settings.ADMIN_EMAIL,
                password=hashed_password,
                role="admin",
                approval_status="approved"
            )
            print(f"   UserModel created")

            # Dump model and ensure datetime is properly serialized
            admin_dict = admin_user.model_dump(by_alias=True, exclude={"id"})
            print(f"   Model dumped to dict: {list(admin_dict.keys())}")

            try:
                result = await db["users"].insert_one(admin_dict)
                print(f"   ✅ Admin user created successfully!")
                print(f"   Email: {settings.ADMIN_EMAIL}")
                print(f"   ID: {result.inserted_id}")

                # Verify the user was created
                verify_admin = await db["users"].find_one({"email": settings.ADMIN_EMAIL})
                if verify_admin:
                    print(f"   ✅ Admin verified in database")
                else:
                    print(f"   ⚠️  Warning: Admin created but could not be verified")

            except Exception as insert_error:
                # Handle duplicate key error gracefully
                if "duplicate key" in str(insert_error).lower():
                    print(f"   ℹ️  Admin user already exists (duplicate key)")
                else:
                    raise
        else:
            print(f"   ℹ️  Admin user already exists")
            print(f"   Email: {admin.get('email')}")
            print(f"   Name: {admin.get('name')}")
            print(f"   Role: {admin.get('role')}")
            print(f"   Status: {admin.get('approval_status')}")
            print(f"   ID: {admin.get('_id')}")

    except Exception as e:
        import traceback
        print(f"   ❌ Error creating initial admin: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Traceback:\n{traceback.format_exc()}")
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
@router.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = await get_database()
    user = await db["users"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Removed approval status check - users can get tokens regardless of approval status
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
    # Removed approval status check for login - users can login regardless of approval status
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}