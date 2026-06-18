import os
import json
import fnmatch
import hashlib
import logging
from pathlib import Path


logger = logging.getLogger("JDSClient")

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".jds_backup_state.json")


def should_exclude(file_path, exclude_patterns):
    name = os.path.basename(file_path)
    for pattern in exclude_patterns:
        p = pattern.strip()
        if not p:
            continue
        if fnmatch.fnmatch(name, p):
            return True
        if p in file_path:
            return True
    return False


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, IOError):
            logger.warning("Backup-State beschädigt – starte mit leerem State")
    return {}


def save_state(state):
    try:
        state_dir = os.path.dirname(STATE_FILE)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        logger.error("State konnte nicht gespeichert werden: %s", e)


def _collect_files(paths, exclude_patterns, max_bytes):
    files = []
    for base_path in paths:
        base = Path(base_path)
        if not base.exists():
            logger.warning("Pfad existiert nicht: %s", base_path)
            continue

        try:
            for entry in base.rglob("*"):
                try:
                    if should_exclude(str(entry), exclude_patterns):
                        continue
                    if not entry.is_file():
                        continue
                    try:
                        stat = entry.stat()
                        size = stat.st_size
                        mtime = stat.st_mtime
                    except (OSError, PermissionError):
                        continue

                    if size > max_bytes:
                        continue
                    if size == 0:
                        continue

                    files.append({
                        "path": str(entry),
                        "size": size,
                        "name": entry.name,
                        "mtime": mtime,
                    })
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError) as e:
            logger.warning("Kann Pfad nicht scannen: %s – %s", base_path, e)
            continue

    return files


def scan_files(paths, exclude_patterns, max_size_mb=500):
    max_bytes = max_size_mb * 1024 * 1024
    files = _collect_files(paths, exclude_patterns, max_bytes)
    total_size = sum(f["size"] for f in files)
    return files, total_size


def scan_changed_files(paths, exclude_patterns, max_size_mb=500):
    prev_state = load_state()
    max_bytes = max_size_mb * 1024 * 1024
    all_files = _collect_files(paths, exclude_patterns, max_bytes)

    changed = []
    unchanged = 0
    current_paths = set()

    for f in all_files:
        current_paths.add(f["path"])
        key = f["path"].replace("\\", "/")

        prev = prev_state.get(key)
        if prev is None:
            changed.append(f)
        elif isinstance(prev, dict):
            if prev.get("size") != f["size"] or prev.get("mtime") != f["mtime"]:
                changed.append(f)
            else:
                unchanged += 1
        else:
            changed.append(f)

    deleted_count = len(set(prev_state.keys()) - {p.replace("\\", "/") for p in current_paths})

    logger.info(
        "Scan: %d total | %d geändert | %d unverändert | %d gelöscht",
        len(all_files), len(changed), unchanged, deleted_count
    )

    return changed, prev_state, all_files


def build_new_state(all_files):
    state = {}
    for f in all_files:
        key = f["path"].replace("\\", "/")
        state[key] = {"size": f["size"], "mtime": f["mtime"]}
    return state


def compute_hash(file_path):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error("Hash-Fehler bei %s: %s", file_path, e)
        return None
