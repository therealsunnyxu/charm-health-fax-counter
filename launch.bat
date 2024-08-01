@echo off
setlocal

REM Step 1: Check if the virtual environment exists
if not exist "charm-health-fax-counter" (
	echo App not installed.
)
cd charm-health-fax-counter
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Please create it first.
    exit /b 1
)

REM Step 2: Activate the virtual environment
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate the virtual environment.
    exit /b 1
)

REM Step 3: Run the specified Python module
venv\Scripts\python.exe -m fax_counter.app
if %errorlevel% neq 0 (
    echo Failed to run the Python module: fax_counter.app.
    deactivate
    exit /b 1
)

echo Module fax_counter.app ran successfully.
deactivate
exit /b 0