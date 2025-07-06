# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from markupsafe import Markup
import markdown as md
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from io import BytesIO
import base64
import os
import uuid
import requests
import json
from datetime import datetime, timedelta
import markdown
import threading
import time
import secrets
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///presentations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfiguration für die Feedback-Verarbeitung
app.config['FEEDBACK_PROCESSING_INTERVAL'] = 30  # Sekunden zwischen den Verarbeitungen
app.config['FEEDBACK_BATCH_WINDOW'] = 30  # Sekunden, in denen Feedback gesammelt wird
app.config['CLIENT_REFRESH_INTERVAL'] = 20  # Sekunden zwischen Client-Aktualisierungen

# Registrierungspasswort
REGISTRATION_PASSWORD = os.environ.get('REGISTRATION_PASSWORD')
if not REGISTRATION_PASSWORD:
    # Generiere ein zufälliges Passwort, wenn keines gesetzt ist
    chars = string.ascii_letters + string.digits
    REGISTRATION_PASSWORD = ''.join(secrets.choice(chars) for _ in range(12))
    print(f"\n\n*** WICHTIG: Generiertes Registrierungspasswort: {REGISTRATION_PASSWORD} ***\n\n")

# Markdown-Filter für Templates
@app.template_filter('markdown')
def markdown_filter(text):
    return Markup(md.markdown(text))

# OpenAI API Key - in production, use environment variables
app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'your-api-key')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Datenbank-Modelle
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    presentations = db.relationship('Presentation', 
                                    foreign_keys='Presentation.user_id',
                                    backref='creator', lazy=True)
    deleted_presentations = db.relationship('Presentation', 
                                           foreign_keys='Presentation.deleted_by_user_id',
                                           backref='deleted_by', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Presentation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    context = db.Column(db.Text)
    content = db.Column(db.Text)
    access_code = db.Column(db.String(10), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedbacks = db.relationship('Feedback', backref='presentation', lazy=True, cascade="all, delete-orphan")
    cached_ai_content = db.Column(db.Text)  # Deprecated - wird durch static_info_content ersetzt
    static_info_content = db.Column(db.Text)  # Statische Info-Seite (einmal generiert)
    feedback_content = db.Column(db.Text)     # Dynamischer Feedback-Bereich
    last_updated = db.Column(db.DateTime)
    processing_scheduled = db.Column(db.Boolean, default=False)
    next_processing_time = db.Column(db.DateTime)
    
    # Fehlerbehandlung für KI-Anfragen
    last_error_message = db.Column(db.Text, nullable=True)
    last_error_time = db.Column(db.DateTime, nullable=True)
    failed_context = db.Column(db.Text, nullable=True)  # Kontext bei Fehlern beibehalten
    retry_after = db.Column(db.DateTime, nullable=True)  # Wann frühestens wieder versucht werden darf
    
    # Soft Delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Soft Delete Helper Methods
    def soft_delete(self, deleted_by_user_id):
        """Markiert die Präsentation als gelöscht"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by_user_id = deleted_by_user_id
    
    @classmethod
    def get_active(cls, id):
        """Gibt eine aktive (nicht gelöschte) Präsentation zurück"""
        return cls.query.filter_by(id=id, is_deleted=False).first()
    
    @classmethod
    def get_active_or_404(cls, id):
        """Gibt eine aktive Präsentation zurück oder 404"""
        presentation = cls.get_active(id)
        if not presentation:
            from flask import abort
            abort(404)
        return presentation
    
    @classmethod
    def get_by_access_code(cls, access_code):
        """Gibt eine aktive Präsentation anhand des Access Codes zurück"""
        return cls.query.filter_by(access_code=access_code, is_deleted=False).first()
    
    @classmethod
    def get_active_by_user(cls, user_id):
        """Gibt alle aktiven Präsentationen eines Benutzers zurück"""
        return cls.query.filter_by(user_id=user_id, is_deleted=False).all()

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentation.id'), nullable=False)
    is_processed = db.Column(db.Boolean, default=False)
    ai_response = db.Column(db.Text)
    participant_name = db.Column(db.String(100), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Markdown zu HTML konvertieren
def clean_markdown_response(text):
    """Entfernt Markdown-Code-Block-Markierungen aus KI-Antworten"""
    if not text:
        return text
    
    # Entferne ```markdown am Anfang und ``` am Ende
    text = text.strip()
    
    # Prüfe und entferne ```markdown am Anfang (case-insensitive)
    if text.lower().startswith('```markdown'):
        text = text[11:].strip()
    elif text.startswith('```'):
        text = text[3:].strip()
    
    # Entferne ``` am Ende
    if text.endswith('```'):
        text = text[:-3].strip()
    
    return text

def markdown_to_html(text):
    """Konvertiert Markdown-Text zu HTML"""
    # Erst die Code-Block-Markierungen entfernen
    cleaned_text = clean_markdown_response(text)
    return Markup(markdown.markdown(cleaned_text, extensions=['tables']))

# KI-Integration

def generate_static_info_content(title, description, context, content):
    """Generiert statische Info-Seite basierend auf Präsentationsdaten."""
    print("\n--- Statische Info-Generierung ---")
    print(f"Titel: {title}")
    print(f"Beschreibung: {description}")
    print("----------------------------------\n")
    
    prompt = f"""
    Erstelle eine strukturierte und informative Seite im Markdown-Format basierend auf den folgenden Präsentationsinformationen.
    
    WICHTIGE REGELN:
    - Verwende nur die gegebenen Informationen als Grundlage
    - Du kannst allgemein bekannte Fakten zu dem Thema ergänzen, aber keine spekulativen Informationen
    - Strukturiere den Inhalt logisch und verständlich
    - Verwende Markdown-Formatierung für klare Struktur
    - Keine Feedback-Sektionen erstellen - das ist nur die Info-Seite
    - Keine Informationen erfinden, die nicht aus den gegebenen Daten ableitbar sind
    
    # Titel der Präsentation
    {title}
    
    # Beschreibung
    {description}
    
    # Kontext/Hintergrund
    {context}
    
    # Hauptinhalt
    {content}
    """
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app.config['OPENAI_API_KEY']}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Du bist ein Experte für die Erstellung von informativen und gut strukturierten Präsentationsinhalten im Markdown-Format. Erstelle klare, sachliche Inhalte basierend auf den gegebenen Informationen."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500
            }
        )
        response_data = response.json()
        if 'choices' not in response_data:
            print(f"Fehler bei der statischen Info-Generierung: {response_data}")
            return None
        
        ai_response = response_data['choices'][0]['message']['content']
        cleaned_response = clean_markdown_response(ai_response)
        return cleaned_response
    except Exception as e:
        print(f"Fehler bei der statischen Info-Generierung: {str(e)}")
        return None

def generate_feedback_content(feedbacks, static_info_content, existing_feedback_content=None):
    """Generiert dynamischen Feedback-Bereich basierend auf Zuhörer-Feedback."""
    print("\n--- Feedback-Bereich Generierung ---")
    print(f"Anzahl der Feedbacks: {len(feedbacks) if feedbacks else 0}")
    print("-----------------------------------\n")
    
    if not feedbacks:
        return ""
    
    prompt = f"""
    Erstelle einen strukturierten Feedback-Bereich im Markdown-Format basierend auf den Zuhörer-Feedbacks.
    
    WICHTIGE REGELN FÜR KATEGORISIERUNG UND FILTERUNG:
    - Kategorisiere das Feedback AUTOMATISCH und INTELLIGENT in folgende Bereiche:
      * Faktische Informationen und Ergänzungen (konkrete Daten, Zahlen, Fakten)
      * Fragen (erkennbar an Fragezeichen oder Fragewörtern)
      * Antworten auf vorherige Fragen
      * Ungeprüfte Links (URLs, Links - SEPARATE Sektion mit Warnung!)
      * Positive Kommentare und Meinungen
      * Sonstige relevante Kommentare
    
    - IGNORIERE KOMPLETT und ERWÄHNE NICHT:
      * Beleidigungen, Schimpfwörter, persönliche Angriffe
      * Spam, Werbung, Off-Topic Inhalte
      * Unpassende oder anstößige Inhalte
      * Trolle und unsinnige Beiträge
    
    - SPEZIELLE BEHANDLUNG:
      * **ZUSAMMENFASSUNG**: Fasse ähnliche Fragen/Kommentare/Hinweise intelligent zusammen für bessere Lesbarkeit
      * **Links einzeln auflisten**: Jeder Link in eigener Zeile mit kurzer KI-Beschreibung (falls erkennbar)
      * **Struktur**: Verwende klare Markdown-Überschriften und Unterpunkte
      * **Kontext nutzen**: Verwende die Info-Seite als Kontext für bessere Kategorisierung
      * **Nur echtes Feedback**: Keine Informationen erfinden - nur echtes, relevantes Feedback verwenden
    
    # Info-Seite (als Kontext für Kategorisierung)
    {static_info_content}
    
    # Bisheriger Feedback-Bereich (falls vorhanden)
    {existing_feedback_content or "Noch kein Feedback vorhanden."}
    
    # Alle Zuhörer-Feedbacks (bitte intelligent kategorisieren und filtern):
    """
    
    for i, feedback in enumerate(feedbacks, 1):
        prompt += f"\n{i}. {feedback.content}"
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app.config['OPENAI_API_KEY']}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Du bist ein Experte für die Kategorisierung und Strukturierung von Feedback im Markdown-Format. Erstelle klare, strukturierte Feedback-Bereiche und ignoriere unpassende Inhalte komplett."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500
            }
        )
        response_data = response.json()
        if 'choices' not in response_data:
            print(f"Fehler bei der Feedback-Generierung: {response_data}")
            return None
        
        ai_response = response_data['choices'][0]['message']['content']
        cleaned_response = clean_markdown_response(ai_response)
        return cleaned_response
    except Exception as e:
        print(f"Fehler bei der Feedback-Generierung: {str(e)}")
        return None


def store_error_context(presentation_id, error_msg, previous_content, feedbacks):
    """Speichert Fehlerkontext für spätere Wiederverwendung."""
    if presentation_id:
        try:
            presentation = Presentation.query.get(presentation_id)
            if presentation:
                now = datetime.utcnow()
                presentation.last_error_message = error_msg
                presentation.last_error_time = now
                
                # Retry-Verzögerung: 10 Sekunden warten
                from datetime import timedelta
                presentation.retry_after = now + timedelta(seconds=10)
                
                # Kontext für Wiederverwendung speichern
                # WICHTIG: Aktuellen Seiteninhalt verwenden (vor dem fehlgeschlagenen Update)
                # Das ist der cached_ai_content OHNE die neuen Feedbacks
                if presentation.cached_ai_content:
                    presentation.failed_context = presentation.cached_ai_content
                else:
                    # Bei Ersterstellung Kontext aus Präsentation verwenden
                    presentation.failed_context = f"## {presentation.title}\n\n{presentation.description or ''}"
                
                db.session.commit()
        except Exception as e:
            print(f"Fehler beim Speichern des Fehlerkontexts: {e}")

# Routen
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error="Ungültiger Benutzername oder Passwort")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        reg_password = request.form.get('registration_password')
        
        # Prüfen, ob das Registrierungspasswort korrekt ist
        if reg_password != REGISTRATION_PASSWORD:
            return render_template('register.html', error="Falsches Registrierungspasswort")
        
        # Prüfen, ob Benutzer bereits existiert
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Benutzername bereits vergeben")
        
        # Neuen Benutzer erstellen
        user = User(username=username)
        user.set_password(password)
        
        # Ersten Benutzer zum Admin machen
        if User.query.count() == 0:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registrierung erfolgreich!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    presentations = Presentation.get_active_by_user(current_user.id)
    return render_template('dashboard.html', presentations=presentations)

@app.route('/presentation/new', methods=['GET', 'POST'])
@login_required
def new_presentation():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        context = request.form.get('context')
        content = request.form.get('content')
        
        # Eindeutigen Zugangscode generieren
        access_code = str(uuid.uuid4())[:8]
        
        presentation = Presentation(
            title=title,
            description=description,
            context=context,
            content=content,
            access_code=access_code,
            user_id=current_user.id
        )
        
        db.session.add(presentation)
        db.session.commit()
        
        # Statische Info-Seite generieren
        static_info = generate_static_info_content(title, description, context, content)
        if static_info:
            presentation.static_info_content = static_info
            db.session.commit()
        
        return redirect(url_for('dashboard'))
    
    return render_template('new_presentation.html')

@app.route('/presentation/<int:id>')
@login_required
def view_presentation(id):
    presentation = Presentation.get_active_or_404(id)
    
    # Überprüfen, ob der Benutzer der Ersteller ist
    if presentation.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    # QR-Code generieren
    presentation_url = url_for('public_view', access_code=presentation.access_code, _external=True)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(presentation_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered)
    qr_code = base64.b64encode(buffered.getvalue()).decode()
    
    feedbacks = Feedback.query.filter_by(presentation_id=id).order_by(Feedback.created_at.desc()).all()
    
    return render_template('view_presentation.html', presentation=presentation, qr_code=qr_code, 
                          presentation_url=presentation_url, feedbacks=feedbacks)

@app.route('/presentation/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_presentation(id):
    presentation = Presentation.get_active_or_404(id)
    
    # Überprüfen, ob der Benutzer der Ersteller ist
    if presentation.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        presentation.title = request.form.get('title')
        presentation.description = request.form.get('description')
        presentation.context = request.form.get('context')
        presentation.content = request.form.get('content')
        
        # Cache zurücksetzen, da sich der Inhalt geändert hat
        presentation.cached_ai_content = None
        
        db.session.commit()
        return redirect(url_for('view_presentation', id=id))
    
    return render_template('edit_presentation.html', presentation=presentation)

@app.route('/presentation/<int:id>/delete', methods=['POST'])
@login_required
def delete_presentation(id):
    presentation = Presentation.get_active_or_404(id)
    
    # Überprüfen, ob der Benutzer der Ersteller ist
    if presentation.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    # Soft Delete: Präsentation als gelöscht markieren, aber in DB behalten
    presentation.soft_delete(current_user.id)
    db.session.commit()
    
    flash(f'Präsentation "{presentation.title}" wurde gelöscht.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/presentation/<int:id>/retry_ai', methods=['POST'])
@login_required
def retry_ai_generation(id):
    presentation = Presentation.get_active_or_404(id)
    
    # Überprüfen, ob der Benutzer der Ersteller ist
    if presentation.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    # Unverarbeitete Feedbacks abrufen
    unprocessed_feedbacks = Feedback.query.filter_by(
        presentation_id=id, 
        is_processed=False
    ).all()
    
    # Kontext für KI-Aufruf bestimmen (mit Fehlerkontext falls verfügbar)
    content_to_use = presentation.failed_context or presentation.cached_ai_content
    
    # Manuellen KI-Aufruf durchführen
    if unprocessed_feedbacks or content_to_use:
        ai_response = generate_ai_content(
            feedbacks=unprocessed_feedbacks,
            previous_content=content_to_use,
            context=presentation.context,
            content=presentation.content,
            presentation_id=id
        )
        
        # Bei erfolgreichem KI-Aufruf aktualisieren
        if ai_response is not None:
            for feedback in unprocessed_feedbacks:
                feedback.ai_response = ai_response
                feedback.is_processed = True
            
            # Präsentations-Cache aktualisieren und Fehlerkontext löschen
            presentation.cached_ai_content = ai_response
            presentation.last_updated = datetime.utcnow()
            presentation.processing_scheduled = False
            presentation.next_processing_time = None
            presentation.last_error_message = None
            presentation.last_error_time = None
            presentation.failed_context = None
            presentation.retry_after = None  # Retry-Verzögerung zurücksetzen
            
            db.session.commit()
            flash('KI-Inhalte erfolgreich aktualisiert!', 'success')
        else:
            flash('Fehler beim Generieren der KI-Inhalte. Bitte versuchen Sie es später erneut.', 'error')
    else:
        flash('Keine neuen Feedbacks zum Verarbeiten vorhanden.', 'info')
    
    return redirect(url_for('view_presentation', id=id))

@app.route('/p/<access_code>')
def public_view(access_code):
    presentation = Presentation.get_by_access_code(access_code)
    if not presentation:
        from flask import abort
        abort(404)
    
    # Status der Verarbeitung
    processing_status = {
        'scheduled': presentation.processing_scheduled,
        'next_update': presentation.next_processing_time.isoformat() if presentation.next_processing_time else None
    }
    
    return render_template('public_view.html', presentation=presentation, 
                          processing_status=processing_status,
                          config=app.config)

# Globales Wörterbuch für die Feedback-Verarbeitung
feedback_processing_queue = {}
processing_thread = None
processing_lock = threading.Lock()

def process_feedback_queue():
    """Hintergrundthread zur Verarbeitung von Feedback-Anfragen in Batches"""
    global feedback_processing_queue
    
    while True:
        time.sleep(1)  # Kurze Pause, um CPU-Last zu reduzieren
        
        now = datetime.utcnow()
        presentations_to_process = []
        
        with processing_lock:
            # Präsentationen identifizieren, die verarbeitet werden müssen
            for presentation_id, data in list(feedback_processing_queue.items()):
                if now >= data['next_processing_time']:
                    presentations_to_process.append(presentation_id)
        
        # Verarbeitung der identifizierten Präsentationen
        for presentation_id in presentations_to_process:
            try:
                with app.app_context():
                    # Präsentation und alle zugehörigen Feedbacks abrufen
                    presentation = Presentation.query.get(presentation_id)
                    if not presentation or presentation.is_deleted:
                        with processing_lock:
                            if presentation_id in feedback_processing_queue:
                                del feedback_processing_queue[presentation_id]
                        continue
                    
                    # Prüfen, ob Retry-Verzögerung noch aktiv ist
                    if presentation.retry_after and now < presentation.retry_after:
                        print(f"Presentation {presentation_id}: Retry-Verzögerung noch aktiv bis {presentation.retry_after}")
                        continue
                    
                    # Unverarbeitete Feedbacks abrufen
                    unprocessed_feedbacks = Feedback.query.filter_by(
                        presentation_id=presentation_id, 
                        is_processed=False
                    ).all()

                    if not unprocessed_feedbacks:
                        with processing_lock:
                            if presentation_id in feedback_processing_queue:
                                del feedback_processing_queue[presentation_id]
                        continue

                    # Alle Feedbacks für diese Präsentation abrufen (für Kontext)
                    all_feedbacks = Feedback.query.filter_by(presentation_id=presentation_id).all()
                    
                    # Neuen Feedback-Bereich generieren
                    feedback_response = generate_feedback_content(
                        feedbacks=all_feedbacks,
                        static_info_content=presentation.static_info_content,
                        existing_feedback_content=presentation.feedback_content
                    )
                    
                    # Nur bei erfolgreichem KI-Aufruf aktualisieren
                    if feedback_response is not None:
                        for feedback in unprocessed_feedbacks:
                            feedback.is_processed = True
                        
                        # Feedback-Bereich aktualisieren und Fehlerkontext löschen
                        presentation.feedback_content = feedback_response
                        presentation.last_updated = datetime.utcnow()
                        presentation.processing_scheduled = False
                        presentation.next_processing_time = None
                        presentation.last_error_message = None
                        presentation.last_error_time = None
                        presentation.failed_context = None
                        presentation.retry_after = None  # Retry-Verzögerung zurücksetzen
                        
                        db.session.commit()
                        
                        # Aus der Warteschlange entfernen
                        with processing_lock:
                            if presentation_id in feedback_processing_queue:
                                del feedback_processing_queue[presentation_id]
                    else:
                        # Bei Fehler: Feedbacks nicht als verarbeitet markieren
                        # Warteschlange nicht entfernen, damit später erneut versucht wird
                        print(f"Feedback-Generierung für Präsentation {presentation_id} fehlgeschlagen - wird später erneut versucht")
                        db.session.commit()  # Fehlerkontext speichern
            
            except Exception as e:
                print(f"Fehler bei der Verarbeitung von Präsentation {presentation_id}: {e}")
                # Bei schwerwiegenden Fehlern aus der Warteschlange entfernen
                # API-Fehler werden bereits oben behandelt
                with processing_lock:
                    if presentation_id in feedback_processing_queue:
                        del feedback_processing_queue[presentation_id]

def schedule_feedback_processing(presentation_id):
    """Plant die Verarbeitung von Feedback für eine Präsentation"""
    global feedback_processing_queue, processing_thread
    
    # Verarbeitungsthread starten, falls noch nicht gestartet
    if processing_thread is None or not processing_thread.is_alive():
        processing_thread = threading.Thread(target=process_feedback_queue, daemon=True)
        processing_thread.start()
    
    now = datetime.utcnow()
    processing_interval = timedelta(seconds=app.config['FEEDBACK_PROCESSING_INTERVAL'])
    
    with processing_lock:
        # Wenn die Präsentation bereits in der Warteschlange ist, Verarbeitungszeit aktualisieren
        if presentation_id in feedback_processing_queue:
            feedback_processing_queue[presentation_id]['next_processing_time'] = now + processing_interval
        else:
            # Sonst zur Warteschlange hinzufügen
            feedback_processing_queue[presentation_id] = {
                'next_processing_time': now + processing_interval
            }

@app.route('/p/<access_code>/feedback', methods=['POST'])
def submit_feedback(access_code):
    presentation = Presentation.get_by_access_code(access_code)
    if not presentation:
        from flask import abort
        abort(404)
    
    feedback_content = request.form.get('feedback')
    participant_name = request.form.get('participant_name')
    
    feedback = Feedback(
        content=feedback_content,
        presentation_id=presentation.id,
        participant_name=participant_name
    )
    
    db.session.add(feedback)
    
    # Verarbeitung planen
    presentation.processing_scheduled = True
    presentation.next_processing_time = datetime.utcnow() + timedelta(seconds=app.config['FEEDBACK_PROCESSING_INTERVAL'])
    
    db.session.commit()
    
    # Feedback-Verarbeitung im Hintergrund planen
    schedule_feedback_processing(presentation.id)
    
    # Temporäre Antwort zurückgeben
    temp_response = "Ihre Anfrage wurde entgegengenommen und wird verarbeitet. Die Seite wird in Kürze aktualisiert."
    temp_response_html = f"<p>{temp_response}</p><p><em>Wird verarbeitet...</em></p>"
    
    return jsonify({
        'success': True,
        'ai_response': temp_response,
        'ai_response_html': temp_response_html,
        'processing': True
    })

@app.route('/api/presentation/<int:id>/ai_content', methods=['GET'])
@login_required
def api_get_ai_content(id):
    presentation = Presentation.get_active_or_404(id)
    
    # Überprüfen, ob der Benutzer der Ersteller ist
    if presentation.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    # Statische Info-Seite und Feedback-Bereich kombinieren
    combined_content = ""
    
    # Statische Info-Seite hinzufügen
    if presentation.static_info_content:
        combined_content += presentation.static_info_content
    
    # Feedback-Bereich hinzufügen (falls vorhanden)
    if presentation.feedback_content:
        combined_content += "\n\n---\n\n# Feedback der Zuhörer\n\n" + presentation.feedback_content

    # Markdown zu HTML konvertieren
    combined_html = markdown_to_html(combined_content)

    return jsonify({'success': True, 'html': combined_html})


@app.route('/api/feedbacks/<int:presentation_id>', methods=['GET'])
def api_get_feedbacks(presentation_id):
    feedbacks = Feedback.query.filter_by(presentation_id=presentation_id).order_by(Feedback.created_at.desc()).all()
    
    result = []
    for feedback in feedbacks:
        result.append({
            'id': feedback.id,
            'content': feedback.content,
            'created_at': feedback.created_at.isoformat(),
            'is_processed': feedback.is_processed,
            'ai_response': feedback.ai_response,
            'participant_name': feedback.participant_name
        })
    
    return jsonify(result)

@app.route('/api/generate_preview', methods=['POST'])
def api_generate_preview():
    data = request.json
    context = data.get('context', '')
    content = data.get('content', '')
    
    if not context or not content:
        return jsonify({
            'success': False,
            'error': 'Kontext und Inhalt sind erforderlich'
        })
    
    try:
        # KI-Inhalte generieren ohne Feedbacks
        ai_content = generate_ai_content(feedbacks=None, context=context, content=content)
        
        # Markdown zu HTML konvertieren
        ai_content_html = markdown_to_html(ai_content)
        
        return jsonify({
            'success': True,
            'preview': ai_content,
            'preview_html': str(ai_content_html)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Hilfsfunktion für Datenbankmigrationen
def add_columns_if_not_exist():
    with app.app_context():
        # Überprüfen, ob die Spalten bereits existieren
        inspector = db.inspect(db.engine)
        presentation_columns = [column['name'] for column in inspector.get_columns('presentation')]
        feedback_columns = [column['name'] for column in inspector.get_columns('feedback')]
        
        # Presentation table columns
        if 'cached_ai_content' not in presentation_columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN cached_ai_content TEXT'))
        
        if 'last_updated' not in presentation_columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN last_updated TIMESTAMP'))
                
        if 'processing_scheduled' not in presentation_columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN processing_scheduled BOOLEAN'))
                
        if 'next_processing_time' not in presentation_columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN next_processing_time TIMESTAMP'))
        
        # New content separation columns
        if 'static_info_content' not in presentation_columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN static_info_content TEXT'))
        
        if 'feedback_content' not in presentation_columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN feedback_content TEXT'))
        
        # Feedback table columns
        if 'participant_name' not in feedback_columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE feedback ADD COLUMN participant_name VARCHAR(100)'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_columns_if_not_exist()
    app.run(debug=True)
