"""Add performance indexes for trauma mapping

Revision ID: add_performance_indexes
Revises: e7b9eaa16b62
Create Date: 2025-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_performance_indexes'
down_revision: Union[str, None] = 'e7b9eaa16b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes."""
    # Life Events indexes
    op.create_index('idx_life_events_user_id', 'life_events', ['user_id'])
    op.create_index('idx_life_events_event_date', 'life_events', ['event_date'])
    op.create_index('idx_life_events_user_date', 'life_events', ['user_id', 'event_date'])
    op.create_index('idx_life_events_trauma_severity', 'life_events', ['trauma_severity'])
    op.create_index('idx_life_events_is_resolved', 'life_events', ['is_resolved'])
    op.create_index('idx_life_events_event_type', 'life_events', ['event_type'])
    op.create_index('idx_life_events_category', 'life_events', ['category'])
    
    # Trauma Mappings indexes
    op.create_index('idx_trauma_mappings_user_id', 'trauma_mappings', ['user_id'])
    op.create_index('idx_trauma_mappings_life_event_id', 'trauma_mappings', ['life_event_id'])
    op.create_index('idx_trauma_mappings_analyzed_at', 'trauma_mappings', ['analyzed_at'])
    op.create_index('idx_trauma_mappings_user_analyzed', 'trauma_mappings', ['user_id', 'analyzed_at'])
    
    # Reframe Sessions indexes
    op.create_index('idx_reframe_sessions_user_id', 'reframe_sessions', ['user_id'])
    op.create_index('idx_reframe_sessions_life_event_id', 'reframe_sessions', ['life_event_id'])
    op.create_index('idx_reframe_sessions_status', 'reframe_sessions', ['status'])
    op.create_index('idx_reframe_sessions_created_at', 'reframe_sessions', ['created_at'])
    op.create_index('idx_reframe_sessions_user_status', 'reframe_sessions', ['user_id', 'status'])


def downgrade() -> None:
    """Remove performance indexes."""
    # Life Events indexes
    op.drop_index('idx_life_events_user_id')
    op.drop_index('idx_life_events_event_date')
    op.drop_index('idx_life_events_user_date')
    op.drop_index('idx_life_events_trauma_severity')
    op.drop_index('idx_life_events_is_resolved')
    op.drop_index('idx_life_events_event_type')
    op.drop_index('idx_life_events_category')
    
    # Trauma Mappings indexes
    op.drop_index('idx_trauma_mappings_user_id')
    op.drop_index('idx_trauma_mappings_life_event_id')
    op.drop_index('idx_trauma_mappings_analyzed_at')
    op.drop_index('idx_trauma_mappings_user_analyzed')
    
    # Reframe Sessions indexes
    op.drop_index('idx_reframe_sessions_user_id')
    op.drop_index('idx_reframe_sessions_life_event_id')
    op.drop_index('idx_reframe_sessions_status')
    op.drop_index('idx_reframe_sessions_created_at')
    op.drop_index('idx_reframe_sessions_user_status')
