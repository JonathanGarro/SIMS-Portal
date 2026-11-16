"""Map data endpoints that replaced the generated static/data files (#24)."""
import pytest

from SIMS_Portal import db
from SIMS_Portal.models import Emergency, NationalSociety, User
from tests.seed import MEMBER_ID


def test_response_history_counts_emergencies_per_country(client):
	db.session.add(NationalSociety(id=2, ns_name='Other RC', country_name='Otherland', ns_go_id=2, iso3='OTH'))
	db.session.add_all([
		Emergency(id=2, emergency_name='Quake', emergency_location_id=2),
		Emergency(id=3, emergency_name='Storm', emergency_location_id=2),
	])
	db.session.commit()
	data = client.get('/data/response_history.json').get_json()
	assert sorted(data, key=lambda d: d['iso3']) == [{'iso3': 'OTH', 'count': 2}, {'iso3': 'TST', 'count': 1}]


def test_member_locations_are_public_coordinates_only(client):
	data = client.get('/data/member_locations.json').get_json()
	assert data == [{'latitude': 0.0, 'longitude': 0.0}, {'latitude': 0.0, 'longitude': 0.0}]


@pytest.mark.parametrize('bad_value', ['None', '[abc, def]', '[1.5]'])
def test_member_locations_skip_malformed_coordinates(client, bad_value):
	db.session.query(User).filter(User.id == MEMBER_ID).update({'coordinates': bad_value})
	db.session.commit()
	assert client.get('/data/member_locations.json').get_json() == [{'latitude': 0.0, 'longitude': 0.0}]


def test_member_locations_skip_users_without_coordinates(client):
	db.session.query(User).filter(User.id == MEMBER_ID).update({'coordinates': None})
	db.session.commit()
	assert len(client.get('/data/member_locations.json').get_json()) == 1


def test_endpoints_are_cached_and_invalidated(app, client):
	from SIMS_Portal import cache
	from SIMS_Portal.main import map_data

	original = app.config['CACHE_TYPE']
	app.config['CACHE_TYPE'] = 'SimpleCache'
	cache.init_app(app)
	try:
		assert len(client.get('/data/member_locations.json').get_json()) == 2
		db.session.query(User).filter(User.id == MEMBER_ID).update({'coordinates': None})
		db.session.commit()
		assert len(client.get('/data/member_locations.json').get_json()) == 2  # still cached
		with app.app_context():
			map_data.invalidate_member_locations()
		assert len(client.get('/data/member_locations.json').get_json()) == 1
	finally:
		with app.app_context():
			cache.clear()
		app.config['CACHE_TYPE'] = original
		cache.init_app(app)
