# Windows-spezifische Problembehebung

## Port-Berechtigungsfehler (WinError 10013)

### Problem:
```
PermissionError: [WinError 10013] Der Zugriff auf einen Socket war aufgrund der Zugriffsrechte des Sockets unzulässig
```

### Ursachen:
1. **Port 5000 ist gesperrt** - Windows reserviert viele Ports für System-Dienste
2. **Andere Anwendung nutzt den Port** - z.B. andere Web-Server
3. **Firewall-Einstellungen** - Windows Defender blockiert Port-Zugriff
4. **Administrator-Rechte erforderlich** - Manche Ports benötigen erhöhte Rechte

### Lösungen:

#### 1. Alternative Ports verwenden (empfohlen)
Das mitgelieferte `start_production.bat` verwendet Port 8000:
```cmd
start_production.bat
```
Zugriff dann über: http://127.0.0.1:8000

#### 2. Manuelle Port-Wahl
```cmd
# Port 8080 (oft frei)
python -m waitress --host=127.0.0.1 --port=8080 --threads=4 app:app

# Port 3000 (entwickler-freundlich)
python -m waitress --host=127.0.0.1 --port=3000 --threads=4 app:app

# Port 8888 (Jupyter-Alternative)
python -m waitress --host=127.0.0.1 --port=8888 --threads=4 app:app
```

#### 3. Port-Verfügbarkeit prüfen
```cmd
# Prüfen welche Ports belegt sind
netstat -an | findstr :5000

# Alle TCP-Ports anzeigen
netstat -an | findstr TCP
```

#### 4. Als Administrator ausführen
1. Kommandozeile als Administrator öffnen
2. Zum Projektverzeichnis navigieren
3. `start_production.bat` ausführen

#### 5. Windows Firewall konfigurieren
1. Windows-Taste + R → `wf.msc`
2. "Eingehende Regeln" → "Neue Regel"
3. Port auswählen → TCP → Port 5000 oder 8000
4. "Verbindung zulassen" → "Alle Profile" → Name vergeben

## Häufig freie Ports unter Windows:

| Port | Beschreibung | Wahrscheinlichkeit |
|------|--------------|-------------------|
| 8000 | HTTP-Alternative | ✅ Sehr hoch |
| 8080 | HTTP-Proxy | ✅ Hoch |
| 3000 | Node.js Standard | ✅ Hoch |
| 8888 | Jupyter Alternative | ✅ Hoch |
| 9000 | Verschiedene Apps | ✅ Mittel |
| 5000 | Flask Standard | ❌ Oft gesperrt |

## Python-Kommando Probleme

### Problem: `python3` nicht gefunden
```
'python3' ist nicht als interner oder externer Befehl erkannt
```

**Lösung:** Unter Windows meist `python` verwenden:
```cmd
python -m waitress --host=127.0.0.1 --port=8000 --threads=4 app:app
```

### Problem: Python nicht im PATH
```
'python' ist nicht als interner oder externer Befehl erkannt
```

**Lösung:**
1. Python-Installation prüfen
2. PATH-Variable erweitern
3. Oder vollständigen Pfad verwenden:
```cmd
C:\Python39\python.exe -m waitress --host=127.0.0.1 --port=8000 --threads=4 app:app
```

## Waitress vs. Gunicorn unter Windows

| Feature | Waitress | Gunicorn |
|---------|----------|----------|
| Windows-Support | ✅ Nativ | ❌ Nur WSL |
| Performance | ✅ Gut | ✅ Exzellent |
| Setup-Komplexität | ✅ Einfach | ❌ WSL erforderlich |
| Empfehlung | Windows | Linux/macOS |

## Schnelle Problemdiagnose

### 1. Basis-Test
```cmd
python -c "print('Python funktioniert')"
```

### 2. Waitress-Test
```cmd
python -c "import waitress; print('Waitress installiert')"
```

### 3. Port-Test
```cmd
python -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 8000)); print('Port 8000 frei'); s.close()"
```

### 4. Flask-App-Test
```cmd
python -c "import app; print('App importierbar')"
```

## Wenn alles andere fehlschlägt

### Option 1: WSL verwenden
```cmd
# WSL installieren und Linux-Skripte verwenden
wsl --install
wsl
./start_production.sh
```

### Option 2: Docker verwenden
```dockerfile
# Dockerfile erstellen und Container nutzen
docker build -t presentai .
docker run -p 8000:5000 presentai
```

### Option 3: Entwicklungsserver
```cmd
# Als letzter Ausweg (nur für Tests)
python app.py
```