import os
import sys
import time
import logging
import platform
import argparse
import traceback

import schedule

from config import (
    get_config, save_config, save_token, save_client_data,
    load_client_data, load_token, parse_paths, parse_patterns
)
from api_client import APIClient
from backup_engine import (
    scan_files, scan_changed_files, build_new_state, save_state
)


def setup_logging(config):
    log_file = config.get("logging", "log_file", fallback="jds_client.log")
    log_level = config.get("logging", "log_level", fallback="INFO").upper()
    log_level = getattr(logging, log_level, logging.INFO)

    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(log_dir, log_file)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("JDSClient")


def register_client(api, config):
    name = config.get("client", "name", fallback=platform.node() or "Mein-PC")
    machine_id = config.get("client", "machine_id", fallback="unknown")
    if machine_id == "auto":
        from config import get_machine_id
        machine_id = str(get_machine_id())
        config.set("client", "machine_id", machine_id)

    os_name = f"{platform.system()} {platform.release()}"
    logger.info("Registriere Client: %s (ID: %s)", name, machine_id)

    for attempt in range(3):
        result = api.register(name, machine_id, os_name)
        if result and "api_token" in result:
            token = result["api_token"]
            client_id = result.get("client_id")
            save_token(token)
            save_client_data(client_id, token)
            api.set_token(token)
            save_config(config)
            logger.info("Registrierung erfolgreich! Client-ID: %s", client_id)
            return True
        logger.warning("Registrierungsversuch %d/3 fehlgeschlagen", attempt + 1)
        time.sleep(2)

    logger.error("Registrierung nach 3 Versuchen fehlgeschlagen")
    return False


def run_backup(api, config, full_backup=False):
    mode = "VOLL" if full_backup else "INKREMENTELL"
    logger.info("=== Starte Backup (%s) ===", mode)

    status = api.get_status()
    if status is None:
        logger.warning("Server nicht erreichbar – Backup wird beim nächsten Intervall wiederholt")
        api.log_event("warning", "Server nicht erreichbar, Backup verschoben")
        return

    result = api.start_backup()
    if result is None:
        logger.warning("Konnte Backup-Job nicht starten")
        return

    job_id = result.get("job_id")
    if not job_id:
        logger.warning("Keine Job-ID vom Server erhalten")
        return

    logger.info("Backup-Job #%s gestartet", job_id)

    paths = parse_paths(config.get("backup", "paths", fallback=""))
    exclude = parse_patterns(config.get("backup", "exclude_patterns", fallback=""))
    max_size_mb = int(config.get("backup", "max_file_size_mb", fallback="500"))

    logger.info("Scanne %d Pfad(e)...", len(paths))

    if full_backup:
        files, total_size = scan_files(paths, exclude, max_size_mb)
        logger.info("VOLL-Scan: %d Dateien, %.1f MB", len(files), total_size / (1024 * 1024))
    else:
        result = scan_changed_files(paths, exclude, max_size_mb)
        changed_files, prev_state, all_files = result
        files = changed_files
        total_size = sum(f["size"] for f in changed_files)

        if not changed_files:
            logger.info("Keine Änderungen seit letztem Backup")
            api.update_backup(job_id, {"status": "completed", "total_files": 0, "total_size": 0})
            api.log_event("info", "Inkrementelles Backup: Keine Änderungen – nichts zu tun")
            return

    api.update_backup(job_id, {"total_files": len(files), "total_size": total_size})

    uploaded, failed, transferred = 0, 0, 0

    for file_info in files:
        try:
            with open(file_info["path"], "rb") as f:
                up_result = api.upload_file(job_id, file_info["path"], f)

            if up_result:
                uploaded += 1
                transferred += file_info["size"]
                if uploaded % 50 == 0:
                    api.update_backup(job_id, {"transferred_size": transferred})
                    logger.info("Fortschritt: %d Dateien, %.1f MB", uploaded, transferred / (1024 * 1024))
            else:
                failed += 1
                logger.warning("Upload fehlgeschlagen: %s", file_info["name"])

        except (PermissionError, OSError) as e:
            failed += 1
            logger.warning("Nicht lesbar: %s – %s", file_info["name"], e)
        except Exception as e:
            failed += 1
            logger.error("Unerwarteter Fehler bei %s: %s", file_info["name"], e)

    final_status = "completed" if failed == 0 else "completed"
    api.update_backup(job_id, {"status": final_status, "transferred_size": transferred})

    if failed > 0:
        api.update_backup(job_id, {
            "error_message": f"{failed} von {len(files)} Dateien fehlgeschlagen"
        })

    if not full_backup and 'all_files' in locals():
        new_state = build_new_state(all_files)
        save_state(new_state)

    summary = (
        f"Backup fertig: {uploaded} Dateien, {failed} Fehler, "
        f"{(transferred / (1024 * 1024)):.1f} MB übertragen"
    )
    logger.info(summary)
    api.log_event("info", summary)


def main():
    parser = argparse.ArgumentParser(description="JDS Client – Automatisches Backup")
    parser.add_argument("--register", action="store_true", help="Client registrieren")
    parser.add_argument("--backup", action="store_true", help="Einmaliges Backup (inkrementell)")
    parser.add_argument("--full", action="store_true", help="Vollständiges Backup erzwingen")
    parser.add_argument("--daemon", action="store_true", help="Dauermodus mit Zeitplan")
    parser.add_argument("--interval", type=int, help="Intervall in Minuten")
    args = parser.parse_args()

    config = get_config()
    global logger
    logger = setup_logging(config)

    logger.info("JDS Client gestartet")
    logger.debug("Python %s / %s %s", platform.python_version(), platform.system(), platform.release())

    server_url = config.get("server", "url", fallback="http://127.0.0.1:8000")
    api = APIClient(server_url)

    client_id, token = load_client_data()
    if token:
        api.set_token(token)
        logger.info("Token geladen (Client #%s)", client_id)
    else:
        token = load_token()
        if token:
            api.set_token(token)
            logger.info("Legacy-Token geladen")

    no_token = not token
    if args.register or no_token:
        logger.info("Keine Registrierung gefunden – starte Registrierung...")
        if not register_client(api, config):
            logger.error("Registrierung fehlgeschlagen – breche ab")
            if args.register:
                sys.exit(1)

    if args.backup:
        run_backup(api, config, full_backup=args.full)
        return

    if args.daemon:
        interval = args.interval or int(config.get("client", "backup_interval_minutes", fallback="180"))
        logger.info("DAEMON-MODUS – alle %d Minuten (%.1f Std)", interval, interval / 60)

        schedule.every(interval).minutes.do(run_backup, api, config, False)

        logger.info("Erstes Backup in 10 Sekunden...")
        time.sleep(10)
        run_backup(api, config, full_backup=args.full)

        logger.info("Daemon läuft – warte auf nächstes Intervall...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)
            except KeyboardInterrupt:
                logger.info("Daemon durch Nutzer beendet")
                break
            except Exception as e:
                logger.error("Fehler im Daemon-Loop: %s\n%s", e, traceback.format_exc())
                time.sleep(60)
    else:
        run_backup(api, config, full_backup=args.full)


if __name__ == "__main__":
    logger = logging.getLogger("JDSClient")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
