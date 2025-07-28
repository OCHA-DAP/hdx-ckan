"""Update partial unique index to include 'active' and 'shadow' states

Revision ID: f98a43b1a0cd
Revises: affc4afb7c02
Create Date: 2025-07-28 13:00:00.000000

This migration updates the partial unique index on the 'user' table to enforce uniqueness
of the (email, state) pair for users whose state is either 'active' or 'shadow'. It allows
duplicate emails for all other states (e.g., 'deleted').
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'f98a43b1a0cd'
down_revision = 'affc4afb7c02'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old index (state = 'active')
    op.drop_index('idx_only_one_active_email', table_name='user')

    # Recreate the index with extended condition (state IN ('active', 'shadow'))
    op.create_index(
        'idx_only_one_active_email',  # same name
        'user',
        ['email', 'state'],
        unique=True,
        postgresql_where=sa.text("state IN ('active', 'shadow')")
    )


def downgrade():
    # Restore the original condition (state = 'active')
    op.drop_index('idx_only_one_active_email', table_name='user')

    op.create_index(
        'idx_only_one_active_email',
        'user',
        ['email', 'state'],
        unique=True,
        postgresql_where=sa.text("state = 'active'")
    )
