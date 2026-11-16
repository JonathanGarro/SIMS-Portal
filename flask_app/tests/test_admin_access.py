"""Admin-only pages refuse regular members with a 403 (rather than a 500)."""
import pytest

ADMIN_ONLY_GET = [
	'/admin/assign_badge',
	'/admin/edit_skills',
	'/admin/upload_badges',
	'/manual_refresh',
]


@pytest.mark.parametrize('url', ADMIN_ONLY_GET)
def test_members_get_403(member_client, url):
	assert member_client.get(url).status_code == 403


@pytest.mark.parametrize('url', ADMIN_ONLY_GET)
def test_admins_are_let_through(admin_client, url):
	assert admin_client.get(url).status_code in (200, 302)


def test_process_review_hidden_from_members(member_client):
	# this view answers non-admins with a 404 rather than revealing the review
	assert member_client.get('/operation_review/process/1').status_code == 404


def test_logs_page_handles_untagged_messages_without_modifying_them(admin_client):
	from SIMS_Portal import db
	from SIMS_Portal.models import Log

	db.session.add_all([Log(id=100, message='[ERROR] tagged failure', user_id=0), Log(id=101, message='untagged note', user_id=0)])
	db.session.commit()

	html = admin_client.get('/admin/view_logs').get_data(as_text=True)
	assert 'tagged failure' in html and 'untagged note' in html
	assert '<span class="error">ERROR</span>' in html

	db.session.expire_all()
	assert db.session.get(Log, 100).message == '[ERROR] tagged failure'


FLASK_ADMIN_URLS = ['/admin/', '/admin/user/', '/admin/user/new/', '/admin/nationalsociety/new/', '/admin/user/export/csv/']


@pytest.mark.parametrize('url', FLASK_ADMIN_URLS)
def test_flask_admin_is_admin_only(client, member_client, url):
	assert client.get(url).status_code == 403
	assert member_client.get(url).status_code == 403


@pytest.mark.parametrize('url', FLASK_ADMIN_URLS)
def test_flask_admin_pages_render_for_admins(admin_client, url):
	# CSV export is disabled (Flask-Admin's default can_export=False), so it redirects to the list
	expected = 302 if '/export/' in url else 200
	assert admin_client.get(url).status_code == expected


def test_flask_admin_user_list_hides_password_hash(admin_client):
	html = admin_client.get('/admin/user/').get_data(as_text=True)
	assert 'member@example.org' in html
	assert '$2b$' not in html  # bcrypt hash prefix
