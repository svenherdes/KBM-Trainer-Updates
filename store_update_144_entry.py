"""Microsoft-Store-Update 1.4.4: separater Startpunkt ohne GitHub-Updates.

Die normale Windows-Version, ihr Installer und ihr Updater bleiben unangetastet.
Die App-Logik kommt aus dem geprüften Entwicklungszweig; nur die Store-
Versionsanzeige wird auf 1.4.4 gesetzt.
"""
import app as original

# Ausschliesslich in diesem Store-Update-Einstieg: korrekte 1.4.4-Anzeige.
original.APP_VERSION = "1.4.4"
original.APP_TITLE = "KBM Trainer 1.4.4"

# Bewaehrter Store-Einstieg deaktiviert die GitHub-Update-Wege.
from store_entry import KBMStoreApp


if __name__ == "__main__":
    KBMStoreApp().mainloop()
