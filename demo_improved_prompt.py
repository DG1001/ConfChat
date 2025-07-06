#!/usr/bin/env python3
"""
Demo script to show improved prompt behavior
"""

from app import app, categorize_and_filter_feedback, Feedback

def demo_improved_prompt():
    print("=== Demo: Verbesserter KI-Prompt ===\n")
    
    # Simuliere verschiedene Feedback-Arten
    sample_feedbacks = [
        "Hier ist ein hilfreicher Link: https://python.org/docs",
        "Siehe auch www.stackoverflow.com für weitere Infos",
        "Wie funktioniert das Exception Handling in Python?",
        "Was ist der Unterschied zwischen List und Tuple?",
        "Können Sie das nochmal erklären?",
        "Super Vortrag, sehr interessant!",
        "Toll erklärt, danke!",
        "Das gefällt mir sehr gut",
        "Bei uns im Unternehmen machen wir das ähnlich",
        "Das erinnert mich an mein letztes Projekt",
        "Zu der Frage nach Performance: Das hängt von der Datenmenge ab",
        "Die Antwort auf die Implementierung: Wir verwenden async/await",
        "Das ist totaler Mist",  # Sollte gefiltert werden
        "Link zum GitHub Repository: https://github.com/example/repo"
    ]
    
    # Erstelle Mock-Feedback-Objekte für die Demo
    class MockFeedback:
        def __init__(self, content):
            self.content = content
    
    mock_feedbacks = [MockFeedback(content) for content in sample_feedbacks]
    
    print(f"📝 Beispiel-Feedbacks ({len(sample_feedbacks)} gesamt):")
    for i, feedback in enumerate(sample_feedbacks, 1):
        print(f"   {i:2d}. {feedback}")
    
    print(f"\n🔍 Kategorisierung und Filterung:")
    
    # Kategorisiere die Feedbacks
    categorized = categorize_and_filter_feedback(mock_feedbacks)
    
    print(f"\n📊 Ergebnisse:")
    print(f"   Faktische Informationen: {len(categorized['factual_info'])}")
    if categorized['factual_info']:
        for feedback in categorized['factual_info']:
            print(f"     - {feedback.content}")
    
    print(f"\n   ❓ Fragen: {len(categorized['questions'])}")
    if categorized['questions']:
        for feedback in categorized['questions']:
            print(f"     - {feedback.content}")
    
    print(f"\n   👍 Positive Kommentare: {len(categorized['positive_comments'])}")
    if categorized['positive_comments']:
        for feedback in categorized['positive_comments']:
            print(f"     - {feedback.content}")
    
    print(f"\n   💭 Neutrale/Antworten: {len(categorized['neutral_comments'])}")
    if categorized['neutral_comments']:
        for feedback in categorized['neutral_comments']:
            print(f"     - {feedback.content}")
    
    # Zeige Filterung
    total_processed = sum(len(cat) for cat in categorized.values())
    filtered_out = len(sample_feedbacks) - total_processed
    
    print(f"\n🛡️ Sicherheitsfilter:")
    print(f"   Original: {len(sample_feedbacks)} Feedbacks")
    print(f"   Verarbeitet: {total_processed} Feedbacks")
    print(f"   Gefiltert: {filtered_out} unangemessene Inhalte")
    
    print(f"\n📋 Prompt-Verbesserungen:")
    print(f"   ✅ Faktische Infos (Links, URLs) → Direkt in Haupttext")
    print(f"   ✅ Fragen → Nur bei 100% Sicherheit beantworten")
    print(f"   ✅ Unklare Fragen → 'Offene Fragen' Sektion")
    print(f"   ✅ Antworten auf Fragen → Zu entsprechender Frage hinzufügen")
    print(f"   ✅ Positive Kommentare → 'Feedback der Teilnehmer' sammeln")
    print(f"   ✅ Unangemessene Inhalte → Automatisch gefiltert")
    
    print(f"\n🎯 Intelligente Verarbeitung:")
    print(f"   • Links und URLs werden automatisch erkannt")
    print(f"   • Fragezeichen und Fragewörter identifizieren Fragen")
    print(f"   • Positive Begriffe erkennen Lob/Dank")
    print(f"   • Antwort-Indikatoren ('Zu der Frage...') werden richtig zugeordnet")
    print(f"   • Blacklist filtert unangemessene Inhalte")

if __name__ == "__main__":
    demo_improved_prompt()