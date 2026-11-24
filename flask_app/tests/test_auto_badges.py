"""
Automatic badge assigners that count assignments: Old Salt (three or more as SIMS
Remote Coordinator) and World Traveler (emergencies in five or more countries).
"""
import pytest
from sqlalchemy import text

from SIMS_Portal import db
from SIMS_Portal.main import utils as main_utils
from SIMS_Portal.models import Assignment, Badge, Emergency, NationalSociety
from tests.seed import ADMIN_ID, MEMBER_ID


@pytest.fixture(autouse=True)
def badges():
	db.session.add_all([
		Badge(id=main_utils.OLD_SALT_BADGE_ID, name='Old Salt', badge_url='old_salt.png'),
		Badge(id=main_utils.WORLD_TRAVELER_BADGE_ID, name='World Traveler', badge_url='world_traveler.png'),
	])
	db.session.commit()


def _holders(badge_id):
	rows = db.session.execute(text('SELECT user_id FROM user_badge WHERE badge_id = :b'), {'b': badge_id})
	return sorted(row.user_id for row in rows)


_next_id = iter(range(1000, 2000))


def _assign(user_id, emergency_id=1, role='Information Management Coordinator', status='Active'):
	db.session.add(Assignment(id=next(_next_id), user_id=user_id, emergency_id=emergency_id, role=role, assignment_status=status))
	db.session.commit()


def _emergency_in(country, status='Active'):
	"""A new emergency located in a new National Society for `country`; returns its id."""
	n = next(_next_id)
	db.session.add(NationalSociety(id=n, ns_name=f'{country} Red Cross', country_name=country, ns_go_id=n))
	db.session.add(Emergency(id=n, emergency_name=f'{country} Flood', emergency_status=status,
	                         emergency_location_id=n, emergency_type_id=1))
	db.session.commit()
	return n


# --- Old Salt -----------------------------------------------------------------------

def test_old_salt_goes_to_three_time_remote_coordinators():
	for _ in range(3):
		_assign(MEMBER_ID, role='SIMS Remote Coordinator')
	main_utils.auto_badge_assigner_old_salt()
	assert _holders(main_utils.OLD_SALT_BADGE_ID) == [MEMBER_ID]


def test_old_salt_needs_three_coordinator_roles_not_counting_removed_ones():
	_assign(MEMBER_ID, role='SIMS Remote Coordinator')
	_assign(MEMBER_ID, role='SIMS Remote Coordinator')
	_assign(MEMBER_ID, role='SIMS Remote Coordinator', status='Removed')
	_assign(MEMBER_ID, role='Information Management Coordinator')
	main_utils.auto_badge_assigner_old_salt()
	assert _holders(main_utils.OLD_SALT_BADGE_ID) == []


def test_old_salt_is_not_given_twice():
	for _ in range(4):
		_assign(ADMIN_ID, role='SIMS Remote Coordinator')
	main_utils.auto_badge_assigner_old_salt()
	main_utils.auto_badge_assigner_old_salt()
	assert _holders(main_utils.OLD_SALT_BADGE_ID) == [ADMIN_ID]


# --- World Traveler -------------------------------------------------------------------
# (the admin has no seeded assignments; the member already has one in Testland)

def test_world_traveler_goes_to_members_with_emergencies_in_five_countries():
	for country in ['Chad', 'Peru', 'Nepal', 'Fiji', 'Mali']:
		_assign(ADMIN_ID, emergency_id=_emergency_in(country))
	main_utils.auto_badge_assigner_world_traveler()
	assert _holders(main_utils.WORLD_TRAVELER_BADGE_ID) == [ADMIN_ID]


def test_world_traveler_counts_countries_not_emergencies():
	# five emergencies but only two countries
	for country in ['Chad', 'Chad', 'Chad', 'Peru', 'Peru']:
		_assign(ADMIN_ID, emergency_id=_emergency_in(country))
	main_utils.auto_badge_assigner_world_traveler()
	assert _holders(main_utils.WORLD_TRAVELER_BADGE_ID) == []


def test_world_traveler_ignores_removed_assignments_and_emergencies():
	for country in ['Chad', 'Peru', 'Nepal', 'Fiji']:
		_assign(ADMIN_ID, emergency_id=_emergency_in(country))
	_assign(ADMIN_ID, emergency_id=_emergency_in('Mali'), status='Removed')
	_assign(ADMIN_ID, emergency_id=_emergency_in('Laos', status='Removed'))
	main_utils.auto_badge_assigner_world_traveler()
	assert _holders(main_utils.WORLD_TRAVELER_BADGE_ID) == []


def test_world_traveler_uses_the_emergency_country_not_a_matching_id():
	# the old query matched NationalSociety.id to Emergency.id, so an emergency's
	# "country" was whichever society happened to share its row id
	for country in ['Chad', 'Peru', 'Nepal', 'Fiji', 'Mali']:
		emergency_id = _emergency_in(country)
		# point each emergency at the seeded Testland society instead
		db.session.get(Emergency, emergency_id).emergency_location_id = 1
		_assign(ADMIN_ID, emergency_id=emergency_id)
	db.session.commit()
	main_utils.auto_badge_assigner_world_traveler()
	assert _holders(main_utils.WORLD_TRAVELER_BADGE_ID) == []  # all five are in Testland
