import os
import sys
import time
import tkinter as tk
from tkinter import messagebox, filedialog
import tkinter.ttk as ttk
import platform
import uuid
import subprocess
import requests
import configparser

BG_DARK = "#0f172a"
BG_CARD = "#1e293b"
TEXT_LIGHT = "#f8fafc"
TEXT_MUTED = "#94a3b8"
ACCENT_BLUE = "#3b82f6"
ACCENT_HOVER = "#2563eb"
ACCENT_GREEN = "#10b981"
ACCENT_RED = "#ef4444"
BORDER_COLOR = "#334155"


class ModernButton(tk.Button):
    def __init__(self, master, text, command=None, bg=ACCENT_BLUE, fg=TEXT_LIGHT, active_bg=ACCENT_HOVER, **kwargs):
        super().__init__(
            master, text=text, command=command, bg=bg, fg=fg,
            activebackground=active_bg, activeforeground=TEXT_LIGHT,
            bd=0, cursor="hand2", font=("Segoe UI", 11, "bold"),
            padx=20, pady=8, relief="flat", **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=active_bg))
        self.bind("<Leave>", lambda e: self.config(bg=bg))


class ModernInput(tk.Entry):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, bg=BG_CARD, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
            bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_BLUE, relief="flat", font=("Segoe UI", 11), **kwargs
        )


def get_default_paths():
    up = os.environ.get("USERPROFILE", "C:\\Users")
    docs = os.path.join(up, "Documents")
    desktop = os.path.join(up, "Desktop")
    parts = []
    if os.path.isdir(docs):
        parts.append(docs)
    if os.path.isdir(desktop):
        parts.append(desktop)
    return ", ".join(parts) if parts else up


def get_machine_id():
    try:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node() + "_" + os.environ.get("USERNAME", "unknown")))
    except Exception:
        return str(uuid.uuid4())


class JDSInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JDS Serv - Client Installer")
        self.geometry("620x460")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.current_step = 1
        self.steps_data = {
            "server_url": "https://deine-app.onrender.com",
            "client_name": platform.node() or "Mein-PC",
            "backup_paths": get_default_paths(),
            "interval": "180",
        }

        self.header_frame = tk.Frame(self, bg=BG_DARK, height=70)
        self.header_frame.pack(fill="x", side="top", pady=(20, 10))
        self.title_label = tk.Label(self.header_frame, text="JDS Backup Setup Wizard",
                                    font=("Segoe UI", 18, "bold"), bg=BG_DARK, fg=TEXT_LIGHT)
        self.title_label.pack()
        self.subtitle_label = tk.Label(self.header_frame, text="Schritt 1 von 4: Willkommen",
                                       font=("Segoe UI", 10), bg=BG_DARK, fg=TEXT_MUTED)
        self.subtitle_label.pack()

        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill="x", padx=40, pady=10)

        self.content_frame = tk.Frame(self, bg=BG_DARK)
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=10)

        self.bottom_frame = tk.Frame(self, bg=BG_DARK, height=80)
        self.bottom_frame.pack(fill="x", side="bottom", pady=20, padx=40)

        self.btn_prev = ModernButton(self.bottom_frame, text="Zurück", command=self.prev_step,
                                     bg=BG_CARD, active_bg=BORDER_COLOR, fg=TEXT_LIGHT)
        self.btn_prev.pack(side="left")
        self.btn_prev.pack_forget()

        self.btn_next = ModernButton(self.bottom_frame, text="Weiter", command=self.next_step)
        self.btn_next.pack(side="right")

        self.load_step(1)

    def load_step(self, step):
        self.current_step = step
        for w in self.content_frame.winfo_children():
            w.destroy()

        if step == 1:
            self.subtitle_label.config(text="Schritt 1 von 4: Willkommen bei JDS Serv")
            self.btn_prev.pack_forget()
            self.btn_next.config(text="Starten")
            self._show_welcome()
        elif step == 2:
            self.subtitle_label.config(text="Schritt 2 von 4: Server-Verbindung einrichten")
            self.btn_prev.pack(side="left")
            self.btn_next.config(text="Weiter")
            self._show_server()
        elif step == 3:
            self.subtitle_label.config(text="Schritt 3 von 4: Backup-Einstellungen festlegen")
            self.btn_prev.pack(side="left")
            self.btn_next.config(text="Weiter")
            self._show_backup()
        elif step == 4:
            self.subtitle_label.config(text="Schritt 4 von 4: Installation & Registrierung")
            self.btn_prev.pack_forget()
            self.btn_next.config(text="Fertigstellen")
            self._show_install()

    def prev_step(self):
        if self.current_step > 1:
            self.load_step(self.current_step - 1)

    def next_step(self):
        if self.current_step == 2:
            url = self.entry_server_url.get().strip()
            if not url:
                messagebox.showerror("Fehler", "Bitte gib eine Server-URL ein!")
                return
            self.steps_data["server_url"] = url.rstrip("/")
        elif self.current_step == 3:
            name = self.entry_client_name.get().strip()
            paths = self.entry_paths.get().strip()
            interval = self.entry_interval.get().strip()
            if not name:
                messagebox.showerror("Fehler", "Bitte gib einen PC-Namen ein!")
                return
            if not paths:
                messagebox.showerror("Fehler", "Bitte gib mindestens einen Ordner an!")
                return
            if not interval or not interval.isdigit():
                messagebox.showerror("Fehler", "Bitte gib ein gültiges Intervall in Minuten ein!")
                return
            self.steps_data["client_name"] = name
            self.steps_data["backup_paths"] = paths
            self.steps_data["interval"] = interval

        if self.current_step < 4:
            self.load_step(self.current_step + 1)
        else:
            self.destroy()

    def _show_welcome(self):
        tk.Label(self.content_frame, text="Willkommen beim JDS Backup Client-Installer!",
                 font=("Segoe UI", 14, "bold"), bg=BG_DARK, fg=TEXT_LIGHT,
                 wraplength=540, justify="center").pack(pady=(20, 10))
        tk.Label(self.content_frame,
                 text="Dieser Assistent richtet die automatische Backup-Anwendung "
                      "auf deinem PC ein.\n\nAlle deine wichtigen Ordner werden "
                      "vollautomatisch alle 3 Stunden auf dem JDS-Server gesichert.\n\n"
                      "Die Installation erfordert keine Vorkenntnisse – "
                      "einfach den Anweisungen folgen.",
                 font=("Segoe UI", 11), bg=BG_DARK, fg=TEXT_MUTED,
                 wraplength=500, justify="center").pack(pady=10)

    def _show_server(self):
        tk.Label(self.content_frame, text="Trage hier die Adresse deines JDS-Servers ein.",
                 font=("Segoe UI", 11), bg=BG_DARK, fg=TEXT_MUTED,
                 wraplength=500, justify="left").pack(anchor="w", pady=(10, 20))
        tk.Label(self.content_frame, text="Server-URL (z.B. https://deine-app.onrender.com)",
                 font=("Segoe UI", 10, "bold"), bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w")
        self.entry_server_url = ModernInput(self.content_frame)
        self.entry_server_url.insert(0, self.steps_data["server_url"])
        self.entry_server_url.pack(fill="x", pady=(5, 15))
        ModernButton(self.content_frame, text="Verbindung testen",
                     command=self._test_connection, bg=BG_CARD,
                     active_bg=BORDER_COLOR).pack(anchor="w")
        self.lbl_status = tk.Label(self.content_frame, text="", font=("Segoe UI", 10),
                                   bg=BG_DARK, fg=TEXT_LIGHT)
        self.lbl_status.pack(anchor="w", pady=10)

    def _test_connection(self):
        url = self.entry_server_url.get().strip().rstrip("/")
        if not url:
            self.lbl_status.config(text="Bitte gib eine gültige URL ein.", fg=ACCENT_RED)
            return
        self.lbl_status.config(text="Verbindung wird geprüft...", fg=TEXT_MUTED)
        self.update()
        try:
            resp = requests.get(f"{url}/api/actions/", timeout=5)
            if resp.status_code in (200, 401, 403):
                self.lbl_status.config(text="Server ist online – Verbindung OK!", fg=ACCENT_GREEN)
            else:
                self.lbl_status.config(text=f"Server antwortet (Code {resp.status_code})", fg="orange")
        except Exception:
            self.lbl_status.config(text="Server nicht erreichbar – bitte URL prüfen", fg=ACCENT_RED)

    def _show_backup(self):
        tk.Label(self.content_frame, text="Konfiguriere deinen PC-Namen und die zu sichernden Ordner.",
                 font=("Segoe UI", 11), bg=BG_DARK, fg=TEXT_MUTED,
                 wraplength=500).pack(anchor="w", pady=(0, 15))
        tk.Label(self.content_frame, text="PC-Name (für die Server-Übersicht)",
                 font=("Segoe UI", 10, "bold"), bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w")
        self.entry_client_name = ModernInput(self.content_frame)
        self.entry_client_name.insert(0, self.steps_data["client_name"])
        self.entry_client_name.pack(fill="x", pady=(5, 10))

        tk.Label(self.content_frame, text="Zu sichernde Ordner (durch Komma getrennt)",
                 font=("Segoe UI", 10, "bold"), bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w")
        pf = tk.Frame(self.content_frame, bg=BG_DARK)
        pf.pack(fill="x", pady=(5, 10))
        self.entry_paths = ModernInput(pf)
        self.entry_paths.insert(0, self.steps_data["backup_paths"])
        self.entry_paths.pack(side="left", fill="x", expand=True)
        ModernButton(pf, text="Ordner wählen", command=self._browse_folder,
                     bg=BG_CARD, active_bg=BORDER_COLOR, padx=10, pady=4).pack(side="right", padx=(10, 0))

        tk.Label(self.content_frame,
                 text="Backup-Intervall (in Minuten, empfohlen: 180 = alle 3 Std)",
                 font=("Segoe UI", 10, "bold"), bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w")
        self.entry_interval = ModernInput(self.content_frame)
        self.entry_interval.insert(0, self.steps_data["interval"])
        self.entry_interval.pack(fill="x", pady=(5, 10))

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            current = self.entry_paths.get().strip()
            self.entry_paths.delete(0, tk.END)
            self.entry_paths.insert(0, f"{current}, {folder}" if current else folder)

    def _show_install(self):
        self.btn_next.config(state="disabled")
        tk.Label(self.content_frame, text="Installation läuft...",
                 font=("Segoe UI", 12, "bold"), bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", pady=(10, 10))
        self.lbl_progress_detail = tk.Label(self.content_frame, text="Bereite vor...",
                                            font=("Segoe UI", 10), bg=BG_DARK, fg=TEXT_MUTED)
        self.lbl_progress_detail.pack(anchor="w", pady=(0, 20))
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Modern.Horizontal.TProgressbar", thickness=15,
                        troughcolor=BG_CARD, background=ACCENT_BLUE,
                        bordercolor=BG_CARD, lightcolor=ACCENT_BLUE, darkcolor=ACCENT_BLUE)
        self.progress = ttk.Progressbar(self.content_frame, style="Modern.Horizontal.TProgressbar",
                                        orient="horizontal", length=500, mode="determinate")
        self.progress.pack(fill="x", pady=10)
        self.after(500, self._run_installation)

    def _run_installation(self):
        try:
            self.lbl_progress_detail.config(text="1. Speichere Konfiguration...")
            self.progress["value"] = 20
            self.update()
            self._write_config()

            self.lbl_progress_detail.config(text="2. Registriere Client am Server...")
            self.progress["value"] = 50
            self.update()
            registered = self._register_client()

            self.lbl_progress_detail.config(text="3. Richte automatische Backups ein...")
            self.progress["value"] = 80
            self.update()
            self._setup_scheduler()

            msg = ("JDS Backup erfolgreich installiert!" if registered
                   else "JDS Backup installiert (Offline-Modus).\nRegistrierung beim nächsten Server-Kontakt.")
            self.lbl_progress_detail.config(text=msg, fg=ACCENT_GREEN)
            self.progress["value"] = 100
            self.btn_next.config(state="normal", text="Fertigstellen")
        except Exception as e:
            messagebox.showerror("Fehler", f"Installation fehlgeschlagen:\n{e}")
            self.lbl_progress_detail.config(text=f"Fehler: {e}", fg=ACCENT_RED)
            self.btn_next.config(state="normal", text="Schließen")

    def _write_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(self.base_dir, "config.ini")

        machine_id = get_machine_id()
        for section in ("server", "client", "backup", "logging"):
            config.add_section(section)

        config.set("server", "url", self.steps_data["server_url"])
        config.set("server", "register_url", f"{self.steps_data['server_url']}/api/register/")
        config.set("client", "name", self.steps_data["client_name"])
        config.set("client", "machine_id", machine_id)
        config.set("client", "backup_interval_minutes", self.steps_data["interval"])
        config.set("backup", "paths", self.steps_data["backup_paths"])
        config.set("backup", "exclude_patterns", "*.tmp, *.log, node_modules, .git, __pycache__")
        config.set("backup", "max_file_size_mb", "500")
        config.set("logging", "log_file", "jds_client.log")
        config.set("logging", "log_level", "INFO")

        with open(config_path, "w") as f:
            config.write(f)

    def _register_client(self):
        register_url = f"{self.steps_data['server_url']}/api/register/"
        machine_id = get_machine_id()
        payload = {
            "name": self.steps_data["client_name"],
            "machine_id": machine_id,
            "operating_system": f"{platform.system()} {platform.release()}",
        }
        try:
            resp = requests.post(register_url, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                token = data.get("api_token")
                client_id = data.get("client_id")
                if token:
                    token_path = os.path.join(self.base_dir, ".jds_token")
                    data_path = os.path.join(self.base_dir, ".jds_data")
                    with open(token_path, "w") as f:
                        f.write(token)
                    with open(data_path, "w") as f:
                        f.write(f"{client_id}\n{token}")
                    return True
        except Exception:
            pass
        return False

    def _setup_scheduler(self):
        if platform.system() != "Windows":
            return
        if getattr(sys, 'frozen', False):
            exe = sys.executable
            args = "--daemon"
        else:
            exe = sys.executable
            main_py = os.path.join(self.base_dir, "main.py")
            args = f'"{main_py}" --daemon'

        task_name = "JDS-Backup"
        interval = self.steps_data["interval"]
        cmd = f'schtasks /create /tn "{task_name}" /tr "\'{exe}\' {args}" /sc minute /mo {interval} /f'
        try:
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


if __name__ == "__main__":
    app = JDSInstaller()
    app.mainloop()
