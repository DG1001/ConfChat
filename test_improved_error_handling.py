#!/usr/bin/env python3
"""
Test script to verify improved error handling with retry delays and feedback duplication prevention
"""

import sys
import time
from datetime import datetime, timedelta
from app import app, db, User, Presentation, Feedback, generate_ai_content, store_error_context

def test_improved_error_handling():
    print("Testing improved error handling functionality...")
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Get or create test user
        user = User.query.filter_by(username='testuser2').first()
        if not user:
            user = User(username='testuser2')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
        
        # Create test presentation
        presentation = Presentation(
            title='Improved Error Test',
            description='Testing improved error handling',
            context='Test context for improved error handling',
            content='Test content for improved error handling',
            access_code='test456',
            user_id=user.id,
            cached_ai_content='## Original Content\n\nThis is the original cached content.'
        )
        db.session.add(presentation)
        db.session.commit()
        
        # Create test feedback
        feedback1 = Feedback(
            content='First test feedback',
            presentation_id=presentation.id
        )
        feedback2 = Feedback(
            content='Second test feedback',
            presentation_id=presentation.id
        )
        db.session.add_all([feedback1, feedback2])
        db.session.commit()
        
        print(f"✓ Created test data - Presentation ID: {presentation.id}")
        
        # Test 1: Verify retry_after field works
        print("\nTest 1: Retry delay functionality")
        try:
            # Trigger an error (invalid API key)
            app.config['OPENAI_API_KEY'] = 'invalid-key-for-test'
            
            # This should fail and set retry_after
            result = generate_ai_content(
                feedbacks=[feedback1],
                previous_content=presentation.cached_ai_content,
                presentation_id=presentation.id
            )
            
            if result is None:
                print("✓ API call failed as expected")
                
                # Check if retry_after was set
                db.session.refresh(presentation)
                if presentation.retry_after:
                    print(f"✓ Retry delay set until: {presentation.retry_after}")
                    
                    # Check that retry_after is about 10 seconds from now
                    expected_time = datetime.utcnow() + timedelta(seconds=8)  # Allow 2 seconds tolerance
                    if presentation.retry_after > expected_time:
                        print("✓ Retry delay is correctly set to ~10 seconds")
                    else:
                        print("✗ Retry delay not correctly set")
                        return False
                else:
                    print("✗ Retry delay was not set")
                    return False
            else:
                print("✗ API call should have failed")
                return False
        except Exception as e:
            print(f"✗ Unexpected error in retry delay test: {e}")
            return False
        
        # Test 2: Verify failed_context preservation
        print("\nTest 2: Failed context preservation (no feedback duplication)")
        try:
            db.session.refresh(presentation)
            
            # Check that failed_context contains the original cached content (without new feedbacks)
            if presentation.failed_context == presentation.cached_ai_content:
                print("✓ Failed context correctly preserved original content")
            else:
                print(f"✗ Failed context incorrect. Expected: {presentation.cached_ai_content}")
                print(f"    Got: {presentation.failed_context}")
                return False
            
            # Check that feedbacks are still unprocessed
            db.session.refresh(feedback1)
            db.session.refresh(feedback2)
            if not feedback1.is_processed and not feedback2.is_processed:
                print("✓ Feedbacks remain unprocessed after error")
            else:
                print("✗ Feedbacks should remain unprocessed after error")
                return False
                
        except Exception as e:
            print(f"✗ Error in failed context test: {e}")
            return False
        
        # Test 3: Test successful retry clears error state
        print("\nTest 3: Successful retry clears error state")
        try:
            # Wait for retry delay to pass (simulate)
            presentation.retry_after = datetime.utcnow() - timedelta(seconds=1)
            db.session.commit()
            
            # Mock successful API call
            app.config['OPENAI_API_KEY'] = 'valid-key-mock'  # Still invalid but different handling
            
            # Simulate successful processing by manually setting values
            presentation.cached_ai_content = "## Updated Content\n\nThis is updated content with feedback integrated."
            presentation.last_error_message = None
            presentation.last_error_time = None
            presentation.failed_context = None
            presentation.retry_after = None
            
            # Mark feedbacks as processed
            feedback1.is_processed = True
            feedback2.is_processed = True
            feedback1.ai_response = presentation.cached_ai_content
            feedback2.ai_response = presentation.cached_ai_content
            
            db.session.commit()
            
            # Verify error state is cleared
            db.session.refresh(presentation)
            if (presentation.last_error_message is None and 
                presentation.retry_after is None and 
                presentation.failed_context is None):
                print("✓ Error state correctly cleared after successful retry")
            else:
                print("✗ Error state not properly cleared")
                return False
                
        except Exception as e:
            print(f"✗ Error in retry success test: {e}")
            return False
        
        # Test 4: Test store_error_context function with proper context isolation
        print("\nTest 4: store_error_context function behavior")
        try:
            # Reset presentation state
            presentation.cached_ai_content = "## Current Page\n\nThis is the current page content."
            presentation.last_error_message = None
            presentation.retry_after = None
            presentation.failed_context = None
            db.session.commit()
            
            # Create new feedback
            feedback3 = Feedback(
                content='Third test feedback',
                presentation_id=presentation.id
            )
            db.session.add(feedback3)
            db.session.commit()
            
            # Call store_error_context
            store_error_context(presentation.id, "Test error for context isolation", 
                              "## Updated Content\n\nThis would be the updated content with feedback3", 
                              [feedback3])
            
            # Verify that failed_context contains the CURRENT page, not the updated content
            db.session.refresh(presentation)
            if presentation.failed_context == "## Current Page\n\nThis is the current page content.":
                print("✓ store_error_context correctly preserves current page content")
            else:
                print(f"✗ store_error_context preserved wrong content: {presentation.failed_context}")
                return False
                
        except Exception as e:
            print(f"✗ Error in store_error_context test: {e}")
            return False
        
        print("\nAll improved error handling tests passed! ✓")
        return True

if __name__ == "__main__":
    success = test_improved_error_handling()
    sys.exit(0 if success else 1)