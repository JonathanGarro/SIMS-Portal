"""
The Alembic migrations can build the schema from an empty database and match the
models exactly (#175). Uses the real `flask db` CLI in a subprocess, the way it's
run in production, against a throwaway database next to the test database.
"""
import os
import pathlib
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text

from tests.conftest import TEST_DATABASE_URL

FLASK_APP_DIR = pathlib.Path(__file__).resolve().parent.parent
MIGRATIONS_DB = 'sims_test_migrations'


@pytest.fixture
def migrations_db_url():
	admin = create_engine(TEST_DATABASE_URL, isolation_level='AUTOCOMMIT')
	with admin.connect() as conn:
		conn.execute(text(f'DROP DATABASE IF EXISTS {MIGRATIONS_DB}'))
		conn.execute(text(f'CREATE DATABASE {MIGRATIONS_DB}'))
	yield TEST_DATABASE_URL.rsplit('/', 1)[0] + '/' + MIGRATIONS_DB
	with admin.connect() as conn:
		conn.execute(text(f'DROP DATABASE IF EXISTS {MIGRATIONS_DB} WITH (FORCE)'))
	admin.dispose()


def _flask_db(url, *args):
	env = {
		**os.environ,
		'SIMS_SKIP_DOTENV': '1',
		'FLASK_APP': 'run.py',
		'FLASK_DEBUG': '1',  # DEBUG picks DEV_SQLALCHEMY_DATABASE_URI and keeps the scheduler off
		'DEV_SQLALCHEMY_DATABASE_URI': url,
		'SECRET_KEY': 'test',
	}
	result = subprocess.run([sys.executable, '-m', 'flask', 'db', *args], cwd=FLASK_APP_DIR, env=env,
	                        capture_output=True, text=True, timeout=120)
	return result.returncode, result.stdout + result.stderr


def _table_count(url):
	engine = create_engine(url)
	with engine.connect() as conn:
		n = conn.execute(text(
			"SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name <> 'alembic_version'"
		)).scalar()
	engine.dispose()
	return n


def test_migrations_build_the_schema_from_scratch_and_match_the_models(migrations_db_url):
	code, out = _flask_db(migrations_db_url, 'upgrade')
	assert code == 0, out[-3000:]
	assert _table_count(migrations_db_url) > 0

	# fails (non-zero) if the models and the migrated schema differ: add a migration
	code, out = _flask_db(migrations_db_url, 'check')
	assert code == 0, f'models and migrations have drifted apart - run `flask db migrate`:\n{out[-3000:]}'

	code, out = _flask_db(migrations_db_url, 'downgrade', 'base')
	assert code == 0, out[-3000:]
	assert _table_count(migrations_db_url) == 0

	code, out = _flask_db(migrations_db_url, 'upgrade')
	assert code == 0, out[-3000:]


def test_single_migration_head():
	"""Two heads means two branches of migrations were added in parallel; merge them."""
	code, out = _flask_db(TEST_DATABASE_URL, 'heads')
	heads = [line for line in out.splitlines() if '(head)' in line]
	assert code == 0 and len(heads) == 1, out[-3000:]


def test_duplicate_skill_and_language_rows_are_removed(migrations_db_url):
	code, out = _flask_db(migrations_db_url, 'upgrade', 'b7d3e1a95c42')
	assert code == 0, out[-3000:]
	engine = create_engine(migrations_db_url)
	with engine.begin() as conn:
		conn.execute(text("INSERT INTO \"user\" (id, firstname, lastname, email, password, image_file, password_compliant) "
		                  "VALUES (1, 'A', 'B', 'a@example.org', 'x', 'default.png', true)"))
		conn.execute(text("INSERT INTO skill (id, name) VALUES (1, 'QGIS'), (2, 'R')"))
		conn.execute(text("INSERT INTO language (id, name) VALUES (1, 'English')"))
		conn.execute(text("INSERT INTO user_skill (user_id, skill_id) VALUES (1, 1), (1, 1), (1, 1), (1, 2)"))
		conn.execute(text("INSERT INTO user_language (user_id, language_id) VALUES (1, 1), (1, 1)"))
	code, out = _flask_db(migrations_db_url, 'upgrade')
	assert code == 0, out[-3000:]
	with engine.connect() as conn:
		skills = conn.execute(text('SELECT skill_id FROM user_skill ORDER BY skill_id')).scalars().all()
		languages = conn.execute(text('SELECT language_id FROM user_language')).scalars().all()
	engine.dispose()
	assert skills == [1, 2] and languages == [1]
