"""change token types for general tokens

Revision ID: affc4afb7c02
Revises: 805619810f88
Create Date: 2025-06-02 15:23:20.197755

"""
from alembic import op
import sqlalchemy as sa
from ckanext.hdx_users.general_token_model import HDXGeneralToken


# revision identifiers, used by Alembic.
revision = 'affc4afb7c02'
down_revision = '805619810f88'
branch_labels = None
depends_on = None


def upgrade():
    """
    update the token type column in the hdx_general_token table as follows:
    - 'email-validation-for-dataset' to 'email-validation-for-notification'
    - 'unsubscribe-for-dataset' to 'unsubscribe-for-notification'
    """
    tbl = HDXGeneralToken.__table__
    op.execute(
        tbl.update().where(tbl.c.token_type == 'email-validation-for-dataset')
            .values(token_type='email-validation-for-notification')
    )
    op.execute(
        tbl.update().where(tbl.c.token_type == 'unsubscribe-for-dataset')
            .values(token_type='unsubscribe-for-notification')
    )


def downgrade():
    """
    revert the token type column in the hdx_general_token table as follows:
    - 'email-validation-for-notification' to 'email-validation-for-dataset'
    - 'unsubscribe-for-notification' to 'unsubscribe-for-dataset'
    """
    tbl = HDXGeneralToken.__table__
    op.execute(
        tbl.update().where(tbl.c.token_type == 'email-validation-for-notification')
            .values(token_type='email-validation-for-dataset')
    )
    op.execute(
        tbl.update().where(tbl.c.token_type == 'unsubscribe-for-notification')
            .values(token_type='unsubscribe-for-dataset')
    )
