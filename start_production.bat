@echo off
REM PresentAI - Windows Produktions-Start-Skript
REM Für Windows-Umgebungen ohne WSL

echo === PresentAI Produktions-Start (Windows) ===
echo Verwende Waitress als WSGI-Server...

REM Überprüfung ob Waitress installiert ist
python3 -c "import waitress" >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Waitress ist nicht installiert.
    echo Installieren Sie es mit: python3 -m pip install waitress
    pause
    exit /b 1
)

REM Überprüfung der benötigten Umgebungsvariablen
if "%OPENAI_API_KEY%"=="" (
    echo WARNUNG: OPENAI_API_KEY ist nicht gesetzt.
    echo Setzen Sie die Variable oder die Anwendung wird nicht funktionieren.
)

REM Produktions-Konfiguration
set FLASK_ENV=production

REM Start mit Waitress (Windows-kompatibel)
echo Starte Waitress mit 4 Threads...
echo HINWEIS: Verwendet Port 8000 (Port 5000 oft gesperrt unter Windows)
echo Zugriff über: http://127.0.0.1:8000
echo Zum Beenden: Ctrl+C
echo.

python3 -m waitress --host=127.0.0.1 --port=8000 --threads=4 app:app