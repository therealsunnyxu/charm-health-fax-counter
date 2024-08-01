@echo off
setlocal

REM Step 1: Check if git is in the system path
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git is not installed or not in the system path.
    exit /b 1
)

REM Step 2: Check if .git exists
if not exist ".git" (
    echo .git directory does not exist. Cloning repository.
    git clone https://github.com/therealsunnyxu/charm-health-fax-counter.git
    if %errorlevel% neq 0 (
        echo Failed to clone the repository.
        exit /b 1
    )
) else (
    echo .git directory exists. Fetching updates.
    git pull
    if %errorlevel% neq 0 (
        echo Failed to fetch updates from the repository.
        exit /b 1
    )
)

REM Step 3: Check if the virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Please create it first.
    exit /b 1
)

REM Step 4: Activate the virtual environment
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate the virtual environment.
    exit /b 1
)

REM Step 5: Update the requirements
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements from requirements.txt.
    deactivate
    exit /b 1
)

echo Repository and requirements are up to date.
deactivate
exit /b 0