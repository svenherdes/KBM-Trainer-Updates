@echo off
setlocal EnableExtensions
title KBM Trainer 1.4.3 - Wissensbereiche-Update
cd /d "%~dp0"

echo ==================================================
echo   KBM Trainer 1.4.3 - WISSENSBEREICHE-UPDATE
echo ==================================================
echo.
echo Fester EXE-Name: KBM-Trainer.exe
echo Update-System: externer Windows-Helfer
echo.

echo [1/6] Dateien und Python pruefen ...
python --version
if errorlevel 1 goto :python_missing
if not exist "app.py" goto :files_missing
if not exist "KBM-Update-Helper.cmd" goto :files_missing
if not exist "assets\kbm_trainer.ico" goto :files_missing
if not exist "version_info.txt" goto :files_missing
if not exist "privacy_pool.py" goto :files_missing
if not exist "knowledge_143.py" goto :files_missing
if not exist "FACHQUELLEN_1.4.3.txt" goto :files_missing

echo.
echo [2/6] Tests fuer Programm und neue Wissensbereiche ...
python test_core.py
if errorlevel 1 goto :fail
if exist "test_exam_style.py" (
  python test_exam_style.py
  if errorlevel 1 goto :fail
)
if exist "test_privacy.py" (
  python test_privacy.py
  if errorlevel 1 goto :fail
)

if exist "test_knowledge_143.py" (
  python test_knowledge_143.py
  if errorlevel 1 goto :fail
)
if exist "pool_audit.py" (
  python pool_audit.py
  if errorlevel 1 goto :fail
)

echo.
echo [3/6] PyInstaller vorbereiten ...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :fail

echo.
echo [4/6] KBM-Trainer.exe erstellen ...
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "KBM-Trainer" ^
  --icon "assets\kbm_trainer.ico" ^
  --add-data "assets;assets" ^
  --version-file "version_info.txt" ^
  "app.py"
if errorlevel 1 goto :fail

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC (
  where winget >nul 2>&1
  if not errorlevel 1 (
    echo Inno Setup 6 wird einmalig installiert ...
    winget install --id JRSoftware.InnoSetup -e --accept-source-agreements --accept-package-agreements
    if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
    if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
  )
)
if not defined ISCC goto :inno_missing

echo.
echo [5/6] Windows-Setup erstellen ...
"%ISCC%" "installer.iss"
if errorlevel 1 goto :fail

echo.
echo [6/6] Release-Dateien vorbereiten ...
python "make_release_files.py"
if errorlevel 1 goto :fail

echo.
echo ==================================================
echo   FERTIG - KBM TRAINER 1.4.3
echo ==================================================
echo.
echo ZUERST NUR LOKAL TESTEN.
echo Installer:
echo dist\installer\KBM-Trainer-Setup-1.4.3.exe
echo.
echo NEU: 600 Aufgaben in Finanzbuchhaltung, Steuerung, Einkauf und Logistik.
echo Update-System unveraendert wie beim erfolgreichen 1.4.0 -> 1.4.1 Test.
echo Erst lokal testen, danach als GitHub-Update veroeffentlichen.
echo.
if /I "%~1"=="--auto" exit /b 0
if exist "dist\installer\UPLOAD_DIESE_DATEIEN" explorer "dist\installer\UPLOAD_DIESE_DATEIEN"
pause
exit /b 0

:python_missing
echo FEHLER: Python wurde auf diesem Build-PC nicht gefunden.
pause
exit /b 1

:files_missing
echo FEHLER: Das Paket wurde nicht vollstaendig entpackt.
pause
exit /b 1

:inno_missing
echo FEHLER: Inno Setup 6 wurde nicht gefunden.
pause
exit /b 1

:fail
echo.
echo ==================================================
echo   ERSTELLUNG FEHLGESCHLAGEN
echo ==================================================
echo Bitte die letzte Fehlermeldung fotografieren.
pause
exit /b 1
