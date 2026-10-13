@echo off
setlocal EnableExtensions

rem ---------------------------------------------------------------------------
rem KBM Trainer - externer Update-Helfer
rem Dieser Prozess laeuft ausserhalb der PyInstaller-Anwendung.
rem Er wartet auf das Ende des alten Trainers, installiert das Update und
rem startet die feste Programmdatei KBM-Trainer.exe neu.
rem ---------------------------------------------------------------------------

set "APP_PID=%~1"
set "SETUP_PATH=%~2"
set "INSTALL_DIR=%~3"
set "NEW_VERSION=%~4"
set "APP_EXE=%~5"
set "HELPER_LOG=%~6"
set "INSTALL_LOG=%~7"
set "RESULT_FILE=%~8"

>"%HELPER_LOG%" echo KBM Trainer Update %NEW_VERSION%
>>"%HELPER_LOG%" echo Setup: %SETUP_PATH%
>>"%HELPER_LOG%" echo Ziel: %INSTALL_DIR%
>>"%HELPER_LOG%" echo Warte auf PID %APP_PID%

:wait_for_app
tasklist /FI "PID eq %APP_PID%" /NH 2>nul | find "%APP_PID%" >nul
if not errorlevel 1 (
  timeout /t 1 /nobreak >nul
  goto wait_for_app
)

>>"%HELPER_LOG%" echo Altes Programm beendet.

if not exist "%SETUP_PATH%" (
  >>"%HELPER_LOG%" echo FEHLER: Setup nicht gefunden.
  >"%RESULT_FILE%" echo FEHLER SETUP_FEHLT
  exit /b 2
)

start /wait "" "%SETUP_PATH%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR="%INSTALL_DIR%" /LOG="%INSTALL_LOG%"
set "UPDATE_EXIT=%ERRORLEVEL%"
>>"%HELPER_LOG%" echo Installer Exit-Code: %UPDATE_EXIT%

if not "%UPDATE_EXIT%"=="0" (
  >"%RESULT_FILE%" echo FEHLER %UPDATE_EXIT%
  exit /b %UPDATE_EXIT%
)

if not exist "%APP_EXE%" (
  >>"%HELPER_LOG%" echo FEHLER: Neue EXE nicht gefunden: %APP_EXE%
  >"%RESULT_FILE%" echo FEHLER EXE_FEHLT
  exit /b 3
)

>"%RESULT_FILE%" echo OK %NEW_VERSION%
>>"%HELPER_LOG%" echo Update erfolgreich. Starte %APP_EXE%

rem Wichtig fuer PyInstaller-Onefile: Die neue App darf die alte _MEI-Umgebung
rem nicht erben.
set "PYINSTALLER_RESET_ENVIRONMENT=1"
start "" "%APP_EXE%"

exit /b 0
