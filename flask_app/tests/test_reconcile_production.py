"""
Rehearse bringing production's database (stuck at the 2023 revision 1f05ced78d0d,
without the checklist tables) onto the current migration history:

    flask reconcile-production-schema   ->  stamps c02b8677c08a
    flask db upgrade                     ->  head, with no drift from the models

Starts from a schema-only copy of production (tests/fixtures/), no data.
"""
import pathlib

import pytest
from sqlalchemy import create_engine, text

from tests.conftest import TEST_DATABASE_URL
from tests.test_migrations import _flask_db

FIXTURE = pathlib.Path(__file__).parent / 'fixtures' / 'production_schema_1f05ced78d0d.sql'
DB_NAME = 'sims_test_reconcile'


@pytest.fixture
def production_like_db():
	admin = create_engine(TEST_DATABASE_URL, isolation_level='AUTOCOMMIT')
	with admin.connect() as conn:
		conn.execute(text(f'DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)'))
		conn.execute(text(f'CREATE DATABASE {DB_NAME}'))
	url = TEST_DATABASE_URL.rsplit('/', 1)[0] + '/' + DB_NAME
	engine = create_engine(url)
	# raw cursor, no parameters: the views contain LIKE '%...%', which a parameterised
	# execute would treat as placeholders
	raw = engine.raw_connection()
	try:
		raw.cursor().execute(FIXTURE.read_text())
		raw.commit()
	finally:
		raw.close()
	with engine.begin() as conn:
		conn.execute(text("SELECT pg_catalog.set_config('search_path', 'public', false)"))
		conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('1f05ced78d0d')"))
		# a little data, including an untagged and a tagged log line
		conn.execute(text("INSERT INTO nationalsociety (id, ns_name, country_name, ns_go_id) VALUES (1, 'NS', 'C', 1)"))
		conn.execute(text('INSERT INTO "user" (id, firstname, lastname, email, password, image_file, ns_id, twitter) '
		                  "VALUES (1, 'A', 'B', 'a@example.org', 'x', 'default.png', 1, '@a')"))
		conn.execute(text("INSERT INTO acronym (id, acronym_eng, def_eng, added_by) VALUES (1, 'TST', 'Test', 1)"))
	yield url, engine
	engine.dispose()
	with admin.connect() as conn:
		conn.execute(text(f'DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)'))
	admin.dispose()


def _revision(engine):
	with engine.connect() as conn:
		return conn.execute(text('SELECT version_num FROM public.alembic_version')).scalar()


def _tables(engine):
	with engine.connect() as conn:
		return {r[0] for r in conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))}


def test_dry_run_changes_nothing(production_like_db):
	url, engine = production_like_db
	code, out = _flask_db_cli(url, 'reconcile-production-schema', '--dry-run')
	assert code == 0, out
	assert 'create table checklist' in out and 'acronym.def_eng: VARCHAR -> TEXT' in out and 'Dry run' in out
	assert _revision(engine) == '1f05ced78d0d'
	assert 'checklist' not in _tables(engine)


def test_reconcile_then_upgrade_reaches_head_without_drift(production_like_db):
	url, engine = production_like_db
	code, out = _flask_db_cli(url, 'reconcile-production-schema')
	assert code == 0, out
	assert _revision(engine) == 'c02b8677c08a'
	assert {'checklist', 'sub_task', 'assignment_checklist', 'assignment_sub_task'} <= _tables(engine)

	# deploy step: align with production, keeping user.twitter for now
	code, out = _flask_db(url, 'upgrade', '4f2b1c9e7a30')
	assert code == 0, out
	# later: drop user.twitter
	code, out = _flask_db(url, 'upgrade')
	assert code == 0, out

	code, out = _flask_db(url, 'check')
	assert code == 0, f'schema still differs from the models:\n{out[-3000:]}'

	with engine.begin() as conn:
		assert conn.execute(text('SELECT count(*) FROM public."user"')).scalar() == 1  # data kept
		conn.execute(text("INSERT INTO public.log (message, user_id) VALUES ('[INFO] hello', 1)"))
		assert conn.execute(text("SELECT log_type FROM public.log WHERE message = '[INFO] hello'")).scalar() == 'INFO'


def test_refuses_on_any_other_revision(production_like_db):
	url, engine = production_like_db
	with engine.begin() as conn:
		conn.execute(text("UPDATE public.alembic_version SET version_num = 'c02b8677c08a'"))
	code, out = _flask_db_cli(url, 'reconcile-production-schema')
	assert code != 0 and 'nothing to reconcile' in out
	assert 'checklist' not in _tables(engine)


def _flask_db_cli(url, *args):
	"""Run a top-level flask command (not `flask db ...`) against url."""
	import os
	import subprocess
	import sys
	env = {**os.environ, 'SIMS_SKIP_DOTENV': '1', 'FLASK_APP': 'run.py', 'FLASK_DEBUG': '1',
	       'DEV_SQLALCHEMY_DATABASE_URI': url, 'SECRET_KEY': 'test'}
	result = subprocess.run([sys.executable, '-m', 'flask', *args], cwd=pathlib.Path(__file__).resolve().parent.parent,
	                        env=env, capture_output=True, text=True, timeout=120)
	return result.returncode, result.stdout + result.stderr
