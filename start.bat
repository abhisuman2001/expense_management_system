@echo off
echo Starting Expense Management System...

echo.
echo Starting Backend Server...
cd backend
start "Backend" cmd /k "python run.py"

echo.
echo Starting Frontend Development Server...
cd ..\frontend
start "Frontend" cmd /k "npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window...
pause > nul