@echo off
cd frontend
call npm install
cd ..

echo Iniciando backend...
start "Backend" cmd /c "uvicorn backend.app.main:app --reload --port 8000"

echo Iniciando frontend...
start "Frontend" cmd /c "cd frontend && npm run dev"
