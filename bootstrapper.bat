@echo off
title Secure Video Player - Full Setup Bootstrapper
cls
setlocal

set SCRIPT_DIR=%~dp0
set logfile="%SCRIPT_DIR%setup_log.txt"
echo Starting Setup Process > "%logfile%"

:: Function to log messages
:log_message
echo [%DATE% %TIME%] %* >> "%logfile%"
exit /b

:: Step 1: Check for Python (more robust)
call :log_message "Checking Python installation..."
where python >nul 2>&1
if %errorlevel% neq 0 (
    call :log_message "Python not found. Downloading installer..."
    set "python_version=3.11.5"
    set "python_arch=amd64"
    set "python_installer=python-%python_version%-%python_arch%.exe"
    set "python_url=https://www.python.org/ftp/python/%python_version%/%python_installer%"

    if not exist "%SCRIPT_DIR%python-installer.exe" (
        call :log_message "Failed to download Python installer."
        pause
        exit /b
    )

    call :log_message "Installing Python..."
    start /wait "" "%SCRIPT_DIR%python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1
    if %errorlevel% neq 0 (
        call :log_message "Python installation failed."
        pause
        exit /b
    )
    call :log_message "Python installed successfully. You might need to restart your command prompt or system for changes to fully take effect."
) else (
    call :log_message "Python is already installed."
)

:: Step 2: Ensure pip is installed and updated
call :log_message "Checking and updating pip..."
python -m ensurepip >> "%logfile%" 2>&1
if %errorlevel% neq 0 (
    call :log_message "Pip installation failed."
    pause
    exit /b
)
python -m pip install --upgrade pip >> "%logfile%" 2>&1
if %errorlevel% neq 0 (
    call :log_message "Pip upgrade failed."
    pause
    exit /b
)
call :log_message "Pip is up to date."

:: Step 3: Install dependencies from requirements.txt
call :log_message "Installing dependencies from requirements.txt..."

:: Create requirements.txt if it doesn't exist in the same directory as the script
if not exist "%SCRIPT_DIR%requirements.txt" (
    echo pynput>=1.7.1> "%SCRIPT_DIR%requirements.txt"
    echo python-vlc>> "%SCRIPT_DIR%requirements.txt"
    echo pillow>> "%SCRIPT_DIR%requirements.txt"
    echo pywin32>> "%SCRIPT_DIR%requirements.txt"
    echo pyautogui>> "%SCRIPT_DIR%requirements.txt"
    call :log_message "Created default requirements.txt in the script directory."
)

python -m pip install -r "%SCRIPT_DIR%requirements.txt" >> "%logfile%" 2>&1
if %errorlevel% neq 0 (
    call :log_message "Dependency installation failed. Check requirements.txt and ensure you have a stable internet connection."
    pause
    exit /b
)
call :log_message "Dependencies installed successfully."

:: Step 4: Run configurator
call :log_message "Starting Configurator..."
start "" pythonw "%SCRIPT_DIR%configurator.py"

endlocal
exit /b