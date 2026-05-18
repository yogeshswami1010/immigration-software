@echo off
setlocal

:: ── Configuration ──────────────────────────────────────────
set PROJECT_DIR=D:\rio_software\Rio\rio_imm
set BACKUP_ROOT=D:\rio_backups
set PYTHON=C:\Users\yoges\AppData\Local\Programs\Python\Python311\python.exe

:: ── Timestamp ───────────────────────────────────────────────
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DATETIME=%%I
set TIMESTAMP=%DATETIME:~0,4%-%DATETIME:~4,2%-%DATETIME:~6,2%_%DATETIME:~8,2%-%DATETIME:~10,2%

:: ── Create backup folder for this run ───────────────────────
set BACKUP_DIR=%BACKUP_ROOT%\backup_%TIMESTAMP%
mkdir "%BACKUP_DIR%"
mkdir "%BACKUP_DIR%\database"
mkdir "%BACKUP_DIR%\media"
mkdir "%BACKUP_DIR%\code"

echo.
echo ============================================
echo  RIO Backup Started: %TIMESTAMP%
echo ============================================

:: ── 1. Django dumpdata (all app data as JSON) ───────────────
echo [1/4] Exporting Django data...
cd /d "%PROJECT_DIR%"
"%PYTHON%" manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 > "%BACKUP_DIR%\database\django_data.json"
if %errorlevel%==0 (
    echo       Django data exported successfully.
) else (
    echo       ERROR: Django dumpdata failed!
)

:: ── 2. SQLite database file copy ────────────────────────────
echo [2/4] Copying SQLite database...
if exist "%PROJECT_DIR%\db.sqlite3" (
    copy "%PROJECT_DIR%\db.sqlite3" "%BACKUP_DIR%\database\db.sqlite3"
    echo       SQLite file copied successfully.
) else (
    echo       WARNING: db.sqlite3 not found, skipping.
)

:: ── 3. Media files ───────────────────────────────────────────
echo [3/4] Copying media files...
if exist "%PROJECT_DIR%\media" (
    xcopy "%PROJECT_DIR%\media" "%BACKUP_DIR%\media" /E /I /Q /Y
    echo       Media files copied successfully.
) else (
    echo       WARNING: media folder not found, skipping.
)

:: ── 4. Project code (robocopy - more reliable than xcopy) ────
echo [4/4] Copying project code...
robocopy "%PROJECT_DIR%" "%BACKUP_DIR%\code" /E /XD __pycache__ .git node_modules venv env rio_backups /XF *.pyc *.pyo /NFL /NDL /NJH /NJS /NC /NS
echo       Project code copied successfully.

:: ── Done ─────────────────────────────────────────────────────
echo.
echo ============================================
echo  Backup Complete!
echo  Location: %BACKUP_DIR%
echo ============================================

:: ── Show backup size ─────────────────────────────────────────
echo.
echo Backup folder contents:
dir "%BACKUP_DIR%" /s /-c | find "File(s)"

:: ── Auto-delete backups older than 30 days ───────────────────
echo.
echo Cleaning old backups (older than 30 days)...
forfiles /p "%BACKUP_ROOT%" /d -30 /c "cmd /c if @isdir==TRUE rmdir /s /q @path" 2>nul
echo Done.

echo.
pause