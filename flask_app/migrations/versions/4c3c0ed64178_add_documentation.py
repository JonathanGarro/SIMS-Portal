"""add documentation

Revision ID: 4c3c0ed64178
Revises: c0f52bcd2a84
Create Date: 2023-10-09 16:33:21.469995

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c3c0ed64178'
down_revision = 'c0f52bcd2a84'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('documentation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('article_name', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_foreign_key(None, 'assignment', 'user', ['user_id'], ['id'])
    op.create_foreign_key(None, 'learning', 'assignment', ['assignment_id'], ['id'])
    op.create_foreign_key(None, 'story', 'emergency', ['emergency_id'], ['id'])
    op.drop_column('workinggroup', 'focal_point_name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('workinggroup', sa.Column('focal_point_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'story', type_='foreignkey')
    op.drop_constraint(None, 'learning', type_='foreignkey')
    op.drop_constraint(None, 'assignment', type_='foreignkey')
    op.drop_table('documentation')
    # ### end Alembic commands ###
