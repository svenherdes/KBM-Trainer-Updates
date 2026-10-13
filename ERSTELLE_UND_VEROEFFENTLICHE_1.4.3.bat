@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title KBM Trainer 1.4.3 - Windows-Update automatisch veroeffentlichen

echo ==================================================
echo  Schritt 1: Windows-Setup bauen und pruefen
 echo ==================================================
call "%~dp0ERSTELLE_UPDATE_1.4.3.bat" --auto
if errorlevel 1 goto :failed

echo.
echo ==================================================
echo  WICHTIG: Windows-Installer lokal testen.
echo  Setup-Datei: dist\installer\KBM-Trainer-Setup-1.4.3.exe
echo  Starte das Setup und kontrolliere Programmstart,
echo  deine Profile und eine neue Frage pro Wissensbereich.
echo ==================================================
start "" "%~dp0dist\installer\"
choice /C JN /N /M "Lokal geprueft und alles okay? (J/N): "
if errorlevel 2 goto :failed

echo.
echo ==================================================
echo  Schritt 2: GitHub-Zugang pruefen
 echo ==================================================
where gh >nul 2>&1
if errorlevel 1 (
  echo GitHub CLI ist noch nicht installiert. Versuche Installation ...
  winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
  if errorlevel 1 goto :failed
  echo Falls gh nach der Installation nicht gefunden wird, Fenster erneut starten.
)
set "PATH=%PATH%;%ProgramFiles%\GitHub CLI;%LOCALAPPDATA%\Programs\GitHub CLI"
gh auth status >nul 2>&1
if errorlevel 1 (
  echo Bitte einmalig in GitHub anmelden. Browser-Anmeldung wird gestartet.
  gh auth login --web
  if errorlevel 1 goto :failed
)

echo.
echo ==================================================
echo  Schritt 3: Setup hochladen, SHA-256 pruefen,
echo  dann Updatehinweis per version.json freigeben.
echo ==================================================
python publish_github_143.py
if errorlevel 1 goto :failed

echo.
echo ERFOLG: Update 1.4.3 wurde auf GitHub freigegeben.
pause
exit /b 0
:failed
echo.
echo Abbruch: Update wurde NICHT vollstaendig veroeffentlicht.
echo Pruefe die obigen Fehlermeldungen. Falls ein Release schon existiert,
echo aber version.json noch 1.4.2 meldet, bitte erst den Fehler klaeren.
pause
exit /b 1
