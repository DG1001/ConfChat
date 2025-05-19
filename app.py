# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///presentations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# KI-Integration
def generate_ai_content(context, content, feedback=None):
    """Generiert KI-basierte Inhalte basierend auf dem Kontext, Inhalt und optional Feedback"""
    
    # Prompt für die KI erstellen
    prompt = f"""
    Erstelle aus dem Kontext, dem Hauptinhalt und dem Feedback der Zuhörer eine Infoseite. Wichtig hierbei, die Anmerkungen der Zuhörer zu verarbeiten und einzubringen.
    Kontext der Präsentation: {context}
    
    Hauptinhalt: {content}
    """
    
    if feedback:
        prompt += f"\n\nZusätzliche Informationen vom Zuhörer: {feedback}"
    
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
                    {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Präsentationsinhalte interaktiv und informativ darstellt."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500
            }
        )
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    except Exception as e:
        print(f"Fehler bei der KI-Anfrage: {e}")
        return "Es ist ein Fehler bei der Generierung des KI-Inhalts aufgetreten."

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
    
    # KI-Inhalte generieren
    ai_content = generate_ai_content(presentation.context, presentation.content)
    
    return render_template('public_view.html', presentation=presentation, ai_content=ai_content)

@app.route('/p/<access_code>/feedback', methods=['POST'])
def submit_feedback(access_code):
    presentation = Presentation.query.filter_by(access_code=access_code).first_or_404()
    
    feedback_content = request.form.get('feedback')
    
    feedback = Feedback(
        content=feedback_content,
        presentation_id=presentation.id
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    # KI-Antwort generieren
    ai_response = generate_ai_content(presentation.context, presentation.content, feedback_content)
    
    # Feedback aktualisieren
    feedback.ai_response = ai_response
    feedback.is_processed = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'ai_response': ai_response
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
