"""
16-character password policy, the forced upgrade for older accounts, and the rate
limits on login, password reset and password change.
"""
from datetime import date, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from SIMS_Portal import bcrypt, db
from SIMS_Portal.models import User
from SIMS_Portal.password_policy import SKIP_SESSION_KEY, safe_next_url
from SIMS_Portal.users import routes as user_routes
from tests.seed import MEMBER_ID, TEST_PASSWORD

MEMBER_EMAIL = 'member@example.org'
LONG_PASSWORD = 'copper lantern river shoe'  # 25 characters
SHORT_PASSWORD = 'fifteen-chars!!'  # 15 characters

assert len(TEST_PASSWORD) < 16  # the seeded password predates the policy


def _member():
	return db.session.get(User, MEMBER_ID)


def _set_member(password=None, compliant=None):
	member = _member()
	if password is not None:
		member.password = bcrypt.generate_password_hash(password).decode('utf-8')
	if compliant is not None:
		member.password_compliant = compliant
	db.session.commit()


@pytest.fixture
def legacy_member():
	"""A member whose account predates the policy (short password, not yet compliant)."""
	_set_member(compliant=False)


@pytest.fixture
def deadline(app):
	original = app.config.get('PASSWORD_UPGRADE_DEADLINE')
	def set_deadline(value):
		app.config['PASSWORD_UPGRADE_DEADLINE'] = value
	yield set_deadline
	app.config['PASSWORD_UPGRADE_DEADLINE'] = original


def _login(client, password, email=MEMBER_EMAIL, next_url=None):
	query = {'next': next_url} if next_url else None
	return client.post('/login', query_string=query, data={'email': email, 'password': password})


def _location(response):
	return urlsplit(response.headers['Location'])


# --- logging in -------------------------------------------------------------------

def test_legacy_member_with_short_password_can_log_in_but_is_sent_to_change_it(client, legacy_member):
	response = _login(client, TEST_PASSWORD)
	assert response.status_code == 302
	assert _location(response).path == '/change_password'
	assert _member().password_compliant is False


def test_legacy_member_whose_password_is_already_long_is_marked_compliant_at_login(client):
	_set_member(password=LONG_PASSWORD, compliant=False)
	response = _login(client, LONG_PASSWORD)
	assert response.status_code == 302 and _location(response).path == '/dashboard'
	assert _member().password_compliant is True


def test_next_page_survives_the_detour_through_change_password(client, legacy_member):
	response = _login(client, TEST_PASSWORD, next_url='/members')
	assert parse_qs(_location(response).query) == {'next': ['/members']}


def test_login_ignores_offsite_next(client):
	response = _login(client, TEST_PASSWORD, next_url='https://evil.example/phish')
	assert response.status_code == 302 and _location(response).path == '/dashboard'
	assert _location(response).netloc in ('', 'localhost')


@pytest.mark.parametrize('target,expected', [
	('/members', '/members'),
	('/profile?tab=1', '/profile?tab=1'),
	('https://evil.example/', None),
	('//evil.example/', None),
	('/\\evil.example', None),
	('javascript:alert(1)', None),
	('', None),
	(None, None),
])
def test_safe_next_url(target, expected):
	assert safe_next_url(target) == expected


# --- the redirect on every page -----------------------------------------------------

def test_signed_in_legacy_member_is_redirected_from_any_page(member_client, legacy_member):
	# covers members who stay signed in via a remember-me cookie and never see /login
	response = member_client.get('/members')
	assert response.status_code == 302
	assert _location(response).path == '/change_password'
	assert parse_qs(_location(response).query) == {'next': ['/members']}


def test_compliant_member_is_not_redirected(member_client):
	assert member_client.get('/dashboard').status_code == 200


def test_legacy_member_can_still_reach_change_password_and_log_out(member_client, legacy_member):
	assert member_client.get('/change_password').status_code == 200
	response = member_client.get('/logout')
	assert response.status_code == 302 and _location(response).path != '/change_password'


def test_anonymous_visitors_are_unaffected(client):
	assert client.get('/login').status_code == 200


# --- changing the password ----------------------------------------------------------

def _change(client, current, new, confirm=None, next_url=None):
	query = {'next': next_url} if next_url else None
	return client.post('/change_password', query_string=query, data={
		'current_password': current, 'password': new, 'confirm_password': new if confirm is None else confirm,
	})


def test_change_password_success_marks_compliant_and_returns_to_next(member_client, legacy_member):
	response = _change(member_client, TEST_PASSWORD, LONG_PASSWORD, next_url='/members')
	assert response.status_code == 302 and _location(response).path == '/members'
	member = _member()
	assert member.password_compliant is True
	assert bcrypt.check_password_hash(member.password, LONG_PASSWORD)
	assert member_client.get('/members').status_code == 200


@pytest.mark.parametrize('current,new,confirm,error', [
	('wrong password', LONG_PASSWORD, None, 'current password is incorrect'),
	(TEST_PASSWORD, SHORT_PASSWORD, None, 'between 16 and 64 characters'),
	(TEST_PASSWORD, 'x' * 65, None, 'between 16 and 64 characters'),
	(TEST_PASSWORD, LONG_PASSWORD, LONG_PASSWORD + '!', 'Passwords must match'),
])
def test_change_password_rejects_bad_input(member_client, legacy_member, current, new, confirm, error):
	response = _change(member_client, current, new, confirm)
	assert response.status_code == 200 and error in response.get_data(as_text=True)
	assert _member().password_compliant is False


def test_change_password_rejects_reusing_the_current_password(member_client):
	_set_member(password=LONG_PASSWORD, compliant=False)
	response = _change(member_client, LONG_PASSWORD, LONG_PASSWORD)
	assert 'must be different' in response.get_data(as_text=True)


def test_change_password_ignores_offsite_next(member_client, legacy_member):
	response = _change(member_client, TEST_PASSWORD, LONG_PASSWORD, next_url='https://evil.example/')
	assert _location(response).path == '/dashboard'


def test_change_password_requires_login(client):
	response = client.get('/change_password')
	assert response.status_code == 302 and _location(response).path == '/login'


# --- "Remind me later" ----------------------------------------------------------------

def test_no_skip_offered_without_a_deadline(member_client, legacy_member, deadline):
	deadline(None)
	assert 'Remind me later' not in member_client.get('/change_password').get_data(as_text=True)
	response = member_client.post('/change_password/skip')
	assert _location(response).path == '/change_password'
	assert member_client.get('/members').status_code == 302


def test_skip_before_deadline_lets_member_through_for_the_session(member_client, legacy_member, deadline):
	deadline((date.today() + timedelta(days=7)).isoformat())
	assert 'Remind me later' in member_client.get('/change_password').get_data(as_text=True)
	response = member_client.post('/change_password/skip', query_string={'next': '/members'})
	assert _location(response).path == '/members'
	assert member_client.get('/members').status_code == 200


def test_skip_stops_working_once_the_deadline_passes(member_client, legacy_member, deadline):
	deadline(date.today().isoformat())
	member_client.post('/change_password/skip')
	deadline((date.today() - timedelta(days=1)).isoformat())
	assert member_client.get('/members').status_code == 302


def test_skip_refused_after_deadline(member_client, legacy_member, deadline):
	deadline((date.today() - timedelta(days=1)).isoformat())
	member_client.post('/change_password/skip')
	with member_client.session_transaction() as sess:
		assert SKIP_SESSION_KEY not in sess


def test_malformed_deadline_means_no_skip(member_client, legacy_member, deadline):
	deadline('next tuesday')
	assert 'Remind me later' not in member_client.get('/change_password').get_data(as_text=True)


# --- registration and Slack reset -------------------------------------------------------

def test_registration_requires_16_characters(client, monkeypatch):
	monkeypatch.setattr(user_routes, 'check_valid_slack_ids', lambda slack_id: True)
	data = {'firstname': 'New', 'lastname': 'Person', 'email': 'new@example.org', 'ns_id': '1', 'slack_id': 'UNEW'}
	response = client.post('/register', data={**data, 'password': SHORT_PASSWORD, 'confirm_password': SHORT_PASSWORD})
	assert 'between 16 and 64 characters' in response.get_data(as_text=True)
	assert User.query.filter_by(email='new@example.org').first() is None

	client.post('/register', data={**data, 'password': LONG_PASSWORD, 'confirm_password': LONG_PASSWORD})
	assert User.query.filter_by(email='new@example.org').one().password_compliant is True


def test_slack_reset_requires_16_characters_and_marks_compliant(client, legacy_member):
	token = _member().get_reset_token()
	response = client.post(f'/reset_password/{token}', data={'password': SHORT_PASSWORD, 'confirm_password': SHORT_PASSWORD})
	assert 'between 16 and 64 characters' in response.get_data(as_text=True)
	assert _member().password_compliant is False

	client.post(f'/reset_password/{token}', data={'password': LONG_PASSWORD, 'confirm_password': LONG_PASSWORD})
	assert _member().password_compliant is True


# --- rate limits ---------------------------------------------------------------------

def test_repeated_failed_logins_for_one_account_are_limited(client):
	for _ in range(5):
		assert _login(client, 'wrong password').status_code == 200
	response = _login(client, 'wrong password')
	assert response.status_code == 429
	assert 'too many attempts' in response.get_data(as_text=True)
	# even the right password is refused until the window passes
	assert _login(client, TEST_PASSWORD).status_code == 429


def test_account_limit_is_per_account(client):
	for _ in range(5):
		_login(client, 'wrong password')
	assert _login(client, 'wrong password', email='admin@example.org').status_code == 200


def test_failed_logins_from_one_ip_are_limited_across_accounts(client):
	for i in range(10):
		assert _login(client, 'wrong password', email=f'nobody{i}@example.org').status_code == 200
	assert _login(client, 'wrong password', email='someone-else@example.org').status_code == 429


def test_successful_logins_do_not_count_toward_the_limit(app):
	for _ in range(8):
		client = app.test_client()
		assert _login(client, TEST_PASSWORD).status_code == 302


def test_login_page_itself_is_never_limited(client):
	for _ in range(15):
		assert client.get('/login').status_code == 200


def test_password_reset_requests_are_limited_per_slack_id(client, monkeypatch):
	sent = []
	monkeypatch.setattr(user_routes, 'send_reset_slack', sent.append)
	slack_id = 'UMEMBER01'
	_member().slack_id = slack_id
	db.session.commit()
	for _ in range(3):
		assert client.post('/reset_password', data={'slack_id': slack_id}).status_code == 302
	assert client.post('/reset_password', data={'slack_id': slack_id}).status_code == 429
	assert len(sent) == 3


def test_failed_password_changes_are_limited(member_client):
	for _ in range(5):
		assert _change(member_client, 'wrong password', LONG_PASSWORD).status_code == 200
	assert _change(member_client, 'wrong password', LONG_PASSWORD).status_code == 429
