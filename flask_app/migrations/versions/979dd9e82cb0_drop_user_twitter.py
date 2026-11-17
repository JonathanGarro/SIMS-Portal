"""Drop user.twitter (the Twitter/X profile field, removed from the UI in #136)

Revision ID: 979dd9e82cb0
Revises: 4f2b1c9e7a30
Create Date: 2026-11-16 15:00:00.000000

Irreversible for data: downgrade re-creates the column empty. Back up the
database first if any stored handles need to be kept (see #37).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '979dd9e82cb0'
down_revision = '4f2b1c9e7a30'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('user', 'twitter')


def downgrade():
    op.add_column('user', sa.Column('twitter', sa.String(length=120), nullable=True))
