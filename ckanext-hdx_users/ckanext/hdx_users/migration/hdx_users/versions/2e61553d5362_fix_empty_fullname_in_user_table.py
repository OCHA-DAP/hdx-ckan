"""fix_empty_fullname_in_user_table

Revision ID: 2e61553d5362
Revises: e76394fad066
Create Date: 2025-08-01 09:18:06.404522

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '2e61553d5362'
down_revision = 'e76394fad066'
branch_labels = None
depends_on = None


def upgrade():
    # Update users where fullname is empty string or null to use their name instead
    op.execute("""
        UPDATE "user" 
        SET fullname = name 
        WHERE (fullname = '' OR fullname IS NULL)
    """)


def downgrade():
    # No downgrade needed - this is a data fix migration
    pass
