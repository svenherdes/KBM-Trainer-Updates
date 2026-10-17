"""Isolierter UI-Test fuer Stufenfortschritt. Keine Installation und keine GitHub-Updates.

Alle Profile, Versuche und Einstellungen landen ausschliesslich unter
%LOCALAPPDATA%\\KBMTrainer-Stufenfortschritt-TEST\\KBMTrainer.
Die offizielle KBM-Trainer-Installation wird nicht veraendert.
"""
import os
from pathlib import Path

_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
_test_root = _base / "KBMTrainer-Stufenfortschritt-TEST"
_test_root.mkdir(parents=True, exist_ok=True)
os.environ["LOCALAPPDATA"] = str(_test_root)

# Import erst NACH dem Setzen von LOCALAPPDATA: db.DB_PATH wird beim Import festgelegt.
from store_entry import KBMStoreApp


class StufenfortschrittTest(KBMStoreApp):
    def __init__(self):
        super().__init__()
        self.title("KBM-Trainer - Stufenfortschritt-TEST (getrennte Profildaten)")


if __name__ == "__main__":
    StufenfortschrittTest().mainloop()
