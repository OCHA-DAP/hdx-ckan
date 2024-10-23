"""General Token Model

Revision ID: e76394fad066
Revises:
Create Date: 2024-09-22 22:18:38.950929

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'e76394fad066'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hdx_general_token',
        sa.Column('id', sa.UnicodeText, primary_key=True),
        sa.Column('token', sa.UnicodeText, index=True, unique=True, nullable=False),
        sa.Column('token_type', sa.UnicodeText, index=True, nullable=False),
        sa.Column('state', sa.UnicodeText, index=True, nullable=False),
        sa.Column('user_id', sa.UnicodeText, index=True, nullable=False),
        sa.Column('object_type', sa.UnicodeText, nullable=True),
        sa.Column('object_id', sa.UnicodeText, nullable=True),
        sa.Column('created', sa.DateTime, nullable=False),
        sa.Column('expires', sa.DateTime, nullable=True),
        sa.Column('extras', JSONB, nullable=True),
    )

    op.create_index(
            "idx_one_active_token_per_user_type_object", "hdx_general_token",
            ["user_id", "token_type", "object_type", "object_id", "state"],
            unique=True, postgresql_where=sa.text('"hdx_general_token".state=\'active\''))

def downgrade():
    op.drop_table('hdx_general_token')
