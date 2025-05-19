# ConfChat - Interaktive KI-gestützte Präsentationsplattform

## Systemanforderungen
- Python 3.8 oder höher
- Flask 2.0 oder höher
- SQLAlchemy
- Flask-Login
- Werkzeug
- qrcode
- Pillow (für QR-Code-Generierung)
- requests (für API-Kommunikation)
- markdown (für Markdown-Rendering)
- markupsafe (für sicheres HTML-Rendering)

## Installation

1. Repository klonen oder Dateien herunterladen

2. Virtuelle Umgebung erstellen:
```bash
python -m venv venv
```

3. Virtuelle Umgebung aktivieren:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

5. Umgebungsvariablen setzen:
```bash
# Windows
set FLASK_APP=app.py
set FLASK_ENV=development
set SECRET_KEY=dein-geheimer-schlüssel
set OPENAI_API_KEY=dein-openai-api-schlüssel

# macOS/Linux
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY=dein-geheimer-schlüssel
export OPENAI_API_KEY=dein-openai-api-schlüssel
```

6. Anwendung starten:
```bash
python app.py
```

7. Im Browser öffnen: http://127.0.0.1:5000/

## Projektstruktur

```
/
├── app.py                 # Hauptanwendung
├── requirements.txt       # Abhängigkeiten
├── templates/             # HTML-Templates
│   ├── base.html          # Basis-Template
│   ├── index.html         # Startseite
│   ├── login.html         # Login-Seite
│   ├── register.html      # Registrierungsseite
│   ├── dashboard.html     # Dashboard-Seite
│   ├── new_presentation.html    # Neue Präsentation
│   ├── view_presentation.html   # Präsentation anzeigen
│   ├── edit_presentation.html   # Präsentation bearbeiten
│   └── public_view.html         # Öffentliche Ansicht
├── static/                # Statische Dateien
└── presentations.db       # SQLite-Datenbank
```

## Verwendung

### Admin-Bereich
1. Registrieren Sie sich - der erste Benutzer wird automatisch als Admin eingerichtet
2. Erstellen Sie neue Präsentationen mit Titel, Beschreibung, Kontext und Inhalt
3. Verwalten Sie bestehende Präsentationen (anzeigen, bearbeiten, löschen)
4. Teilen Sie den Link oder QR-Code mit Ihrem Publikum

### Zuhörer-Bereich
1. Zugriff auf die öffentliche Ansicht über den geteilten Link oder QR-Code
2. Anzeige der KI-generierten Informationen basierend auf der Präsentation
3. Möglichkeit, Fragen oder zusätzliche Informationen einzugeben
4. Automatische Aktualisierung der Seite, wenn neue Inhalte verfügbar sind

## Leistungsmerkmale

### KI-Integration
- Automatische Generierung von Präsentationsinhalten basierend auf Kontext und Inhalt
- Intelligente Verarbeitung von Zuhörer-Feedback
- Markdown-Unterstützung für formatierte Inhalte (Überschriften, Listen, Tabellen, etc.)

### Optimierte Leistung
- Batch-Verarbeitung von Feedback-Anfragen zur Reduzierung der API-Aufrufe
- Caching von KI-generierten Inhalten zur Verbesserung der Ladezeiten
- Konfigurierbare Client-Aktualisierungsintervalle

### Benutzerfreundlichkeit
- Automatische Benachrichtigungen bei Inhaltsänderungen
- Echtzeit-Aktualisierung der Inhalte ohne manuelles Neuladen
- Responsive Design für verschiedene Geräte

## Konfiguration

Die Anwendung bietet verschiedene Konfigurationsoptionen in app.py:

- `FEEDBACK_PROCESSING_INTERVAL`: Zeit in Sekunden zwischen Feedback-Verarbeitungen (Standard: 30)
- `FEEDBACK_BATCH_WINDOW`: Zeitfenster in Sekunden, in dem Feedback gesammelt wird (Standard: 30)
- `CLIENT_REFRESH_INTERVAL`: Zeit in Sekunden zwischen Client-Aktualisierungen (Standard: 20)

## KI-Integration

Die Anwendung nutzt OpenAI's GPT-4 für die KI-Funktionalität. Wenn Sie keinen OpenAI API-Schlüssel haben, können Sie folgende Optionen nutzen:

1. Beantragen Sie einen API-Schlüssel bei OpenAI: https://openai.com/api/
2. Verwenden Sie alternative KI-Dienste wie:
   - Hugging Face API
   - Google Gemini API
   - Claude (Anthropic) API

Ändern Sie dafür die `generate_ai_content`-Funktion in app.py entsprechend.

## Anpassung und Erweiterung

### Design anpassen
- Bearbeiten Sie base.html und die CSS-Stile nach Ihren Wünschen

### Funktionalität erweitern
- Fügen Sie weitere KI-Funktionen hinzu, z.B. Zusammenfassungen oder Übersetzungen
- Implementieren Sie Datei-Uploads für Präsentationen
- Erstellen Sie eine Echtzeit-Chat-Funktion mit WebSockets
- Fügen Sie erweiterte Benutzerverwaltung und Berechtigungen hinzu
