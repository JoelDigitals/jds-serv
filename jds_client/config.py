import os
import configparser
import platform
import uuid


CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
TOKEN_FILE = os.path.join(CONFIG_DIR, ".jds_token")
DATA_FILE = os.path.join(CONFIG_DIR, ".jds_data")


DEFAULT_CONFIG = {
    "server": {
        "url": "http://127.0.0.1:8000",
        "register_url": "http://127.0.0.1:8000/api/register/",
    },
    "client": {
        "name": platform.node() or "Mein-PC",
        "machine_id": "auto",
        "backup_interval_minutes": "180",
    },
    "backup": {
        "paths": os.path.join(os.environ.get("USERPROFILE", "C:\\Users"), "Documents"),
        "exclude_patterns": "*.tmp, *.log, node_modules, .git, __pycache__",
        "max_file_size_mb": "500",
    },
    "logging": {
        "log_file": "jds_client.log",
        "log_level": "INFO",
    },
}


def get_machine_id():
    try:
        return str(uuid.uuid5(
            uuid.NAMESPACE_DNS,
            platform.node() + "_" + os.environ.get("USERNAME", "unknown")
        ))
    except Exception:
        return str(uuid.uuid4())


def _create_default_config():
    config = configparser.ConfigParser()
    for section, items in DEFAULT_CONFIG.items():
        config.add_section(section)
        for key, value in items.items():
            config.set(section, key, value)
    try:
        with open(CONFIG_FILE, "w") as f:
            config.write(f)
    except Exception:
        pass
    return config


def get_config():
    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):
        config = _create_default_config()
    else:
        try:
            config.read(CONFIG_FILE, encoding="utf-8")
        except Exception:
            config = _create_default_config()

    for section in DEFAULT_CONFIG:
        if not config.has_section(section):
            config.add_section(section)
        for key, value in DEFAULT_CONFIG[section].items():
            if not config.has_option(section, key):
                config.set(section, key, value)

    if config.get("client", "machine_id", fallback="auto") == "auto":
        config.set("client", "machine_id", get_machine_id())

    return config


def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            config.write(f)
    except Exception as e:
        pass


def save_token(token):
    try:
        with open(TOKEN_FILE, "w") as f:
            f.write(token.strip())
    except Exception:
        pass


def load_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return f.read().strip()
        except Exception:
            pass
    return None


def save_client_data(client_id, token):
    try:
        with open(DATA_FILE, "w") as f:
            f.write(f"{client_id}\n{token}")
    except Exception:
        pass


def load_client_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                lines = f.read().strip().split("\n")
                if len(lines) >= 2:
                    return lines[0], lines[1]
        except Exception:
            pass
    return None, None


def parse_paths(paths_str):
    if not paths_str:
        return [os.path.join(os.environ.get("USERPROFILE", "C:\\Users"), "Documents")]
    paths = []
    for p in paths_str.split(","):
        p = p.strip()
        if p:
            paths.append(p)
    return paths if paths else [os.path.join(os.environ.get("USERPROFILE", "C:\\Users"), "Documents")]


def parse_patterns(patterns_str):
    if not patterns_str:
        return ["*.tmp", "*.log", "node_modules", ".git", "__pycache__"]
    return [p.strip() for p in patterns_str.split(",") if p.strip()]
