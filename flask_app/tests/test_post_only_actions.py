"""State-changing actions are POST-only (with CSRF), and the flows that used to chain
through GET routes do their writes in the POST handler."""
import pytest
from sqlalchemy import select

from SIMS_Portal import db
from SIMS_Portal.models import Assignment, Badge, Emergency, Portfolio, user_badge, user_profile
from tests.seed import ADMIN_ID, MEMBER_ID

POST_ONLY_URLS = [
	'/acronym/approve/1', '/acronym/delete/1', '/assignment/delete/1',
	'/availability/result/1', '/availability/result/next_week/1',
	'/admin/manage_checklist/remove/1', '/admin/manage_checklist/remove_subtask/1',
	'/admin/manage_checklist/delete_assigned_checklist/1', '/admin/manage_checklist/delete_assigned_subtask/1',
	'/emergency/closeout/1', '/emergency/delete/1', '/emergency/refresh_github/1',
	'/portfolio/add_supporter/1', '/portfolio/remove_supporter/1', '/portfolio/delete/1',
	'/portfolio/approve/1/1', '/portfolio/reject/1/1', '/operation_review/drop/1', '/story/delete/1',
	f'/delete_skill/{MEMBER_ID}/1', '/user/approve/2', '/user/delete/2', f'/user/save_slack_photo/{MEMBER_ID}',
]
REMOVED_GET_ROUTES = ['/badge_assignment/2/1', f'/badge_assignment/2/1/{ADMIN_ID}/1', '/assign_profiles/2/1/1', '/staging']


@pytest.mark.parametrize('url', POST_ONLY_URLS)
def test_get_is_rejected(admin_client, url):
	assert admin_client.get(url).status_code == 405


@pytest.mark.parametrize('url', REMOVED_GET_ROUTES)
def test_removed_get_routes_are_gone(admin_client, url):
	assert admin_client.get(url).status_code == 404


def test_post_requires_csrf_token(app, admin_client):
	app.config['WTF_CSRF_ENABLED'] = True
	try:
		assert admin_client.post('/emergency/delete/1').status_code == 400
	finally:
		app.config['WTF_CSRF_ENABLED'] = False
	db.session.expire_all()
	assert db.session.get(Emergency, 1).emergency_status == 'Active'


def test_post_performs_the_action(admin_client):
	assert admin_client.post('/emergency/delete/1').status_code == 302
	db.session.expire_all()
	assert db.session.get(Emergency, 1).emergency_status == 'Removed'


def test_pages_render_post_forms_with_csrf_tokens(app, admin_client):
	app.config['WTF_CSRF_ENABLED'] = True
	try:
		html = admin_client.get('/emergency/1').get_data(as_text=True)
	finally:
		app.config['WTF_CSRF_ENABLED'] = False
	for action in ('/emergency/closeout/1', '/emergency/delete/1', '/emergency/refresh_github/1'):
		assert f'<form method="POST" action="{action}"' in html
	assert 'name="csrf_token"' in html


# --- checklist admin tool ---------------------------------------------------------

CHECKLIST_PAGES = ['/admin/manage_checklist', '/admin/manage_checklist/edit/1']


# (member_client and admin_client share one client, so each persona gets its own test)
@pytest.mark.parametrize('url', CHECKLIST_PAGES)
def test_checklist_tool_forbidden_for_members(member_client, url):
	assert member_client.get(url).status_code == 403


@pytest.mark.parametrize('url', CHECKLIST_PAGES)
def test_checklist_tool_open_to_admins(admin_client, url):
	assert admin_client.get(url).status_code == 200


def test_member_cannot_delete_checklist_data(member_client):
	assert member_client.post('/admin/manage_checklist/delete_assigned_checklist/1').status_code == 403


# --- badges -------------------------------------------------------------------------

def _badges_of(user_id):
	return db.session.execute(select(user_badge.c.badge_id, user_badge.c.assigner_id, user_badge.c.assigner_justify)
	                          .where(user_badge.c.user_id == user_id)).fetchall()


@pytest.fixture
def second_badge():
	db.session.add(Badge(id=2, name='Second Badge', badge_url='b.png', description='d', limited_edition=False))
	db.session.commit()


def test_admin_awards_badge_once(admin_client, second_badge, monkeypatch):
	monkeypatch.setattr('SIMS_Portal.users.utils.send_slack_dm', lambda *a: None)
	form = {'user_name': str(MEMBER_ID), 'badge_name': '2', 'assigner_justify': 'Great work', 'submit_badge': 'Assign'}
	admin_client.post('/admin/assign_badge', data=form)
	admin_client.post('/admin/assign_badge', data=form)  # a resubmit must not duplicate it
	db.session.expire_all()
	awarded = [b for b in _badges_of(MEMBER_ID) if b.badge_id == 2]
	assert awarded == [(2, ADMIN_ID, 'Great work')]


def test_sims_coordinator_awards_badge_as_themselves(member_client, second_badge, monkeypatch):
	monkeypatch.setattr('SIMS_Portal.users.utils.send_slack_dm', lambda *a: None)
	# make the member a SIMS coordinator on emergency 1, and the admin a supporter there
	db.session.add(Assignment(id=10, role='SIMS Remote Coordinator', user_id=MEMBER_ID, emergency_id=1, assignment_status='Active'))
	db.session.add(Assignment(id=11, role='Remote IM Support', user_id=ADMIN_ID, emergency_id=1, assignment_status='Active'))
	db.session.commit()
	form = {'user_name': str(ADMIN_ID), 'badge_name': '2', 'assigner_justify': 'Thanks', 'submit_badge': 'Assign'}
	member_client.post('/badge_assignment_simsco/1', data=form)
	db.session.expire_all()
	assert [b for b in _badges_of(ADMIN_ID) if b.badge_id == 2] == [(2, MEMBER_ID, 'Thanks')]


# --- profiles -----------------------------------------------------------------------

def test_admin_assigns_profile_replacing_other_tiers(admin_client):
	admin_client.post('/admin/manage_profiles', data={'user_name': str(MEMBER_ID), 'profiles': '1', 'tier': '3', 'submit': 'Assign'})
	db.session.expire_all()
	rows = db.session.execute(select(user_profile.c.profile_id, user_profile.c.tier).where(user_profile.c.user_id == MEMBER_ID)).fetchall()
	assert [tuple(r) for r in rows] == [(1, 3)]


def test_portfolio_delete_still_works_for_creator(member_client):
	member_client.post('/portfolio/delete/1')
	db.session.expire_all()
	assert db.session.get(Portfolio, 1).product_status == 'Removed'


def test_cookie_settings():
	from SIMS_Portal.config import Config
	assert Config.SESSION_COOKIE_SAMESITE == 'Lax' and Config.REMEMBER_COOKIE_SAMESITE == 'Lax'
	assert Config.SESSION_COOKIE_SECURE == (not Config.DEBUG)
