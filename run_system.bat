@echo off
echo Starting Expense Management System...
cd /d "%~dp0backend"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
start http://127.0.0.1:8000
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
