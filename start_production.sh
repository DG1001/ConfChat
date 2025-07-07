#!/bin/bash

# PresentAI - Produktions-Start-Skript
# Minimal-Setup für parallele Zugriffe

echo "=== PresentAI Produktions-Start ==="
echo "Verwende Gunicorn für bessere Performance..."

# Überprüfung ob Gunicorn installiert ist
if ! python -c "import gunicorn" &> /dev/null; then
    echo "FEHLER: Gunicorn ist nicht installiert."
    echo "Installieren Sie es mit: python -m pip install gunicorn"
    exit 1
fi

# Überprüfung der benötigten Umgebungsvariablen
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNUNG: OPENAI_API_KEY ist nicht gesetzt."
    echo "Setzen Sie die Variable oder die Anwendung wird nicht funktionieren."
fi

# Produktions-Konfiguration
export FLASK_ENV=production

# Start mit optimalen Einstellungen für Threading-Kompatibilität
echo "Starte Gunicorn mit 1 Worker + 4 Threads..."
echo "Zugriff über: http://0.0.0.0:5000"
echo "Zum Beenden: Ctrl+C"
echo ""

python -m gunicorn \
    --workers 1 \
    --threads 4 \
    --bind 0.0.0.0:5000 \
    --timeout 60 \
    --keep-alive 2 \
    --log-level info \
    app:app