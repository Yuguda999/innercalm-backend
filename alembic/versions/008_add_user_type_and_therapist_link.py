"""Add user_type field and therapist profile link

Revision ID: 008_add_user_type_and_therapist_link
Revises: 007_add_community_tables
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_user_type_and_therapist_link'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """Add user_type field to users table and user_id to therapist_profiles."""
    
    # Add user_type column to users table
    op.add_column('users', sa.Column('user_type', sa.String(), nullable=True))
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True))
    
    # Set default values for existing users
    op.execute("UPDATE users SET user_type = 'client' WHERE user_type IS NULL")
    op.execute("UPDATE users SET is_verified = false WHERE is_verified IS NULL")
    
    # Make columns non-nullable after setting defaults
    op.alter_column('users', 'user_type', nullable=False)
    op.alter_column('users', 'is_verified', nullable=False)
    
    # Add user_id column to therapist_profiles table
    op.add_column('therapist_profiles', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_therapist_profiles_user_id',
        'therapist_profiles', 
        'users',
        ['user_id'], 
        ['id']
    )
    
    # Create unique constraint on user_id
    op.create_unique_constraint('uq_therapist_profiles_user_id', 'therapist_profiles', ['user_id'])


def downgrade():
    """Remove user_type field and therapist profile link."""
    
    # Drop constraints and columns from therapist_profiles
    op.drop_constraint('uq_therapist_profiles_user_id', 'therapist_profiles', type_='unique')
    op.drop_constraint('fk_therapist_profiles_user_id', 'therapist_profiles', type_='foreignkey')
    op.drop_column('therapist_profiles', 'user_id')
    
    # Drop columns from users table
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'user_type')
