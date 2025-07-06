# PresentAI - Intelligente Interaktive Präsentationsplattform

![logo](screen.png)

PresentAI ist eine moderne, KI-gestützte Webanwendung für interaktive Präsentationen. Die Plattform ermöglicht es Präsentatoren, dynamische Inhalte zu erstellen, die sich automatisch basierend auf Zuhörer-Feedback weiterentwickeln. Mit fortschrittlicher KI-Integration, intelligentem Feedback-Management und robusten Fehlerbehandlungssystemen bietet PresentAI eine nahtlose Erfahrung für moderne Präsentationen.

## 🎯 Hauptfunktionen

### KI-gestützte Inhaltsgenerierung
- **Intelligente Feedback-Kategorisierung**: Automatische Unterscheidung zwischen faktischen Informationen, Fragen, Kommentaren und Antworten
- **Kontextuelle Verarbeitung**: Faktische Infos (Links, URLs) werden direkt in den Haupttext integriert
- **Strukturierte Antworten**: Fragen werden nur bei 100%iger Sicherheit beantwortet, ansonsten in "Offene Fragen" gesammelt
- **Automatische Content-Bereinigung**: Entfernung von Markdown-Markierungen für saubere Darstellung

### Robuste Fehlerbehandlung
- **Kontext-Erhaltung**: Bei API-Fehlern bleibt der bestehende Inhalt sichtbar
- **Intelligente Retry-Mechanismen**: Automatische Wiederholungsversuche mit konfigurierbaren Verzögerungen
- **Manuelle Retry-Funktion**: Präsentatoren können fehlgeschlagene KI-Aufrufe manuell erneut starten
- **Transparente Fehlermeldungen**: Klare Kommunikation bei Problemen

### Erweiterte Sicherheit
- **Content-Filterung**: Automatische Entfernung unangemessener oder beleidigender Inhalte
- **Soft-Delete System**: Gelöschte Präsentationen bleiben in der Datenbank erhalten
- **Audit-Trail**: Vollständige Nachverfolgung von Löschungen und Änderungen

### Echtzeit-Interaktion
- **Batch-Verarbeitung**: Effiziente Verarbeitung von Feedback zur API-Optimierung
- **Live-Updates**: Automatische Aktualisierung ohne manuelles Neuladen
- **QR-Code Integration**: Einfacher Zugang für Zuhörer

## 🛠️ Systemanforderungen

- Python 3.8 oder höher
- Flask 2.0+
- SQLAlchemy
- OpenAI API-Zugang (gpt-4o-mini)
- Weitere Abhängigkeiten siehe `requirements.txt`

## 🚀 Installation

### 1. Repository vorbereiten
```bash
git clone <repository-url>
cd ConfChat
```

### 2. Virtuelle Umgebung einrichten
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren
```bash
# Erforderlich
export OPENAI_API_KEY=ihr-openai-api-schlüssel

# Optional (wird automatisch generiert wenn nicht gesetzt)
export REGISTRATION_PASSWORD=ihr-registrierungspasswort
export SECRET_KEY=ihr-geheimer-schlüssel
```

**Wichtig**: Das `REGISTRATION_PASSWORD` wird beim ersten Start automatisch generiert und in der Konsole angezeigt, falls nicht gesetzt.

### 5. Datenbank migrieren (falls erforderlich)
```bash
python migrate_db.py
```

### 6. Anwendung starten
```bash
python app.py
```

### 7. Zugriff
- Hauptanwendung: http://127.0.0.1:5000/
- H2-Datenbank-Konsole: http://127.0.0.1:5000/h2-console (falls verfügbar)

## 📁 Projektstruktur

```
ConfChat/
├── app.py                      # Hauptanwendung (Flask)
├── migrate_db.py              # Datenbank-Migrierungsskript
├── requirements.txt           # Python-Abhängigkeiten
├── CLAUDE.md                  # Entwickler-Dokumentation
├── instance/
│   └── presentations.db      # SQLite-Datenbank
├── templates/                 # Jinja2-Templates
│   ├── base.html             # Basis-Layout
│   ├── dashboard.html        # Präsentations-Dashboard
│   ├── view_presentation.html # Präsentations-Manager
│   ├── public_view.html      # Öffentliche Zuhörer-Ansicht
│   └── ...                   # Weitere Templates
├── static/                    # Statische Dateien
└── test_*.py                 # Test-Suiten
```

## 🎭 Verwendung

### Für Präsentatoren

1. **Registrierung/Anmeldung**
   - Erster Benutzer wird automatisch als Admin eingerichtet
   - Nutzen Sie das generierte Registrierungspasswort

2. **Präsentation erstellen**
   - Titel, Beschreibung, Kontext und Hauptinhalt eingeben
   - KI generiert automatisch strukturierte Inhalte

3. **Zuhörer einladen**
   - QR-Code oder direkten Link teilen
   - Zuhörer erhalten Zugang zur Live-Infoseite

4. **Feedback verwalten**
   - Überwachung eingehender Fragen und Kommentare
   - Manuelle Retry-Funktion bei KI-Problemen
   - Automatische Kategorisierung verschiedener Feedback-Arten

### Für Zuhörer

1. **Zugang über QR-Code oder Link**
2. **Live-Infoseite betrachten**
   - Automatisch aktualisierte Inhalte
   - Strukturierte Darstellung mit Markdown-Formatierung
3. **Interaktion**
   - Fragen stellen
   - Zusätzliche Informationen oder Links teilen
   - Kommentare abgeben

## ⚙️ Erweiterte Konfiguration

### Feedback-Verarbeitung
```python
# In app.py anpassbar
FEEDBACK_PROCESSING_INTERVAL = 30  # Sekunden zwischen Verarbeitungen
FEEDBACK_BATCH_WINDOW = 30         # Sammelzeit für Batch-Processing
CLIENT_REFRESH_INTERVAL = 20       # Client-Aktualisierungsintervall
```

### Retry-Mechanismen
- **Automatische Verzögerung**: 10 Sekunden nach API-Fehlern
- **Kontext-Erhaltung**: Bestehende Inhalte bleiben bei Fehlern sichtbar
- **Manuelle Kontrolle**: Retry-Button für Präsentatoren

### Content-Filterung
- **Blacklist-basiert**: Automatische Entfernung unangemessener Begriffe
- **Kategorisierung**: Links, Fragen, Kommentare werden intelligent sortiert
- **Markdown-Bereinigung**: Entfernung störender Code-Block-Markierungen

## 🔧 Entwicklung & Erweiterung

### Wichtige Komponenten

1. **KI-Integration** (`generate_ai_content()`)
   - Feedback-Kategorisierung
   - Prompt-Engineering für verschiedene Content-Typen
   - Fehlerbehandlung und Retry-Logik

2. **Soft-Delete System**
   - Präsentationen werden als gelöscht markiert, bleiben aber in DB
   - Vollständiger Audit-Trail
   - Wiederherstellbarkeit

3. **Background Processing**
   - Thread-basierte Feedback-Verarbeitung
   - Intelligente Warteschlangen-Verwaltung
   - Retry-Verzögerungen respektieren

### Tests ausführen
```bash
# Einzelne Tests
python test_improved_prompt.py
python test_soft_delete.py
python test_markdown_filter.py

# Alle Tests
python -m pytest test_*.py
```

### Demo-Skripte
```bash
python demo_improved_prompt.py    # Feedback-Kategorisierung
python demo_soft_delete.py        # Soft-Delete Verhalten
python demo_improved_behavior.py  # Fehlerbehandlung
```

## 🎨 Anpassungen

### KI-Provider wechseln
Die Anwendung kann einfach für andere KI-APIs angepasst werden:
- OpenAI GPT-4o-mini (Standard)
- Claude (Anthropic)
- Google Gemini
- Hugging Face

### UI-Anpassungen
- Templates in `templates/` Verzeichnis
- Bootstrap 4 für responsives Design
- Erweiterbare CSS-Klassen

### Funktionalitäts-Erweiterungen
- WebSocket-Integration für Echtzeit-Chat
- Datei-Upload für Präsentationen
- Erweiterte Benutzerverwaltung
- Export-Funktionen (PDF, Word)

## 🛡️ Sicherheit

- **Eingabe-Validierung**: Schutz vor Injection-Angriffen
- **Content-Filterung**: Automatische Moderation
- **Session-Management**: Sichere Benutzer-Sessions
- **API-Schlüssel-Schutz**: Umgebungsvariablen für sensible Daten

## 📊 Monitoring & Debugging

- **Konsolen-Logging**: Detaillierte Logs für Debugging
- **Error-Tracking**: Vollständige Fehlerprotokollierung
- **Performance-Monitoring**: API-Aufruf-Optimierung
- **Audit-Trail**: Benutzeraktivitäten nachverfolgbar

## 🤝 Contributing

1. Fork des Repositories
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE` Datei für Details.

## 🙏 Danksagungen

- OpenAI für GPT-4o-mini API
- Flask-Community für das excellente Framework
- Bootstrap für das responsive UI-Framework
- Alle Contributor und Tester