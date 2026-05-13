@echo off
echo Stopping Product Tool API...
taskkill /f /im uvicorn.exe 2>nul
echo Done.
pause
