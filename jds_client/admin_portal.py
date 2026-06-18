import os
import sys
import time
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

import requests

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
            bd=0, cursor="hand2", font=("Segoe UI", 10, "bold"),
            padx=16, pady=6, relief="flat", **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=active_bg))
        self.bind("<Leave>", lambda e: self.config(bg=bg))


class ModernInput(tk.Entry):
    def __init__(self, master, show=None, **kwargs):
        super().__init__(
            master, bg=BG_CARD, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
            bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_BLUE, relief="flat", font=("Segoe UI", 11),
            show=show, **kwargs
        )


class JDSAdminPortal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JDS Serv – Admin Portal")
        self.geometry("860x600")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.minsize(700, 500)

        self.token = None
        self.server_url = "http://127.0.0.1:8000"
        self.user_info = None
        self.clients_data = []

        self._show_login()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Token {self.token}"
        return h

    def _api(self, method, path, json_data=None):
        url = f"{self.server_url}{path}"
        try:
            resp = requests.request(method, url, headers=self._headers(), json=json_data, timeout=15)
            resp.raise_for_status()
            return resp.json() if resp.text else {}
        except requests.exceptions.ConnectionError:
            return {"_error": "Server nicht erreichbar"}
        except requests.exceptions.Timeout:
            return {"_error": "Timeout – Server antwortet nicht"}
        except requests.exceptions.HTTPError as e:
            msg = f"HTTP {e.response.status_code}"
            try:
                msg += f" – {e.response.json().get('error', '')}"
            except Exception:
                pass
            return {"_error": msg}
        except Exception as e:
            return {"_error": str(e)}

    def _show_login(self):
        self._clear()
        self.title("JDS Serv – Admin Login")

        frame = tk.Frame(self, bg=BG_DARK)
        frame.place(relx=0.5, rely=0.4, anchor="center")

        tk.Label(frame, text="JDS Serv – Admin Portal", font=("Segoe UI", 20, "bold"),
                 bg=BG_DARK, fg=TEXT_LIGHT).pack(pady=(0, 20))

        card = tk.Frame(frame, bg=BG_CARD, padx=30, pady=30, bd=1,
                        highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.pack()

        tk.Label(card, text="Server-URL", font=("Segoe UI", 10, "bold"),
                 bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w")
        self.entry_url = ModernInput(card, width=38)
        self.entry_url.insert(0, "https://deine-app.onrender.com")
        self.entry_url.pack(fill="x", pady=(4, 12))

        tk.Label(card, text="Benutzername", font=("Segoe UI", 10, "bold"),
                 bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w")
        self.entry_user = ModernInput(card, width=38)
        self.entry_user.pack(fill="x", pady=(4, 12))

        tk.Label(card, text="Passwort", font=("Segoe UI", 10, "bold"),
                 bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w")
        self.entry_pass = ModernInput(card, width=38, show="\u2022")
        self.entry_pass.bind("<Return>", lambda e: self._do_login())
        self.entry_pass.pack(fill="x", pady=(4, 20))

        self.lbl_err = tk.Label(card, text="", font=("Segoe UI", 9),
                                bg=BG_CARD, fg=ACCENT_RED)
        self.lbl_err.pack(pady=(0, 10))

        ModernButton(card, text="Anmelden", command=self._do_login).pack()

    def _do_login(self):
        url = self.entry_url.get().strip().rstrip("/")
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not url or not username or not password:
            self.lbl_err.config(text="Alle Felder ausfüllen")
            return

        self.server_url = url
        self.lbl_err.config(text="Anmeldung läuft...", fg=TEXT_MUTED)
        self.update()

        try:
            resp = requests.post(f"{url}/api/login/", json={
                "username": username, "password": password
            }, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token")
                self.user_info = data
                self._show_dashboard()
            else:
                msg = resp.json().get("error", "Anmeldung fehlgeschlagen")
                self.lbl_err.config(text=msg, fg=ACCENT_RED)
        except requests.exceptions.ConnectionError:
            self.lbl_err.config(text="Server nicht erreichbar", fg=ACCENT_RED)
        except Exception as e:
            self.lbl_err.config(text=f"Fehler: {e}", fg=ACCENT_RED)

    def _show_dashboard(self):
        self._clear()
        self.title("JDS Serv – Admin Portal")

        header = tk.Frame(self, bg=BG_DARK, height=60)
        header.pack(fill="x", padx=20, pady=(15, 5))

        co = self.user_info.get("company") or {}
        co_name = co.get("name", "Super-Admin") if co else "Super-Admin"
        tk.Label(header, text=f"JDS Admin  |  {co_name}",
                 font=("Segoe UI", 16, "bold"), bg=BG_DARK, fg=TEXT_LIGHT).pack(side="left")
        ModernButton(header, text="Logout", command=self._logout,
                     bg=BG_CARD, active_bg=BORDER_COLOR).pack(side="right")

        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill="x", padx=20)

        content = tk.Frame(self, bg=BG_DARK)
        content.pack(fill="both", expand=True, padx=20, pady=15)

        left = tk.Frame(content, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="Ihre Clients", font=("Segoe UI", 13, "bold"),
                 bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 8))

        tree_frame = tk.Frame(left, bg=BG_CARD, bd=1,
                              highlightbackground=BORDER_COLOR, highlightthickness=1)
        tree_frame.pack(fill="both", expand=True)

        cols = ("name", "os", "status", "last_seen")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=BG_CARD, foreground=TEXT_LIGHT,
                        fieldbackground=BG_CARD, rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=BG_DARK, foreground=TEXT_LIGHT,
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", ACCENT_BLUE)])

        for col, label in zip(cols, ["Client-Name", "Betriebssystem", "Status", "Zuletzt gesehen"]):
            self.tree.heading(col, text=label)
        self.tree.column("name", width=180)
        self.tree.column("os", width=140)
        self.tree.column("status", width=80)
        self.tree.column("last_seen", width=150)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        right = tk.Frame(content, bg=BG_DARK, width=220)
        right.pack(side="right", fill="y", padx=(15, 0))
        right.pack_propagate(False)

        card = tk.Frame(right, bg=BG_CARD, padx=16, pady=16, bd=1,
                        highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="Aktionen", font=("Segoe UI", 12, "bold"),
                 bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

        ModernButton(card, text="Aktualisieren", command=self._refresh,
                     bg=BG_CARD, active_bg=BORDER_COLOR).pack(fill="x", pady=2)
        ModernButton(card, text="Metadaten exportieren",
                     command=self._export_metadata, bg=ACCENT_GREEN,
                     active_bg="#059669").pack(fill="x", pady=2)

        tk.Label(card, text="", bg=BG_CARD).pack(pady=4)
        tk.Label(card, text="Angemeldet als:", font=("Segoe UI", 9),
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(card, text=self.user_info.get("username", ""),
                 font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w")
        tk.Label(card, text="Server:", font=("Segoe UI", 9), bg=BG_CARD,
                 fg=TEXT_MUTED).pack(anchor="w", pady=(8, 0))
        tk.Label(card, text=self.server_url, font=("Segoe UI", 9),
                 bg=BG_CARD, fg=TEXT_MUTED, wraplength=180).pack(anchor="w")

        self.lbl_status = tk.Label(self, text="Bereit", font=("Segoe UI", 9),
                                   bg=BG_DARK, fg=TEXT_MUTED, anchor="w")
        self.lbl_status.pack(fill="x", padx=20, pady=10)

        self._refresh()

    def _refresh(self):
        self.lbl_status.config(text="Lade Clients...")
        self.update()
        data = self._api("GET", "/api/clients/")
        if "_error" in data:
            self.lbl_status.config(text=f"Fehler: {data['_error']}")
            return
        self.clients_data = data.get("clients", [])
        for row in self.tree.get_children():
            self.tree.delete(row)
        for c in self.clients_data:
            status = "Aktiv" if c["is_active"] else "Inaktiv"
            last = c.get("last_seen", "")
            try:
                last = datetime.fromisoformat(last.replace("Z", "")).strftime("%d.%m.%Y %H:%M")
            except Exception:
                last = last[:16] if last else "-"
            self.tree.insert("", "end", values=(c["name"], c.get("os") or "-", status, last))
        self.lbl_status.config(text=f"{len(self.clients_data)} Clients geladen")

    def _export_metadata(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Datei", "*.json")],
            initialfile=f"jds_metadata_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )
        if not path:
            return

        self.lbl_status.config(text="Exportiere Metadaten...")
        self.update()

        data = self._api("GET", "/api/metadata/export/")
        if "_error" in data:
            messagebox.showerror("Fehler", f"Export fehlgeschlagen:\n{data['_error']}")
            self.lbl_status.config(text="Export fehlgeschlagen")
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.lbl_status.config(text=f"Gespeichert: {path}")
            messagebox.showinfo("Erfolg", f"Metadaten gespeichert:\n{path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def _logout(self):
        self.token = None
        self.user_info = None
        self.clients_data = []
        self._show_login()


if __name__ == "__main__":
    app = JDSAdminPortal()
    app.mainloop()
