"""
Shared pytest fixtures for the SIMS Portal test suite.

Safety rails (all set up before the app package is imported):
  * SIMS_SKIP_DOTENV=1 stops SIMS_Portal/__init__.py from loading the developer's
    real .env, so no production/dev database URL or Slack/Dropbox/GitHub/AWS token
    can ever reach a test run.
  * The test database URL must point at localhost and have "test" in its name,
    because the suite drops and recreates every table in it.
  * Outbound network connections to anything other than localhost are blocked, so
    a route that calls an external API fails loudly instead of really posting to
    Slack, hitting GO/Molnix, etc.
"""
import os
import socket
from urllib.parse import urlparse

import pytest
from sqlalchemy import orm

TEST_DATABASE_URL = os.environ.get(
	'TEST_DATABASE_URL', 'postgresql://sims:sims@localhost:5433/sims_test'
)

os.environ['SIMS_SKIP_DOTENV'] = '1'
os.environ.pop('FLASK_DEBUG', None)
os.environ['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URL
os.environ.setdefault('SECRET_KEY', 'test-secret-key')

_parsed = urlparse(TEST_DATABASE_URL)
if _parsed.hostname not in ('localhost', '127.0.0.1') or 'test' not in (_parsed.path or ''):
	raise RuntimeError(
		f'Refusing to run tests against {_parsed.hostname}{_parsed.path}: TEST_DATABASE_URL '
		'must be a localhost database with "test" in its name (its tables get dropped).'
	)


class ExternalNetworkBlocked(OSError):
	"""Raised when code under test tries to reach a non-local host."""


_LOCAL_HOSTS = {'localhost', '127.0.0.1', '::1'}
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _check_address(address):
	if isinstance(address, tuple) and address and address[0] not in _LOCAL_HOSTS:
		raise ExternalNetworkBlocked(f'Test tried to open a network connection to {address!r}')


def _guarded_connect(self, address):
	_check_address(address)
	return _real_connect(self, address)


def _guarded_connect_ex(self, address):
	_check_address(address)
	return _real_connect_ex(self, address)


socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex


from SIMS_Portal import create_app, db  # noqa: E402  (must come after the env setup above)
from SIMS_Portal.config import Config  # noqa: E402

from tests.seed import seed_database, ADMIN_ID, MEMBER_ID  # noqa: E402


class TestConfig(Config):
	TESTING = True
	DEBUG = False
	SECRET_KEY = 'test-secret-key'
	SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URL
	WTF_CSRF_ENABLED = False
	SCHEDULER_ENABLED = False
	CACHE_TYPE = 'NullCache'
	SERVER_NAME = 'localhost'
	RECAPTCHA_PUBLIC_KEY = 'test'
	RECAPTCHA_PRIVATE_KEY = 'test'


@pytest.fixture(scope='session')
def app():
	app = create_app(TestConfig)

	# _rollback_db keeps one app context open for the whole test, and Flask reuses an
	# open app context for test-client requests, so `g` (where Flask-Login caches the
	# current user) would carry one request's user into the next - even across
	# different clients. Production gets a fresh context per request; mirror that.
	@app.before_request
	def _forget_cached_user():
		from flask import g
		g.pop('_login_user', None)
	with app.app_context():
		db.drop_all()
		db.create_all()
		seed_database()
	yield app
	with app.app_context():
		db.session.remove()
		db.drop_all()


class _BoundSession(orm.Session):
	# Flask-SQLAlchemy passes its `db` object into the session constructor
	def __init__(self, db=None, **kwargs):
		super().__init__(**kwargs)


@pytest.fixture(autouse=True)
def _rollback_db(app):
	"""
	Run each test inside an outer transaction that is rolled back afterwards, so
	routes with side effects (several delete/approve routes accept GET) can't change
	the seeded data that later tests rely on.

	Caveat: Flask-Admin model views capture db.session when create_app() runs, so
	they keep using the real session. That's fine for GET-only smoke tests, but a
	test that POSTs to /admin/<model>/ would need to handle cleanup itself.
	"""
	with app.app_context():
		connection = db.engine.connect()
		transaction = connection.begin()
		original_session = db.session
		# A plain SQLAlchemy Session, not Flask-SQLAlchemy's: the latter's get_bind()
		# looks up the engine itself and ignores `bind`, so route commits would escape.
		db.session = db._make_scoped_session({
			'class_': _BoundSession,
			'bind': connection,
			'join_transaction_mode': 'create_savepoint',
		})
		try:
			yield
		finally:
			db.session.remove()
			db.session = original_session
			transaction.rollback()
			connection.close()


@pytest.fixture
def client(app):
	return app.test_client()


def _login(client, user_id):
	with client.session_transaction() as sess:
		sess['_user_id'] = str(user_id)
		sess['_fresh'] = True
	return client


@pytest.fixture
def member_client(client):
	return _login(client, MEMBER_ID)


@pytest.fixture
def admin_client(client):
	return _login(client, ADMIN_ID)
