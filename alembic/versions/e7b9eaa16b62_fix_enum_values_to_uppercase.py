"""Fix enum values to uppercase

Revision ID: e7b9eaa16b62
Revises: 845fbb16f2e6
Create Date: 2025-05-28 17:10:12.541368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7b9eaa16b62'
down_revision: Union[str, None] = '845fbb16f2e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update existing life_events data to use uppercase enum values
    connection = op.get_bind()

    # Update event_type values
    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'POSITIVE'
        WHERE event_type = 'positive'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'NEGATIVE'
        WHERE event_type = 'negative'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'NEUTRAL'
        WHERE event_type = 'neutral'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'TRAUMATIC'
        WHERE event_type = 'traumatic'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'MILESTONE'
        WHERE event_type = 'milestone'
    """))

    # Update category values
    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'FAMILY'
        WHERE category = 'family'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'RELATIONSHIPS'
        WHERE category = 'relationships'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'CAREER'
        WHERE category = 'career'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'HEALTH'
        WHERE category = 'health'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'EDUCATION'
        WHERE category = 'education'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'LOSS'
        WHERE category = 'loss'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'ACHIEVEMENT'
        WHERE category = 'achievement'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'TRAUMA'
        WHERE category = 'trauma'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'OTHER'
        WHERE category = 'other'
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # Revert to lowercase enum values
    connection = op.get_bind()

    # Revert event_type values
    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'positive'
        WHERE event_type = 'POSITIVE'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'negative'
        WHERE event_type = 'NEGATIVE'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'neutral'
        WHERE event_type = 'NEUTRAL'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'traumatic'
        WHERE event_type = 'TRAUMATIC'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET event_type = 'milestone'
        WHERE event_type = 'MILESTONE'
    """))

    # Revert category values
    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'family'
        WHERE category = 'FAMILY'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'relationships'
        WHERE category = 'RELATIONSHIPS'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'career'
        WHERE category = 'CAREER'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'health'
        WHERE category = 'HEALTH'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'education'
        WHERE category = 'EDUCATION'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'loss'
        WHERE category = 'LOSS'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'achievement'
        WHERE category = 'ACHIEVEMENT'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'trauma'
        WHERE category = 'TRAUMA'
    """))

    connection.execute(sa.text("""
        UPDATE life_events
        SET category = 'other'
        WHERE category = 'OTHER'
    """))
