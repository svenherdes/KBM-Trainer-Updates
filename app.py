from __future__ import annotations

import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import db
from questions import CATEGORIES, FIXED, LEVELS, MIXED_SUBTOPIC, Question, available_subtopics, generate_question, parse_number, points_for, pool_count, semantic_key, semantic_keys_for_ids


APP_VERSION = "1.4.3"
APP_TITLE = f"KBM Trainer {APP_VERSION}"
UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/svenherdes/KBM-Trainer-Updates/main/version.json"
# Produktionsversion: Versionsvergleich erfolgt gegen die tatsächlich installierte Version.
UPDATE_COMPARE_VERSION = APP_VERSION
UPDATE_TEST_MODE = False
BG = "#f5f7fa"
CARD = "#ffffff"
NAV = "#182433"
NAV_ACTIVE = "#263a52"
NAV_HOVER = "#213248"
TEXT = "#172033"
MUTED = "#697586"
ACCENT = "#315f8f"
ACCENT_HOVER = "#284f78"
SUCCESS = "#2f6f52"
DANGER = "#a74444"
WARNING = "#8a642f"
BORDER = "#dce3ea"
SOFT_BLUE = "#eef4f9"
SOFT_BLUE_BORDER = "#d2e0ec"
FOOTER = "#7d8794"

def maximize_window(window: tk.Misc) -> None:
    """Maximize a Tk/Toplevel window while keeping normal Windows chrome.

    On Windows ``state("zoomed")`` is the native maximized state.  The
    fallbacks keep the test build usable on other Tk platforms as well.
    """
    try:
        window.state("zoomed")
        return
    except (tk.TclError, AttributeError):
        pass
    try:
        window.attributes("-zoomed", True)
        return
    except (tk.TclError, AttributeError):
        pass
    try:
        sw = int(window.winfo_screenwidth())
        sh = int(window.winfo_screenheight())
        window.geometry(f"{sw}x{sh}+0+0")
    except Exception:
        pass


def center_window(window: tk.Misc, width: int = 1080, height: int = 760) -> None:
    """Open a normal-sized window centered on the current screen.

    The size is limited on smaller displays so the window never extends beyond
    the usable-looking screen area.
    """
    try:
        window.update_idletasks()
        sw = int(window.winfo_screenwidth())
        sh = int(window.winfo_screenheight())
        w = min(width, max(760, sw - 100))
        h = min(height, max(560, sh - 140))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 10)
        window.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        try:
            window.geometry(f"{width}x{height}")
        except Exception:
            pass


def resource_path(relative: str) -> Path:
    """Return a resource path that works from source and from a PyInstaller bundle."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative


class KBMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        db.init_db()
        self.title(APP_TITLE)
        self.geometry("1220x800")
        self.minsize(1020, 680)
        self.configure(bg=BG)
        self._app_icon = None
        self._load_app_icon()
        self.profile_id: int | None = None
        self.profile_name = ""
        self.current_frame = None
        self.stats_period = tk.StringVar(value="Woche")
        self.stats_mode = tk.StringVar(value="Alle")
        self.settings = self._load_settings()
        self.current_update: dict | None = None
        self.update_status_label = None
        self.update_notes_label = None
        self.update_install_button = None
        self._configure_styles()
        self.show_profiles()
        # Hauptfenster beim Start im normalen Windows-Maximiert-Zustand öffnen.
        # Dadurch bleiben Titelleiste, Minimieren und Schließen erhalten.
        self.after_idle(lambda: maximize_window(self))
        if self.settings.get("check_updates_on_start", False):
            self.after(1200, lambda: self.check_for_updates(silent=True))

    def _settings_path(self) -> Path:
        return db.app_data_dir() / "settings.json"

    def _load_settings(self) -> dict:
        defaults = {"check_updates_on_start": True}
        try:
            path = self._settings_path()
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    defaults.update(data)
        except Exception:
            pass
        return defaults

    def _save_settings(self) -> None:
        try:
            self._settings_path().write_text(
                json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def _installed_update_marker_path(self) -> Path:
        return db.app_data_dir() / "installed_update_version.txt"

    def _read_installed_update_version(self) -> str:
        try:
            path = self._installed_update_marker_path()
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        return ""

    def _effective_compare_version(self) -> str:
        """Return the version used for the update comparison.

        Production builds compare against APP_VERSION.  The alternate branch
        remains only for source-level update tests.
        """
        if not UPDATE_TEST_MODE:
            return APP_VERSION
        simulated = UPDATE_COMPARE_VERSION
        installed = self._read_installed_update_version()
        if installed and self._version_tuple(installed) > self._version_tuple(simulated):
            return installed
        return simulated

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, ...]:
        parts = []
        for piece in str(version).strip().split("."):
            digits = "".join(ch for ch in piece if ch.isdigit())
            if digits:
                parts.append(int(digits))
            else:
                parts.append(0)
        while len(parts) < 4:
            parts.append(0)
        return tuple(parts[:4])

    def _set_update_status(self, text: str, *, notes: str = "", install_enabled: bool = False) -> None:
        if self.update_status_label is not None and self.update_status_label.winfo_exists():
            self.update_status_label.config(text=text)
        if self.update_notes_label is not None and self.update_notes_label.winfo_exists():
            self.update_notes_label.config(text=notes or "")
        if self.update_install_button is not None and self.update_install_button.winfo_exists():
            self.update_install_button.config(state="normal" if install_enabled else "disabled")

    def check_for_updates(self, silent: bool = False) -> None:
        self._set_update_status("Update-Server wird geprüft …", install_enabled=False)

        def worker():
            try:
                url = f"{UPDATE_MANIFEST_URL}?t={int(time.time())}"
                req = urllib.request.Request(url, headers={"User-Agent": "KBM-Trainer-Updater/1.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    manifest = json.loads(response.read().decode("utf-8"))
                required = {"version", "download_url", "sha256"}
                if not required.issubset(manifest):
                    raise ValueError("Die Versionsdatei ist unvollständig.")
                self.after(0, lambda: self._handle_update_manifest(manifest, silent))
            except Exception as exc:
                self.after(0, lambda e=str(exc), s=silent: self._handle_update_error(e, s))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_update_error(self, error: str, silent: bool) -> None:
        self.current_update = None
        self._set_update_status("Update-Prüfung derzeit nicht möglich.", notes=error, install_enabled=False)
        if not silent:
            messagebox.showwarning(
                "Updates",
                "Die Update-Prüfung konnte nicht durchgeführt werden.\n\n"
                "Das Training funktioniert weiterhin ohne Internet.\n\n"
                f"Technische Meldung: {error}",
                parent=self,
            )

    def _handle_update_manifest(self, manifest: dict, silent: bool) -> None:
        remote_version = str(manifest.get("version", "0"))
        local_compare = self._effective_compare_version()
        is_newer = self._version_tuple(remote_version) > self._version_tuple(local_compare)
        if is_newer:
            self.current_update = manifest
            notes = str(manifest.get("notes", "Keine Änderungsbeschreibung vorhanden."))
            self._set_update_status(
                f"Update verfügbar: Version {remote_version}",
                notes=notes,
                install_enabled=True,
            )
            if silent:
                if messagebox.askyesno(
                    "Neues KBM-Trainer-Update",
                    f"Eine neue Version ist verfügbar: {remote_version}\n\n"
                    f"Änderungen:\n{notes}\n\n"
                    "Deine Profile, Lernstände, Statistiken und Fehlerhistorie bleiben erhalten. "
                    "Sie sind getrennt vom Programm gespeichert.\n\n"
                    "Update jetzt herunterladen und automatisch installieren?",
                    parent=self,
                ):
                    self.download_and_install_update(preconfirmed=True)
        else:
            self.current_update = None
            local_effective = self._effective_compare_version()
            extra = ""
            if UPDATE_TEST_MODE and self._read_installed_update_version():
                extra = f"\n\nTeststatus: Version {local_effective} wurde bereits erfolgreich installiert und lokal vermerkt."
            self._set_update_status(
                f"Kein neueres Update verfügbar. Server-Version: {remote_version}",
                notes=str(manifest.get("notes", "")) + extra,
                install_enabled=False,
            )
            if not silent:
                messagebox.showinfo("Updates", "Du verwendest bereits die aktuelle Version.", parent=self)

    def _toggle_auto_update(self) -> None:
        try:
            self.settings["check_updates_on_start"] = bool(self.auto_update_var.get())
            self._save_settings()
        except Exception:
            pass

    def show_updates_window(self):
        """Update-Center, das auch ohne geöffnetes Profil funktioniert."""
        win = tk.Toplevel(self)
        win.title("KBM Trainer – Updates")
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        width = min(820, max(680, screen_w - 140))
        height = min(720, max(520, screen_h - 120))
        win.geometry(f"{width}x{height}")
        win.minsize(650, 500)
        win.resizable(True, True)
        win.configure(bg=BG)
        win.transient(self)

        root = tk.Frame(win, bg=BG)
        root.pack(fill="both", expand=True)

        holder = tk.Frame(root, bg=BG)
        holder.pack(fill="both", expand=True, padx=(20, 10), pady=(18, 8))
        canvas = tk.Canvas(holder, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(canvas, bg=BG)
        content_window = canvas.create_window((0, 0), window=outer, anchor="nw")

        def sync_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        outer.bind("<Configure>", sync_scrollregion)
        canvas.bind("<Configure>", sync_width)

        tk.Label(outer, text="Updates", font=("Segoe UI Semibold", 25), bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(
            outer,
            text="Neue Versionen prüfen und nach Bestätigung automatisch installieren",
            font=("Segoe UI", 10), bg=BG, fg=MUTED,
        ).pack(anchor="w", pady=(2, 18))

        card = tk.Frame(outer, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", pady=(0, 14))
        tk.Label(card, text="Diese Version", font=("Segoe UI Semibold", 12), bg=CARD, fg=TEXT).pack(anchor="w", padx=18, pady=(16, 2))
        tk.Label(card, text=APP_VERSION, font=("Segoe UI", 10), bg=CARD, fg=ACCENT).pack(anchor="w", padx=18)
        if UPDATE_TEST_MODE:
            tk.Label(
                card,
                text=(
                    "Für diesen Funktionstest wird beim Versionsvergleich absichtlich "
                    f"Version {UPDATE_COMPARE_VERSION} simuliert. Das GitHub-Release 1.3.4 sollte deshalb als Update erkannt werden."
                ),
                font=("Segoe UI", 9), bg=CARD, fg=WARNING, wraplength=700, justify="left"
            ).pack(anchor="w", padx=18, pady=(8, 10))

        self.auto_update_var = tk.BooleanVar(value=bool(self.settings.get("check_updates_on_start", True)))
        tk.Checkbutton(
            card,
            text="Beim Programmstart automatisch nach Updates suchen",
            variable=self.auto_update_var,
            command=self._toggle_auto_update,
            font=("Segoe UI", 10), bg=CARD, fg=TEXT, activebackground=CARD, selectcolor=CARD,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        status = tk.Frame(outer, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        status.pack(fill="x", pady=(0, 14))
        tk.Label(status, text="Update-Status", font=("Segoe UI Semibold", 12), bg=CARD, fg=TEXT).pack(anchor="w", padx=18, pady=(16, 5))
        self.update_status_label = tk.Label(status, text="Noch nicht geprüft.", font=("Segoe UI", 11), bg=CARD, fg=TEXT)
        self.update_status_label.pack(anchor="w", padx=18)
        self.update_notes_label = tk.Label(status, text="", font=("Segoe UI", 9), bg=CARD, fg=MUTED, wraplength=700, justify="left")
        self.update_notes_label.pack(anchor="w", padx=18, pady=(5, 12))

        buttons = tk.Frame(status, bg=CARD)
        buttons.pack(fill="x", padx=18, pady=(0, 18))
        ttk.Button(buttons, text="Nach Updates suchen", command=lambda: self.check_for_updates(silent=False)).pack(side="left")
        self.update_install_button = ttk.Button(
            buttons,
            text="Update herunterladen und installieren",
            style="Accent.TButton",
            command=self.download_and_install_update,
            state="disabled",
        )
        self.update_install_button.pack(side="left", padx=10)

        info = tk.Frame(outer, bg=SOFT_BLUE, highlightthickness=1, highlightbackground=SOFT_BLUE_BORDER)
        info.pack(fill="x", pady=(0, 10))
        tk.Label(info, text="Ablauf und Datensicherheit", font=("Segoe UI Semibold", 10), bg=SOFT_BLUE, fg=ACCENT).pack(anchor="w", padx=14, pady=(10, 3))
        tk.Label(
            info,
            text=(
                "Wenn beim Programmstart ein neues Update gefunden wird, fragt der KBM Trainer automatisch, "
                "ob es jetzt installiert werden soll. Du kannst mit Ja oder Nein antworten. "
                "Bei Ja wird der Installer von GitHub heruntergeladen und per SHA-256 geprüft. Erst bei korrekter Prüfsumme "
                "schließt sich der KBM Trainer und führt die Installation automatisch aus.\n\n"
                "Wichtig: Deine Profile, Lernstände, Statistiken, Prüfungsergebnisse und Fehlerhistorie liegen getrennt vom Programm "
                "und bleiben bei einem Update erhalten."
            ),
            font=("Segoe UI", 9), bg=SOFT_BLUE, fg="#49637b", wraplength=700, justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 12))

        # Falls beim Programmstart bereits ein Update gefunden wurde, soll der Status auch
        # beim späteren Öffnen dieses Fensters sofort sichtbar sein.
        if self.current_update:
            remote_version = str(self.current_update.get("version", ""))
            notes = str(self.current_update.get("notes", ""))
            self._set_update_status(
                f"Update verfügbar: Version {remote_version}",
                notes=notes,
                install_enabled=True,
            )

        self._bind_mousewheel_tree(outer, canvas)

        bottom = tk.Frame(root, bg=BG)
        bottom.pack(fill="x", padx=20, pady=(0, 14))
        ttk.Button(bottom, text="Schließen", command=win.destroy).pack(side="right")

    def show_updates(self):
        content = self.shell("Updates")
        self.title_block(content, "Updates", "Neue Versionen sicher prüfen und nach Bestätigung installieren")

        card = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=38, pady=(0, 16))
        tk.Label(card, text="Installierte Version", font=("Segoe UI Semibold", 13), bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(18, 2))
        tk.Label(card, text=APP_VERSION, font=("Segoe UI", 11), bg=CARD, fg=ACCENT).pack(anchor="w", padx=20)
        if UPDATE_TEST_MODE:
            tk.Label(
                card,
                text=(
                    "Hinweis für diesen Test: Der Vergleich beginnt zunächst bei Version "
                    f"{UPDATE_COMPARE_VERSION}. Eine erfolgreich installierte Version wird lokal vermerkt und beim nächsten Start "
                    "als aktueller Stand berücksichtigt."
                ),
                font=("Segoe UI", 9), bg=CARD, fg=WARNING, wraplength=760, justify="left"
            ).pack(anchor="w", padx=20, pady=(8, 12))

        self.auto_update_var = tk.BooleanVar(value=bool(self.settings.get("check_updates_on_start", False)))
        tk.Checkbutton(
            card,
            text="Beim Programmstart automatisch nach Updates suchen",
            variable=self.auto_update_var,
            command=self._toggle_auto_update,
            font=("Segoe UI", 10), bg=CARD, fg=TEXT, activebackground=CARD,
            selectcolor=CARD,
        ).pack(anchor="w", padx=20, pady=(0, 16))

        status = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        status.pack(fill="both", expand=False, padx=38, pady=(0, 16))
        tk.Label(status, text="Update-Status", font=("Segoe UI Semibold", 13), bg=CARD, fg=TEXT).pack(anchor="w", padx=20, pady=(18, 6))
        self.update_status_label = tk.Label(status, text="Noch nicht geprüft.", font=("Segoe UI", 11), bg=CARD, fg=TEXT)
        self.update_status_label.pack(anchor="w", padx=20)
        self.update_notes_label = tk.Label(status, text="", font=("Segoe UI", 9), bg=CARD, fg=MUTED, wraplength=800, justify="left")
        self.update_notes_label.pack(anchor="w", padx=20, pady=(6, 16))

        buttons = tk.Frame(status, bg=CARD)
        buttons.pack(fill="x", padx=20, pady=(0, 20))
        ttk.Button(buttons, text="Nach Updates suchen", command=lambda: self.check_for_updates(silent=False)).pack(side="left")
        self.update_install_button = ttk.Button(
            buttons,
            text="Update herunterladen und installieren",
            style="Accent.TButton",
            command=self.download_and_install_update,
            state="disabled",
        )
        self.update_install_button.pack(side="left", padx=10)

        info = tk.Frame(content, bg=SOFT_BLUE, highlightthickness=1, highlightbackground=SOFT_BLUE_BORDER)
        info.pack(fill="x", padx=38, pady=(0, 18))
        tk.Label(info, text="So funktioniert das Update", font=("Segoe UI Semibold", 10), bg=SOFT_BLUE, fg=ACCENT).pack(anchor="w", padx=16, pady=(12, 4))
        tk.Label(
            info,
            text=(
                "Nach deiner Bestätigung lädt der KBM Trainer den Installer von GitHub herunter, prüft ihn mit SHA-256, "
                "schließt sich und führt die Installation automatisch aus. Profile und Lernstände liegen getrennt und bleiben erhalten."
            ),
            font=("Segoe UI", 9), bg=SOFT_BLUE, fg="#49637b", wraplength=820, justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 12))

    def download_and_install_update(self, preconfirmed: bool = False) -> None:
        manifest = self.current_update
        if not manifest:
            messagebox.showinfo("Updates", "Bitte zuerst nach Updates suchen.", parent=self)
            return
        version = str(manifest.get("version", ""))
        notes = str(manifest.get("notes", ""))
        if not preconfirmed:
            if not messagebox.askyesno(
                "Update installieren",
                f"Version {version} herunterladen und installieren?\n\n{notes}\n\n"
                "Deine Profile, Lernstände, Statistiken und Fehlerhistorie bleiben erhalten. "
                "Sie sind getrennt vom Programm gespeichert.\n\n"
                "Nach erfolgreicher Prüfung wird der KBM Trainer geschlossen, aktualisiert und automatisch neu gestartet.",
                parent=self,
            ):
                return
        self._set_update_status("Update wird heruntergeladen …", notes=notes, install_enabled=False)

        def format_error(exc: BaseException) -> str:
            text = str(exc).strip()
            if not text or text.lower() == "none":
                text = repr(exc)
            return f"{type(exc).__name__}: {text}"

        def worker():
            try:
                url = str(manifest["download_url"]).strip()
                expected_hash = str(manifest["sha256"]).strip().lower()
                if not url.lower().startswith(("https://", "http://")):
                    raise ValueError("Ungültiger Download-Link in version.json.")
                if len(expected_hash) != 64 or any(c not in "0123456789abcdef" for c in expected_hash):
                    raise ValueError("Ungültige SHA-256-Prüfsumme in version.json.")

                # Jeder Update-Versuch bekommt seinen eigenen Ordner. Dadurch können
                # alte/gesperrte Temp-Dateien keinen späteren Download blockieren.
                updates_root = db.app_data_dir() / "updates"
                updates_root.mkdir(parents=True, exist_ok=True)
                update_dir = Path(tempfile.mkdtemp(prefix=f"{version}-", dir=str(updates_root)))
                filename = url.split("/")[-1].split("?")[0] or f"KBM-Trainer-Setup-{version}.exe"
                setup_path = update_dir / filename
                part_path = update_dir / (filename + ".part")

                last_error: BaseException | None = None
                actual_hash = ""
                for attempt in range(1, 4):
                    try:
                        if part_path.exists():
                            part_path.unlink()
                        req = urllib.request.Request(
                            url,
                            headers={
                                "User-Agent": f"KBM-Trainer/{APP_VERSION} Windows-Updater",
                                "Accept": "application/octet-stream,*/*;q=0.8",
                                "Cache-Control": "no-cache",
                            },
                        )
                        sha = hashlib.sha256()
                        with urllib.request.urlopen(req, timeout=60) as response, part_path.open("wb") as out:
                            while True:
                                chunk = response.read(1024 * 256)
                                if not chunk:
                                    break
                                out.write(chunk)
                                sha.update(chunk)
                        actual_hash = sha.hexdigest().lower()
                        os.replace(part_path, setup_path)
                        last_error = None
                        break
                    except BaseException as exc:
                        last_error = exc
                        try:
                            part_path.unlink(missing_ok=True)
                        except OSError:
                            pass
                        if attempt < 3:
                            time.sleep(attempt * 1.5)

                if last_error is not None:
                    raise RuntimeError(
                        "Der Update-Download ist nach 3 Versuchen fehlgeschlagen. " + format_error(last_error)
                    )

                if actual_hash != expected_hash:
                    try:
                        setup_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                    raise ValueError(
                        "Die SHA-256-Prüfung ist fehlgeschlagen. Das Update wurde aus Sicherheitsgründen nicht gestartet."
                    )

                self.after(0, lambda: self._start_verified_installer(setup_path, manifest))
            except BaseException as exc:
                self.after(0, lambda e=format_error(exc): self._update_download_failed(e))

        threading.Thread(target=worker, daemon=True).start()

    def _update_download_failed(self, error: str) -> None:
        if not error or str(error).strip().lower() == "none":
            error = "Unbekannter Update-Fehler. Bitte den Update-Versuch erneut starten."
        self._set_update_status("Update fehlgeschlagen.", notes=error, install_enabled=True)
        messagebox.showerror("Update fehlgeschlagen", error, parent=self)

    def _start_verified_installer(self, setup_path: Path, manifest: dict) -> None:
        """Hand the verified installer to an external Windows helper.

        The running PyInstaller process never tries to overwrite or restart itself.
        A separate CMD helper waits until this process is gone, runs Inno Setup,
        and starts the freshly installed KBM-Trainer.exe afterwards.
        """
        version = str(manifest.get("version", ""))
        if os.name != "nt":
            self._update_download_failed("Die automatische Installation wird nur unter Windows unterstützt.")
            return

        if getattr(sys, "frozen", False):
            running_exe = Path(sys.executable).resolve()
        else:
            running_exe = Path(__file__).resolve()

        install_dir = running_exe.parent
        installed_exe = install_dir / "KBM-Trainer.exe"
        installed_helper = install_dir / "KBM-Update-Helper.cmd"
        current_pid = os.getpid()

        if not installed_helper.exists():
            self._update_download_failed(
                "Der Update-Helfer fehlt in der Installation. Bitte den KBM Trainer einmal mit dem aktuellen Setup reparieren."
            )
            return

        update_data_dir = db.app_data_dir()
        update_data_dir.mkdir(parents=True, exist_ok=True)
        helper_log = update_data_dir / "update-helper.log"
        install_log = update_data_dir / "update-install.log"
        result_file = update_data_dir / "update-result.txt"

        # Der installierte Helfer wird in den versionsbezogenen Downloadordner
        # kopiert. So darf der Installer die installierte Helferdatei gefahrlos
        # aktualisieren, während die Kopie weiterläuft.
        helper_copy = setup_path.parent / "KBM-Update-Helper.cmd"
        try:
            shutil.copy2(installed_helper, helper_copy)
        except OSError as exc:
            self._update_download_failed(f"Update-Helfer konnte nicht vorbereitet werden: {exc}")
            return

        messagebox.showinfo(
            "Update bereit",
            "Die Prüfsumme stimmt. Der KBM Trainer wird jetzt beendet und das Update automatisch installiert.\n\n"
            "Nach erfolgreicher Installation startet der KBM Trainer automatisch wieder. Deine Profile und Lernstände bleiben erhalten.",
            parent=self,
        )

        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            cmd = [
                "cmd.exe", "/d", "/c", str(helper_copy),
                str(current_pid),
                str(setup_path),
                str(install_dir),
                version,
                str(installed_exe),
                str(helper_log),
                str(install_log),
                str(result_file),
            ]
            env = os.environ.copy()
            # Child PyInstaller apps must start with a clean runtime environment.
            env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
            subprocess.Popen(cmd, creationflags=flags, env=env)
        except BaseException as exc:
            self._update_download_failed(f"Update-Helfer konnte nicht gestartet werden: {type(exc).__name__}: {exc}")
            return

        self.destroy()

    def _load_app_icon(self):
        try:
            icon_file = resource_path("assets/kbm_trainer_icon.png")
            if icon_file.exists():
                self._app_icon = tk.PhotoImage(file=str(icon_file))
                self.iconphoto(True, self._app_icon)
        except Exception:
            # Das Programmsymbol ist rein optisch; ein fehlendes Symbol darf den Start nicht verhindern.
            self._app_icon = None

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=(13, 8),
            foreground=TEXT,
            background="#eef1f5",
            bordercolor=BORDER,
            lightcolor="#eef1f5",
            darkcolor="#eef1f5",
            relief="flat",
        )
        style.map("TButton", background=[("active", "#e4e9ef")], foreground=[("disabled", "#9aa3ad")])
        style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(15, 9),
            foreground="white",
            background=ACCENT,
            bordercolor=ACCENT,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
            relief="flat",
        )
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)], foreground=[("active", "white")])
        style.configure("TEntry", padding=7, fieldbackground="white", bordercolor=BORDER)
        style.configure("TCombobox", padding=6, fieldbackground="white", bordercolor=BORDER)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="white", fieldbackground="white", bordercolor=BORDER)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10), background="#eef1f5", foreground=TEXT, relief="flat")
        style.map("Treeview", background=[("selected", "#dbe8f4")], foreground=[("selected", TEXT)])

    def clear(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = None

    @staticmethod
    def _bind_mousewheel_tree(widget, canvas):
        """Make the mouse wheel scroll a canvas even when the pointer is over child labels/cards."""
        def on_mousewheel(event):
            # Windows/macOS Tk wheel event
            if getattr(event, "delta", 0):
                step = -1 if event.delta > 0 else 1
                canvas.yview_scroll(step * 3, "units")
            return "break"

        def on_linux_up(_event):
            canvas.yview_scroll(-3, "units")
            return "break"

        def on_linux_down(_event):
            canvas.yview_scroll(3, "units")
            return "break"

        def bind_recursive(w):
            try:
                w.bind("<MouseWheel>", on_mousewheel)
                w.bind("<Button-4>", on_linux_up)
                w.bind("<Button-5>", on_linux_down)
            except tk.TclError:
                return
            for child in w.winfo_children():
                bind_recursive(child)

        bind_recursive(widget)

    def show_profiles(self):
        self.clear()
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)
        self.current_frame = root

        wrap = tk.Frame(root, bg=BG)
        wrap.place(relx=0.5, rely=0.47, anchor="center", width=700, height=625)

        tk.Label(wrap, text="KBM TRAINER", font=("Segoe UI Semibold", 31), bg=BG, fg=TEXT).pack(pady=(0, 5))
        tk.Label(wrap, text="Lokal lernen · klar strukturiert · ohne Cloud", font=("Segoe UI", 11), bg=BG, fg=MUTED).pack(pady=(0, 24))

        card = tk.Frame(wrap, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True)
        tk.Label(card, text="Wer lernt heute?", font=("Segoe UI Semibold", 18), bg=CARD, fg=TEXT).pack(anchor="w", padx=28, pady=(26, 16))

        self.profile_list = tk.Listbox(
            card,
            font=("Segoe UI", 12),
            height=9,
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            activestyle="none",
            bg="#fbfcfd",
            fg=TEXT,
            selectbackground="#dce9f5",
            selectforeground=TEXT,
            relief="flat",
        )
        self.profile_list.pack(fill="x", padx=28)
        profiles = db.list_profiles()
        self.profile_map = []
        for row in profiles:
            self.profile_list.insert("end", row["name"])
            self.profile_map.append((row["id"], row["name"]))
        if profiles:
            self.profile_list.selection_set(0)
        self.profile_list.bind("<Double-Button-1>", lambda e: self.open_selected_profile())

        button_row = tk.Frame(card, bg=CARD)
        button_row.pack(fill="x", padx=28, pady=(18, 8))
        ttk.Button(button_row, text="Profil öffnen", style="Accent.TButton", command=self.open_selected_profile).pack(side="left")
        ttk.Button(button_row, text="Neues Profil", command=self.create_profile_dialog).pack(side="left", padx=8)
        ttk.Button(button_row, text="Profil löschen", command=self.delete_selected_profile).pack(side="right")

        backup_row = tk.Frame(card, bg=CARD)
        backup_row.pack(fill="x", padx=28, pady=(0, 16))
        ttk.Button(backup_row, text="Profil sichern", command=self.backup_selected_profile).pack(side="left")
        ttk.Button(backup_row, text="Sicherung importieren", command=self.import_profile_backup).pack(side="left", padx=8)
        ttk.Button(backup_row, text="Über den KBM Trainer", command=self.show_about).pack(side="right")
        ttk.Button(backup_row, text="Updates", command=self.show_updates_window).pack(side="right", padx=8)

        tk.Label(
            card,
            text="Alle Lernstände werden ausschließlich auf diesem Computer gespeichert. Profilsicherungen können z. B. auf einem USB-Stick abgelegt werden.",
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
            wraplength=590,
            justify="left",
        ).pack(anchor="w", padx=28, pady=(0, 22))

        self.add_footer(root)

    def add_footer(self, parent):
        footer = tk.Frame(parent, bg=BG)
        footer.pack(side="bottom", fill="x", padx=24, pady=(4, 10))
        tk.Label(
            footer,
            text=f"Powered by Sven Herdes  ·  KBM Trainer {APP_VERSION}",
            font=("Segoe UI", 8),
            bg=BG,
            fg=FOOTER,
        ).pack(side="right")
        return footer

    def create_profile_dialog(self):
        win = tk.Toplevel(self)
        win.title("Neues Profil")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        tk.Label(win, text="Name oder Lernname", font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=18, pady=(18, 8))
        entry = ttk.Entry(win, width=34, font=("Segoe UI", 11))
        entry.pack(padx=18)
        entry.focus_set()

        def save():
            try:
                db.create_profile(entry.get())
            except Exception as exc:
                messagebox.showerror("Profil", str(exc), parent=win)
                return
            win.destroy()
            self.show_profiles()

        ttk.Button(win, text="Profil anlegen", style="Accent.TButton", command=save).pack(pady=18)
        win.bind("<Return>", lambda e: save())

    def open_selected_profile(self):
        sel = self.profile_list.curselection()
        if not sel:
            messagebox.showinfo("Profil", "Bitte zuerst ein Profil auswählen.")
            return
        self.profile_id, self.profile_name = self.profile_map[sel[0]]
        db.touch_profile(self.profile_id)
        self.show_dashboard()

    def delete_selected_profile(self):
        sel = self.profile_list.curselection()
        if not sel:
            return
        pid, name = self.profile_map[sel[0]]
        if messagebox.askyesno("Profil löschen", f"Profil „{name}“ und alle zugehörigen Lernstände wirklich löschen?"):
            db.delete_profile(pid)
            self.show_profiles()

    def backup_selected_profile(self):
        sel = self.profile_list.curselection()
        if not sel:
            messagebox.showinfo("Profil sichern", "Bitte zuerst ein Profil auswählen.")
            return
        pid, name = self.profile_map[sel[0]]
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip() or "KBM-Profil"
        filename = filedialog.asksaveasfilename(
            title="KBM-Profil sichern",
            defaultextension=".kbmbackup",
            initialfile=f"{safe_name}_KBM_Sicherung.kbmbackup",
            filetypes=[("KBM-Trainer-Sicherung", "*.kbmbackup"), ("Alle Dateien", "*.*")],
        )
        if not filename:
            return
        try:
            result = db.export_profile(pid, filename, APP_VERSION)
        except Exception as exc:
            messagebox.showerror("Profil sichern", f"Die Sicherung konnte nicht erstellt werden.\n\n{exc}")
            return
        messagebox.showinfo(
            "Profil gesichert",
            f"Das Profil „{result['name']}“ wurde erfolgreich gesichert.\n\n"
            f"Gespeicherte Antworten: {result['attempts']}\n"
            f"Prüfungen: {result['exams']}\n\n"
            f"Datei:\n{result['path']}",
        )

    def import_profile_backup(self):
        filename = filedialog.askopenfilename(
            title="KBM-Profilsicherung importieren",
            filetypes=[("KBM-Trainer-Sicherung", "*.kbmbackup"), ("Alle Dateien", "*.*")],
        )
        if not filename:
            return
        try:
            data = db.inspect_backup(filename)
            original_name = str(data["profile"]["name"]).strip()
            import_name = original_name
            if db.profile_name_exists(original_name):
                import_name = db.unique_profile_name(original_name)
                proceed = messagebox.askyesno(
                    "Profil bereits vorhanden",
                    f"Ein Profil mit dem Namen „{original_name}“ ist auf diesem PC bereits vorhanden.\n\n"
                    f"Die Sicherung kann sicher als „{import_name}“ importiert werden. "
                    "Das vorhandene Profil wird nicht verändert.\n\nImportieren?",
                )
                if not proceed:
                    return
            result = db.import_profile(filename, import_name)
        except Exception as exc:
            messagebox.showerror("Sicherung importieren", f"Die Sicherung konnte nicht importiert werden.\n\n{exc}")
            return

        self.show_profiles()
        # Select the freshly imported profile when possible.
        for idx, (pid, _name) in enumerate(self.profile_map):
            if pid == result["profile_id"]:
                self.profile_list.selection_clear(0, "end")
                self.profile_list.selection_set(idx)
                self.profile_list.see(idx)
                break
        messagebox.showinfo(
            "Import abgeschlossen",
            f"Das Profil „{result['name']}“ wurde wiederhergestellt.\n\n"
            f"Antworten: {result['attempts']}\n"
            f"Prüfungen: {result['exams']}\n\n"
            "Statistiken und Fehlertraining werden aus diesen Daten automatisch wieder aufgebaut.",
        )

    def show_about(self):
        win = tk.Toplevel(self)
        win.title("Über den KBM Trainer")
        # Das Fenster bleibt auch bei kleiner Bildschirmhöhe vollständig bedienbar.
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        width = min(720, max(560, screen_w - 120))
        height = min(680, max(460, screen_h - 140))
        win.geometry(f"{width}x{height}")
        win.minsize(540, 430)
        win.resizable(True, True)
        win.configure(bg=BG)
        win.transient(self)

        outer = tk.Frame(win, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=BG)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def sync_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        content.bind("<Configure>", sync_scrollregion)
        canvas.bind("<Configure>", sync_width)

        def on_mousewheel(event):
            delta = -1 if event.delta > 0 else 1
            canvas.yview_scroll(delta * 3, "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        win.bind("<Destroy>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        card = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True, padx=4, pady=4)

        tk.Label(card, text="KBM TRAINER", font=("Segoe UI Semibold", 25), bg=CARD, fg=TEXT).pack(anchor="w", padx=26, pady=(26, 2))
        tk.Label(card, text=f"Version {APP_VERSION}", font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack(anchor="w", padx=26)
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=26, pady=18)

        tk.Label(card, text="Entwickelt von Sven Herdes", font=("Segoe UI Semibold", 14), bg=CARD, fg=ACCENT).pack(anchor="w", padx=26)
        tk.Label(
            card,
            text="Der KBM Trainer ist ein unabhängiges lokales Lernprogramm zur Vorbereitung und Übung im kaufmännischen Bereich. Er ist kein offizielles Angebot einer Kammer oder Bildungseinrichtung.",
            font=("Segoe UI", 10), bg=CARD, fg=TEXT, wraplength=560, justify="left"
        ).pack(anchor="w", padx=26, pady=(12, 14))

        info = [
            "• Anfänger, Fortgeschritten und Experte",
            "• Training, Prüfung, Fehlertraining und Langzeitstatistik",
            "• Profil-Backup und Import, z. B. über USB-Stick",
            "• Keine Cloud und kein Benutzerkonto erforderlich",
            "• Lernstände werden ausschließlich lokal gespeichert",
        ]
        tk.Label(card, text="\n".join(info), font=("Segoe UI", 10), bg=CARD, fg=MUTED, justify="left").pack(anchor="w", padx=26)

        privacy = tk.Frame(card, bg=SOFT_BLUE, highlightthickness=1, highlightbackground=SOFT_BLUE_BORDER)
        privacy.pack(fill="x", padx=26, pady=(18, 16))
        tk.Label(privacy, text="Datenschutz", font=("Segoe UI Semibold", 10), bg=SOFT_BLUE, fg=ACCENT).pack(anchor="w", padx=14, pady=(10, 2))
        tk.Label(privacy, text="Profile, Antworten, Prüfungen und Statistiken verlassen den Computer nicht. Für das Training ist keine Internetverbindung erforderlich.", font=("Segoe UI", 9), bg=SOFT_BLUE, fg="#49637b", wraplength=520, justify="left").pack(anchor="w", padx=14, pady=(0, 10))

        tk.Label(card, text="© 2026 Sven Herdes", font=("Segoe UI", 8), bg=CARD, fg=FOOTER).pack(anchor="e", padx=26, pady=(0, 22))

        bottom = tk.Frame(win, bg=BG)
        bottom.pack(fill="x", padx=24, pady=(0, 14))
        ttk.Button(bottom, text="Schließen", command=win.destroy).pack(side="right")

    def shell(self, active: str):
        self.clear()
        shell = tk.Frame(self, bg=BG)
        shell.pack(fill="both", expand=True)
        self.current_frame = shell

        nav = tk.Frame(shell, bg=NAV, width=236)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        tk.Label(nav, text="KBM TRAINER", font=("Segoe UI Semibold", 18), bg=NAV, fg="white").pack(anchor="w", padx=22, pady=(24, 2))
        tk.Label(nav, text=f"Version {APP_VERSION}", font=("Segoe UI", 8), bg=NAV, fg="#8fa2b7").pack(anchor="w", padx=22, pady=(0, 15))
        tk.Frame(nav, bg="#2b3b4d", height=1).pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(nav, text=self.profile_name, font=("Segoe UI Semibold", 10), bg=NAV, fg="#d7e0e9").pack(anchor="w", padx=22, pady=(0, 18))

        items = [
            ("Start", self.show_dashboard),
            ("Training", self.show_training_setup),
            ("Lernempfehlung", self.show_learning_recommendations),
            ("Prüfung", self.show_exam_setup),
            ("Statistik", self.show_statistics),
            ("Fehler ansehen", self.show_errors),
        ]
        for label, command in items:
            bg = NAV_ACTIVE if label == active else NAV
            btn = tk.Button(
                nav,
                text=label,
                command=command,
                font=("Segoe UI", 11),
                bg=bg,
                fg="white",
                activebackground=NAV_HOVER,
                activeforeground="white",
                bd=0,
                relief="flat",
                anchor="w",
                padx=22,
                pady=13,
                cursor="hand2",
            )
            btn.pack(fill="x")

        tk.Frame(nav, bg=NAV).pack(fill="both", expand=True)
        tk.Button(
            nav,
            text="Über den KBM Trainer",
            command=self.show_about,
            font=("Segoe UI", 9),
            bg=NAV,
            fg="#9fb0c2",
            activebackground=NAV_ACTIVE,
            activeforeground="white",
            bd=0,
            anchor="w",
            padx=20,
            pady=8,
        ).pack(fill="x")
        tk.Button(
            nav,
            text="Profil wechseln",
            command=self.show_profiles,
            font=("Segoe UI", 10),
            bg=NAV,
            fg="#cbd5e1",
            activebackground=NAV_ACTIVE,
            activeforeground="white",
            bd=0,
            anchor="w",
            padx=20,
            pady=12,
        ).pack(fill="x", pady=(0, 12))

        right_area = tk.Frame(shell, bg=BG)
        right_area.pack(side="left", fill="both", expand=True)
        self.add_footer(right_area)
        content = tk.Frame(right_area, bg=BG)
        content.pack(side="top", fill="both", expand=True)
        return content

    def title_block(self, parent, title: str, subtitle: str = ""):
        block = tk.Frame(parent, bg=BG)
        block.pack(fill="x", padx=38, pady=(30, 18))
        tk.Label(block, text=title, font=("Segoe UI Semibold", 25), bg=BG, fg=TEXT).pack(anchor="w")
        if subtitle:
            tk.Label(block, text=subtitle, font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(4, 0))
        return block

    def stat_card(self, parent, title: str, value: str, sub: str = ""):
        card = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        tk.Label(card, text=title, font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(card, text=value, font=("Segoe UI Semibold", 20), bg=CARD, fg=TEXT).pack(anchor="w", padx=16)
        if sub:
            tk.Label(card, text=sub, font=("Segoe UI", 8), bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(3, 12))
        else:
            tk.Frame(card, bg=CARD, height=14).pack()
        return card

    def show_dashboard(self):
        # Die Startseite ist vertikal scrollbar, damit auch bei kleineren
        # Auflösungen alle Bereiche (inkl. Datenschutz) erreichbar bleiben.
        base = self.shell("Start")
        holder = tk.Frame(base, bg=BG)
        holder.pack(fill="both", expand=True)

        canvas = tk.Canvas(holder, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=BG)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def sync_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        def on_mousewheel(event):
            if event.delta == 0:
                return
            direction = -1 if event.delta > 0 else 1
            canvas.yview_scroll(direction * 3, "units")

        content.bind("<Configure>", sync_scrollregion)
        canvas.bind("<Configure>", sync_width)

        self.title_block(content, f"Hallo {self.profile_name}", "Dein lokaler Lernstand auf einen Blick")
        stats = db.summary(self.profile_id, "Gesamt")
        today = db.summary(self.profile_id, "Tag")
        errors = db.active_errors(self.profile_id)

        row = tk.Frame(content, bg=BG)
        row.pack(fill="x", padx=38)
        cards = [
            ("Heute bearbeitet", str(today["total"]), "Aufgaben"),
            ("Heute richtig", f"{today['rate']:.0f}%", f"{today['correct']} von {today['total']}" if today["total"] else "Noch keine Aufgabe"),
            ("Gesamt bearbeitet", str(stats["total"]), "seit Profilerstellung"),
            ("Aktive Fehler", str(len(errors)), "für Fehlertraining"),
        ]
        for i, args in enumerate(cards):
            c = self.stat_card(row, *args)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6, 0 if i == len(cards) - 1 else 6))
            row.grid_columnconfigure(i, weight=1)

        actions = tk.Frame(content, bg=BG)
        actions.pack(fill="x", padx=38, pady=26)
        left = tk.Frame(actions, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        left.pack(side="left", fill="both", expand=True, padx=(0, 9))
        tk.Label(left, text="Weiterlernen", font=("Segoe UI Semibold", 17), bg=CARD, fg=TEXT).pack(anchor="w", padx=22, pady=(22, 6))
        tk.Label(left, text="Wähle einen Bereich und trainiere in deiner passenden Stufe.", font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack(anchor="w", padx=22)
        ttk.Button(left, text="Training starten", style="Accent.TButton", command=self.show_training_setup).pack(anchor="w", padx=22, pady=22)

        right = tk.Frame(actions, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True, padx=(9, 0))
        tk.Label(right, text="Fortschritt prüfen", font=("Segoe UI Semibold", 17), bg=CARD, fg=TEXT).pack(anchor="w", padx=22, pady=(22, 6))
        tk.Label(right, text="Vergleiche Tag, Woche, Monat, Jahr oder deinen gesamten Lernstand.", font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack(anchor="w", padx=22)
        ttk.Button(right, text="Statistik öffnen", command=self.show_statistics).pack(anchor="w", padx=22, pady=22)

        recommendations = self._valid_learning_recommendations(limit=1)
        recommend_card = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        recommend_card.pack(fill="x", padx=38, pady=(0, 18))
        tk.Label(recommend_card, text="Hier solltest du noch üben", font=("Segoe UI Semibold", 14), bg=CARD, fg=TEXT).pack(anchor="w", padx=18, pady=(14, 4))
        if recommendations:
            rec = recommendations[0]
            details = f"{rec['topic']} · {rec['level']}   |   Trefferquote {rec['rate']:.0f}% aus {rec['total']} Aufgaben"
            if rec['active_errors']:
                details += f"   |   {rec['active_errors']} aktive Fehler"
            line = tk.Frame(recommend_card, bg=CARD)
            line.pack(fill="x", padx=18, pady=(2, 14))
            tk.Label(line, text=f"{rec['status']}: {rec['category']}", font=("Segoe UI Semibold", 10), bg=CARD, fg=WARNING if rec['status'] == "Festigen" else DANGER).pack(anchor="w")
            tk.Label(line, text=details, font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(side="left", pady=(4, 0))
            ttk.Button(line, text="Jetzt trainieren", style="Accent.TButton", command=lambda r=rec: self.start_recommended_training(r)).pack(side="right", padx=(12, 0))
        else:
            line = tk.Frame(recommend_card, bg=CARD)
            line.pack(fill="x", padx=18, pady=(2, 14))
            tk.Label(line, text="Aktuell gibt es noch keine eindeutige Lernempfehlung. Nach einigen bearbeiteten Aufgaben wird hier automatisch ein passendes Thema vorgeschlagen.", font=("Segoe UI", 9), bg=CARD, fg=MUTED, wraplength=760, justify="left").pack(side="left")
            ttk.Button(line, text="Training öffnen", command=self.show_training_setup).pack(side="right", padx=(12, 0))

        self._stage_progress_card(content)

        privacy = tk.Frame(content, bg=SOFT_BLUE, highlightthickness=1, highlightbackground=SOFT_BLUE_BORDER)
        privacy.pack(fill="x", padx=38, pady=(0, 20))
        tk.Label(privacy, text="Datenschutz", font=("Segoe UI Semibold", 11), bg=SOFT_BLUE, fg=ACCENT).pack(anchor="w", padx=16, pady=(12, 2))
        tk.Label(
            privacy,
            text="Profile, Antworten und Statistiken werden nur lokal auf diesem Computer gespeichert. Für das Training ist keine Internetverbindung erforderlich.",
            font=("Segoe UI", 9),
            bg=SOFT_BLUE,
            fg="#49637b",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Mausrad funktioniert über der gesamten Startseite, nicht nur direkt
        # über dem Scrollbalken.
        def bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", on_mousewheel, add="+")
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child)

        bind_mousewheel_recursive(content)
        canvas.bind("<MouseWheel>", on_mousewheel, add="+")
        sync_scrollregion()

    def _valid_learning_recommendations(self, limit: int = 8):
        """Return only recommendations that still map to an active question pool."""
        rows = db.learning_recommendations(self.profile_id, limit=max(limit * 3, 12))
        valid = []
        for row in rows:
            if row["category"] not in CATEGORIES or row["level"] not in LEVELS:
                continue
            if pool_count(row["category"], row["level"], row["topic"]) <= 0:
                continue
            valid.append(row)
            if len(valid) >= limit:
                break
        return valid

    def start_recommended_training(self, recommendation):
        """Start a targeted 10-question session from a learning recommendation."""
        TrainingSession(
            self,
            self.profile_id,
            recommendation["category"],
            recommendation["level"],
            10,
            mode="training",
            subtopic=recommendation["topic"],
        )

    def start_stage_recommendation(self, recommendation):
        """Start a mixed ten-question session in the recommended next stage."""
        TrainingSession(
            self,
            self.profile_id,
            "Gemischt",
            recommendation["to_level"],
            10,
            mode="training",
        )

    def _stage_progress_card(self, parent):
        """Always show progress toward the next two difficulty stages."""
        outer = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        outer.pack(fill="x", padx=38, pady=(0, 18))

        tk.Label(
            outer,
            text="Stufenfortschritt",
            font=("Segoe UI Semibold", 14),
            bg=CARD,
            fg=TEXT,
        ).pack(anchor="w", padx=18, pady=(14, 2))
        tk.Label(
            outer,
            text="So siehst du jederzeit, was dir für die Empfehlung zur nächsten Stufe noch fehlt.",
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
        ).pack(anchor="w", padx=18, pady=(0, 10))

        body = tk.Frame(outer, bg=CARD)
        body.pack(fill="x", padx=18, pady=(0, 16))

        transitions = [("Anfänger", "Fortgeschritten"), ("Fortgeschritten", "Experte")]
        for col, (from_level, to_level) in enumerate(transitions):
            progress = db.stage_progress(self.profile_id, from_level)
            qualification = db.stage_qualification(progress)
            requirements = qualification["requirements"]
            criteria = qualification["criteria"]
            qualified = qualification["qualified"]

            panel_bg = "#eef8f2" if qualified else "#f8fafc"
            panel_border = "#cfe5d7" if qualified else BORDER
            panel = tk.Frame(body, bg=panel_bg, highlightthickness=1, highlightbackground=panel_border)
            panel.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 7, 7 if col == 0 else 0))
            body.grid_columnconfigure(col, weight=1)

            status_text = f"Bereit für {to_level}" if qualified else f"Noch nicht bereit für {to_level}"
            status_color = SUCCESS if qualified else WARNING
            tk.Label(
                panel,
                text=f"{from_level} → {to_level}",
                font=("Segoe UI Semibold", 11),
                bg=panel_bg,
                fg=TEXT,
            ).pack(anchor="w", padx=14, pady=(12, 2))
            tk.Label(
                panel,
                text=status_text,
                font=("Segoe UI Semibold", 9),
                bg=panel_bg,
                fg=status_color,
            ).pack(anchor="w", padx=14, pady=(0, 8))

            exam_rate = progress.get("latest_exam_rate")
            rows = [
                ("Bearbeitete Aufgaben", f"{progress['total']} / {requirements['attempts']}", criteria["attempts"]),
                ("Gesamtquote", f"{progress['rate']:.0f}% / {requirements['rate']:.0f}%", criteria["rate"]),
                ("Letzte Prüfung", (f"{exam_rate:.0f}% / {requirements['exam']:.0f}%" if exam_rate is not None else f"noch keine / {requirements['exam']:.0f}%"), criteria["exam"]),
                ("Aktive Fehler", f"{progress['active_errors']} / max. {requirements['errors']}", criteria["errors"]),
            ]
            for label_text, value_text, passed in rows:
                row = tk.Frame(panel, bg=panel_bg)
                row.pack(fill="x", padx=14, pady=1)
                marker = "✓" if passed else "○"
                marker_color = SUCCESS if passed else MUTED
                tk.Label(row, text=marker, width=2, font=("Segoe UI Semibold", 9), bg=panel_bg, fg=marker_color).pack(side="left")
                tk.Label(row, text=label_text, font=("Segoe UI", 9), bg=panel_bg, fg=MUTED).pack(side="left")
                tk.Label(row, text=value_text, font=("Segoe UI Semibold", 9), bg=panel_bg, fg=TEXT).pack(side="right")

            if qualified:
                rec = {
                    "from_level": from_level,
                    "to_level": to_level,
                    **progress,
                }
                ttk.Button(
                    panel,
                    text=f"{to_level} starten",
                    style="Accent.TButton",
                    command=lambda r=rec: self.start_stage_recommendation(r),
                ).pack(anchor="e", padx=14, pady=(9, 12))
            else:
                tk.Label(
                    panel,
                    text="Die Stufe bleibt frei wählbar. Das ist nur eine Empfehlung.",
                    font=("Segoe UI", 8),
                    bg=panel_bg,
                    fg=MUTED,
                ).pack(anchor="w", padx=14, pady=(8, 12))

        return outer

    def _stage_recommendation_card(self, parent, recommendation):
        card = tk.Frame(parent, bg="#eef8f2", highlightthickness=1, highlightbackground="#cfe5d7")
        card.pack(fill="x", padx=38, pady=(0, 18))
        tk.Label(card, text="Stufenempfehlung", font=("Segoe UI Semibold", 14), bg="#eef8f2", fg=SUCCESS).pack(anchor="w", padx=18, pady=(14, 4))
        tk.Label(
            card,
            text=f"Du bist bereit für die nächste Stufe: {recommendation['to_level']}",
            font=("Segoe UI Semibold", 11),
            bg="#eef8f2",
            fg=TEXT,
        ).pack(anchor="w", padx=18)
        exam_rate = recommendation.get("latest_exam_rate") or 0.0
        details = (
            f"{recommendation['from_level']}: {recommendation['rate']:.0f}% Gesamtquote aus "
            f"{recommendation['total']} Aufgaben · letzte Prüfung {exam_rate:.0f}% · "
            f"{recommendation['active_errors']} aktive Fehler"
        )
        line = tk.Frame(card, bg="#eef8f2")
        line.pack(fill="x", padx=18, pady=(6, 14))
        tk.Label(line, text=details, font=("Segoe UI", 9), bg="#eef8f2", fg="#496b5b", wraplength=720, justify="left").pack(side="left", fill="x", expand=True)
        ttk.Button(
            line,
            text=f"{recommendation['to_level']} starten",
            style="Accent.TButton",
            command=lambda r=recommendation: self.start_stage_recommendation(r),
        ).pack(side="right", padx=(12, 0))
        return card

    def show_learning_recommendations(self):
        content = self.shell("Lernempfehlung")
        self.title_block(
            content,
            "Hier solltest du noch üben",
            "Automatisch aus deinem bisherigen Lernstand berechnet – ohne KI und ohne Cloud",
        )

        info = tk.Frame(content, bg=SOFT_BLUE, highlightthickness=1, highlightbackground=SOFT_BLUE_BORDER)
        info.pack(fill="x", padx=38, pady=(0, 16))
        tk.Label(
            info,
            text="Ein Thema erscheint hier normalerweise nach mindestens 5 bearbeiteten Aufgaben, wenn die aktuelle Trefferquote unter 85 % liegt. Mehrere offene Fehler können ein Thema auch früher sichtbar machen.",
            font=("Segoe UI", 9),
            bg=SOFT_BLUE,
            fg="#49637b",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", padx=16, pady=12)

        recommendations = self._valid_learning_recommendations(limit=6)
        if not recommendations:
            card = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", padx=38)
            tk.Label(card, text="Noch keine eindeutige Lernempfehlung", font=("Segoe UI Semibold", 14), bg=CARD, fg=TEXT).pack(anchor="w", padx=18, pady=(18, 5))
            tk.Label(card, text="Bearbeite zunächst einige Aufgaben. Sobald genügend Ergebnisse vorliegen, erkennt der KBM Trainer automatisch, welche Themen du noch üben oder festigen solltest.", font=("Segoe UI", 10), bg=CARD, fg=MUTED, wraplength=790, justify="left").pack(anchor="w", padx=18, pady=(0, 14))
            ttk.Button(card, text="Training starten", style="Accent.TButton", command=self.show_training_setup).pack(anchor="w", padx=18, pady=(0, 18))
            return

        list_frame = tk.Frame(content, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=38, pady=(0, 20))
        for idx, rec in enumerate(recommendations):
            card = tk.Frame(list_frame, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=(0, 9))
            left = tk.Frame(card, bg=CARD)
            left.pack(side="left", fill="both", expand=True, padx=18, pady=13)
            status_color = DANGER if rec["status"] == "Noch üben" else WARNING
            tk.Label(left, text=rec["status"], font=("Segoe UI Semibold", 9), bg=CARD, fg=status_color).pack(anchor="w")
            tk.Label(left, text=f"{rec['category']} · {rec['topic']} · {rec['level']}", font=("Segoe UI Semibold", 11), bg=CARD, fg=TEXT).pack(anchor="w", pady=(3, 2))
            details = f"Trefferquote {rec['rate']:.0f}% aus den letzten {rec['total']} passenden Aufgaben"
            if rec["active_errors"]:
                details += f" · {rec['active_errors']} aktive Fehler"
            tk.Label(left, text=details, font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(anchor="w")
            ttk.Button(card, text="Jetzt trainieren", style="Accent.TButton", command=lambda r=rec: self.start_recommended_training(r)).pack(side="right", padx=18, pady=18)

    def show_training_setup(self):
        content = self.shell("Training")
        self.title_block(content, "Training", "Bereich, Unterthema und Schwierigkeitsstufe auswählen")

        form = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        form.pack(fill="x", padx=38, pady=(0, 24))
        inner = tk.Frame(form, bg=CARD)
        inner.pack(fill="x", padx=24, pady=24)

        tk.Label(inner, text="Aufgabenbereich", font=("Segoe UI Semibold", 11), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w", pady=(0, 8))
        category = ttk.Combobox(inner, values=CATEGORIES, state="readonly", width=34, font=("Segoe UI", 10))
        category.set(CATEGORIES[0])
        category.grid(row=1, column=0, sticky="w", padx=(0, 24))

        tk.Label(inner, text="Stufe", font=("Segoe UI Semibold", 11), bg=CARD, fg=TEXT).grid(row=0, column=1, sticky="w", pady=(0, 8))
        level = ttk.Combobox(inner, values=LEVELS, state="readonly", width=24, font=("Segoe UI", 10))
        level.set(LEVELS[0])
        level.grid(row=1, column=1, sticky="w")

        tk.Label(inner, text="Unterthema", font=("Segoe UI Semibold", 11), bg=CARD, fg=TEXT).grid(row=2, column=0, sticky="w", pady=(24, 8))
        subtopic = ttk.Combobox(inner, state="readonly", width=34, font=("Segoe UI", 10))
        subtopic.grid(row=3, column=0, sticky="w", padx=(0, 24))

        tk.Label(inner, text="Trainingsumfang", font=("Segoe UI Semibold", 11), bg=CARD, fg=TEXT).grid(row=2, column=1, sticky="w", pady=(24, 8))
        count = ttk.Combobox(inner, values=[5, 10, 15, 20], state="readonly", width=10, font=("Segoe UI", 10))
        count.set("10")
        count.grid(row=3, column=1, sticky="w")

        pool_info = tk.Label(inner, text="", font=("Segoe UI", 9), bg=CARD, fg=MUTED)
        pool_info.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

        def update_pool_info(*_args):
            selected = subtopic.get() or MIXED_SUBTOPIC
            amount = pool_count(category.get(), level.get(), selected)
            if selected == MIXED_SUBTOPIC:
                pool_info.config(text=f"Aufgabenpool: {amount} Aufgaben aus allen verfügbaren Unterthemen dieser Stufe")
            else:
                pool_info.config(text=f"Aufgabenpool: {amount} Aufgaben im Unterthema „{selected}“")

        def update_subtopics(*_args):
            values = available_subtopics(category.get(), level.get())
            subtopic["values"] = values
            subtopic.set(MIXED_SUBTOPIC if MIXED_SUBTOPIC in values else (values[0] if values else ""))
            update_pool_info()

        category.bind("<<ComboboxSelected>>", update_subtopics)
        level.bind("<<ComboboxSelected>>", update_subtopics)
        subtopic.bind("<<ComboboxSelected>>", update_pool_info)
        update_subtopics()

        def start():
            selected = subtopic.get() or MIXED_SUBTOPIC
            amount = pool_count(category.get(), level.get(), selected)
            if amount <= 0:
                messagebox.showinfo("Training", "Für diese Auswahl sind noch keine Aufgaben hinterlegt.")
                return
            TrainingSession(
                self, self.profile_id, category.get(), level.get(), int(count.get()),
                mode="training", subtopic=selected
            )

        ttk.Button(inner, text="Training starten", style="Accent.TButton", command=start).grid(row=5, column=0, sticky="w", pady=(28, 0))

        info = tk.Frame(content, bg=BG)
        info.pack(fill="x", padx=34)
        descriptions = [
            ("Gezieltes Training", "Wähle ein Unterthema, wenn du genau an einer Schwäche arbeiten möchtest."),
            ("Gemischtes Training", "Mischt alle verfügbaren Unterthemen des gewählten Bereichs und der Stufe."),
            ("Drei Stufen", "Anfänger, Fortgeschritten und Experte bleiben für jedes verfügbare Unterthema erhalten."),
        ]
        for i, (name, desc) in enumerate(descriptions):
            c = tk.Frame(info, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6, 0 if i == 2 else 6))
            tk.Label(c, text=name, font=("Segoe UI Semibold", 12), bg=CARD, fg=TEXT).pack(anchor="w", padx=16, pady=(14, 5))
            tk.Label(c, text=desc, font=("Segoe UI", 9), bg=CARD, fg=MUTED, wraplength=230, justify="left").pack(anchor="w", padx=16, pady=(0, 14))
            info.grid_columnconfigure(i, weight=1)

    def show_exam_setup(self):
        content = self.shell("Prüfung")
        self.title_block(content, "Prüfungssimulation", "Ohne Hinweise. Auswertung gesammelt am Ende.")
        card = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=34)
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=24, pady=24)
        tk.Label(inner, text="Stufe", font=("Segoe UI Semibold", 11), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w", pady=(0, 8))
        level = ttk.Combobox(inner, values=LEVELS, state="readonly", width=24)
        level.set("Fortgeschritten")
        level.grid(row=1, column=0, sticky="w")
        tk.Label(inner, text="Die Simulation mischt alle fünf Aufgabenbereiche.", font=("Segoe UI", 9), bg=CARD, fg=MUTED).grid(row=2, column=0, sticky="w", pady=(14, 4))
        tk.Label(inner, text="Die Prüfung verwendet den erweiterten Aufgabenpool und vermeidet direkte Wiederholungen.", font=("Segoe UI", 9), bg=CARD, fg=MUTED).grid(row=3, column=0, sticky="w", pady=(0, 4))

        def start_exam():
            TrainingSession(self, self.profile_id, "Gemischt", level.get(), 20, mode="exam")

        ttk.Button(inner, text="20 Aufgaben starten", style="Accent.TButton", command=start_exam).grid(row=4, column=0, sticky="w", pady=(20, 0))
        ttk.Button(inner, text="Prüfungsverlauf anzeigen", command=self.show_exam_history).grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(20, 0))

    def show_statistics(self):
        content = self.shell("Statistik")
        self.title_block(content, "Statistik", "Vergleiche Lernfortschritt nach Zeitraum, Training und Prüfung")
        self.stats_period.set("Woche")
        self.stats_mode.set("Alle")

        controls = tk.Frame(content, bg=BG)
        controls.pack(fill="x", padx=34, pady=(0, 10))

        tk.Label(controls, text="Zeitraum", font=("Segoe UI Semibold", 9), bg=BG, fg=MUTED).pack(side="left", padx=(0, 8))
        stats_area = tk.Frame(content, bg=BG)
        for period in ["Tag", "Woche", "Monat", "Jahr", "Gesamt"]:
            tk.Radiobutton(
                controls,
                text=period,
                variable=self.stats_period,
                value=period,
                command=lambda: self.render_stats(stats_area),
                indicatoron=False,
                padx=13,
                pady=7,
                font=("Segoe UI", 9),
                selectcolor="#dbeafe",
                bg=CARD,
                fg=TEXT,
                activebackground="#eff6ff",
                bd=1,
                relief="solid",
            ).pack(side="left", padx=(0, 5))

        tk.Label(controls, text="Daten", font=("Segoe UI Semibold", 9), bg=BG, fg=MUTED).pack(side="left", padx=(18, 8))
        for mode in ["Alle", "Training", "Prüfungen"]:
            tk.Radiobutton(
                controls,
                text=mode,
                variable=self.stats_mode,
                value=mode,
                command=lambda: self.render_stats(stats_area),
                indicatoron=False,
                padx=13,
                pady=7,
                font=("Segoe UI", 9),
                selectcolor="#dcfce7" if mode == "Training" else "#ede9fe" if mode == "Prüfungen" else "#e5e7eb",
                bg=CARD,
                fg=TEXT,
                activebackground="#f3f4f6",
                bd=1,
                relief="solid",
            ).pack(side="left", padx=(0, 5))

        ttk.Button(controls, text="Prüfungsverlauf", command=self.show_exam_history).pack(side="right")

        stats_area.pack(fill="both", expand=True, padx=34, pady=(0, 24))
        self.render_stats(stats_area)

    def render_stats(self, area):
        for child in area.winfo_children():
            child.destroy()
        period = self.stats_period.get()
        mode_filter = self.stats_mode.get()
        s = db.summary(self.profile_id, period, mode_filter)
        prev = db.previous_summary(self.profile_id, period, mode_filter) if period != "Gesamt" else None

        top = tk.Frame(area, bg=BG)
        top.pack(fill="x")
        values = [
            ("Aufgaben", str(s["total"]), f"{mode_filter.lower()} im Zeitraum" if mode_filter != "Alle" else "im Zeitraum"),
            ("Richtig", f"{s['rate']:.1f}%", f"{s['correct']} richtig / {s['wrong']} falsch"),
            ("Lernzeit", self.format_duration(s["seconds"]), "aktive Bearbeitungszeit"),
            ("Punkte", str(s["points"]), "aus beantworteten Aufgaben"),
        ]
        for i, item in enumerate(values):
            c = self.stat_card(top, *item)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 5, 0 if i == 3 else 5))
            top.grid_columnconfigure(i, weight=1)

        if prev is not None:
            comparison = tk.Frame(area, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            comparison.pack(fill="x", pady=12)
            if prev["total"] == 0:
                text = "Für den vorherigen Zeitraum liegen noch keine Vergleichsdaten vor."
            else:
                delta_rate = s["rate"] - prev["rate"]
                delta_total = s["total"] - prev["total"]
                text = f"Vergleich zum vorherigen Zeitraum: Aufgaben {delta_total:+d}  |  Erfolgsquote {delta_rate:+.1f} Prozentpunkte"
            tk.Label(comparison, text=text, font=("Segoe UI", 10), bg=CARD, fg=TEXT).pack(anchor="w", padx=16, pady=10)

        lower = tk.Frame(area, bg=BG)
        lower.pack(fill="both", expand=True)

        left = tk.Frame(lower, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        tk.Label(left, text="Bereiche", font=("Segoe UI Semibold", 13), bg=CARD, fg=TEXT).pack(anchor="w", padx=16, pady=(12, 6))
        cat_rows = db.category_stats(self.profile_id, period, mode_filter)
        if not cat_rows:
            tk.Label(left, text="Für diesen Zeitraum liegen noch keine Daten vor.", font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=8)
        else:
            for r in cat_rows:
                line = tk.Frame(left, bg=CARD)
                line.pack(fill="x", padx=16, pady=3)
                tk.Label(line, text=r["category"], width=25, anchor="w", font=("Segoe UI", 9), bg=CARD, fg=TEXT).pack(side="left")
                ttk.Progressbar(line, maximum=100, value=r["rate"], length=135).pack(side="left", padx=8)
                tk.Label(line, text=f"{r['rate']:.0f}% ({r['total']})", font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(side="left")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(10, 8))
        tk.Label(left, text="Schwierigkeitsstufen", font=("Segoe UI Semibold", 13), bg=CARD, fg=TEXT).pack(anchor="w", padx=16, pady=(0, 6))
        levels = db.level_stats(self.profile_id, period, mode_filter)
        for level in LEVELS:
            data = levels.get(level)
            line = tk.Frame(left, bg=CARD)
            line.pack(fill="x", padx=16, pady=3)
            tk.Label(line, text=level, width=25, anchor="w", font=("Segoe UI", 9), bg=CARD, fg=TEXT).pack(side="left")
            rate = data["rate"] if data else 0
            total = data["total"] if data else 0
            ttk.Progressbar(line, maximum=100, value=rate, length=135).pack(side="left", padx=8)
            tk.Label(line, text=f"{rate:.0f}% ({total})" if total else "—", font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(side="left")

        right = tk.Frame(lower, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True, padx=(7, 0))
        tk.Label(right, text="Verlauf", font=("Segoe UI Semibold", 13), bg=CARD, fg=TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        trend = db.trend(self.profile_id, period, mode_filter)
        canvas = tk.Canvas(right, bg=CARD, highlightthickness=0, height=250)
        canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.after(50, lambda: self.draw_trend(canvas, trend))

    @staticmethod
    def draw_trend(canvas, data):
        canvas.delete("all")
        w = max(canvas.winfo_width(), 350)
        h = max(canvas.winfo_height(), 220)
        pad_l, pad_r, pad_t, pad_b = 42, 18, 18, 36
        canvas.create_line(pad_l, pad_t, pad_l, h - pad_b, fill="#cbd5e1")
        canvas.create_line(pad_l, h - pad_b, w - pad_r, h - pad_b, fill="#cbd5e1")
        for pct in [0, 25, 50, 75, 100]:
            y = h - pad_b - (h - pad_t - pad_b) * pct / 100
            canvas.create_text(pad_l - 8, y, text=str(pct), anchor="e", fill=MUTED, font=("Segoe UI", 8))
            canvas.create_line(pad_l, y, w - pad_r, y, fill="#eef2f7")
        if not data:
            canvas.create_text(w / 2, h / 2, text="Noch keine Verlaufsdaten", fill=MUTED, font=("Segoe UI", 10))
            return
        if len(data) == 1:
            xs = [pad_l + (w - pad_l - pad_r) / 2]
        else:
            step = (w - pad_l - pad_r) / (len(data) - 1)
            xs = [pad_l + i * step for i in range(len(data))]
        pts = []
        for x, item in zip(xs, data):
            y = h - pad_b - (h - pad_t - pad_b) * item["rate"] / 100
            pts.extend([x, y])
        if len(pts) >= 4:
            canvas.create_line(*pts, fill=ACCENT, width=2.5, smooth=False)
        for x, item in zip(xs, data):
            y = h - pad_b - (h - pad_t - pad_b) * item["rate"] / 100
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=ACCENT, outline="white", width=1)
            if len(data) <= 14:
                canvas.create_text(x, h - pad_b + 16, text=item["label"], fill=MUTED, font=("Segoe UI", 8))
                canvas.create_text(x, y - 12, text=f"{item['rate']:.0f}%", fill=TEXT, font=("Segoe UI", 8))

    def question_from_error(self, row) -> Question:
        data = dict(row)
        kind = data.get("question_kind")
        options = None
        if data.get("options_json"):
            try:
                options = json.loads(data["options_json"])
            except Exception:
                options = None
        hint = data.get("hint") or ""

        if not kind:
            fixed = next((q for q in FIXED if q.id == data["question_id"]), None)
            if fixed:
                kind = fixed.kind
                options = list(fixed.options or [])
                hint = fixed.hint
            else:
                kind = "number" if parse_number(data["correct_answer"]) is not None else "text"

        if kind == "choice" and not options:
            kind = "text"

        return Question(
            data["question_id"],
            data["category"],
            data["topic"],
            data["level"],
            data["prompt"],
            kind,
            data["correct_answer"],
            data.get("explanation") or "",
            options,
            hint,
        )

    def show_errors(self):
        content = self.shell("Fehler ansehen")
        active_rows = db.active_errors(self.profile_id)
        self.title_block(content, "Fehlertraining", "Falsch beantwortete Aufgaben gezielt wiederholen")

        action = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        action.pack(fill="x", padx=38, pady=(0, 14))
        tk.Label(action, text=f"Aktive Fehler: {len(active_rows)}", font=("Segoe UI Semibold", 12), bg=CARD, fg=TEXT).pack(side="left", padx=16, pady=14)
        tk.Label(action, text="Ein Fehler gilt nach zwei späteren richtigen Antworten als gefestigt.", font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(side="left", padx=(12, 0))
        ttk.Button(action, text="Fehlerhistorie", command=self.show_error_history).pack(side="right", padx=12, pady=8)
        if active_rows:
            ttk.Button(action, text="Fehlertraining starten", style="Accent.TButton", command=lambda: self.start_error_training(active_rows)).pack(side="right", pady=8)

        if not active_rows:
            empty = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            empty.pack(fill="x", padx=38)
            tk.Label(empty, text="Aktuell sind keine offenen Fehler vorhanden.", font=("Segoe UI Semibold", 12), bg=CARD, fg=SUCCESS).pack(anchor="w", padx=18, pady=(18, 4))
            tk.Label(empty, text="Frühere falsche Antworten bleiben über die Fehlerhistorie sichtbar.", font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(anchor="w", padx=18, pady=(0, 18))
            return

        holder = tk.Frame(content, bg=BG)
        holder.pack(fill="both", expand=True, padx=38, pady=(0, 24))
        canvas = tk.Canvas(holder, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        for row in active_rows:
            card = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=(0, 10))
            tk.Label(card, text=f"{row['category']} · {row['topic']} · {row['level']}", font=("Segoe UI Semibold", 10), bg=CARD, fg=TEXT).pack(anchor="w", padx=16, pady=(12, 4))
            tk.Label(card, text=row["prompt"], font=("Segoe UI", 9), bg=CARD, fg=TEXT, wraplength=790, justify="left").pack(anchor="w", padx=16)
            tk.Label(card, text=f"Deine letzte falsche Antwort: {row['user_answer'] or '—'}", font=("Segoe UI", 9), bg=CARD, fg=DANGER).pack(anchor="w", padx=16, pady=(6, 0))
            tk.Label(card, text=f"Richtige Antwort: {row['correct_answer']}", font=("Segoe UI", 9), bg=CARD, fg=SUCCESS).pack(anchor="w", padx=16, pady=(2, 0))
            if row.get("explanation"):
                tk.Label(
                    card,
                    text=f"Erklärung: {row['explanation']}",
                    font=("Segoe UI", 9),
                    bg=CARD,
                    fg=TEXT,
                    wraplength=790,
                    justify="left",
                ).pack(anchor="w", padx=16, pady=(5, 0))
            recovered = int(row["recovery_correct"])
            needed = int(row["recovery_required"])
            tk.Label(card, text=f"Festigung: {recovered} von {needed} späteren richtigen Antworten", font=("Segoe UI", 8), bg=CARD, fg=WARNING).pack(anchor="w", padx=16, pady=(4, 10))

        # Scrollen mit dem Mausrad funktioniert über der gesamten Fehlerliste,
        # nicht nur direkt über dem Scrollbalken.
        self._bind_mousewheel_tree(holder, canvas)

    def start_error_training(self, rows):
        questions = [self.question_from_error(row) for row in rows]
        if not questions:
            return
        TrainingSession(self, self.profile_id, "Fehlertraining", "Gemischt", len(questions), mode="error_training", fixed_questions=questions)

    def show_error_history(self):
        rows = db.wrong_history(self.profile_id, limit=100)
        win = tk.Toplevel(self)
        win.title("Fehlerhistorie")
        win.geometry("920x650")
        win.configure(bg=BG)
        tk.Label(win, text="Fehlerhistorie", font=("Segoe UI Semibold", 22), bg=BG, fg=TEXT).pack(anchor="w", padx=24, pady=(22, 4))
        tk.Label(win, text="Frühere falsche Antworten bleiben erhalten, auch wenn sie im Fehlertraining später gefestigt wurden.", font=("Segoe UI", 9), bg=BG, fg=MUTED).pack(anchor="w", padx=24, pady=(0, 14))
        if not rows:
            tk.Label(win, text="Noch keine falschen Antworten gespeichert.", font=("Segoe UI", 11), bg=BG, fg=MUTED).pack(anchor="w", padx=24)
            return

        holder = tk.Frame(win, bg=BG)
        holder.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        canvas = tk.Canvas(holder, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        for row in rows:
            dt = datetime.fromisoformat(row["created_at"]).strftime("%d.%m.%Y %H:%M")
            card = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=(0, 9))
            tk.Label(card, text=f"{dt} · {row['category']} · {row['topic']} · {row['level']}", font=("Segoe UI Semibold", 9), bg=CARD, fg=TEXT).pack(anchor="w", padx=14, pady=(10, 3))
            tk.Label(card, text=row["prompt"], font=("Segoe UI", 9), bg=CARD, fg=TEXT, wraplength=810, justify="left").pack(anchor="w", padx=14)
            tk.Label(
                card,
                text=f"Deine Antwort: {row['user_answer'] or '—'}",
                font=("Segoe UI", 8),
                bg=CARD,
                fg=DANGER,
                wraplength=810,
                justify="left",
            ).pack(anchor="w", padx=14, pady=(5, 2))
            tk.Label(
                card,
                text=f"Richtige Antwort: {row['correct_answer']}",
                font=("Segoe UI", 8),
                bg=CARD,
                fg=SUCCESS,
                wraplength=810,
                justify="left",
            ).pack(anchor="w", padx=14, pady=(0, 3))
            if row.get("explanation"):
                tk.Label(
                    card,
                    text=f"Erklärung: {row['explanation']}",
                    font=("Segoe UI", 8),
                    bg=CARD,
                    fg=TEXT,
                    wraplength=810,
                    justify="left",
                ).pack(anchor="w", padx=14, pady=(0, 10))

        # Auch im separaten Historienfenster lässt sich die Liste mit dem
        # Mausrad scrollen, während der Zeiger über Text oder Karten steht.
        self._bind_mousewheel_tree(holder, canvas)

    def show_exam_history(self):
        rows = db.exam_history(self.profile_id, limit=30)
        win = tk.Toplevel(self)
        win.title("Prüfungsverlauf")
        win.geometry("860x500")
        win.configure(bg=BG)
        tk.Label(win, text="Prüfungsverlauf", font=("Segoe UI Semibold", 22), bg=BG, fg=TEXT).pack(anchor="w", padx=24, pady=(22, 4))
        tk.Label(win, text="Hier werden die zuletzt abgeschlossenen Prüfungen dieses Profils angezeigt.", font=("Segoe UI", 9), bg=BG, fg=MUTED).pack(anchor="w", padx=24, pady=(0, 14))
        if not rows:
            tk.Label(win, text="Noch keine abgeschlossene Prüfung gespeichert.", font=("Segoe UI", 11), bg=BG, fg=MUTED).pack(anchor="w", padx=24)
            return

        columns = ("date", "level", "result", "rate", "points", "time")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=12)
        headings = {"date": "Datum", "level": "Stufe", "result": "Ergebnis", "rate": "Quote", "points": "Punkte", "time": "Zeit"}
        widths = {"date": 145, "level": 130, "result": 110, "rate": 80, "points": 80, "time": 100}
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="center" if col != "level" else "w")
        tree.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        for row in rows:
            dt = datetime.fromisoformat(row["started_at"]).strftime("%d.%m.%Y %H:%M")
            total = int(row["total_questions"])
            correct = int(row["correct_count"])
            rate = correct / total * 100 if total else 0
            tree.insert("", "end", values=(dt, row["level"], f"{correct} / {total}", f"{rate:.1f}%", row["points"], self.format_duration(row["elapsed_seconds"])))

    @staticmethod
    def format_duration(seconds: float) -> str:
        seconds = max(0, float(seconds))
        if seconds < 60:
            return f"{max(1, int(round(seconds)))} Sek."
        minutes = int(round(seconds / 60))
        if minutes < 60:
            return f"{minutes} Min."
        return f"{minutes // 60} Std. {minutes % 60} Min."


class TrainingSession(tk.Toplevel):
    def __init__(
        self,
        app: KBMApp,
        profile_id: int,
        category: str,
        level: str,
        count: int,
        mode: str = "training",
        fixed_questions: list[Question] | None = None,
        subtopic: str | None = None,
    ):
        super().__init__(app)
        self.app = app
        self.profile_id = profile_id
        self.category = category
        self.level = level
        self.subtopic = subtopic or MIXED_SUBTOPIC
        self.fixed_questions = list(fixed_questions or [])
        self.count = len(self.fixed_questions) if self.fixed_questions else count
        self.mode = mode
        self.index = 0
        self.correct_count = 0
        self.points = 0
        self.hints_used = 0
        self.started_at = datetime.now()
        self.question_started = datetime.now()
        self.current: Question | None = None
        self.answer_var = tk.StringVar()
        self.choice_var = tk.StringVar(value="__NO_SELECTION__")
        self.results: list[tuple[Question, str, bool]] = []
        self.used_question_ids: set[str] = set()
        self.used_semantic_keys: set[str] = set()
        self.recent_by_key: dict[tuple[str, str, str], set[str]] = {}
        self.recent_semantics_by_key: dict[tuple[str, str, str], set[str]] = {}
        self.exam_categories = list(CATEGORIES)
        random.shuffle(self.exam_categories)
        self.session_id: int | None = None
        if self.mode == "exam":
            self.session_id = db.start_exam_session(self.profile_id, self.level, self.count)

        if mode == "exam":
            title = "Prüfungssimulation"
        elif mode == "error_training":
            title = "Fehlertraining"
        else:
            title = "KBM Training"
        self.title(title)
        # Fragefenster bewusst nicht maximieren: etwas größer als früher und
        # mittig auf dem Bildschirm, damit die Aufgabe im Fokus bleibt.
        self.geometry("1080x760")
        self.minsize(820, 620)
        self.configure(bg=BG)
        self.transient(app)
        self.protocol("WM_DELETE_WINDOW", self.confirm_close)
        self.build_ui()
        # Training, Prüfung und Fehlertraining als zentriertes Arbeitsfenster öffnen.
        self.after_idle(lambda: center_window(self, 1080, 760))
        self.next_question()

    def build_ui(self):
        # Kopfzeile bleibt immer sichtbar.
        top = tk.Frame(self, bg=NAV)
        top.pack(fill="x", side="top")
        self.progress_label = tk.Label(top, text="", font=("Segoe UI Semibold", 11), bg=NAV, fg="white")
        self.progress_label.pack(side="left", padx=18, pady=14)
        self.score_label = tk.Label(top, text="", font=("Segoe UI", 10), bg=NAV, fg="#cbd5e1")
        self.score_label.pack(side="right", padx=18)

        # Fußzeile und Aktionsleiste sind bewusst NICHT Teil des Scrollbereichs.
        # Dadurch bleiben „Hinweis“ und vor allem „Nächste Aufgabe“ immer sichtbar,
        # auch wenn Frage, Antworten oder Erklärung sehr lang sind.
        tk.Label(
            self,
            text=f"Powered by Sven Herdes  ·  KBM Trainer {APP_VERSION}",
            font=("Segoe UI", 8),
            bg=BG,
            fg=FOOTER,
        ).pack(side="bottom", anchor="e", padx=20, pady=(0, 8))

        self.buttons = tk.Frame(self, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        self.buttons.pack(fill="x", side="bottom", padx=24, pady=(6, 4))
        self.hint_button = ttk.Button(self.buttons, text="Hinweis", command=self.show_hint, width=16)
        if self.mode in ("training", "error_training"):
            self.hint_button.pack(side="left", padx=10, pady=10)
        self.submit_button = ttk.Button(
            self.buttons,
            text="Antwort prüfen",
            style="Accent.TButton",
            command=self.submit,
            width=20,
        )
        self.submit_button.pack(side="right", padx=10, pady=10)

        # Der eigentliche Aufgabeninhalt ist scrollbar.
        holder = tk.Frame(self, bg=BG)
        holder.pack(fill="both", expand=True, padx=(24, 10), pady=(18, 4))
        self.content_canvas = tk.Canvas(holder, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.content_canvas.yview)
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.content_canvas.pack(side="left", fill="both", expand=True)

        self.body = tk.Frame(self.content_canvas, bg=BG)
        content_window = self.content_canvas.create_window((0, 0), window=self.body, anchor="nw")

        def sync_scrollregion(_event=None):
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

        def sync_width(event):
            self.content_canvas.itemconfigure(content_window, width=event.width)

        def on_mousewheel(event):
            if getattr(event, "delta", 0):
                direction = -1 if event.delta > 0 else 1
                self.content_canvas.yview_scroll(direction * 3, "units")
                return "break"

        self.body.bind("<Configure>", sync_scrollregion)
        self.content_canvas.bind("<Configure>", sync_width)
        self.content_canvas.bind_all("<MouseWheel>", on_mousewheel, add="+")

        self.meta_label = tk.Label(self.body, text="", font=("Segoe UI Semibold", 10), bg=BG, fg=ACCENT)
        self.meta_label.pack(anchor="w", padx=6)
        self.prompt_label = tk.Label(
            self.body, text="", font=("Segoe UI Semibold", 16), bg=BG, fg=TEXT,
            justify="left", wraplength=800
        )
        self.prompt_label.pack(anchor="w", padx=6, pady=(12, 20))
        self.answer_frame = tk.Frame(self.body, bg=BG)
        self.answer_frame.pack(fill="x", padx=6)
        self.feedback = tk.Label(
            self.body, text="", font=("Segoe UI", 10), bg=BG, fg=TEXT,
            justify="left", wraplength=800
        )
        self.feedback.pack(anchor="w", fill="x", padx=6, pady=(18, 18))

        sync_scrollregion()

    def confirm_close(self):
        label = "Prüfung" if self.mode == "exam" else "Training"
        if messagebox.askyesno(f"{label} beenden", "Die aktuelle Aufgabe wird nicht gespeichert. Wirklich beenden?", parent=self):
            if self.mode == "exam" and self.session_id is not None:
                db.abort_exam_session(self.session_id)
            self.destroy()

    def make_question(self) -> Question:
        if self.fixed_questions:
            return self.fixed_questions[self.index]

        if self.category == "Gemischt":
            cat = self.exam_categories[self.index % len(self.exam_categories)]
            if self.index and self.index % len(self.exam_categories) == 0:
                random.shuffle(self.exam_categories)
        else:
            cat = self.category

        selected_subtopic = self.subtopic if self.category != "Gemischt" else MIXED_SUBTOPIC
        key = (cat, self.level, selected_subtopic)
        if key not in self.recent_by_key:
            recent_ids = set(db.recent_question_ids(self.profile_id, cat, self.level, limit=20))
            self.recent_by_key[key] = recent_ids
            self.recent_semantics_by_key[key] = semantic_keys_for_ids(recent_ids)

        excluded = set(self.recent_by_key[key]) | self.used_question_ids
        excluded_semantics = self.used_semantic_keys | self.recent_semantics_by_key.get(key, set())
        question = generate_question(cat, self.level, exclude_ids=excluded, subtopic=selected_subtopic, exclude_semantic_keys=excluded_semantics)
        self.used_question_ids.add(question.id)
        skey = semantic_key(question)
        self.used_semantic_keys.add(skey)
        self.recent_by_key[key].add(question.id)
        self.recent_semantics_by_key.setdefault(key, set()).add(skey)
        return question

    def next_question(self):
        if self.index >= self.count:
            self.finish()
            return
        self.current = self.make_question()
        self.question_started = datetime.now()
        self.hints_used = 0
        self.answer_var.set("")
        self.choice_var.set("__NO_SELECTION__")
        self.feedback.config(text="", fg=TEXT)
        self.submit_button.config(text="Antwort prüfen", command=self.submit, state="normal")
        if self.mode in ("training", "error_training"):
            self.hint_button.config(state="normal")

        self.progress_label.config(text=f"Aufgabe {self.index + 1} von {self.count}")
        self.score_label.config(text=f"Richtig: {self.correct_count}   Punkte: {self.points}")
        self.meta_label.config(text=f"{self.current.category} · {self.current.topic} · {self.current.level}")
        self.prompt_label.config(text=self.current.prompt)
        if hasattr(self, "content_canvas"):
            self.after_idle(lambda: self.content_canvas.yview_moveto(0.0))
        for child in self.answer_frame.winfo_children():
            child.destroy()

        if self.current.kind == "choice" and self.current.options:
            options = list(self.current.options)
            random.shuffle(options)
            for option in options:
                rb = tk.Radiobutton(
                    self.answer_frame,
                    text=option,
                    value=option,
                    variable=self.choice_var,
                    tristatevalue="__TRISTATE__",
                    font=("Segoe UI", 11),
                    bg=BG,
                    fg=TEXT,
                    activebackground=BG,
                    anchor="w",
                    justify="left",
                    wraplength=760,
                    padx=8,
                    pady=6,
                )
                rb.pack(fill="x", anchor="w")
        else:
            tk.Label(self.answer_frame, text="Deine Antwort", font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 5))
            entry = ttk.Entry(self.answer_frame, textvariable=self.answer_var, font=("Segoe UI", 12), width=48)
            entry.pack(anchor="w")
            entry.focus_set()
            if self.current.kind == "number":
                helper = (
                    "Euro-Zeichen ist optional. Komma oder Punkt wird akzeptiert."
                    if "€" in self.current.correct
                    else "Nur den Zahlenwert eingeben. Komma oder Punkt wird akzeptiert."
                )
                tk.Label(self.answer_frame, text=helper, font=("Segoe UI", 8), bg=BG, fg=MUTED).pack(anchor="w", pady=(5, 0))
            entry.bind("<Return>", lambda e: self.submit())

    def show_hint(self):
        if not self.current or not self.current.hint:
            self.feedback.config(text="Für diese Aufgabe ist kein zusätzlicher Hinweis hinterlegt.", fg=MUTED)
            return
        self.hints_used += 1
        self.feedback.config(text=f"Hinweis: {self.current.hint}", fg=WARNING)
        self.hint_button.config(state="disabled")

    def submit(self):
        if not self.current:
            return
        answer = self.choice_var.get() if self.current.kind == "choice" and self.current.options else self.answer_var.get()
        if not answer.strip() or answer == "__NO_SELECTION__":
            messagebox.showinfo("Antwort", "Bitte zuerst eine Antwort eingeben oder auswählen.", parent=self)
            return
        elapsed = (datetime.now() - self.question_started).total_seconds()
        correct = self.current.check(answer)
        pts = points_for(self.current.level, correct, self.hints_used)
        self.correct_count += int(correct)
        self.points += pts
        db.save_attempt(
            self.profile_id,
            self.mode,
            self.current.category,
            self.current.topic,
            self.current.level,
            self.current.id,
            self.current.prompt,
            answer,
            self.current.correct,
            self.current.explanation,
            correct,
            elapsed,
            self.hints_used,
            pts,
            session_id=self.session_id,
            question_kind=self.current.kind,
            options=self.current.options,
            hint=self.current.hint,
        )
        self.results.append((self.current, answer, correct))
        self.index += 1

        if self.mode == "exam":
            self.next_question()
            return

        explanation = (self.current.explanation or "").strip() or "Zu dieser Aufgabe ist noch keine ausführliche Erklärung hinterlegt."
        if correct:
            msg = (
                f"Richtig. +{pts} Punkte\n\n"
                f"Richtige Antwort: {self.current.correct}\n\n"
                f"Erklärung: {explanation}"
            )
            color = SUCCESS
        else:
            msg = (
                f"Nicht richtig.\n\n"
                f"Richtige Antwort: {self.current.correct}\n\n"
                f"Erklärung: {explanation}"
            )
            color = DANGER
        self.feedback.config(text=msg, fg=color)
        self.submit_button.config(text="Nächste Aufgabe", command=self.next_question, state="normal")
        if hasattr(self, "content_canvas"):
            self.after_idle(lambda: self.content_canvas.yview_moveto(1.0))
        self.hint_button.config(state="disabled")
        self.score_label.config(text=f"Richtig: {self.correct_count}   Punkte: {self.points}")

    def finish(self):
        total_seconds = (datetime.now() - self.started_at).total_seconds()
        if self.mode == "exam" and self.session_id is not None:
            db.finish_exam_session(self.session_id, self.correct_count, self.points, total_seconds)

        for child in self.winfo_children():
            child.destroy()
        rate = self.correct_count / self.count * 100 if self.count else 0
        wrong_count = self.count - self.correct_count
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=40, pady=40)
        title = "Prüfung beendet" if self.mode == "exam" else "Fehlertraining beendet" if self.mode == "error_training" else "Training beendet"
        tk.Label(wrap, text=title, font=("Segoe UI Semibold", 26), bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(wrap, text=f"{self.correct_count} von {self.count} Aufgaben richtig", font=("Segoe UI", 13), bg=BG, fg=MUTED).pack(anchor="w", pady=(8, 24))

        cards = tk.Frame(wrap, bg=BG)
        cards.pack(fill="x")
        values = [
            ("Richtig", str(self.correct_count)),
            ("Falsch", str(wrong_count)),
            ("Erfolgsquote", f"{rate:.1f}%"),
            ("Punkte", str(self.points)),
            ("Zeit", self.app.format_duration(total_seconds)),
        ]
        for i, (title_text, value) in enumerate(values):
            card = tk.Frame(cards, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 4, 0 if i == len(values) - 1 else 4))
            cards.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=title_text, font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(anchor="w", padx=12, pady=(12, 3))
            tk.Label(card, text=value, font=("Segoe UI Semibold", 18), bg=CARD, fg=TEXT).pack(anchor="w", padx=12, pady=(0, 12))

        if self.mode == "exam":
            category_results = defaultdict(lambda: [0, 0])
            for question, _answer, correct in self.results:
                category_results[question.category][0] += 1
                category_results[question.category][1] += int(correct)
            detail = tk.Frame(wrap, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            detail.pack(fill="x", pady=(18, 0))
            tk.Label(detail, text="Ergebnis nach Bereichen", font=("Segoe UI Semibold", 11), bg=CARD, fg=TEXT).pack(anchor="w", padx=16, pady=(12, 6))
            line = "   |   ".join(f"{cat}: {vals[1]}/{vals[0]}" for cat, vals in category_results.items())
            tk.Label(detail, text=line, font=("Segoe UI", 9), bg=CARD, fg=MUTED, wraplength=760, justify="left").pack(anchor="w", padx=16, pady=(0, 12))

        if self.mode == "exam":
            stage_rec = db.stage_recommendation(self.profile_id)
            if stage_rec and stage_rec.get("from_level") == self.level:
                stage = tk.Frame(wrap, bg="#eef8f2", highlightthickness=1, highlightbackground="#cfe5d7")
                stage.pack(fill="x", pady=(14, 0))
                tk.Label(stage, text="Stufenempfehlung", font=("Segoe UI Semibold", 11), bg="#eef8f2", fg=SUCCESS).pack(anchor="w", padx=16, pady=(12, 4))
                tk.Label(
                    stage,
                    text=f"Sehr gutes Ergebnis. Deine bisherigen Leistungen sprechen dafür, jetzt mit {stage_rec['to_level']} weiterzumachen.",
                    font=("Segoe UI", 10), bg="#eef8f2", fg=TEXT, wraplength=760, justify="left"
                ).pack(anchor="w", padx=16)
                tk.Label(
                    stage,
                    text=f"Gesamtquote {stage_rec['rate']:.0f}% aus {stage_rec['total']} Aufgaben · Prüfung {(stage_rec.get('latest_exam_rate') or 0):.0f}% · {stage_rec['active_errors']} aktive Fehler",
                    font=("Segoe UI", 9), bg="#eef8f2", fg="#496b5b"
                ).pack(anchor="w", padx=16, pady=(4, 8))
                ttk.Button(
                    stage, text=f"{stage_rec['to_level']} direkt starten", style="Accent.TButton",
                    command=lambda r=stage_rec: self._start_stage_from_result(r)
                ).pack(anchor="w", padx=16, pady=(0, 12))

        buttons = tk.Frame(wrap, bg=BG)
        buttons.pack(fill="x", pady=24)
        ttk.Button(buttons, text="Zurück zum KBM Trainer", style="Accent.TButton", command=self.close_and_refresh).pack(side="left")
        if self.mode == "exam":
            ttk.Button(buttons, text="Antworten & Erklärungen ansehen", command=self.show_exam_review).pack(side="left", padx=10)
        if self.mode == "exam" and wrong_count:
            ttk.Button(buttons, text="Fehler aus dieser Prüfung trainieren", command=self.train_exam_errors).pack(side="left", padx=10)
        if self.mode == "error_training":
            tk.Label(wrap, text="Offene Fehler verschwinden aus dem aktiven Fehlertraining, sobald dieselbe Aufgabe nach dem letzten Fehler zweimal richtig beantwortet wurde.", font=("Segoe UI", 9), bg=BG, fg=MUTED, wraplength=760, justify="left").pack(anchor="w")

    def show_exam_review(self):
        win = tk.Toplevel(self)
        win.title("Prüfungsauswertung – Antworten & Erklärungen")
        win.geometry("1040x760")
        win.minsize(820, 620)
        win.configure(bg=BG)
        win.transient(self)
        center_window(win, 1040, 760)

        tk.Label(
            win,
            text="Antworten & Erklärungen",
            font=("Segoe UI Semibold", 22),
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w", padx=24, pady=(22, 4))
        tk.Label(
            win,
            text="Hier siehst du nach der Prüfung zu jeder Aufgabe deine Antwort, die richtige Lösung und die Erklärung.",
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", padx=24, pady=(0, 14))

        holder = tk.Frame(win, bg=BG)
        holder.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        canvas = tk.Canvas(holder, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        for number, (question, answer, correct) in enumerate(self.results, start=1):
            card = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=(0, 10))
            status = "Richtig" if correct else "Falsch"
            status_color = SUCCESS if correct else DANGER
            tk.Label(
                card,
                text=f"Aufgabe {number} · {question.category} · {question.topic} · {question.level} · {status}",
                font=("Segoe UI Semibold", 10),
                bg=CARD,
                fg=status_color,
            ).pack(anchor="w", padx=16, pady=(12, 4))
            tk.Label(
                card,
                text=question.prompt,
                font=("Segoe UI", 9),
                bg=CARD,
                fg=TEXT,
                wraplength=900,
                justify="left",
            ).pack(anchor="w", padx=16)
            tk.Label(
                card,
                text=f"Deine Antwort: {answer or '—'}",
                font=("Segoe UI", 9),
                bg=CARD,
                fg=SUCCESS if correct else DANGER,
                wraplength=900,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(6, 2))
            tk.Label(
                card,
                text=f"Richtige Antwort: {question.correct}",
                font=("Segoe UI", 9),
                bg=CARD,
                fg=SUCCESS,
                wraplength=900,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 3))
            explanation = (question.explanation or "").strip() or "Zu dieser Aufgabe ist noch keine ausführliche Erklärung hinterlegt."
            tk.Label(
                card,
                text=f"Erklärung: {explanation}",
                font=("Segoe UI", 9),
                bg=CARD,
                fg=TEXT,
                wraplength=900,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 12))

        self.app._bind_mousewheel_tree(holder, canvas)

    def _start_stage_from_result(self, recommendation):
        next_level = recommendation["to_level"]
        self.destroy()
        TrainingSession(
            self.app,
            self.profile_id,
            "Gemischt",
            next_level,
            10,
            mode="training",
        )

    def train_exam_errors(self):
        wrong_questions = [question for question, _answer, correct in self.results if not correct]
        self.destroy()
        self.app.show_errors()
        if wrong_questions:
            TrainingSession(
                self.app,
                self.profile_id,
                "Fehlertraining",
                "Gemischt",
                len(wrong_questions),
                mode="error_training",
                fixed_questions=wrong_questions,
            )

    def close_and_refresh(self):
        self.destroy()
        self.app.show_dashboard()


if __name__ == "__main__":
    KBMApp().mainloop()
