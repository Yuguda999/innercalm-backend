"""
Database migration to add SVG illustration fields to recommendations table.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def upgrade():
    """Add SVG-related fields to recommendations table."""
    with engine.connect() as connection:
        # Add image_url field
        connection.execute(text("""
            ALTER TABLE recommendations
            ADD COLUMN image_url VARCHAR NULL
        """))

        # Add gif_url field
        connection.execute(text("""
            ALTER TABLE recommendations
            ADD COLUMN gif_url VARCHAR NULL
        """))

        # Add illustration_prompt field
        connection.execute(text("""
            ALTER TABLE recommendations
            ADD COLUMN illustration_prompt TEXT NULL
        """))

        connection.commit()
        print("Successfully added SVG fields to recommendations table")


def downgrade():
    """Remove SVG-related fields from recommendations table."""
    with engine.connect() as connection:
        # Remove the added fields
        connection.execute(text("""
            ALTER TABLE recommendations
            DROP COLUMN IF EXISTS image_url
        """))

        connection.execute(text("""
            ALTER TABLE recommendations
            DROP COLUMN IF EXISTS gif_url
        """))

        connection.execute(text("""
            ALTER TABLE recommendations
            DROP COLUMN IF EXISTS illustration_prompt
        """))

        connection.commit()
        print("Successfully removed SVG fields from recommendations table")


if __name__ == "__main__":
    upgrade()
