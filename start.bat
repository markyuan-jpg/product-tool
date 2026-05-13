@echo off
cd /d "%~dp0backend"
echo Starting Product Tool API...
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --timeout-keep-alive 120
pause
