"""
Route smoke test: request every GET route as an anonymous visitor, a regular
member, and an admin, and assert the app never returns a 500 / raises.

This doesn't check that pages are *correct*, only that they render without
crashing. It's a safety net for refactors and dependency upgrades.
URL arguments are filled in from the IDs created in tests/seed.py.
"""
import pytest

from tests.seed import ADMIN_ID, MEMBER_ID

PERSONAS = ('anonymous', 'member', 'admin')

# endpoint -> reason; these are deliberately not requested by the smoke test
SKIP_ENDPOINTS = {
	'static': 'Flask built-in',
}

# default values for non-integer URL arguments
STRING_ARGS = {
	'type': 'Map',
	'start': '2026-01-01',
	'end': '2026-01-07',
	'token': 'not-a-real-token',
	'name': 'does-not-exist.png',
	'filename': 'favicon.ico',
	'export_type': 'csv',
}

# integer URL arguments that should point at a specific seeded user
INT_ARGS = {
	'user_id': MEMBER_ID,
	'assigner_id': ADMIN_ID,
	'tier': 1,
}

# per-endpoint overrides where the generic default isn't meaningful
ENDPOINT_ARGS = {
	'main.view_role_profile': {'type': 'simsco'},
}

# Known 500s that can't be fixed right away. Keyed by (persona, endpoint), where
# persona '*' means all three; the value is '<issue ref>: <reason>', e.g.
#   ('member', 'main.some_page'): '#123: view returns None for non-admins',
# These are strict xfails: once a bug is fixed the test XPASSes, fails, and the
# entry must be removed. (Empty since #160 was cleared.)
KNOWN_FAILURES = {}


def _build_url(rule):
	overrides = ENDPOINT_ARGS.get(rule.endpoint, {})
	values = {}
	for arg in rule.arguments:
		if arg in overrides:
			values[arg] = overrides[arg]
		elif type(rule._converters[arg]).__name__ == 'IntegerConverter':
			values[arg] = INT_ARGS.get(arg, 1)
		else:
			values[arg] = STRING_ARGS[arg]
	return rule.build(values, append_unknown=False)[1]


def _get_routes():
	from tests.conftest import TestConfig
	from SIMS_Portal import create_app

	app = create_app(TestConfig)
	rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
	return [r for r in rules if 'GET' in r.methods and r.endpoint not in SKIP_ENDPOINTS]


def _params():
	params = []
	for persona in PERSONAS:
		for rule in _get_routes():
			reason = KNOWN_FAILURES.get((persona, rule.endpoint)) or KNOWN_FAILURES.get(('*', rule.endpoint))
			marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
			params.append(pytest.param(persona, _build_url(rule), marks=marks, id=f'{persona}-{rule.endpoint}'))
	return params


@pytest.mark.parametrize('persona,url', _params())
def test_get_route_does_not_error(request, persona, url):
	client = request.getfixturevalue({'anonymous': 'client', 'member': 'member_client', 'admin': 'admin_client'}[persona])
	response = client.get(url)
	assert response.status_code < 500, response.get_data(as_text=True)[:500]


def test_known_failures_reference_real_endpoints():
	"""Catch stale KNOWN_FAILURES entries left behind after a route is renamed or removed."""
	endpoints = {r.endpoint for r in _get_routes()}
	stale = [key for key in KNOWN_FAILURES if key[1] not in endpoints]
	assert not stale, f'KNOWN_FAILURES entries for endpoints that no longer exist: {stale}'
