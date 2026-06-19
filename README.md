# JDS Serv — Automatisches Backup-System

Backups von Mitarbeiter-PCs automatisch auf einen zentralen Server sichern. Kostenlos hostbar auf Render.com.

---

## Schritt 1: Code auf GitHub laden

Öffne eine **PowerShell** im Projektordner und führe aus:

```powershell
# Git initialisieren
git init
git add .
git commit -m "JDS Serv"

# Repo auf github.com erstellen (leer, ohne README)
# Dann:
git remote add origin https://github.com/DEIN-USERNAME/jds-serv.git
git branch -M main
git push -u origin main
```

---

## Schritt 2: Kostenlosen Render-Server aufsetzen

1. Gehe auf **[dashboard.render.com](https://dashboard.render.com)** → mit GitHub anmelden
2. Klicke **"New" → "Web Service"**
3. Wähle dein GitHub-Repo `jds-serv` aus
4. Fülle die Felder **exakt** so aus:

| Feld | Wert |
|------|-------|
| **Name** | `deine-app` (bestimmt deine URL: `deine-app.onrender.com`) |
| **Region** | Frankfurt (EU) |
| **Branch** | `main` |
| **Build Command** | `pip install -r jds_web/requirements.txt` |
| **Start Command** | `cd jds_web && python manage.py collectstatic --noinput && gunicorn jds_web.wsgi:application --preload --workers=2 --threads=2 --timeout=120 --bind=0.0.0.0:$PORT` |
| **Instance Type** | **Free** |

5. Ganz unten: **"Add Disk"**
   - **Name**: `backup-data`
   - **Mount Path**: `/opt/render/project/src/jds_web/media`
   - **Size**: `10 GB`

6. **Environment Variables**: **ALLE FELDER LEER LASSEN!** Keine Env-Variablen nötig.

7. Klicke **"Create Web Service"** — Render baut und deployed jetzt (~3 Minuten)

8. Dein Server läuft unter: **`https://deine-app.onrender.com`**

9. Admin-Login: **`admin`** / Passwort: **`admin123`** → sofort ändern unter `/admin/`

---

## Schritt 3: Server wach halten (Fastcron)

Render Free Tier schläft nach **15 Minuten Inaktivität** ein. Mit Fastcron bleibt der Server dauerhaft wach:

1. Gehe auf **[fastcron.com](https://fastcron.com)** → kostenlos registrieren
2. **"New Cron Job"** anlegen:
   - **URL**: `https://deine-app.onrender.com/api/actions/`
   - **Interval**: `Every 10 minutes`
   - Klicke **"Create"**

Der Ping alle 10 Minuten hält deinen Render-Server dauerhaft aktiv — **kostenlos**.

---

## Schritt 4: Client auf Mitarbeiter-PCs installieren

### Option A: Python direkt (einfach)

Auf dem Mitarbeiter-PC:

```powershell
cd jds_client
pip install -r requirements.txt
python installer_gui.py
```

Der grafische Setup-Assistent öffnet sich → Server-URL `https://deine-app.onrender.com` eintragen → PC-Name + Ordner wählen → auf **Installieren** klicken. Fertig.

### Option B: Als .exe bauen (für Endnutzer ohne Python)

Auf deinem Admin-PC einmalig:

```powershell
python build_executables.py
```

Erzeugt `build_dist/JDS-Client-Installer.exe` — diese Datei an Mitarbeiter verteilen. Doppelklick → Assistent → Fertig.

---

## Projektstruktur

```
jds-serv/
├── jds_web/                # Django Web-App (Server)
│   ├── jds_web/settings.py # Konfiguration (SQLite, kein Env)
│   ├── backup_app/         # Models, Views, API, Admin
│   └── manage.py           # Django Kommandos
├── jds_client/             # Windows Client
│   ├── installer_gui.py    # GUI-Setup-Assistent
│   ├── admin_portal.py     # Admin-Desktop-App
│   ├── main.py             # Backup-Agent (CLI)
│   └── config.ini          # Client-Konfiguration
├── render.yaml             # Render Blueprint (optional)
├── Procfile                # Render Start-Befehl
├── build_executables.py    # Baut .exe-Dateien
├── build_exe.bat           # Einfacher Doppelklick-Build
└── README.md               # Diese Datei
```

---

## Client-Befehle

```powershell
python main.py --backup             # Einmaliges Backup (inkrementell)
python main.py --backup --full      # Vollständiges Backup
python main.py --daemon             # Dauermodus (alle 3 Std)
python main.py --register           # Nur am Server registrieren
```

---

## Was das System kann

- **Inkrementelle Backups**: Nur geänderte Dateien werden hochgeladen
- **Protokollführung**: Jeder Job, jede Datei, jeder Fehler wird geloggt
- **Metadaten-Export**: Alle Backup-Daten als JSON herunterladen
- **Admin-Oberfläche**: Django-Admin mit voller Kontrolle
- **Auto-Cleanup**: Backups älter als 5 Tage werden automatisch gelöscht
- **Unternehmens-Login**: Mehrere Firmen mit eigenen Clients
- **Windows Task Scheduler**: Automatische Einrichtung bei Installation
- **Null Konfiguration**: Keine Env-Variablen, kein Supabase nötig
