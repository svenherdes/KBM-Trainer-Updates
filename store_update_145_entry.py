"""Nur Microsoft-Store-Paket 1.4.5. Original 1.4.3/GitHub-Updater bleibt unveraendert."""
import tkinter as tk
from tkinter import messagebox
import threading
import webbrowser

import app as original
import db
from store_entry import KBMStoreApp
from store_features_145 import (
    FEEDBACK_URL, STORE_PRODUCT_URL, stage_display_rows,
    prioritized_error_rows, create_store_desktop_shortcut, run_store_helper,
)

original.APP_VERSION = "1.4.5"
original.APP_TITLE = "KBM Trainer 1.4.5"


class KBMStore145(KBMStoreApp):
    def __init__(self):
        super().__init__()
        self.after(1800, lambda: threading.Thread(target=create_store_desktop_shortcut, daemon=True).start())
        self.after(2500, lambda: self.check_for_updates(silent=True))

    def shell(self, active):
        content = super().shell(active)
        nav = self.current_frame.winfo_children()[0]
        about = next((item for item in nav.winfo_children()
                      if isinstance(item, tk.Button) and item.cget("text") == "Über den KBM Trainer"), None)
        if about is not None:
            tk.Button(
                nav, text="Feedback", command=self.open_feedback,
                font=("Segoe UI", 10), bg=original.NAV, fg="#cbd5e1",
                activebackground=original.NAV_ACTIVE, activeforeground="white",
                bd=0, anchor="w", padx=20, pady=8, cursor="hand2",
            ).pack(fill="x", before=about)
        return content

    def open_feedback(self):
        if not webbrowser.open(FEEDBACK_URL):
            messagebox.showinfo("Feedback", "Das Feedbackformular konnte nicht automatisch geöffnet werden.\n\n" + FEEDBACK_URL, parent=self)

    def _stage_progress_card(self, parent, *, has_learning_data=True):
        # Gleiche Logik, gleiche Profildaten und Kriterien. Nur Beschriftungen lesbarer.
        card = tk.Frame(parent, bg=original.CARD, highlightthickness=1, highlightbackground=original.BORDER)
        card.pack(fill="x", padx=38, pady=(0, 18))
        tk.Label(card, text="Stufenfortschritt", font=("Segoe UI Semibold", 14), bg=original.CARD,
                 fg=original.TEXT).pack(anchor="w", padx=18, pady=(14, 8))
        if not has_learning_data:
            tk.Label(card, text="Für dieses Profil liegen noch keine Lerndaten vor. Starte ein Training, um deinen persönlichen Fortschritt zu sehen.",
                     font=("Segoe UI", 10), bg=original.CARD, fg=original.MUTED,
                     wraplength=850, justify="left").pack(anchor="w", padx=18, pady=(0, 16))
            return card
        body = tk.Frame(card, bg=original.CARD)
        body.pack(fill="x", padx=18, pady=(0, 16))
        for col, (from_level, to_level) in enumerate([("Anfänger", "Fortgeschritten"), ("Fortgeschritten", "Experte")]):
            progress = db.stage_progress(self.profile_id, from_level)
            qualification = db.stage_qualification(progress)
            passed = qualification["qualified"]
            background = "#eef8f2" if passed else "#f8fafc"
            panel = tk.Frame(body, bg=background, highlightthickness=1, highlightbackground=original.BORDER)
            panel.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 7, 7 if col == 0 else 0))
            body.grid_columnconfigure(col, weight=1)
            tk.Label(panel, text=f"{from_level} → {to_level}", font=("Segoe UI Semibold", 11),
                     bg=background, fg=original.TEXT).pack(anchor="w", padx=12, pady=(12, 3))
            tk.Label(panel, text=f"Bereit für {to_level}" if passed else f"Noch nicht bereit für {to_level}",
                     font=("Segoe UI Semibold", 9), bg=background,
                     fg=original.SUCCESS if passed else original.WARNING).pack(anchor="w", padx=12, pady=(0, 8))
            for label, value, met in stage_display_rows(progress, qualification):
                row = tk.Frame(panel, bg=background)
                row.pack(fill="x", padx=12, pady=2)
                tk.Label(row, text=("✓ " if met else "○ ") + label, font=("Segoe UI", 9),
                         bg=background, fg=original.SUCCESS if met else original.MUTED).pack(anchor="w")
                tk.Label(row, text=value, font=("Segoe UI Semibold", 9),
                         bg=background, fg=original.TEXT).pack(anchor="w", padx=16)
            if passed:
                recommendation = {"from_level": from_level, "to_level": to_level, **progress}
                tk.Button(panel, text=f"{to_level} starten",
                          command=lambda r=recommendation: self.start_stage_recommendation(r)).pack(anchor="e", padx=12, pady=(10, 12))
            else:
                tk.Label(panel, text="Die Stufe bleibt frei wählbar. Das ist nur eine Empfehlung.",
                         font=("Segoe UI", 8), bg=background, fg=original.MUTED).pack(anchor="w", padx=12, pady=(10, 12))
        return card

    def start_error_training(self, rows):
        # Nur Reihenfolge; zwei richtige Antworten zur Festigung bleiben unveraendert.
        ranked = prioritized_error_rows(rows, db.wrong_history(self.profile_id, limit=100000))
        return super().start_error_training(ranked)

    def _store_update_result(self, status, silent=False):
        if status == "AVAILABLE":
            if messagebox.askyesno("KBM-Trainer Update", "Ein Update ist im Microsoft Store verfügbar.\n\nJetzt herunterladen und installieren?", parent=self):
                threading.Thread(target=self._install_store_update, daemon=True).start()
        elif status == "NONE" and not silent:
            messagebox.showinfo("Updates", "Es ist aktuell kein Store-Update verfügbar.", parent=self)
        elif status in ("ERROR", "UNAVAILABLE") and not silent:
            if messagebox.askyesno("Store-Updates", "Die direkte Store-Abfrage ist derzeit nicht möglich.\n\nMicrosoft Store zur Update-Prüfung öffnen?", parent=self):
                self._open_store()

    def _open_store(self):
        try:
            import os
            os.startfile(STORE_PRODUCT_URL)
        except (OSError, AttributeError):
            webbrowser.open("https://apps.microsoft.com/detail/9NSW4QQ70KVT")

    def _install_store_update(self):
        status = run_store_helper("install", timeout=240)
        self.after(0, lambda: self._store_install_finished(status))

    def _store_install_finished(self, status):
        if status == "INSTALLED":
            messagebox.showinfo("Update", "Der Microsoft Store hat die Installation abgeschlossen. Bitte starte den KBM-Trainer bei Bedarf neu.", parent=self)
        else:
            messagebox.showinfo("Store-Update", "Die Installation konnte nicht direkt abgeschlossen werden. Der Microsoft Store wird geöffnet.", parent=self)
            self._open_store()

    def check_for_updates(self, silent=False):
        # Nie den alten GitHub-Updater in Store-Installationen benutzen.
        def worker():
            status = run_store_helper("check", timeout=90)
            self.after(0, lambda: self._store_update_result(status, silent))
        threading.Thread(target=worker, daemon=True).start()

    def download_and_install_update(self, preconfirmed=False):
        self.check_for_updates(silent=False)

    def show_updates_window(self):
        self.check_for_updates(silent=False)

    def show_updates(self):
        content = self.shell("Updates")
        self.title_block(content, "Updates", "Neue Versionen kommen ausschließlich über den Microsoft Store")
        tk.Button(content, text="Jetzt nach Store-Updates suchen",
                  command=lambda: self.check_for_updates(silent=False)).pack(anchor="w", padx=38, pady=10)
        tk.Button(content, text="Microsoft Store öffnen", command=self._open_store).pack(anchor="w", padx=38, pady=10)


if __name__ == "__main__":
    KBMStore145().mainloop()
