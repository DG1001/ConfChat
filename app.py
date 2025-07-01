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
    presentations = db.relationship('Presentation', backref='creator', lazy=True)

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
    cached_ai_content = db.Column(db.Text)
    last_updated = db.Column(db.DateTime)
    processing_scheduled = db.Column(db.Boolean, default=False)
    next_processing_time = db.Column(db.DateTime)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentation.id'), nullable=False)
    is_processed = db.Column(db.Boolean, default=False)
    ai_response = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Markdown zu HTML konvertieren
def markdown_to_html(text):
    """Konvertiert Markdown-Text zu HTML"""
    return Markup(markdown.markdown(text, extensions=['tables']))

# KI-Integration
def generate_ai_content(context, content, feedbacks=None):
    """Generiert KI-basierte Inhalte basierend auf dem Kontext, Inhalt und allen Feedbacks"""
    
    # Prompt für die KI erstellen
    prompt = f"""
    Erstelle eine gut strukturierte Infoseite im Markdown-Format basierend auf dem Kontext und Hauptinhalt der Präsentation.
    
    # Kontext der Präsentation
    {context}
    
    # Hauptinhalt der Präsentation
    {content}
    """
    
    if feedbacks:
        prompt += "\n\n# Feedback und Fragen der Zuhörer\n"
        for feedback in feedbacks:
            prompt += f"- {feedback.content}\n"
        
        prompt += "\nBitte verarbeite alle Feedbacks und Fragen der Zuhörer und integriere sie sinnvoll in die Infoseite. Strukturiere die Seite mit Markdown-Überschriften, Listen und anderen Formatierungen für eine übersichtliche Darstellung."
    
    # OpenAI-API-Anfrage
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app.config['OPENAI_API_KEY']}"
            },
            json={
                "model": "gpt-4.1-nano",
                "messages": [
                    {"role": "system", "content": "Du bist ein Experte für die Erstellung von informativen und gut strukturierten Präsentationsinhalten im Markdown-Format. Verwende Markdown-Formatierung für eine klare Struktur mit Überschriften, Listen, Hervorhebungen und anderen Elementen."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500
            }
        )
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    except Exception as e:
        print(f"Fehler bei der KI-Anfrage: {e}")
        return "## Fehler\nEs ist ein Fehler bei der Generierung des KI-Inhalts aufgetreten."

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
    presentations = Presentation.query.filter_by(user_id=current_user.id).all()
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
        
        return redirect(url_for('dashboard'))
    
    return render_template('new_presentation.html')

@app.route('/presentation/<int:id>')
@login_required
def view_presentation(id):
    presentation = Presentation.query.get_or_404(id)
    
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
    presentation = Presentation.query.get_or_404(id)
    
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
    presentation = Presentation.query.get_or_404(id)
    
    # Überprüfen, ob der Benutzer der Ersteller ist
    if presentation.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    db.session.delete(presentation)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/p/<access_code>')
def public_view(access_code):
    presentation = Presentation.query.filter_by(access_code=access_code).first_or_404()
    
    # Alle Feedbacks für diese Präsentation abrufen
    feedbacks = Feedback.query.filter_by(presentation_id=presentation.id).all()
    
    # Prüfen, ob wir bereits einen gecachten KI-Inhalt haben
    if presentation.cached_ai_content:
        ai_content = presentation.cached_ai_content
    else:
        # KI-Inhalte generieren mit allen Feedbacks
        ai_content = generate_ai_content(presentation.context, presentation.content, feedbacks)
        
        # Cache aktualisieren
        presentation.cached_ai_content = ai_content
        presentation.last_updated = datetime.utcnow()
        db.session.commit()
    
    # Markdown zu HTML konvertieren
    ai_content_html = markdown_to_html(ai_content)
    
    # Status der Verarbeitung
    processing_status = {
        'scheduled': presentation.processing_scheduled,
        'next_update': presentation.next_processing_time.isoformat() if presentation.next_processing_time else None
    }
    
    return render_template('public_view.html', presentation=presentation, 
                          ai_content=ai_content, ai_content_html=ai_content_html,
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
                    if not presentation:
                        with processing_lock:
                            if presentation_id in feedback_processing_queue:
                                del feedback_processing_queue[presentation_id]
                        continue
                    
                    all_feedbacks = Feedback.query.filter_by(presentation_id=presentation_id).all()
                    
                    # KI-Antwort mit allen Feedbacks generieren
                    ai_response = generate_ai_content(presentation.context, presentation.content, all_feedbacks)
                    
                    # Unverarbeitete Feedbacks aktualisieren
                    unprocessed_feedbacks = Feedback.query.filter_by(
                        presentation_id=presentation_id, 
                        is_processed=False
                    ).all()
                    
                    for feedback in unprocessed_feedbacks:
                        feedback.ai_response = ai_response
                        feedback.is_processed = True
                    
                    # Präsentations-Cache aktualisieren
                    presentation.cached_ai_content = ai_response
                    presentation.last_updated = datetime.utcnow()
                    presentation.processing_scheduled = False
                    presentation.next_processing_time = None
                    
                    db.session.commit()
                    
                    # Aus der Warteschlange entfernen
                    with processing_lock:
                        if presentation_id in feedback_processing_queue:
                            del feedback_processing_queue[presentation_id]
            
            except Exception as e:
                print(f"Fehler bei der Verarbeitung von Präsentation {presentation_id}: {e}")
                # Bei Fehler aus der Warteschlange entfernen, um endlose Wiederholungen zu vermeiden
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
    presentation = Presentation.query.filter_by(access_code=access_code).first_or_404()
    
    feedback_content = request.form.get('feedback')
    
    feedback = Feedback(
        content=feedback_content,
        presentation_id=presentation.id
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
            'ai_response': feedback.ai_response
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
        ai_content = generate_ai_content(context, content)
        
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
        columns = [column['name'] for column in inspector.get_columns('presentation')]
        
        if 'cached_ai_content' not in columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN cached_ai_content TEXT'))
        
        if 'last_updated' not in columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN last_updated TIMESTAMP'))
                
        if 'processing_scheduled' not in columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN processing_scheduled BOOLEAN'))
                
        if 'next_processing_time' not in columns:
            with db.engine.begin() as conn:
                conn.execute(db.text('ALTER TABLE presentation ADD COLUMN next_processing_time TIMESTAMP'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_columns_if_not_exist()
    app.run(debug=True)
