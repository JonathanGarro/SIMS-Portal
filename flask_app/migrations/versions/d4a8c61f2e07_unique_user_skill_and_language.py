"""Remove duplicate user_skill / user_language rows and make each pair unique

Revision ID: d4a8c61f2e07
Revises: b7d3e1a95c42
Create Date: 2026-11-24 18:00:00.000000

Every profile save used to re-add each selected skill and language, so these
association tables collected duplicate (user, skill) and (user, language) rows.
This keeps one row per pair and adds a unique constraint so it can't happen again.
The tables have no primary key, so duplicates are told apart by Postgres's ctid.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd4a8c61f2e07'
down_revision = 'b7d3e1a95c42'
branch_labels = None
depends_on = None

TABLES = (('user_skill', 'skill_id'), ('user_language', 'language_id'))


def upgrade():
	for table, column in TABLES:
		op.execute(f'''
			DELETE FROM {table} a
			USING {table} b
			WHERE a.user_id = b.user_id
			  AND a.{column} = b.{column}
			  AND a.ctid > b.ctid
		''')
		op.create_unique_constraint(f'uq_{table}_user_{column}', table, ['user_id', column])


def downgrade():
	# the removed duplicates are not restored
	for table, column in TABLES:
		op.drop_constraint(f'uq_{table}_user_{column}', table, type_='unique')
