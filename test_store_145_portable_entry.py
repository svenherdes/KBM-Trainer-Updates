"""Separate KBM-Trainer-1.4.5-Vorschau fuer den Haupt-PC.

- Keine Installation und kein Windows-Store-Paket.
- Testprofile, Testantworten und Testeinstellungen in eigenem LOCALAPPDATA.
- Keine Desktopverknuepfung, keine Store- oder GitHub-Updates.
"""
import os
from pathlib import Path
from tkinter import messagebox

base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
test_root = base / "KBMTrainer-145-Entwicklungstest"
test_root.mkdir(parents=True, exist_ok=True)
os.environ["LOCALAPPDATA"] = str(test_root)

# Wichtig: Erst nach dem isolierten Datenpfad importieren.
import store_update_145_entry as store

# Die Vorschau DARF keine Verknuepfungen fuer die offizielle Store-App erzeugen.
store.create_store_desktop_shortcut = lambda: False


class KBM145PortableTest(store.KBMStore145):
    def __init__(self):
        super().__init__()
        self.title("KBM-Trainer 1.4.5 - NUR TEST (getrennte Profildaten)")

    def check_for_updates(self, silent=False):
        # Nie Updates / Downloads aus einer unsignierten, portablen Vorschau.
        if not silent:
            messagebox.showinfo(
                "Testversion 1.4.5",
                "Die Update-Funktion wird ausschliesslich in der echten Microsoft-Store-Version getestet.\n\n"
                "Diese Vorschau veraendert keine bestehende KBM-Trainer-Installation.",
                parent=self,
            )


if __name__ == "__main__":
    KBM145PortableTest().mainloop()
