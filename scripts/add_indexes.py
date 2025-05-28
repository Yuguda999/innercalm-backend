#!/usr/bin/env python3
"""
Script to add performance indexes to the database.
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_indexes():
    """Add performance indexes to the database."""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                logger.info("Adding performance indexes...")
                
                # Life Events indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_life_events_user_id ON life_events(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_life_events_event_date ON life_events(event_date)",
                    "CREATE INDEX IF NOT EXISTS idx_life_events_user_date ON life_events(user_id, event_date)",
                    "CREATE INDEX IF NOT EXISTS idx_life_events_trauma_severity ON life_events(trauma_severity)",
                    "CREATE INDEX IF NOT EXISTS idx_life_events_is_resolved ON life_events(is_resolved)",
                    "CREATE INDEX IF NOT EXISTS idx_life_events_event_type ON life_events(event_type)",
                    "CREATE INDEX IF NOT EXISTS idx_life_events_category ON life_events(category)",
                    
                    # Trauma Mappings indexes
                    "CREATE INDEX IF NOT EXISTS idx_trauma_mappings_user_id ON trauma_mappings(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_trauma_mappings_life_event_id ON trauma_mappings(life_event_id)",
                    "CREATE INDEX IF NOT EXISTS idx_trauma_mappings_analyzed_at ON trauma_mappings(analyzed_at)",
                    "CREATE INDEX IF NOT EXISTS idx_trauma_mappings_user_analyzed ON trauma_mappings(user_id, analyzed_at)",
                    
                    # Reframe Sessions indexes
                    "CREATE INDEX IF NOT EXISTS idx_reframe_sessions_user_id ON reframe_sessions(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_reframe_sessions_life_event_id ON reframe_sessions(life_event_id)",
                    "CREATE INDEX IF NOT EXISTS idx_reframe_sessions_status ON reframe_sessions(status)",
                    "CREATE INDEX IF NOT EXISTS idx_reframe_sessions_created_at ON reframe_sessions(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_reframe_sessions_user_status ON reframe_sessions(user_id, status)",
                ]
                
                for index_sql in indexes:
                    logger.info(f"Executing: {index_sql}")
                    conn.execute(text(index_sql))
                
                # Commit transaction
                trans.commit()
                logger.info("Successfully added all performance indexes!")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error adding indexes: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

if __name__ == "__main__":
    add_indexes()
