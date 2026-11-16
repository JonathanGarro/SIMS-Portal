"""Saving a member's work location (/save_work_location -> /confirm_work_location)."""
import json

import pytest

from SIMS_Portal import db
from SIMS_Portal.models import User
from SIMS_Portal.users.utils import update_member_locations
from tests.seed import ADMIN_ID, MEMBER_ID

URL = f'/confirm_work_location/{MEMBER_ID}'
ORIGINAL_COORDINATES = '[0, 0]'


def _pending_location(client, user_id=MEMBER_ID):
	# what save_user_location() puts in the session after a successful search
	with client.session_transaction() as sess:
		sess['coordinates'] = [40.7, -74.0]
		sess['place_label'] = 'New York'
		sess['time_zone'] = 'America/New_York'
		sess['location_user_id'] = user_id


def _member():
	db.session.expire_all()
	return db.session.get(User, MEMBER_ID)


@pytest.fixture(autouse=True)
def _no_locations_file_write(monkeypatch):
	# confirm_user_location() regenerates the globe data file; not under test here
	monkeypatch.setattr('SIMS_Portal.users.routes.update_member_locations', lambda: None)


def test_get_is_not_allowed(member_client):
	assert member_client.get(URL).status_code == 405
	assert _member().coordinates == ORIGINAL_COORDINATES


def test_requires_login(client):
	response = client.post(URL)
	assert response.status_code == 302 and '/login' in response.headers['Location']


def test_without_pending_location_changes_nothing(member_client):
	response = member_client.post(URL)
	assert response.status_code == 302
	assert f'/save_work_location/{MEMBER_ID}' in response.headers['Location']
	assert _member().coordinates == ORIGINAL_COORDINATES


def test_pending_location_for_another_user_is_not_applied(admin_client):
	_pending_location(admin_client, user_id=ADMIN_ID)
	admin_client.post(URL)
	assert _member().coordinates == ORIGINAL_COORDINATES


def test_saves_pending_location_once(member_client):
	_pending_location(member_client)
	assert member_client.post(URL).status_code == 302
	member = _member()
	assert (member.coordinates, member.place_label, member.time_zone) == ('[40.7, -74.0]', 'New York', 'America/New_York')
	with member_client.session_transaction() as sess:
		assert not {'coordinates', 'place_label', 'time_zone', 'location_user_id'} & set(sess)

	# a second submit has nothing pending and must not overwrite with None
	member_client.post(URL)
	assert _member().coordinates == '[40.7, -74.0]'


def test_member_cannot_save_another_users_location(member_client):
	_pending_location(member_client, user_id=ADMIN_ID)
	member_client.post(f'/confirm_work_location/{ADMIN_ID}')
	db.session.expire_all()
	assert db.session.get(User, ADMIN_ID).coordinates == ORIGINAL_COORDINATES


def test_admin_can_save_a_members_location(admin_client):
	_pending_location(admin_client)
	admin_client.post(URL)
	assert _member().coordinates == '[40.7, -74.0]'


def test_save_page_requires_login(client):
	response = client.get(f'/save_work_location/{MEMBER_ID}')
	assert response.status_code == 302 and '/login' in response.headers['Location']


@pytest.mark.parametrize('bad_value', ['None', '[abc, def]', '[1.5]'])
def test_update_member_locations_skips_malformed_coordinates(app, bad_value):
	with app.app_context():
		db.session.query(User).filter(User.id == MEMBER_ID).update({'coordinates': bad_value})
		db.session.commit()
		update_member_locations()  # must not raise
		with open('SIMS_Portal/static/data/locations.json') as f:
			locations = json.load(f)
	assert locations == [{'latitude': 0.0, 'longitude': 0.0}]  # only the admin's valid row
