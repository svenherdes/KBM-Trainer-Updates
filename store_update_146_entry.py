"""Store-Edition 1.4.6: Desktop-Symbol beim Installieren per MSIX.
Lern- und Profilfunktionen unveraendert aus Version 1.4.5.
"""
from store_update_145_entry import KBMStore145
import app as original

original.APP_VERSION = "1.4.6"
original.APP_TITLE = "KBM Trainer 1.4.6"


class KBMStore146(KBMStore145):
    pass


if __name__ == "__main__":
    KBMStore146().mainloop()
