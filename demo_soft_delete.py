#!/usr/bin/env python3
"""
Demo script to show soft delete behavior
"""

from datetime import datetime
from app import app, db, User, Presentation

def demo_soft_delete():
    print("=== Demo: Soft Delete Verhalten ===\n")
    
    with app.app_context():
        # Zeige alle Präsentationen (auch gelöschte)
        all_presentations = Presentation.query.all()
        active_presentations = Presentation.query.filter_by(is_deleted=False).all()
        deleted_presentations = Presentation.query.filter_by(is_deleted=True).all()
        
        print(f"📊 Datenbank-Statistiken:")
        print(f"   Gesamt: {len(all_presentations)} Präsentationen")
        print(f"   Aktiv: {len(active_presentations)} Präsentationen")
        print(f"   Gelöscht: {len(deleted_presentations)} Präsentationen")
        
        if deleted_presentations:
            print(f"\n🗑️ Gelöschte Präsentationen:")
            for p in deleted_presentations:
                deleted_by = User.query.get(p.deleted_by_user_id)
                deleted_by_name = deleted_by.username if deleted_by else "Unbekannt"
                print(f"   - '{p.title}' (ID: {p.id})")
                print(f"     Gelöscht am: {p.deleted_at}")
                print(f"     Gelöscht von: {deleted_by_name}")
                print(f"     Access Code: {p.access_code} (nicht mehr erreichbar)")
                print()
        
        if active_presentations:
            print(f"✅ Aktive Präsentationen:")
            for p in active_presentations:
                creator = User.query.get(p.user_id)
                creator_name = creator.username if creator else "Unbekannt"
                print(f"   - '{p.title}' (ID: {p.id})")
                print(f"     Erstellt von: {creator_name}")
                print(f"     Access Code: {p.access_code}")
                print(f"     Erreichbar unter: /p/{p.access_code}")
                print()
        
        # Demo Dashboard-Verhalten
        users_with_presentations = User.query.join(Presentation, User.id == Presentation.user_id).distinct().all()
        
        if users_with_presentations:
            print(f"👤 Dashboard-Ansicht für Benutzer:")
            for user in users_with_presentations:
                dashboard_presentations = Presentation.get_active_by_user(user.id)
                print(f"   {user.username}: {len(dashboard_presentations)} aktive Präsentationen sichtbar")
        
        # Zeige Vorteile von Soft Delete
        print(f"\n💡 Vorteile des Soft Delete Systems:")
        print(f"   ✓ Präsentationen bleiben in der Datenbank erhalten")
        print(f"   ✓ Feedbacks und KI-Antworten gehen nicht verloren") 
        print(f"   ✓ Audit-Trail: Wer hat wann gelöscht")
        print(f"   ✓ Möglichkeit zur Wiederherstellung (falls gewünscht)")
        print(f"   ✓ Keine Dateninkonsistenzen durch Fremdschlüssel")

if __name__ == "__main__":
    demo_soft_delete()