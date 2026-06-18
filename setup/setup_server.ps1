Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  JDS Serv - Server Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Prüfe Python
try {
    $pyVersion = python --version
    Write-Host "[OK] Python gefunden: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Python ist nicht installiert!" -ForegroundColor Red
    exit 1
}

# Virtuelle Umgebung
$venvPath = Join-Path $PSScriptRoot "..\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Erstelle virtuelle Umgebung..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "[OK] Virtuelle Umgebung erstellt" -ForegroundColor Green
}

# Aktiviere venv und installiere Abhängigkeiten
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
. $activateScript

Write-Host "Installiere Abhängigkeiten..." -ForegroundColor Yellow
pip install -r (Join-Path $PSScriptRoot "..\jds_web\requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FEHLER] Installation fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Abhängigkeiten installiert" -ForegroundColor Green

# .env-Datei
$envFile = Join-Path $PSScriptRoot "..\jds_web\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $PSScriptRoot "..\jds_web\.env.example") $envFile
    Write-Host "[HINWEIS] .env-Datei erstellt - bitte anpassen!" -ForegroundColor Yellow
}

# Migrationen
Write-Host "Führe Datenbank-Migrationen durch..." -ForegroundColor Yellow
Set-Location (Join-Path $PSScriptRoot "..\jds_web")
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FEHLER] Migration fehlgeschlagen" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Migrationen durchgeführt" -ForegroundColor Green

# Admin erstellen
Write-Host ""
$createAdmin = Read-Host "Admin-Benutzer erstellen? (J/N)"
if ($createAdmin -eq "J") {
    python manage.py createsuperuser
}

# Statische Dateien
Write-Host "Sammle statische Dateien..." -ForegroundColor Yellow
python manage.py collectstatic --noinput
Write-Host "[OK] Statische Dateien gesammelt" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup abgeschlossen!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server starten mit:" -ForegroundColor White
Write-Host "  cd jds_web" -ForegroundColor Gray
Write-Host "  python manage.py runserver 0.0.0.0:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "Admin-Oberfläche:" -ForegroundColor White
Write-Host "  http://localhost:8000/admin/" -ForegroundColor Gray
Write-Host ""
Write-Host "Dashboard:" -ForegroundColor White
Write-Host "  http://localhost:8000/" -ForegroundColor Gray
Write-Host ""
pause
