#!/bin/bash

# PresentAI - Erweiterte Produktions-Konfiguration
# Für höhere Performance (mit kleinem Threading-Risiko)

echo "=== PresentAI Erweiterte Produktions-Konfiguration ==="
echo "WARNUNG: Verwendet 2 Worker - Background-Processing könnte doppelt ausgeführt werden"
echo "Überwachen Sie die Logs auf doppelte Feedback-Verarbeitung!"

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

# Start mit mehr Workern für höhere Performance
echo "Starte Gunicorn mit 2 Workern + 2 Threads pro Worker..."
echo "Zugriff über: http://0.0.0.0:5000"
echo "Zum Beenden: Ctrl+C"
echo ""

python -m gunicorn \
    --workers 2 \
    --threads 2 \
    --bind 0.0.0.0:5000 \
    --timeout 60 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app