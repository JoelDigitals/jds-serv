@echo off
title JDS Client Setup
echo ============================================
echo   JDS Serv - Setup Wizard
echo ============================================
echo.

:: Prüfe Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python 3.10+ von https://www.python.org/downloads/
    echo WICHTIG: "Add Python to PATH" bei der Installation aktivieren!
    pause
    exit /b 1
)

echo Starte grafischen Setup-Assistenten...
cd /d "%~dp0..\jds_client"
pip install -r requirements.txt >nul 2>&1
python installer_gui.py
if %errorlevel% neq 0 (
    echo [FEHLER] Konnte den Setup-Assistenten nicht ausführen.
    pause
    exit /b 1
)
