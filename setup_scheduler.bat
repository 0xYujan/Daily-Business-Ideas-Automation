@echo off
echo ============================================
echo   Daily Business Ideas - Scheduler Setup
echo ============================================
echo.

REM Get the directory where this script lives
set "SCRIPT_DIR=%~dp0"

REM Find Python path
for /f "delims=" %%i in ('where python 2^>nul') do set "PYTHON_PATH=%%i" & goto :found
echo [ERROR] Python not found in PATH. Please install Python first.
pause
exit /b 1

:found
echo [INFO] Python found at: %PYTHON_PATH%
echo [INFO] Script directory: %SCRIPT_DIR%
echo.

REM Delete old task if exists
schtasks /delete /tn "DailyBusinessIdeas" /f >nul 2>&1

REM Create the scheduled task
REM Runs daily at 6:00 AM, starts even if on battery, wakes computer
schtasks /create ^
  /tn "DailyBusinessIdeas" ^
  /tr "\"%PYTHON_PATH%\" \"%SCRIPT_DIR%daily_ideas_sender.py\"" ^
  /sc daily ^
  /st 06:00 ^
  /rl HIGHEST ^
  /f

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   [SUCCESS] Task scheduled successfully!
    echo   Name: DailyBusinessIdeas
    echo   Time: Every day at 6:00 AM
    echo   Script: %SCRIPT_DIR%daily_ideas_sender.py
    echo ============================================
    echo.
    echo To verify, run: schtasks /query /tn "DailyBusinessIdeas"
    echo To run now:     schtasks /run /tn "DailyBusinessIdeas"
    echo To delete:      schtasks /delete /tn "DailyBusinessIdeas" /f
) else (
    echo.
    echo [ERROR] Failed to create scheduled task.
    echo [TIP]  Try running this script as Administrator.
)

echo.
pause
