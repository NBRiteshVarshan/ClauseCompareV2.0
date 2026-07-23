@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set LOG_FILE=install.log
set PORT=8501

echo [ClauseCompare Windows Installer] > %LOG_FILE% 2>&1

:: Check for winget (built‑in on Windows 10/11)
where winget >nul 2>&1
if errorlevel 1 (
    echo ❌ winget not found. This script requires Windows 10/11. >> %LOG_FILE% 2>&1
    echo    Please install Python manually from https://python.org >> %LOG_FILE% 2>&1
    pause
    exit /b 1
)

:: Install Python if missing
echo Checking for Python... >> %LOG_FILE% 2>&1
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Installing Python 3.12 via winget... >> %LOG_FILE% 2>&1
    winget install Python.Python.3.12 --silent
    echo Python installed. Please restart Command Prompt and run this script again. >> %LOG_FILE% 2>&1
    pause
    exit /b 0
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo ✅ Python !PYTHON_VER! found. >> %LOG_FILE% 2>&1
)

:: Create virtual environment
echo Creating virtual environment... >> %LOG_FILE% 2>&1
if not exist "venv" (
    python -m venv venv >> %LOG_FILE% 2>&1
    echo ✅ Virtual environment created. >> %LOG_FILE% 2>&1
) else (
    echo ✅ Virtual environment already exists. >> %LOG_FILE% 2>&1
)

:: Install dependencies
echo Installing dependencies... >> %LOG_FILE% 2>&1
call venv\Scripts\activate.bat
pip install --upgrade pip >> %LOG_FILE% 2>&1
pip install -r requirements.txt >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ❌ Failed to install dependencies. >> %LOG_FILE% 2>&1
    pause
    exit /b 1
)
echo ✅ Dependencies installed. >> %LOG_FILE% 2>&1

:: Create launcher
echo Creating launcher script... >> %LOG_FILE% 2>&1
(
echo @echo off
echo cd /d "%%~dp0"
echo set LOG_FILE=clausecompare.log
echo set PORT=8501
echo netstat -ano ^| findstr :%%PORT%% >nul
echo if %%errorlevel%%==0 (
echo     echo App is already running. Opening browser... >> %%LOG_FILE%% 2>&1
echo     start http://localhost:%%PORT%%
echo     exit /b
echo )
echo call venv\Scripts\activate.bat
echo echo Starting ClauseCompare... >> %%LOG_FILE%% 2>&1
echo start /b streamlit run app.py --server.port %%PORT%% >> %%LOG_FILE%% 2>&1
echo timeout /t 3 /nobreak >nul
echo start http://localhost:%%PORT%%
echo pause
) > run_clausecompare.bat

echo ✅ Launcher created: run_clausecompare.bat >> %LOG_FILE% 2>&1

echo.
echo 🎉 Setup complete!
echo 👉 Double‑click 'run_clausecompare.bat' to start the app.
echo    (Ollama must be installed and running separately.)
pause