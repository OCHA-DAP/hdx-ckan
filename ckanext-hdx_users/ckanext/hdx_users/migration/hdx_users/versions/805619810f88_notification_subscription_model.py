"""Notification Subscription Model

Revision ID: 805619810f88
Revises: e76394fad066
Create Date: 2025-05-13 08:14:12.724835

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '805619810f88'
down_revision = 'e76394fad066'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hdx_notifications_subscription',
        sa.Column('id', sa.UnicodeText, primary_key=True),
        sa.Column('state', sa.UnicodeText, index=True, nullable=False),
        sa.Column('user_id', sa.UnicodeText, sa.ForeignKey('user.id'), index=True, nullable=False),
        sa.Column('unsubscribe_token_id',
                  sa.UnicodeText, sa.ForeignKey('hdx_general_token.id'), index=True, nullable=False, unique=True),
        sa.Column('object', sa.UnicodeText, nullable=False),
        sa.Column('object_type', sa.UnicodeText, nullable=False),
        sa.Column('event_type', sa.UnicodeText, nullable=False),
        sa.Column('params', JSONB, nullable=True),
        sa.Column('created', sa.DateTime, nullable=False),
        sa.Column('updated', sa.DateTime, index=True, nullable=False),
    )

    # Create a partial unique index for active subscriptions only
    op.create_index(
        'ix_hdx_notifications_subscription_unique_active',
        'hdx_notifications_subscription',
        ['user_id', 'object', 'object_type'],
        unique=True,
        postgresql_where=sa.text("state = 'active'")
    )


def downgrade():
    op.drop_index(
        'ix_hdx_notifications_subscription_unique_active',
        'hdx_notifications_subscription',
        if_exists=True
    )
    op.drop_table('hdx_notifications_subscription')
