#!/usr/bin/env python3
"""
Demo script to show the improved error handling behavior
"""

from datetime import datetime, timedelta
from app import app, db, User, Presentation, Feedback

def demo_improved_behavior():
    print("=== Demo: Verbessertes Fehlerverhalten ===\n")
    
    with app.app_context():
        # Suche eine vorhandene Präsentation mit Fehlern
        presentation = Presentation.query.filter(
            Presentation.last_error_message.isnot(None)
        ).first()
        
        if presentation:
            print(f"Präsentation gefunden: '{presentation.title}' (ID: {presentation.id})")
            print(f"Letzter Fehler: {presentation.last_error_time}")
            print(f"Fehlermeldung: {presentation.last_error_message[:100]}...")
            
            if presentation.retry_after:
                print(f"Retry möglich ab: {presentation.retry_after}")
                
                now = datetime.utcnow()
                if now < presentation.retry_after:
                    remaining = (presentation.retry_after - now).total_seconds()
                    print(f"⏰ Noch {remaining:.1f} Sekunden bis zum nächsten Retry-Versuch")
                else:
                    print("✅ Retry-Verzögerung ist abgelaufen, nächster Versuch möglich")
            
            # Zeige unverarbeitete Feedbacks
            unprocessed = Feedback.query.filter_by(
                presentation_id=presentation.id,
                is_processed=False
            ).count()
            
            print(f"📝 Unverarbeitete Feedbacks: {unprocessed}")
            
            if presentation.failed_context:
                print(f"💾 Gespeicherter Kontext (erste 100 Zeichen): {presentation.failed_context[:100]}...")
            
            print(f"📄 Aktuelle Seite (erste 100 Zeichen): {presentation.cached_ai_content[:100] if presentation.cached_ai_content else 'Keine'}...")
            
        else:
            print("Keine Präsentation mit Fehlern gefunden.")
            
            # Zeige alle Präsentationen
            presentations = Presentation.query.all()
            print(f"\nVorhandene Präsentationen ({len(presentations)}):")
            for p in presentations:
                status = "❌ Fehler" if p.last_error_message else "✅ OK"
                print(f"  - {p.title} (ID: {p.id}) - {status}")

if __name__ == "__main__":
    demo_improved_behavior()