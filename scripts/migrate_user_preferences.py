#!/usr/bin/env python3
"""
Migration script to add Inner Ally fields to user_preferences table.
"""
import sys
import os
import sqlite3

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine


def migrate_user_preferences():
    """Add Inner Ally columns to user_preferences table."""
    
    # Get the database file path from the engine
    db_path = engine.url.database
    
    print(f"Migrating database: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Existing columns: {columns}")
        
        # Add missing columns
        new_columns = [
            ("agent_persona", "VARCHAR", "gentle_mentor"),
            ("custom_persona_name", "VARCHAR", "NULL"),
            ("custom_persona_description", "TEXT", "NULL"),
            ("favorite_affirmations", "TEXT", "NULL"),
            ("preferred_coping_styles", "TEXT", "NULL"),
            ("crisis_contact_enabled", "BOOLEAN", "1"),
            ("widget_enabled", "BOOLEAN", "1"),
            ("micro_checkin_frequency", "INTEGER", "4")
        ]
        
        for column_name, column_type, default_value in new_columns:
            if column_name not in columns:
                if default_value == "NULL":
                    sql = f"ALTER TABLE user_preferences ADD COLUMN {column_name} {column_type}"
                else:
                    sql = f"ALTER TABLE user_preferences ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                
                print(f"Adding column: {sql}")
                cursor.execute(sql)
                print(f"✅ Added column: {column_name}")
            else:
                print(f"⏭️  Column already exists: {column_name}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(user_preferences)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    """Main function."""
    print("Starting user_preferences table migration...")
    
    try:
        migrate_user_preferences()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
