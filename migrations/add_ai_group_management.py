"""
Database migration to add AI group management fields to SharedWoundGroup table.
Run this script to update existing database schema.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy import text
from database import engine

logger = logging.getLogger(__name__)


def run_migration():
    """Run the migration to add AI group management fields."""
    try:
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()

            try:
                # Add new columns to shared_wound_groups table
                migration_sql = """
                -- Add AI management columns
                ALTER TABLE shared_wound_groups ADD COLUMN cluster_id VARCHAR;
                ALTER TABLE shared_wound_groups ADD COLUMN ai_generated BOOLEAN DEFAULT TRUE;
                ALTER TABLE shared_wound_groups ADD COLUMN confidence_score FLOAT;

                -- Add dynamic metrics columns
                ALTER TABLE shared_wound_groups ADD COLUMN member_count INTEGER DEFAULT 0;
                ALTER TABLE shared_wound_groups ADD COLUMN activity_score FLOAT DEFAULT 0.0;
                ALTER TABLE shared_wound_groups ADD COLUMN cohesion_score FLOAT DEFAULT 0.0;
                ALTER TABLE shared_wound_groups ADD COLUMN growth_potential FLOAT DEFAULT 0.0;

                -- Add AI management timestamps
                ALTER TABLE shared_wound_groups ADD COLUMN last_ai_review DATETIME;
                ALTER TABLE shared_wound_groups ADD COLUMN next_ai_review DATETIME;

                -- Update max_members default for AI-managed groups
                UPDATE shared_wound_groups SET max_members = 50 WHERE max_members < 50;

                -- Update requires_approval default for AI-managed groups
                UPDATE shared_wound_groups SET requires_approval = FALSE WHERE ai_generated = TRUE;

                -- Create unique index on cluster_id
                CREATE UNIQUE INDEX idx_shared_wound_groups_cluster_id ON shared_wound_groups(cluster_id);
                """

                # Execute each statement separately
                statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

                for statement in statements:
                    if statement:
                        logger.info(f"Executing: {statement[:50]}...")
                        connection.execute(text(statement))

                # Commit transaction
                trans.commit()
                logger.info("Migration completed successfully")

            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Migration failed, rolling back: {e}")
                raise

    except Exception as e:
        logger.error(f"Error running migration: {e}")
        raise


def rollback_migration():
    """Rollback the migration (remove added columns)."""
    try:
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()

            try:
                # Remove added columns
                rollback_sql = """
                -- Drop unique index
                DROP INDEX IF EXISTS idx_shared_wound_groups_cluster_id;

                -- Remove AI management columns
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS cluster_id;
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS ai_generated;
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS confidence_score;

                -- Remove dynamic metrics columns
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS member_count;
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS activity_score;
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS cohesion_score;
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS growth_potential;

                -- Remove AI management timestamps
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS last_ai_review;
                ALTER TABLE shared_wound_groups DROP COLUMN IF EXISTS next_ai_review;
                """

                # Execute each statement separately
                statements = [stmt.strip() for stmt in rollback_sql.split(';') if stmt.strip()]

                for statement in statements:
                    if statement:
                        logger.info(f"Executing rollback: {statement[:50]}...")
                        connection.execute(text(statement))

                # Commit transaction
                trans.commit()
                logger.info("Rollback completed successfully")

            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Rollback failed: {e}")
                raise

    except Exception as e:
        logger.error(f"Error running rollback: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("Running migration rollback...")
        rollback_migration()
        print("Rollback completed!")
    else:
        print("Running migration...")
        run_migration()
        print("Migration completed!")
