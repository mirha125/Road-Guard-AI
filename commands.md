open command prompt from + button

backend

cd backend
.\venv\scripts\activate
cd ..
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

==============================================================================

FRONT END

cd frontend
npm run dev