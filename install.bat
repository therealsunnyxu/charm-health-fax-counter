@echo off
setlocal

REM Step 1: Check if python is in the system path
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in the system path.
    exit /b 1
)

REM Step 2: Create a virtual environment
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create a virtual environment.
    exit /b 1
)

REM Step 3: Install requirements
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate the virtual environment.
    exit /b 1
)
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements from requirements.txt.
    deactivate
    exit /b 1
)

echo All steps completed successfully.
deactivate
exit /b 0
