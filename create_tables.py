"""
Script to manually create database tables.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all models to ensure they're registered
from models import user, conversation, emotion, recommendation
from database import create_tables

if __name__ == "__main__":
    print("Creating database tables...")
    try:
        create_tables()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
