"""
GET requests must never change data (#178 follow-up to the GET-link audit).

Every GET route is requested as an admin and as a member, and the whole database
is compared before and after. CSRF protection only covers POST, so a GET that
writes can be triggered by a link, an <img> on another site, a refresh or a
prefetch. State-changing actions belong behind POST forms.
"""
import pytest
from sqlalchemy import text

from SIMS_Portal import db
from tests.test_smoke import _build_url, _get_routes

# endpoints whose GET legitimately writes something harmless
ALLOWED_GET_WRITES = {}


def _snapshot():
	"""Every row of every table, as comparable tuples."""
	state = {}
	for table in db.metadata.sorted_tables:
		rows = db.session.execute(text(f'SELECT * FROM "{table.name}"')).fetchall()
		state[table.name] = sorted(tuple(str(v) for v in row) for row in rows)
	return state


def _diff(before, after):
	changed = []
	for table in before:
		if before[table] != after[table]:
			added = len(set(after[table]) - set(before[table]))
			removed = len(set(before[table]) - set(after[table]))
			changed.append(f'{table} (+{added}/-{removed} rows)')
	return changed


ROUTES = [r for r in _get_routes() if r.endpoint not in ALLOWED_GET_WRITES]


@pytest.mark.parametrize('persona', ['admin', 'member'])
@pytest.mark.parametrize('rule', ROUTES, ids=lambda r: r.endpoint)
def test_get_does_not_change_data(request, persona, rule):
	client = request.getfixturevalue(f'{persona}_client')
	before = _snapshot()
	client.get(_build_url(rule))
	db.session.expire_all()
	changed = _diff(before, _snapshot())
	assert not changed, f'GET {rule.rule} as {persona} changed: {", ".join(changed)} - make it POST-only'
