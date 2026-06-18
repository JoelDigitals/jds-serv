import os
import time
import logging
import requests
from config import load_token


logger = logging.getLogger("JDSClient")


class APIClient:
    MAX_RETRIES = 2
    RETRY_DELAY = 2

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.token = load_token()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JDS-Client/2.0",
            "Accept": "application/json",
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def set_token(self, token):
        self.token = token
        self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        timeout = kwargs.pop("timeout", 120)

        for attempt in range(1 + self.MAX_RETRIES):
            try:
                resp = self.session.request(method, url, timeout=timeout, **kwargs)
                if resp.status_code == 401 and self.token:
                    logger.warning("Token abgelaufen oder ungültig")
                if resp.status_code >= 500:
                    logger.warning("Server-Fehler %d – Versuch %d", resp.status_code, attempt + 1)
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_DELAY * (attempt + 1))
                        continue
                resp.raise_for_status()
                return resp.json() if resp.text else {}

            except requests.exceptions.ConnectionError:
                logger.warning("Server nicht erreichbar: %s (Versuch %d)", url, attempt + 1)
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                return None

            except requests.exceptions.Timeout:
                logger.warning("Timeout bei %s (Versuch %d)", url, attempt + 1)
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                return None

            except requests.exceptions.HTTPError as e:
                msg = f"HTTP {e.response.status_code}"
                try:
                    detail = e.response.json()
                    msg += f" – {detail}"
                except Exception:
                    msg += f" – {e.response.text[:100]}"
                logger.warning(msg)
                return None

            except Exception as e:
                logger.error("Unerwarteter Fehler: %s – %s", url, e)
                return None

        return None

    def register(self, name, machine_id, operating_system):
        return self._request("POST", "/api/register/", json={
            "name": name,
            "machine_id": machine_id,
            "operating_system": operating_system,
        })

    def get_status(self):
        return self._request("GET", "/api/status/")

    def start_backup(self):
        return self._request("POST", "/api/backup/start/")

    def update_backup(self, job_id, data):
        return self._request("POST", f"/api/backup/{job_id}/update/", json=data)

    def upload_file(self, job_id, file_path, file_obj, extra_data=None):
        data = {"file_path": file_path}
        if extra_data:
            data.update(extra_data)
        files = {"file": (os.path.basename(file_path), file_obj, "application/octet-stream")}
        url = f"{self.base_url}/api/backup/{job_id}/upload/"

        for attempt in range(1 + self.MAX_RETRIES):
            try:
                resp = self.session.post(url, files=files, data=data, timeout=300)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.ConnectionError:
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                logger.error("Upload fehlgeschlagen (Verbindung): %s", os.path.basename(file_path))
                return None
            except requests.exceptions.Timeout:
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                logger.error("Upload Timeout: %s", os.path.basename(file_path))
                return None
            except Exception as e:
                logger.error("Upload-Fehler: %s – %s", os.path.basename(file_path), e)
                return None

        return None

    def log_event(self, level, message):
        return self._request("POST", "/api/log/", json={"level": level, "message": message})

    def check_actions(self):
        return self._request("GET", "/api/actions/")
