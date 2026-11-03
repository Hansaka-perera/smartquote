@echo off
REM SmartQuote Studio - one-time setup (Windows)
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.10+ is required. Install from https://www.python.org/downloads/ and tick "Add python.exe to PATH". & pause & exit /b 1)
if not exist backend\.venv (
  echo Creating virtual environment...
  python -m venv backend\.venv || (echo Failed to create venv & pause & exit /b 1)
)
echo Installing Python packages...
backend\.venv\Scripts\python -m pip install --upgrade pip >nul
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt || (echo Package install failed & pause & exit /b 1)
where npm >nul 2>nul
if %errorlevel%==0 (
  echo Building the web interface...
  pushd frontend
  call npm install --no-audit --no-fund
  call npm run build
  popd
) else (
  if exist frontend\dist (echo Node.js not found - using the pre-built interface in frontend\dist.) else (echo Node.js 18+ is required to build the interface. Install from https://nodejs.org & pause & exit /b 1)
)
echo Loading SAMPLE materials for testing (you can delete or edit them in the app)...
pushd backend
.venv\Scripts\python -m app.seed
popd
echo.
echo Setup complete. Run start.bat to launch SmartQuote Studio.
pause
