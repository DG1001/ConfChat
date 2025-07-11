#!/usr/bin/env python3
"""
Database migration script to add error handling fields to the Presentation model
"""

import sqlite3
import sys
import os

def migrate_database():
    db_path = 'instance/presentations.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. No migration needed.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the new columns already exist
        cursor.execute("PRAGMA table_info(presentation)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = ['last_error_message', 'last_error_time', 'failed_context', 'retry_after', 'is_deleted', 'deleted_at', 'deleted_by_user_id', 'additional_info', 'live_info_visible', 'feedback_disabled']
        columns_to_add = [col for col in new_columns if col not in columns]
        
        if not columns_to_add:
            print("Database already up to date. No migration needed.")
            return
        
        print(f"Adding new columns: {columns_to_add}")
        
        # Add new columns for error handling
        if 'last_error_message' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN last_error_message TEXT")
            print("Added last_error_message column")
        
        if 'last_error_time' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN last_error_time DATETIME")
            print("Added last_error_time column")
        
        if 'failed_context' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN failed_context TEXT")
            print("Added failed_context column")
        
        if 'retry_after' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN retry_after DATETIME")
            print("Added retry_after column")
        
        if 'is_deleted' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL")
            print("Added is_deleted column")
        
        if 'deleted_at' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN deleted_at DATETIME")
            print("Added deleted_at column")
        
        if 'deleted_by_user_id' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN deleted_by_user_id INTEGER")
            print("Added deleted_by_user_id column")
        
        if 'additional_info' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN additional_info TEXT")
            print("Added additional_info column")
        
        if 'live_info_visible' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN live_info_visible BOOLEAN DEFAULT 0 NOT NULL")
            print("Added live_info_visible column")
        
        if 'feedback_disabled' in columns_to_add:
            cursor.execute("ALTER TABLE presentation ADD COLUMN feedback_disabled BOOLEAN DEFAULT 0 NOT NULL")
            print("Added feedback_disabled column")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()