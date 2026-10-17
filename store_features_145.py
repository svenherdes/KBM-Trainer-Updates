"""Isolierte Funktionen fuer die Microsoft-Store-Ausgabe 1.4.5.

Keine Aenderungen an Datenbank, Lernregeln oder GitHub-Updater.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import os
import subprocess
import sys

FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdUJqQ4CNQPNbCcYr-So82fEnjxDAShc4xQL1QpGSUFShDFtw/viewform?usp=publish-editor"
STORE_PRODUCT_URL = "ms-windows-store://pdp/?ProductId=9NSW4QQ70KVT"


def stage_display_rows(progress: dict, qualification: dict):
    """Einfacher lesbare Werte, exakt dieselben Qualifikationsregeln."""
    limits = qualification["requirements"]
    criteria = qualification["criteria"]
    exam = progress.get("latest_exam_rate")
    rows = [
        ("Bearbeitete Aufgaben", f"{progress['total']} bearbeitet · Ziel mindestens {limits['attempts']}", criteria["attempts"]),
        ("Gesamtquote", f"{progress['rate']:.0f}% erreicht · Ziel {limits['rate']:.0f}%", criteria["rate"]),
        ("Letzte Pruefung", f"{exam:.0f}% erreicht · Ziel {limits['exam']:.0f}%" if exam is not None else f"Noch keine · Ziel {limits['exam']:.0f}%", criteria["exam"]),
        ("Aktive Fehler", f"{progress['active_errors']} offen · hoechstens {limits['errors']}", criteria["errors"]),
    ]
    return rows


def prioritized_error_rows(active_rows, wrong_history):
    """Mehrfach falsch beantwortete offene Fragen zuerst, ohne die DB zu aendern.

    Profilbezogene Historie muss vom Aufrufer zum selben Profil stammen.
    Bereits teilweise gefestigte Fehler folgen danach.
    """
    counts = Counter(str(row["question_id"]) for row in wrong_history)
    return sorted(
        active_rows,
        key=lambda row: (
            -counts.get(str(row["question_id"]), 0),
            int(row.get("recovery_correct", 0)),
            -int(row.get("id", 0)),
        ),
    )


def create_store_desktop_shortcut():
    """Einmal beim Start der Store-Ausgabe eine stabile AppsFolder-Verknuepfung.

    Nutzt den Windows-Paketfamiliennamen statt versionsabhaengiger EXE-Pfade.
    Verhindert Dopplungen. Uebergeht Systeme ohne Store-Paketidentitaet.
    """
    if os.name != "nt":
        return False
    command = r'''
$ErrorActionPreference = 'Stop'
$pkg = Get-AppxPackage -Name 'SvenHerdes.KBM-Trainer' |
       Sort-Object Version -Descending | Select-Object -First 1
if ($null -eq $pkg) { exit 2 }
$desktop = [Environment]::GetFolderPath('Desktop')
if (-not $desktop) { exit 3 }
$path = Join-Path $desktop 'KBM-Trainer.lnk'
$icon = Join-Path $pkg.InstallLocation 'KBM-Trainer.exe'
if (-not (Test-Path -LiteralPath $icon)) { exit 4 }
$ws = New-Object -ComObject WScript.Shell
if (Test-Path -LiteralPath $path) {
    # Nur die eigene alte Store-Verknuepfung reparieren; keine fremden Links ersetzen.
    $existing = $ws.CreateShortcut($path)
    $expectedArguments = "shell:AppsFolder\$($pkg.PackageFamilyName)!KBMTrainer"
    $expectedTarget = Join-Path $env:WINDIR 'explorer.exe'
    if (($existing.TargetPath -ieq $expectedTarget) -and
        ($existing.Arguments -eq $expectedArguments)) {
        $existing.IconLocation = "$icon,0"
        $existing.Save()
    }
    exit 0
}
$link = $ws.CreateShortcut($path)
$link.TargetPath = Join-Path $env:WINDIR 'explorer.exe'
$link.Arguments = "shell:AppsFolder\$($pkg.PackageFamilyName)!KBMTrainer"
$link.IconLocation = "$icon,0"
$link.Description = 'KBM-Trainer aus dem Microsoft Store'
$link.Save()
'''
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            check=False, timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            capture_output=True, text=True,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def helper_path() -> Path:
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    return base / "KBM-Store-Update.exe"


def run_store_helper(action: str, timeout: int = 100):
    """Uebergibt Store-Updates ausschliesslich an Windows.Services.Store."""
    if action not in ("check", "install"):
        raise ValueError("Unbekannte Update-Aktion")
    executable = helper_path()
    if os.name != "nt" or not executable.is_file():
        return "UNAVAILABLE"
    try:
        result = subprocess.run([str(executable), action], capture_output=True,
                                text=True, timeout=timeout,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        output = (result.stdout or "").strip().splitlines()
        status = output[-1].strip() if output else "UNAVAILABLE"
        return status if result.returncode == 0 else "ERROR"
    except (OSError, subprocess.TimeoutExpired):
        return "ERROR"
