"""Add user.password_compliant (16-character password policy)

Revision ID: b7d3e1a95c42
Revises: 979dd9e82cb0
Create Date: 2026-11-23 12:00:00.000000

Every existing account starts False: their passwords are stored as bcrypt hashes,
so there's no way to tell which already meet the new minimum. The flag flips to
True the next time the member logs in with a long-enough password or sets a new one.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d3e1a95c42'
down_revision = '979dd9e82cb0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('password_compliant', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column('user', 'password_compliant')
