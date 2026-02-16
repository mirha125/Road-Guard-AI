# Database and Admin User Setup - FIXED ✅

## Problem Summary
The MongoDB models weren't being created and the admin user wasn't being set up during app startup.

## Root Cause
**bcrypt compatibility issue**: The system had `bcrypt==5.0.0` installed, which has compatibility issues with `passlib==1.7.4`. This caused password hashing to fail silently during admin creation.

## What Was Fixed

### 1. **Bcrypt Version Fixed**
- Downgraded `bcrypt` from `5.0.0` to `4.0.1`
- Updated `requirements.txt` to pin the compatible version
- This fixed the password hashing error that prevented admin creation

### 2. **Updated to Modern FastAPI Lifespan**
- Replaced deprecated `@app.on_event("startup")` with modern `lifespan` context manager
- Better error handling during startup
- Cleaner shutdown process

### 3. **Enhanced Database Initialization**
- Added explicit collection creation with proper indexes
- Creates unique index on `users.email`
- Creates index on `alerts.time` for performance
- Lists all collections during startup for visibility

### 4. **Improved Admin Creation Logic**
- Better logging at each step
- Handles duplicate key errors gracefully
- Verifies admin creation after insertion
- Shows detailed error messages if something fails

## Current Status ✅

### Database Collections
All collections are now created and indexed:
- ✅ `users` - 1 document (System Admin)
- ✅ `cameras` - 0 documents
- ✅ `streams` - 0 documents
- ✅ `alerts` - 0 documents

### Admin User
- ✅ **Email**: `admin@example.com`
- ✅ **Password**: `admin123`
- ✅ **Role**: `admin`
- ✅ **Status**: `approved`
- ✅ **ID**: `69935bc2a159db120cee3d5d`

## How to Start Your Server

### Option 1: Standard Start
```bash
cd /Users/saadzafar/Documents/🐼/FYP/RoadGuardAI
uvicorn backend.main:app --reload
```

### Option 2: With Custom Host/Port
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Production Mode (no reload)
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Startup Logs You Should See

When the server starts, you'll see:
```
==================================================
🚀 Starting Road Safety Monitoring System
==================================================
📡 Connecting to database...
✅ Connected to MongoDB - Database: traffic_safety_db
🔧 Initializing database collections...
   Existing collections: [...]
   ✅ Created unique index on users.email
   ✅ Created index on alerts.time
   📚 Available collections: [...]
✅ Database connected successfully
👤 Creating initial admin user...
   Checking for admin with email: admin@example.com
   Database obtained: traffic_safety_db
   ℹ️  Admin user already exists
   Email: admin@example.com
   Name: System Admin
   Role: admin
   Status: approved
✅ Admin setup completed
==================================================
```

## Testing Your Setup

### 1. Test Database Connection
```bash
python3 backend/test_db.py
```

### 2. Test Admin Login
After starting the server, login with:
- **Email**: `admin@example.com`
- **Password**: `admin123`

### 3. API Endpoints
- Server: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Login: `POST http://localhost:8000/login`

## Files Modified

1. **backend/main.py** - Updated to use lifespan context manager
2. **backend/database.py** - Added collection initialization and indexes
3. **backend/routes/auth.py** - Enhanced admin creation with better error handling
4. **backend/requirements.txt** - Pinned bcrypt==4.0.1 and added certifi

## Important Notes

⚠️ **Do not upgrade bcrypt to 5.x** - It has compatibility issues with passlib 1.7.4
⚠️ **Always use the virtual environment** if you have one set up
✅ **MongoDB collections are created automatically** on first document insert (this is normal behavior)
✅ **Admin user is only created once** - subsequent startups will skip creation

## Troubleshooting

### If admin still not created:
```bash
# Run this to manually create admin
python3 backend/test_startup.py
```

### If bcrypt errors occur:
```bash
# Reinstall correct bcrypt version
pip3 install bcrypt==4.0.1
```

### If connection fails:
1. Check `.env` file has correct MONGO_URI
2. Verify MongoDB Atlas cluster is running
3. Check network/firewall settings
4. Verify database user has read/write permissions

## Next Steps

1. ✅ Start your server: `uvicorn backend.main:app --reload`
2. ✅ Login with admin credentials
3. ✅ Start building your application features
4. ✅ Create additional users as needed

---
**Status**: All issues resolved ✅
**Date**: 2026-02-16
