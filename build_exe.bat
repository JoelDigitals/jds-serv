@echo off
title JDS Serv - Executables Bauen
echo ============================================
echo   JDS Serv - Build Executables (.exe)
echo ============================================
echo.

:: Prüfe Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python 3.10+ von https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Starte Kompilierung...
python build_executables.py
if %errorlevel% neq 0 (
    echo.
    echo [FEHLER] Beim Bauen ist ein Fehler aufgetreten.
    pause
    exit /b 1
)

echo.
pause
