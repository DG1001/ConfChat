# Produktions-Setup Notizen

## Multi-Platform Produktions-Setup

### Linux/macOS/WSL (Gunicorn):
- `./start_production.sh` - Empfohlene Konfiguration (1 Worker + 4 Threads)
- `./start_production_advanced.sh` - Höhere Performance (2 Worker + 2 Threads)

### Windows (Waitress):
- `start_production.bat` - Windows-kompatible Lösung (4 Threads)

### Manuelle Ausführung:

**Linux/macOS/WSL:**
```bash
# Sichere Konfiguration
python -m gunicorn --workers 1 --threads 4 --bind 0.0.0.0:5000 app:app

# Erweiterte Konfiguration  
python -m gunicorn --workers 2 --threads 2 --bind 0.0.0.0:5000 app:app
```

**Windows:**
```cmd
# Waitress (Windows-kompatibel)
python -m waitress --host=0.0.0.0 --port=5000 --threads=4 app:app
```

## Abhängigkeits-Kompatibilität

### SQLAlchemy-Problem (Python 3.13):
Falls SQLAlchemy-Kompatibilitätsfehler auftreten:

```bash
# Spezifische SQLAlchemy-Version installieren
pip install "SQLAlchemy<2.1" 

# Oder Flask-SQLAlchemy downgraden
pip install "Flask-SQLAlchemy<3.1"
```

### Empfohlene Python-Versionen:
- **Python 3.8-3.11**: Vollständig kompatibel
- **Python 3.12**: Meist kompatibel
- **Python 3.13**: Mögliche SQLAlchemy-Probleme

## Performance-Erwartungen

| Konfiguration | Concurrent Users | Empfehlung |
|---------------|------------------|------------|
| `python app.py` | 10-20 | Nur Entwicklung |
| `start_production.sh` | 100-200 | Empfohlen |
| `start_production_advanced.sh` | 200-500 | Erfahrene Nutzer |

## Threading-Verhalten

### Sichere Konfiguration (1 Worker):
- Background-Processing funktioniert wie erwartet
- Keine doppelte Feedback-Verarbeitung
- Robuste SQLite-Performance

### Erweiterte Konfiguration (2+ Worker):
- **Risiko**: Background-Threads in jedem Worker
- **Monitoring erforderlich**: Logs auf doppelte Verarbeitung prüfen
- **Lösung bei Problemen**: Zurück zu 1 Worker

## Monitoring

### Wichtige Log-Nachrichten:
```
"Feedback für Präsentation X markiert" - Normal
"Feedback-Generierung für Präsentation X fehlgeschlagen" - Retry-Verhalten
```

### Doppelte Verarbeitung erkennen:
- Gleiche Feedback-IDs mehrfach in Logs
- Identische AI-Responses zur selben Zeit
- Unerwartete Performance-Probleme

## Nächste Schritte für Skalierung

Wenn mehr als 500 concurrent users benötigt:
1. **PostgreSQL** statt SQLite
2. **Celery** für Background-Tasks
3. **Redis** für Sessions
4. **Nginx** als Reverse Proxy