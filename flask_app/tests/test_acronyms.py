"""Acronym search, visibility of unapproved submissions, and the admin review queue."""
import pytest

from SIMS_Portal import db
from SIMS_Portal.models import Acronym
from tests.seed import MEMBER_ID

PENDING_ID = 40


@pytest.fixture
def pending_acronym():
	# an old anonymous submission: filed under the bot account, never approved, with
	# the submitter's private contact details
	db.session.add(Acronym(id=PENDING_ID, acronym_eng='PND', def_eng='Pending thing', added_by=MEMBER_ID, approved_by=None,
	                       anonymous_submitter_name='Secret Person', anonymous_submitter_email='secret@private.example'))
	db.session.commit()


# --- search ---------------------------------------------------------------------

@pytest.mark.parametrize('url', ['/acronyms/search', '/acronyms/api/search'])
def test_search_cannot_filter_on_hidden_columns(client, url):
	db.session.query(Acronym).filter(Acronym.id == 1).update({'anonymous_submitter_email': 'tst-owner@private.example'})
	db.session.commit()
	# searching the email column for the domain would match acronym 1 if hidden columns
	# were searchable; with the allowlist it falls back to acronym_eng, which doesn't match
	response = client.get(url, query_string={'search_column': 'anonymous_submitter_email', 'search_term': 'private.example'})
	assert response.status_code == 200
	assert 'TST' not in response.get_data(as_text=True)


@pytest.mark.parametrize('column', ['national_society', 'query', '__class__', 'nonexistent'])
def test_search_with_bad_column_falls_back_instead_of_erroring(client, column):
	response = client.get('/acronyms/search', query_string={'search_column': column, 'search_term': 'TST'})
	assert response.status_code == 200 and 'TST' in response.get_data(as_text=True)


@pytest.mark.parametrize('column,term', [('acronym_eng', 'TST'), ('def_eng', 'Test')])
def test_allowed_columns_still_search(client, column, term):
	data = client.get('/acronyms/api/search', query_string={'search_column': column, 'search_term': term}).get_json()['results']
	assert [d['acronym_eng'] for d in data] == ['TST']


def test_search_excludes_unapproved(client, pending_acronym):
	data = client.get('/acronyms/api/search', query_string={'search_term': 'PND'}).get_json()['results']
	assert data == []


# --- view page -------------------------------------------------------------------

def test_unapproved_acronym_hidden_from_anonymous_and_members(client, pending_acronym):
	assert client.get(f'/view_acronym/{PENDING_ID}').status_code == 404


def test_unapproved_acronym_hidden_from_members(member_client, pending_acronym):
	assert member_client.get(f'/view_acronym/{PENDING_ID}').status_code == 404


def test_unapproved_acronym_visible_to_admins(admin_client, pending_acronym):
	assert admin_client.get(f'/view_acronym/{PENDING_ID}').status_code == 200


def test_approved_acronym_is_public(client):
	assert client.get('/view_acronym/1').status_code == 200


def test_similar_matches_skip_unapproved(client):
	db.session.add(Acronym(id=41, acronym_eng='TST', def_eng='Another meaning', added_by=MEMBER_ID, approved_by=None))
	db.session.commit()
	assert 'Another meaning' not in client.get('/view_acronym/1').get_data(as_text=True)


# --- admin queue -------------------------------------------------------------------

def test_queue_lists_every_pending_acronym(admin_client, pending_acronym):
	html = admin_client.get('/admin/process_acronyms').get_data(as_text=True)
	assert 'PND' in html
	assert 'TST' not in html  # already approved


def test_approving_from_the_queue_publishes_it(admin_client, pending_acronym):
	admin_client.post(f'/acronym/approve/{PENDING_ID}')
	db.session.expire_all()
	assert db.session.get(Acronym, PENDING_ID).approved_by is not None
	assert 'PND' not in admin_client.get('/admin/process_acronyms').get_data(as_text=True)


def test_member_submissions_are_auto_approved(member_client):
	from SIMS_Portal.models import User
	# auto-approval credits the Clara Barton bot account (user 63), which exists in production
	db.session.add(User(id=63, firstname='Clara', lastname='Barton', email='clara@example.org', password='x', status='Active', ns_id=1))
	db.session.commit()
	member_client.post('/submit_acronym/member', data={'acronym_eng': 'NEWX', 'def_eng': 'New example', 'scope': 'general', 'submit': 'Submit Acronym'})
	created = db.session.query(Acronym).filter(Acronym.acronym_eng == 'NEWX').first()
	assert created is not None and created.approved_by == 63
