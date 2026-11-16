"""Admin-only pages refuse regular members with a 403 (rather than a 500)."""
import pytest

ADMIN_ONLY_GET = [
	'/acronym/delete/1',
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
