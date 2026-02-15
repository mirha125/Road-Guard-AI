# Windows Setup Guide

This guide provides step-by-step instructions to set up and run the project on a Windows machine that has no prior development tools installed.

## 1. Prerequisites

Before you begin, you need to install the following software:

### A. Python (for Backend)
1. Download the latest version of Python from [python.org](https://www.python.org/downloads/).
2. Run the installer.
3. **IMPORTANT:** Check the box **"Add Python to PATH"** before clicking "Install Now". This is crucial for running Python commands from the terminal.

### B. Node.js (for Frontend)
1. Download the "LTS" (Long Term Support) version of Node.js from [nodejs.org](https://nodejs.org/).
2. Run the installer and follow the default prompts.

### C. Git (Version Control)
1. Download Git for Windows from [git-scm.com](https://git-scm.com/download/win).
2. Run the installer and follow the default prompts.

### D. MongoDB (Database)
You have two options:
*   **Option 1 (Recommended for Local Dev):** Install MongoDB Community Server.
    1. Download from [mongodb.com](https://www.mongodb.com/try/download/community).
    2. Run the installer. Choose "Complete" setup.
    3. It is recommended to install "MongoDB Compass" when prompted (it helps you view your data).
*   **Option 2 (Cloud):** Use MongoDB Atlas (Cloud). You will need your connection string.

---

## 2. Clone the Repository

1. Open **Command Prompt** (cmd) or **PowerShell**.
2. Navigate to the folder where you want to save the project:
   ```powershell
   cd Documents
   ```
3. Clone the project (replace URL with your actual repo URL if you have one, otherwise just copy the files):
   ```powershell
   git clone <YOUR_REPOSITORY_URL>
   cd "Front end"
   ```
   *(Note: If you copied the files manually, just `cd` into the project folder)*

---

## 3. Backend Setup

1. Open a terminal in the project root folder.
2. Navigate to the backend directory:
   ```powershell
   cd backend
   ```

3. **Create a Virtual Environment:**
   This isolates the project dependencies.
   ```powershell
   python -m venv venv
   ```

4. **Activate the Virtual Environment:**
   ```powershell
   venv\Scripts\activate
   ```
   *(You should see `(venv)` appear at the start of your command line)*

5. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

6. **Configure Environment Variables:**
   *   Create a new file named `.env` inside the `backend` folder.
   *   Copy the contents from `sample.env` (if it exists) or add the following:
     ```env
     MONGO_URI=mongodb://localhost:27017
     DB_NAME=traffic_db
     SECRET_KEY=your_secret_key_here
     ALGORITHM=HS256
     ACCESS_TOKEN_EXPIRE_MINUTES=30
     
     # Admin Setup
     ADMIN_EMAIL=admin@example.com
     ADMIN_PASSWORD=admin
     
     # Email Settings (Optional)
     EMAIL_SENDER=your_email@gmail.com
     EMAIL_PASSWORD=your_app_password
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     
     # Server
     HOST=0.0.0.0
     PORT=8000
     ```
   *   *Note: If you are using MongoDB Atlas, replace `mongodb://localhost:27017` with your connection string.*

7. **Run the Backend Server:**
   
   First, navigate back to the project root:
   ```powershell
   cd ..
   ```
   
   Then run the backend using uvicorn:
   ```powershell
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   *The server should start running at `http://localhost:8000`.*

---

## 4. Frontend Setup

1. Open a **new** terminal window (keep the backend running in the first one).
2. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

3. **Install Dependencies:**
   ```powershell
   npm install
   ```

4. **Run the Frontend:**
   ```powershell
   npm run dev
   ```
   *The frontend should start, usually at `http://localhost:5173`.*

---

## 5. Accessing the Application

1. Open your web browser (Chrome, Edge, etc.).
2. Go to `http://localhost:5173` (or the URL shown in your frontend terminal).
3. Login with the admin credentials you set in the `.env` file (default: `admin@example.com` / `admin`).

## Troubleshooting

*   **"python is not recognized"**: You didn't check "Add Python to PATH" during installation. Reinstall Python and check that box.
*   **"npm is not recognized"**: Restart your terminal after installing Node.js.
*   **MongoDB Connection Error**: Ensure MongoDB is running (Open Task Manager > Services > MongoDB) or check your connection string in `.env`.
*   **Execution Policy Error (PowerShell)**: If you can't activate the venv, run this command in PowerShell as Administrator: `Set-ExecutionPolicy RemoteSigned`.
