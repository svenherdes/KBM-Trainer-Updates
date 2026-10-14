"""Microsoft-Store-Startpunkt fuer KBM-Trainer 1.4.3.

Wichtig: Diese Datei wird NUR vom separaten MSIX-Testbuild verwendet.
Der regulaere Windows-Build nutzt unveraendert app.py und seinen GitHub-Updater.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import app as original


STORE_UPDATE_NOTICE = (
    "Diese Ausgabe des KBM-Trainers wird ueber den Microsoft Store aktualisiert.\n\n"
    "Bitte oeffne fuer verfuegbare Updates die Bibliothek im Microsoft Store.\n\n"
    "Der GitHub-Installer ist in dieser Store-Ausgabe deaktiviert. "
    "Deine Lernstaende bleiben lokal gespeichert."
)


class KBMStoreApp(original.KBMApp):
    """Originaltrainer mit ausschliesslich Store-spezifischem Updateverhalten."""

    def _load_settings(self) -> dict:
        # Unabhaengig von gespeicherten Einstellungen: kein GitHub-Check beim Start.
        values = super()._load_settings()
        return {**values, "check_updates_on_start": False}

    def check_for_updates(self, silent: bool = False) -> None:
        # Auch manuelle oder spaeter hinzugefuegte Aufrufe oeffnen keinen GitHub-Link.
        if not silent:
            messagebox.showinfo("KBM-Trainer – Updates", STORE_UPDATE_NOTICE, parent=self)

    def download_and_install_update(self, preconfirmed: bool = False) -> None:
        # Zweite Sicherheitsbarriere: kein Download und kein Start des GitHub-Installers.
        messagebox.showinfo("KBM-Trainer – Updates", STORE_UPDATE_NOTICE, parent=self)

    def show_updates_window(self) -> None:
        # Der Profilbildschirm besitzt weiterhin den bekannten Updates-Einstieg.
        messagebox.showinfo("KBM-Trainer – Updates", STORE_UPDATE_NOTICE, parent=self)

    def show_updates(self) -> None:
        # Eventuell vorhandene interne Navigation zeigt einen Store-Hinweis.
        content = self.shell("Updates")
        self.title_block(content, "Updates", "Updates fuer diese Ausgabe kommen aus dem Microsoft Store")
        card = tk.Frame(
            content,
            bg=original.CARD,
            highlightthickness=1,
            highlightbackground=original.BORDER,
        )
        card.pack(fill="x", padx=38, pady=(0, 16))
        tk.Label(
            card,
            text=f"Installierte Store-Version: {original.APP_VERSION}",
            font=("Segoe UI Semibold", 13),
            bg=original.CARD,
            fg=original.TEXT,
        ).pack(anchor="w", padx=20, pady=(18, 10))
        tk.Label(
            card,
            text=STORE_UPDATE_NOTICE,
            font=("Segoe UI", 10),
            bg=original.CARD,
            fg=original.MUTED,
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 18))


if __name__ == "__main__":
    KBMStoreApp().mainloop()
