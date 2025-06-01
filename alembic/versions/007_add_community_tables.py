"""Add community tables for peer circles and reflection chains

Revision ID: 007
Revises: e7b9eaa16b62
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = 'e7b9eaa16b62'
branch_labels = None
depends_on = None


def upgrade():
    # Create shared_wound_groups table
    op.create_table('shared_wound_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('emotional_pattern', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('trauma_themes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('healing_stage', sa.String(), nullable=True),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shared_wound_groups_id'), 'shared_wound_groups', ['id'], unique=False)

    # Create peer_circles table
    op.create_table('peer_circles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shared_wound_group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'CLOSED', name='circlestatus'), nullable=True),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=True),
        sa.Column('requires_invitation', sa.Boolean(), nullable=True),
        sa.Column('facilitator_id', sa.Integer(), nullable=True),
        sa.Column('professional_moderator_id', sa.Integer(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['facilitator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['professional_moderator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['shared_wound_group_id'], ['shared_wound_groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_peer_circles_id'), 'peer_circles', ['id'], unique=False)

    # Create circle_memberships table
    op.create_table('circle_memberships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('peer_circle_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PENDING', 'LEFT', 'REMOVED', name='membershipstatus'), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['peer_circle_id'], ['peer_circles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_circle_memberships_id'), 'circle_memberships', ['id'], unique=False)

    # Create circle_messages table
    op.create_table('circle_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('peer_circle_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'FLAGGED', 'REMOVED', name='messagestatus'), nullable=True),
        sa.Column('flagged_by', sa.Integer(), nullable=True),
        sa.Column('flagged_reason', sa.String(), nullable=True),
        sa.Column('moderated_by', sa.Integer(), nullable=True),
        sa.Column('moderation_notes', sa.Text(), nullable=True),
        sa.Column('support_count', sa.Integer(), nullable=True),
        sa.Column('reply_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['flagged_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['moderated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['peer_circle_id'], ['peer_circles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_circle_messages_id'), 'circle_messages', ['id'], unique=False)

    # Create circle_message_replies table
    op.create_table('circle_message_replies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'FLAGGED', 'REMOVED', name='messagestatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['circle_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_circle_message_replies_id'), 'circle_message_replies', ['id'], unique=False)

    # Create message_supports table
    op.create_table('message_supports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('support_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['circle_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_supports_id'), 'message_supports', ['id'], unique=False)

    # Create reflection_chains table
    op.create_table('reflection_chains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('healing_module', sa.String(), nullable=False),
        sa.Column('difficulty_level', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('max_entries', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reflection_chains_id'), 'reflection_chains', ['id'], unique=False)

    # Create reflection_entries table
    op.create_table('reflection_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chain_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('reflection_type', sa.String(), nullable=True),
        sa.Column('target_stage', sa.String(), nullable=True),
        sa.Column('target_emotions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'FLAGGED', 'REMOVED', name='reflectionstatus'), nullable=True),
        sa.Column('flagged_by', sa.Integer(), nullable=True),
        sa.Column('flagged_reason', sa.String(), nullable=True),
        sa.Column('moderated_by', sa.Integer(), nullable=True),
        sa.Column('helpful_count', sa.Integer(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['chain_id'], ['reflection_chains.id'], ),
        sa.ForeignKeyConstraint(['flagged_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['moderated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reflection_entries_id'), 'reflection_entries', ['id'], unique=False)

    # Create user_cluster_profiles table
    op.create_table('user_cluster_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('dominant_emotions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('emotion_intensity', sa.Float(), nullable=False),
        sa.Column('emotion_variability', sa.Float(), nullable=False),
        sa.Column('trauma_themes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('healing_stage', sa.String(), nullable=True),
        sa.Column('coping_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('communication_style', sa.String(), nullable=True),
        sa.Column('support_preference', sa.String(), nullable=True),
        sa.Column('activity_level', sa.String(), nullable=True),
        sa.Column('cluster_vector', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('last_clustered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cluster_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_cluster_profiles_id'), 'user_cluster_profiles', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_user_cluster_profiles_id'), table_name='user_cluster_profiles')
    op.drop_table('user_cluster_profiles')
    
    op.drop_index(op.f('ix_reflection_entries_id'), table_name='reflection_entries')
    op.drop_table('reflection_entries')
    
    op.drop_index(op.f('ix_reflection_chains_id'), table_name='reflection_chains')
    op.drop_table('reflection_chains')
    
    op.drop_index(op.f('ix_message_supports_id'), table_name='message_supports')
    op.drop_table('message_supports')
    
    op.drop_index(op.f('ix_circle_message_replies_id'), table_name='circle_message_replies')
    op.drop_table('circle_message_replies')
    
    op.drop_index(op.f('ix_circle_messages_id'), table_name='circle_messages')
    op.drop_table('circle_messages')
    
    op.drop_index(op.f('ix_circle_memberships_id'), table_name='circle_memberships')
    op.drop_table('circle_memberships')
    
    op.drop_index(op.f('ix_peer_circles_id'), table_name='peer_circles')
    op.drop_table('peer_circles')
    
    op.drop_index(op.f('ix_shared_wound_groups_id'), table_name='shared_wound_groups')
    op.drop_table('shared_wound_groups')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS reflectionstatus')
    op.execute('DROP TYPE IF EXISTS messagestatus')
    op.execute('DROP TYPE IF EXISTS membershipstatus')
    op.execute('DROP TYPE IF EXISTS circlestatus')
