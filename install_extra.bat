@echo off
REM Extra Dependencies Installer for product_tool
REM
REM Usage:
REM     install_extra.bat
REM
REM Install this after activating the virtual environment:
REM     venv\Scripts\activate
REM     install_extra.bat
REM

echo ================================================
echo Installing Extra Dependencies
echo ================================================

echo.
echo [1/3] Installing pdfplumber...
pip install pdfplumber
if errorlevel 1 (
    echo   Failed: pdfplumber
) else (
    echo   OK: pdfplumber
)

echo.
echo [2/3] Installing paddlepaddle...
pip install paddlepaddle==2.6.1
if errorlevel 1 (
    echo   Failed: paddlepaddle
) else (
    echo   OK: paddlepaddle
)

echo.
echo [3/3] Installing paddleocr...
pip install paddleocr==2.7.3
if errorlevel 1 (
    echo   Failed: paddleocr
) else (
    echo   OK: paddleocr
)

echo.
echo ================================================
echo Installation Complete!
echo ================================================
echo.
echo Note: paddleocr may require extra dependencies.
echo If installation fails, check your Python version compatibility.
echo.

pause