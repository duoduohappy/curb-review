@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Please install Python 3.10 or newer from https://www.python.org/downloads/
  pause
  exit /b 1
)
echo Open http://127.0.0.1:18765 in your browser after the server starts.
python server.py
pause
