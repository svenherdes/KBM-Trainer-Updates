from pathlib import Path
import hashlib, json, shutil

VERSION = "1.4.3"
SETUP_NAME = f"KBM-Trainer-Setup-{VERSION}.exe"
RELEASE_TAG = f"v{VERSION}"
REPO = "svenherdes/KBM-Trainer-Updates"

root = Path(__file__).resolve().parent
installer_dir = root / "dist" / "installer"
setup = installer_dir / SETUP_NAME
if not setup.exists():
    raise SystemExit(f"FEHLER: {setup} wurde nicht gefunden.")

sha = hashlib.sha256(setup.read_bytes()).hexdigest().lower()
download_url = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}/{SETUP_NAME}"

manifest = {
    "version": VERSION,
    "channel": "stable",
    "download_url": download_url,
    "sha256": sha,
    "notes": (
        "600 neue Aufgaben: Finanzbuchhaltung (180), kaufmännische Steuerung (180), "
        "Einkauf (120) und Logistik (120). Je drei Schwierigkeitsstufen; "
        "insgesamt 4.200 Fragen. Keine Änderungen an Benutzerprofilen oder "
        "dem bestehenden automatischen GitHub-Updateverfahren."
    ),
}

(installer_dir / "SHA256.txt").write_text(f"{sha}  {SETUP_NAME}\n", encoding="utf-8")
(installer_dir / "version.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

upload = installer_dir / "UPLOAD_DIESE_DATEIEN"
if upload.exists():
    shutil.rmtree(upload)
upload.mkdir()
shutil.copy2(setup, upload / setup.name)
shutil.copy2(installer_dir / "version.json", upload / "version.json")
shutil.copy2(installer_dir / "SHA256.txt", upload / "SHA256.txt")

print("UPDATE-RELEASEDATEIEN ERSTELLT")
print(f"Setup: {setup}")
print(f"SHA-256: {sha}")
print(f"Release-Tag: {RELEASE_TAG}")
print(f"Download: {download_url}")
print(f"Ordner: {upload}")
