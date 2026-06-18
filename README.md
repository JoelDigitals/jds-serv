# JDS Serv - Backup-Management-System

Automatische Backups für Unternehmen — von Mitarbeiter-Laptops/PCs auf einen zentralen Server. Inklusive **Protokollführung, Metadaten-Export, Client-Verwaltung, Admin-Portal und vollständiger Unternehmensverwaltung**.

## Architektur

```
┌──────────────────────────┐     ┌────────────────────────┐     ┌─────────────────┐
│  JDS-Client-Installer.exe │────▶│  Django Web Server      │────▶│  Supabase       │
│  (Endnutzer, 1-Klick)     │     │  (jds_web/) auf Render  │     │  (PostgreSQL)   │
│                           │     │                         │     │                 │
│  - Inkrementelles Backup  │     │  - Web-Dashboard         │     │  - Unternehmen  │
│    (nur geänderte Dateien) │     │  - Client-Verwaltung     │     │  - Clients      │
│  - Alle 3 Std automatisch │     │  - Metadaten-Export JSON │     │  - Backups      │
│  - Windows Scheduler      │     │  - REST API              │     │  - Datei-Hashes │
│  - Verbindungstest        │     │  - Admin-Oberfläche      │     │  - Logs         │
├──────────────────────────┤     │  - CRON-Cleanup (5 Tage) │     │  - 5 Tage Daten │
│  JDS-Admin-Portal.exe     │────▶│                         │     │                 │
│  (Admin, Verwaltung)      │     │  Protokollführung:       │     └─────────────────┘
│                           │     │  - BackupLog (Info/Warn/
│  - Client-Übersicht       │     │    Error/Debug)
│  - Metadaten herunterladen│     │  - BackupFile Hashes
│  - JSON-Export            │     │  - Auto-Löschung
└──────────────────────────┘     └────────────────────────┘
```

## Wichtige Features

### Protokollführung & Metadaten
- **Jeder Backup-Job** protokolliert Dateinamen, Pfade, SHA-256-Hashes, Dateigrößen und Timestamps.
- **Backup-Logs** (Infos, Warnungen, Fehler) werden für jeden Client gespeichert.
- **JSON-Metadaten-Export**: Admin kann alle Backup-Daten (Clients, Jobs, Dateien, Hashes) als eine einzige `.json`-Datei herunterladen — perfekt für Audits und externe Sicherung.

### Unternehmen & Clients
- **Unternehmen** werden im Django-Admin oder per Admin-Portal angelegt.
- **UserProfile** verknüpft Django-Benutzer mit einem Unternehmen → jeder Admin sieht nur seine eigenen Clients & Daten.
- Clients können über die **Web-Oberfläche** (`Client anlegen`) oder das **Admin-Portal** erstellt werden.

### Inkrementelles Backup (nur geänderte Dateien)
- **Alle 3 Stunden (180 Min)** scannt der Client nur geänderte und neue Dateien (per mtime-Vergleich).
- Die bereits gesicherten, unveränderten Dateien werden **nicht erneut hochgeladen**.
- Mit `--full` kann ein vollständiges Backup erzwungen werden.
- Ein **Backup-State** (`.jds_backup_state.json`) wird lokal gespeichert.

### Datenspeicherung (max. 5 Tage)
- **Standard: Backups werden nach 5 Tagen automatisch gelöscht** (inkl. Dateien von der Festplatte).
- Konfigurierbar in den Unternehmenseinstellungen (z.B. auf 7 Tage).
- Render-Cron-Job führt den Cleanup alle 6 Stunden automatisch aus.

### Admin-Portal (.exe)
- Eigenständige Desktop-App für Administratoren (kein Python nötig).
- Login mit Django-Benutzername + Passwort.
- Zeigt alle Clients des eigenen Unternehmens in einer übersichtlichen Tabelle.
- **"Metadaten exportieren"** speichert eine vollständige JSON-Datei lokal auf dem Admin-PC.

---

## Schnellstart

### 1. Server & Datenbank

```powershell
# Setup lokal
cd setup
powershell -ExecutionPolicy Bypass -File setup_server.ps1
cd ..\jds_web
python manage.py runserver 0.0.0.0:8000
```

Supabase-Datenbank: SQL aus `deploy/supabase_setup.sql` im Supabase SQL Editor ausführen.

### 1b. Deployment auf Render (kostenlos)

```powershell
# 1. Repo auf GitHub pushen
# 2. Auf dashboard.render.com: "New" → "Blueprint" → Repo auswählen
# 3. render.yaml wird automatisch erkannt
# 4. Supabase-Umgebungsvariablen (SUPABASE_DB_PASSWORD, SUPABASE_DB_HOST) manuell setzen
# 5. Nach dem ersten Deploy: Render Shell öffnen und ausführen:
#    cd jds_web && python manage.py createsuperuser
```

Der Render-Blueprint (`deploy/render.yaml`) erstellt:
- **Web Service** `jds-serv` — Django App mit 10 GB Disk für Backups
- **Cron Job** `jds-cleanup` — Löscht alle 6 Std. Backups älter als 5 Tage

### 2. Executables (.exe) bauen

```powershell
# Doppelklick auf build_exe.bat (oder:)
python build_executables.py
```

Erzeugt im Ordner `build_dist/`:
- **JDS-Client-Installer.exe** — Mitarbeiter-Installer (Doppelklick → Assistent → Fertig)
- **JDS-Backup-Agent.exe** — Hintergrund-Backup-Prozess
- **JDS-Admin-Portal.exe** — Admin-Verwaltungs-App

### 3. Client auf Mitarbeiter-PCs installieren

Der Mitarbeiter öffnet `JDS-Client-Installer.exe` und folgt dem Assistenten:
1. Begrüßung
2. Server-URL + Verbindungstest
3. PC-Name + Ordner wählen + Backup-Intervall (empfohlen: 180 Min = alle 3 Std)
4. Klick auf **Installieren** → automatische Einrichtung + Task Scheduler

**CLI-Nutzung** (fortgeschritten):
```powershell
python main.py --backup           # Inkrementell (nur geänderte Dateien)
python main.py --backup --full    # Vollständiges Backup erzwingen
python main.py --daemon           # Hintergrund-Daemon (alle 3 Std)
python main.py --daemon --interval 120  # Daemon mit 2-Std-Intervall
```

### 4. Admin-Portal starten

Der Admin öffnet `JDS-Admin-Portal.exe`:
1. Server-URL und Django-Login eingeben
2. Client-Übersicht ansehen
3. **Metadaten exportieren** → JSON-Datei speichern

---

## API Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| POST | `/api/register/` | Client registrieren |
| POST | `/api/login/` | Admin-Login (gibt DRF-Token zurück) |
| GET | `/api/status/` | Client-Status abrufen |
| GET | `/api/clients/` | Alle Clients des Unternehmens |
| POST | `/api/backup/start/` | Backup starten |
| POST | `/api/backup/<id>/update/` | Backup-Status aktualisieren |
| POST | `/api/backup/<id>/upload/` | Datei hochladen |
| POST | `/api/log/` | Log-Ereignis senden |
| GET | `/api/metadata/export/` | **Metadaten als JSON exportieren** |

---

## Projektstruktur

```
JDS-Serv/
├── jds_web/               # Django Web-App
│   ├── jds_web/           # Django Projekteinstellungen
│   ├── backup_app/        # Backup-App (Models, Views, API)
│   ├── media/backups/     # Gesicherte Dateien (max 5 Tage)
│   └── manage.py
├── jds_client/            # Windows Client-Anwendungen
│   ├── installer_gui.py   # Moderner GUI-Installer (Tkinter)
│   ├── admin_portal.py    # Admin-Portal GUI (Tkinter)
│   ├── main.py            # Backup-Agent (CLI/Hintergrund)
│   ├── backup_engine.py   # Datei-Scan & Hashing
│   ├── api_client.py      # REST API Client
│   ├── config.py          # Konfigurationsverwaltung
│   └── config.ini         # Standard-Konfiguration
├── build_executables.py   # Baut alle .exe-Dateien
├── build_exe.bat          # Einfacher Doppelklick-Build
├── deploy/                # Deployment-Konfiguration
│   ├── render.yaml        # Render.com Deployment
│   ├── Procfile           # Prozess-Definition
│   └── supabase_setup.sql # Supabase Tabellen-Setup
└── setup/                 # Setup-Skripte
    ├── setup_server.ps1   # Server-Einrichtung
    └── install_client.bat # Client-Installationsstarter
```
