"""Saving a profile: skills/languages aren't duplicated, and GitHub invites only go
out when a username is actually set or changed."""
from sqlalchemy import text

from SIMS_Portal import db
from SIMS_Portal.models import User
from SIMS_Portal.users import routes as user_routes
from tests.seed import ADMIN_ID, MEMBER_ID

BASE = {'firstname': 'Max', 'lastname': 'Member', 'email': 'member@example.org', 'skills': ['QGIS'], 'languages': ['English']}


def _rows(table, user_id=MEMBER_ID):
	return db.session.execute(text(f'SELECT count(*) FROM {table} WHERE user_id = :u'), {'u': user_id}).scalar()


def _invites(monkeypatch):
	sent = []
	monkeypatch.setattr(user_routes, 'invite_user_to_github', sent.append)
	return sent


def test_saving_twice_does_not_duplicate_skills_or_languages(member_client, monkeypatch):
	_invites(monkeypatch)
	for _ in range(3):
		assert member_client.post('/profile_edit', data={**BASE, 'github': ''}).status_code == 302
	assert _rows('user_skill') == 1 and _rows('user_language') == 1


def test_blank_github_field_sends_no_invite(member_client, monkeypatch):
	sent = _invites(monkeypatch)
	member_client.post('/profile_edit', data={**BASE, 'github': '  '})
	assert sent == [] and db.session.get(User, MEMBER_ID).github is None


def test_new_github_username_is_invited_once(member_client, monkeypatch):
	sent = _invites(monkeypatch)
	member_client.post('/profile_edit', data={**BASE, 'github': 'octocat'})
	member_client.post('/profile_edit', data={**BASE, 'github': 'octocat'})
	assert sent == ['octocat'] and db.session.get(User, MEMBER_ID).github == 'octocat'


def test_admin_edit_adds_without_duplicating(admin_client):
	data = {**BASE, 'github': '', 'skills': ['QGIS', 'Python'], 'languages': ['English']}
	db.session.execute(text("INSERT INTO skill (id, name, category) VALUES (900, 'Python', 'Data')"))
	db.session.commit()
	for _ in range(2):
		assert admin_client.post(f'/profile_edit/{MEMBER_ID}', data=data).status_code == 302
	assert _rows('user_skill') == 2 and _rows('user_language') == 1  # Python added once, QGIS kept once
	assert ADMIN_ID != MEMBER_ID
