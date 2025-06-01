"""
Database migration to add multimodal self-expression tables.

This migration adds tables for:
- Voice journaling with real-time sentiment analysis
- Emotion art generation and customization
- Breathing exercise sessions
- Art galleries and sharing
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_multimodal_expression'
down_revision = 'previous_migration'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """Add multimodal self-expression tables."""
    
    # Voice Journal Tables
    op.create_table(
        'voice_journals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='recording'),
        sa.Column('audio_file_path', sa.String(), nullable=True),
        sa.Column('audio_duration', sa.Float(), nullable=True),
        sa.Column('audio_format', sa.String(), nullable=False, default='webm'),
        sa.Column('transcription', sa.Text(), nullable=True),
        sa.Column('transcription_confidence', sa.Float(), nullable=True),
        sa.Column('sentiment_timeline', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('emotion_spikes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('overall_sentiment', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_insights', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recommended_exercises', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('breathing_exercise_suggested', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voice_journals_id'), 'voice_journals', ['id'], unique=False)
    op.create_index(op.f('ix_voice_journals_user_id'), 'voice_journals', ['user_id'], unique=False)
    op.create_index(op.f('ix_voice_journals_status'), 'voice_journals', ['status'], unique=False)
    op.create_index(op.f('ix_voice_journals_created_at'), 'voice_journals', ['created_at'], unique=False)

    op.create_table(
        'voice_journal_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('journal_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('audio_segment_path', sa.String(), nullable=True),
        sa.Column('transcribed_text', sa.Text(), nullable=True),
        sa.Column('segment_start_time', sa.Float(), nullable=False),
        sa.Column('segment_duration', sa.Float(), nullable=False),
        sa.Column('emotions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sentiment_label', sa.String(), nullable=True),
        sa.Column('emotional_intensity', sa.Float(), nullable=True),
        sa.Column('themes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_emotional_spike', sa.Boolean(), nullable=False, default=False),
        sa.Column('spike_type', sa.String(), nullable=True),
        sa.Column('triggered_recommendations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['journal_id'], ['voice_journals.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voice_journal_entries_id'), 'voice_journal_entries', ['id'], unique=False)
    op.create_index(op.f('ix_voice_journal_entries_journal_id'), 'voice_journal_entries', ['journal_id'], unique=False)
    op.create_index(op.f('ix_voice_journal_entries_segment_start_time'), 'voice_journal_entries', ['segment_start_time'], unique=False)

    op.create_table(
        'breathing_exercise_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('voice_journal_id', sa.Integer(), nullable=True),
        sa.Column('exercise_type', sa.String(), nullable=False),
        sa.Column('exercise_name', sa.String(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('completion_percentage', sa.Float(), nullable=False, default=0.0),
        sa.Column('pre_session_mood', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('post_session_mood', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('effectiveness_rating', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['voice_journal_id'], ['voice_journals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_breathing_exercise_sessions_id'), 'breathing_exercise_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_breathing_exercise_sessions_user_id'), 'breathing_exercise_sessions', ['user_id'], unique=False)

    # Emotion Art Tables
    op.create_table(
        'emotion_arts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('art_style', sa.String(), nullable=False, default='abstract'),
        sa.Column('status', sa.String(), nullable=False, default='generating'),
        sa.Column('source_emotion_analysis_id', sa.Integer(), nullable=True),
        sa.Column('source_voice_journal_id', sa.Integer(), nullable=True),
        sa.Column('emotion_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('svg_content', sa.Text(), nullable=True),
        sa.Column('svg_data_url', sa.Text(), nullable=True),
        sa.Column('color_palette', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dominant_emotion', sa.String(), nullable=False),
        sa.Column('emotional_intensity', sa.Float(), nullable=False),
        sa.Column('complexity_level', sa.Integer(), nullable=False, default=3),
        sa.Column('generation_seed', sa.String(), nullable=True),
        sa.Column('generation_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_shared', sa.Boolean(), nullable=False, default=False),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['source_emotion_analysis_id'], ['emotion_analyses.id'], ),
        sa.ForeignKeyConstraint(['source_voice_journal_id'], ['voice_journals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emotion_arts_id'), 'emotion_arts', ['id'], unique=False)
    op.create_index(op.f('ix_emotion_arts_user_id'), 'emotion_arts', ['user_id'], unique=False)
    op.create_index(op.f('ix_emotion_arts_art_style'), 'emotion_arts', ['art_style'], unique=False)
    op.create_index(op.f('ix_emotion_arts_dominant_emotion'), 'emotion_arts', ['dominant_emotion'], unique=False)
    op.create_index(op.f('ix_emotion_arts_created_at'), 'emotion_arts', ['created_at'], unique=False)

    op.create_table(
        'art_customizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emotion_art_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('customization_type', sa.String(), nullable=False),
        sa.Column('original_value', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['emotion_art_id'], ['emotion_arts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_art_customizations_id'), 'art_customizations', ['id'], unique=False)
    op.create_index(op.f('ix_art_customizations_emotion_art_id'), 'art_customizations', ['emotion_art_id'], unique=False)

    op.create_table(
        'art_galleries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('art_pieces', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_pieces', sa.Integer(), nullable=False, default=0),
        sa.Column('total_views', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_art_galleries_id'), 'art_galleries', ['id'], unique=False)
    op.create_index(op.f('ix_art_galleries_user_id'), 'art_galleries', ['user_id'], unique=False)
    op.create_index(op.f('ix_art_galleries_is_public'), 'art_galleries', ['is_public'], unique=False)

    op.create_table(
        'art_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emotion_art_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('share_message', sa.Text(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, default=False),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('like_count', sa.Integer(), nullable=False, default=0),
        sa.Column('comment_count', sa.Integer(), nullable=False, default=0),
        sa.Column('is_approved', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_flagged', sa.Boolean(), nullable=False, default=False),
        sa.Column('shared_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['emotion_art_id'], ['emotion_arts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_art_shares_id'), 'art_shares', ['id'], unique=False)
    op.create_index(op.f('ix_art_shares_emotion_art_id'), 'art_shares', ['emotion_art_id'], unique=False)
    op.create_index(op.f('ix_art_shares_shared_at'), 'art_shares', ['shared_at'], unique=False)


def downgrade():
    """Remove multimodal self-expression tables."""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('art_shares')
    op.drop_table('art_galleries')
    op.drop_table('art_customizations')
    op.drop_table('emotion_arts')
    op.drop_table('breathing_exercise_sessions')
    op.drop_table('voice_journal_entries')
    op.drop_table('voice_journals')
