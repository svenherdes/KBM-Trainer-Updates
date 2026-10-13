@echo off
setlocal
title KBM Trainer - Quellcode unter GPL-3.0 veroeffentlichen
cd /d "%~dp0"
echo.
echo Der Trainer und die installierte Version werden dabei NICHT veraendert.
echo GitHub-Release und version.json bleiben unveraendert.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\publish_sources.ps1"
if errorlevel 1 (
  echo.
  echo VEROEFFENTLICHUNG NICHT ABGESCHLOSSEN. Bitte Fehlermeldung senden.
) else (
  echo.
  echo Quellcode und GPL-3.0-Lizenz wurden auf GitHub veroeffentlicht.
)
echo.
pause
