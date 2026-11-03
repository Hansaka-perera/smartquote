@echo off
REM Developer mode: API on :8000 with auto-reload, UI on :5173 with hot reload
cd /d "%~dp0backend"
start "API" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"
cd /d "%~dp0frontend"
start "UI" cmd /k "npm run dev"
start "" http://localhost:5173
