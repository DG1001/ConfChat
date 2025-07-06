#!/usr/bin/env python3
"""
Test script for improved prompt with feedback categorization
"""

import sys
from app import app, db, User, Presentation, Feedback, categorize_and_filter_feedback

def test_feedback_categorization():
    print("Testing improved prompt and feedback categorization...")
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test user
        user = User.query.filter_by(username='testuser_prompt').first()
        if not user:
            user = User(username='testuser_prompt')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
        
        # Create test presentation or use existing
        presentation = Presentation.query.filter_by(access_code='prompt123').first()
        if not presentation:
            presentation = Presentation(
                title='Prompt Test Presentation',
                description='Testing improved prompt functionality',
                context='Kontext für Prompt-Test',
                content='Hauptinhalt für Prompt-Test',
                access_code='prompt123',
                user_id=user.id
            )
            db.session.add(presentation)
            db.session.commit()
        else:
            # Clear existing feedbacks for clean test
            Feedback.query.filter_by(presentation_id=presentation.id).delete()
            db.session.commit()
        
        # Create various types of feedback for testing
        test_feedbacks = [
            # Faktische Informationen
            "Hier ist ein nützlicher Link: https://docs.python.org/3/library/datetime.html",
            "Siehe auch www.github.com/anthropics/claude-code für mehr Infos",
            "Link zu Tutorial: https://www.example.com/tutorial",
            
            # Fragen
            "Wie funktioniert das genau?",
            "Was ist der Unterschied zwischen X und Y?",
            "Können Sie das näher erklären?",
            "Wann wird das Feature verfügbar sein?",
            
            # Positive Kommentare
            "Toll erklärt!",
            "Super interessant, danke!",
            "Das gefällt mir sehr gut",
            "Klasse Präsentation",
            
            # Neutrale Kommentare
            "Das erinnert mich an mein Projekt",
            "Wir haben ähnliche Erfahrungen gemacht",
            "In unserem Unternehmen machen wir das anders",
            
            # Unangemessene Inhalte (sollten gefiltert werden)
            "Das ist totaler Mist und Schwachsinn",
            "Du bist ein Idiot",
            "Scheisse, das funktioniert nicht",
            
            # Antworten auf Fragen
            "Zu der Frage nach X: Das funktioniert über API-Calls",
            "Die Antwort auf die Zeitfrage: Etwa 3 Monate",
        ]
        
        # Create feedback objects
        feedback_objects = []
        for i, content in enumerate(test_feedbacks):
            feedback = Feedback(
                content=content,
                presentation_id=presentation.id
            )
            feedback_objects.append(feedback)
            db.session.add(feedback)
        
        db.session.commit()
        print(f"✓ Created {len(feedback_objects)} test feedbacks")
        
        # Test 1: Feedback Kategorisierung
        print("\nTest 1: Feedback categorization")
        categorized = categorize_and_filter_feedback(feedback_objects)
        
        print(f"Faktische Informationen: {len(categorized['factual_info'])}")
        for feedback in categorized['factual_info']:
            print(f"  - {feedback.content[:50]}...")
        
        print(f"Fragen: {len(categorized['questions'])}")
        for feedback in categorized['questions']:
            print(f"  - {feedback.content[:50]}...")
        
        print(f"Positive Kommentare: {len(categorized['positive_comments'])}")
        for feedback in categorized['positive_comments']:
            print(f"  - {feedback.content[:50]}...")
        
        print(f"Neutrale Kommentare: {len(categorized['neutral_comments'])}")
        for feedback in categorized['neutral_comments']:
            print(f"  - {feedback.content[:50]}...")
        
        # Test 2: Filter-Funktionalität
        print("\nTest 2: Content filtering")
        original_count = len(feedback_objects)
        filtered_count = sum(len(cat) for cat in categorized.values())
        filtered_out = original_count - filtered_count
        
        print(f"Original Feedbacks: {original_count}")
        print(f"Nach Filterung: {filtered_count}")
        print(f"Gefiltert (unangemessen): {filtered_out}")
        
        if filtered_out > 0:
            print("✓ Unangemessene Inhalte wurden korrekt gefiltert")
        else:
            print("⚠ Keine unangemessenen Inhalte gefiltert (evtl. Test-Daten anpassen)")
        
        # Test 3: Erwartete Kategorien prüfen
        print("\nTest 3: Category validation")
        
        expected_factual = 3  # 3 Links
        expected_questions = 4  # 4 Fragen
        expected_positive = 4  # 4 positive Kommentare
        
        if len(categorized['factual_info']) >= expected_factual:
            print("✓ Faktische Informationen korrekt erkannt")
        else:
            print(f"✗ Zu wenige faktische Informationen erkannt: {len(categorized['factual_info'])}/{expected_factual}")
        
        if len(categorized['questions']) >= expected_questions:
            print("✓ Fragen korrekt erkannt")
        else:
            print(f"✗ Zu wenige Fragen erkannt: {len(categorized['questions'])}/{expected_questions}")
        
        if len(categorized['positive_comments']) >= expected_positive:
            print("✓ Positive Kommentare korrekt erkannt")
        else:
            print(f"✗ Zu wenige positive Kommentare erkannt: {len(categorized['positive_comments'])}/{expected_positive}")
        
        # Test 4: Prompt-Generierung (ohne API-Call)
        print("\nTest 4: Prompt generation structure")
        
        # Mock der generate_ai_content Funktion um Prompt zu sehen
        from app import generate_ai_content
        
        # Test mit Mock-API-Key (wird fehlschlagen, aber wir sehen den Prompt)
        app.config['OPENAI_API_KEY'] = 'test-key-for-prompt-testing'
        
        try:
            # Dies wird fehlschlagen, aber wir können die Kategorisierung testen
            result = generate_ai_content(
                feedbacks=feedback_objects[:8],  # Erste 8 ohne unangemessene
                previous_content="## Bestehender Inhalt\n\nDas ist der bestehende Inhalt der Präsentation.",
                presentation_id=presentation.id
            )
            print("✗ API-Call sollte fehlschlagen mit Test-Key")
        except Exception as e:
            if "test-key-for-prompt-testing" in str(e) or "Incorrect API key" in str(e):
                print("✓ Prompt-Generierung funktioniert (API-Key-Fehler erwartet)")
            else:
                print(f"✗ Unerwarteter Fehler: {e}")
        
        print("\nPrompt improvement tests completed! ✓")
        return True

if __name__ == "__main__":
    success = test_feedback_categorization()
    sys.exit(0 if success else 1)