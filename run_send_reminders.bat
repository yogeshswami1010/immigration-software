@echo off
REM Replace with your project directory
set PROJECT_DIR=D:\SOFTWARE\Rio
REM Replace with your virtual environment directory
set VENV_DIR=D:\SOFTWARE\Rio\virtualenv

REM Navigate to project directory
cd %PROJECT_DIR%
IF ERRORLEVEL 1 (
    echo "Error: Project directory not found."
    pause
    exit /b
)

REM Activate virtual environment
call %VENV_DIR%\Scripts\activate.bat
IF ERRORLEVEL 1 (
    echo "Error: Virtual environment activation failed."
    pause
    exit /b
)

REM Navigate to app directory (if applicable)
cd rio_imm
IF ERRORLEVEL 1 (
    echo "Error: App directory not found."
    pause
    exit /b
)

REM Run the Django development server
python manage.py send_reminders
