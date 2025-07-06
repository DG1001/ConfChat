#!/usr/bin/env python3
"""
Test script to verify improved error handling functionality
"""

import sys
import sqlite3
from app import app, db, User, Presentation, Feedback, generate_ai_content, store_error_context
from datetime import datetime

def test_error_handling():
    print("Testing improved error handling functionality...")
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test user or use existing
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(username='testuser')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
        else:
            print("Using existing test user")
        
        # Create test presentation
        presentation = Presentation(
            title='Test Presentation',
            description='Test description',
            context='Test context',
            content='Test content',
            access_code='test123',
            user_id=user.id
        )
        db.session.add(presentation)
        db.session.commit()
        
        # Create test feedback
        feedback = Feedback(
            content='Test feedback',
            presentation_id=presentation.id
        )
        db.session.add(feedback)
        db.session.commit()
        
        print(f"✓ Created test data - Presentation ID: {presentation.id}")
        
        # Test 1: Verify new fields exist
        print("\nTest 1: Database schema")
        try:
            # Check if new fields can be set
            presentation.last_error_message = "Test error"
            presentation.last_error_time = datetime.utcnow()
            presentation.failed_context = "Test failed context"
            db.session.commit()
            print("✓ New error handling fields work correctly")
        except Exception as e:
            print(f"✗ Error setting new fields: {e}")
            return False
        
        # Test 2: Test store_error_context function
        print("\nTest 2: store_error_context function")
        try:
            store_error_context(presentation.id, "Test error message", "Previous content", [feedback])
            db.session.refresh(presentation)
            if presentation.last_error_message == "Test error message":
                print("✓ store_error_context works correctly")
            else:
                print("✗ store_error_context did not save error message")
                return False
        except Exception as e:
            print(f"✗ Error in store_error_context: {e}")
            return False
        
        # Test 3: Test generate_ai_content with invalid API key (should fail gracefully)
        print("\nTest 3: generate_ai_content error handling")
        try:
            # This should fail due to invalid API key, but should handle the error gracefully
            app.config['OPENAI_API_KEY'] = 'invalid-key'
            result = generate_ai_content(
                feedbacks=[feedback],
                previous_content="Test content",
                presentation_id=presentation.id
            )
            
            if result is None:
                print("✓ generate_ai_content handles errors gracefully (returns None)")
                
                # Check if error was stored
                db.session.refresh(presentation)
                if presentation.last_error_message:
                    print("✓ Error context was stored in database")
                else:
                    print("✗ Error context was not stored")
                    return False
            else:
                print("✗ generate_ai_content should return None on error")
                return False
        except Exception as e:
            print(f"✗ Unexpected exception in generate_ai_content: {e}")
            return False
        
        print("\nAll tests passed! ✓")
        return True

if __name__ == "__main__":
    success = test_error_handling()
    sys.exit(0 if success else 1)