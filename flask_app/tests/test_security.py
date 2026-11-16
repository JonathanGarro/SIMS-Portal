"""
Regression tests for route input handling: SQL built from URL input, and eval()
of URL input or stored values.
"""
from datetime import datetime

import pytest

from SIMS_Portal import db
from SIMS_Portal.main import routes as main_routes
from SIMS_Portal.models import Availability, Portfolio
from tests.seed import MEMBER_ID

# anything that reaches eval() would append to this list
EXECUTED = []
EVAL_PAYLOAD = "__import__('tests.test_security', fromlist=['EXECUTED']).EXECUTED.append(1)"


@pytest.fixture(autouse=True)
def _reset_executed():
	EXECUTED.clear()
	yield
	assert not EXECUTED, 'a payload was executed'


@pytest.fixture
def csrf_enabled(app):
	app.config['WTF_CSRF_ENABLED'] = True
	yield
	app.config['WTF_CSRF_ENABLED'] = False


# --- /role_profile/<type> -----------------------------------------------------

@pytest.mark.parametrize('role_type', main_routes.ROLE_PROFILE_TYPES)
def test_role_profile_known_types_render(client, role_type):
	assert client.get(f'/role_profile/{role_type}').status_code == 200


@pytest.mark.parametrize('payload', [
	"simsco' OR '1'='1",
	"x'; DROP TABLE profile; --",
	"Simsco",
	"../layout",
	"nonexistent",
])
def test_role_profile_rejects_unknown_types(client, payload):
	assert client.get(f'/role_profile/{payload}').status_code == 404


# --- /manual_refresh/<func> ---------------------------------------------------

def test_manual_refresh_rejects_get(admin_client):
	assert admin_client.get('/manual_refresh/update_member_locations').status_code == 405


def test_manual_refresh_requires_login(client):
	response = client.post('/manual_refresh/update_member_locations')
	assert response.status_code == 302
	assert '/login' in response.headers['Location']


def test_manual_refresh_forbidden_for_members(member_client, monkeypatch):
	called = []
	monkeypatch.setitem(main_routes.MANUAL_REFRESH_JOBS, 'update_member_locations', lambda: called.append(1))
	assert member_client.post('/manual_refresh/update_member_locations').status_code == 403
	assert not called


@pytest.mark.parametrize('func', [EVAL_PAYLOAD, 'print', 'db.drop_all', 'auto_badge_assigner_big_wig'])
def test_manual_refresh_rejects_unlisted_names(admin_client, func):
	assert admin_client.post(f'/manual_refresh/{func}').status_code == 404


def test_manual_refresh_runs_allowlisted_job(admin_client, monkeypatch):
	called = []
	monkeypatch.setitem(main_routes.MANUAL_REFRESH_JOBS, 'big_wig', lambda: called.append(1))
	response = admin_client.post('/manual_refresh/big_wig')
	assert response.status_code == 302
	assert called == [1]


def test_manual_refresh_requires_csrf_token(admin_client, csrf_enabled, monkeypatch):
	called = []
	monkeypatch.setitem(main_routes.MANUAL_REFRESH_JOBS, 'big_wig', lambda: called.append(1))
	assert admin_client.post('/manual_refresh/big_wig').status_code == 400
	assert not called


def test_manual_refresh_landing_renders_csrf_forms(admin_client, csrf_enabled):
	html = admin_client.get('/manual_refresh').get_data(as_text=True)
	assert html.count('name=\'csrf_token\'') == len(main_routes.MANUAL_REFRESH_JOBS)
	assert "href='/manual_refresh/" not in html


def test_manual_refresh_landing_forbidden_for_members(member_client):
	assert member_client.get('/manual_refresh').status_code == 403


# --- eval() of stored values --------------------------------------------------

def _this_week():
	# matches the timeframe stamp view_availability() looks up
	return f'{datetime.today().year}-{datetime.today().isocalendar()[1]}'


def test_availability_dates_are_not_evaluated(member_client):
	db.session.query(Availability).filter(Availability.id == 1).update({'dates': EVAL_PAYLOAD, 'timeframe': _this_week()})
	db.session.commit()
	try:
		member_client.get(f'/availability/view/{MEMBER_ID}/1')
	except (ValueError, SyntaxError):
		pass  # literal_eval refusing the payload is the expected outcome


def test_availability_dates_still_parse(member_client):
	db.session.query(Availability).filter(Availability.id == 1).update({'dates': "['Monday, January 05', 'Tuesday, January 06']", 'timeframe': _this_week()})
	db.session.commit()
	assert member_client.get(f'/availability/view/{MEMBER_ID}/1').status_code == 200


def test_portfolio_collaborators_still_parse(member_client):
	db.session.query(Portfolio).filter(Portfolio.id == 1).update({'collaborator_ids': '1,2'})
	db.session.commit()
	assert member_client.get('/portfolio/view/1').status_code == 200
