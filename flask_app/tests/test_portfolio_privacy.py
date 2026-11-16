"""Who can see portfolio products and member profiles."""
import pytest

from SIMS_Portal import db
from SIMS_Portal.models import Portfolio, User
from tests.seed import MEMBER_ID

# (status, external) -> who may view: anonymous, member, admin
VISIBILITY = [
	('Approved', True, (True, True, True)),          # public
	('Approved', False, (False, True, True)),        # approved for internal use only
	('Pending Approval', True, (False, True, True)),  # in the coordinator's review queue
	('Personal', False, (False, True, True)),        # default for new uploads
	('Removed', False, (False, False, True)),        # soft-deleted
]
PRODUCT_ID = 60


def _product(status, external):
	db.session.add(Portfolio(id=PRODUCT_ID, title='Secret map', type='Map', local_file='missing.pdf',
	                         creator_id=MEMBER_ID, emergency_id=1, product_status=status, external=external))
	db.session.commit()


@pytest.mark.parametrize('status,external,allowed', VISIBILITY)
def test_view_page_visibility(status, external, allowed):
	_product(status, external)
	url = f'/portfolio/view/{PRODUCT_ID}'
	for persona, response, ok in zip(('anonymous', 'member', 'admin'), _fresh_responses(url), allowed):
		if ok:
			assert response.status_code == 200 and 'Secret map' in response.get_data(as_text=True), persona
		else:
			assert 'Secret map' not in response.get_data(as_text=True), persona
			if persona == 'anonymous':
				assert response.status_code == 302 and '/login' in response.headers['Location']
			else:
				assert response.status_code == 404, persona


@pytest.mark.parametrize('status,external,allowed', VISIBILITY)
def test_download_visibility(status, external, allowed):
	_product(status, external)
	url = f'/portfolio/download/{PRODUCT_ID}'
	for persona, response, ok in zip(('anonymous', 'member', 'admin'), _fresh_responses(url), allowed):
		# allowed requests reach the file lookup (404: the test file isn't on disk);
		# denied ones never get that far
		if ok:
			assert response.status_code == 404, persona
		elif persona == 'anonymous':
			assert response.status_code == 302 and '/login' in response.headers['Location']
		else:
			assert response.status_code == 404, persona


def _fresh_responses(url):
	"""Request url as anonymous, member and admin using separate clients (fresh sessions)."""
	from flask import current_app  # noqa: F401  (app context comes from the fixtures)
	from tests.conftest import _login
	from tests.seed import ADMIN_ID
	app = _app_ref[0]
	anon = app.test_client()
	member = _login(app.test_client(), MEMBER_ID)
	admin = _login(app.test_client(), ADMIN_ID)
	return [anon.get(url), member.get(url), admin.get(url)]


_app_ref = []


@pytest.fixture(autouse=True)
def _remember_app(app):
	_app_ref[:] = [app]


def test_unknown_product_is_404_for_everyone(member_client):
	assert member_client.get('/portfolio/view/9999').status_code == 404


# --- profiles -------------------------------------------------------------------

def _set_private(value):
	db.session.query(User).filter(User.id == MEMBER_ID).update({'private_profile': value})
	db.session.commit()


def test_private_profile_redirects_anonymous_visitors(client):
	_set_private(True)
	response = client.get(f'/profile/view/{MEMBER_ID}')
	assert response.status_code == 302 and '/login' in response.headers['Location']


def test_private_profile_visible_to_members_with_noindex(member_client):
	_set_private(True)
	html = member_client.get(f'/profile/view/{MEMBER_ID}').get_data(as_text=True)
	assert 'Max' in html and '<meta name="robots" content="noindex">' in html


def test_public_profile_has_no_noindex(client):
	_set_private(False)
	html = client.get(f'/profile/view/{MEMBER_ID}').get_data(as_text=True)
	assert 'noindex' not in html


def test_unknown_profile_is_404(client):
	assert client.get('/profile/view/9999').status_code == 404


def test_anonymous_profile_lists_only_public_products():
	_set_private(False)
	db.session.add_all([
		Portfolio(id=70, title='Public flood map', type='Map', local_file='a.pdf', creator_id=MEMBER_ID, emergency_id=1, product_status='Approved', external=True),
		Portfolio(id=71, title='Draft personal sketch', type='Map', local_file='b.pdf', creator_id=MEMBER_ID, emergency_id=1, product_status='Personal', external=False),
		Portfolio(id=72, title='Waiting in review queue', type='Map', local_file='c.pdf', creator_id=MEMBER_ID, emergency_id=1, product_status='Pending Approval', external=True),
	])
	db.session.commit()
	# the page lists the first three products and shows the total in its header
	import re
	anon_html, _, member_view_html = [r.get_data(as_text=True) for r in _fresh_responses(f'/profile/view/{MEMBER_ID}')]
	count = lambda html: int(re.search(r"Portfolio Highlights: <span class='text-dark'>(\d+)</span>", html).group(1))
	assert count(anon_html) == 1  # only the approved, external product
	assert 'Public flood map' in anon_html
	assert 'Draft personal sketch' not in anon_html and 'Waiting in review queue' not in anon_html
	assert count(member_view_html) == 4  # seeded product + the three above
