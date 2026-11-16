"""
Minimal fixture data: one row of every model, wired together, so that routes with
an <int:...> URL argument have a real record to render. IDs are fixed and set
explicitly so tests can refer to them.
"""
from datetime import date, datetime, timedelta

from sqlalchemy import text

from SIMS_Portal import bcrypt, db
from SIMS_Portal.models import (
	Acronym, Alert, Assignment, AssignmentChecklist, AssignmentSubTask, Availability,
	Badge, Checklist, Documentation, Emergency, EmergencyType, Language, Learning, Log,
	NationalSociety, Portfolio, Profile, Region, RegionalFocalPoint, Review, Skill,
	Story, SubTask, Task, User, WorkingGroup,
)

ADMIN_ID = 1
MEMBER_ID = 2
NS_GO_ID = 1
TEST_PASSWORD = 'test-password'


def seed_database():
	today = date.today()
	now = datetime.utcnow()
	password = bcrypt.generate_password_hash(TEST_PASSWORD).decode('utf-8')

	ns = NationalSociety(id=1, ns_name='Test Red Cross', country_name='Testland', ns_go_id=NS_GO_ID, iso2='TL', iso3='TST')
	profile = Profile(id=1, name='Information Management Coordinator', image='simsco.png')
	skill = Skill(id=1, name='QGIS', category='Geospatial')
	language = Language(id=1, name='English')
	badge = Badge(id=1, name='Test Badge', badge_url='test.png', description='A test badge')
	working_group = WorkingGroup(id=1, wg_name='Test WG', wg_description='desc', wg_url='https://example.org')
	region = Region(id=1, name='Americas')
	db.session.add_all([ns, profile, skill, language, badge, working_group, region])
	db.session.flush()

	admin = User(
		id=ADMIN_ID, firstname='Ada', lastname='Admin', email='admin@example.org', password=password,
		status='Active', is_admin=True, ns_id=NS_GO_ID, job_title='Admin', bio='Admin bio',
		coordinates='[0, 0]', time_zone='America/New_York', place_label='Testville',
	)
	member = User(
		id=MEMBER_ID, firstname='Max', lastname='Member', email='member@example.org', password=password,
		status='Active', is_admin=False, ns_id=NS_GO_ID, job_title='Analyst', bio='Member bio',
		coordinates='[0, 0]', time_zone='America/New_York', place_label='Testville',
	)
	member.skills.append(skill)
	member.profiles.append(profile)
	member.languages.append(language)
	member.badges.append(badge)
	member.working_groups.append(working_group)
	db.session.add_all([admin, member])
	db.session.flush()

	etype = EmergencyType(id=1, emergency_type_go_id=1, emergency_type_name='Flood')
	db.session.add(etype)
	db.session.flush()

	emergency = Emergency(
		id=1, emergency_name='Test Flood', emergency_status='Active', emergency_glide='FL-2026-000001-TST',
		emergency_go_id=1, emergency_location_id=NS_GO_ID, activation_details='details',
		slack_channel='C000000', emergency_type_id=1,
	)
	db.session.add(emergency)
	db.session.flush()

	assignment = Assignment(
		id=1, role='Information Management Coordinator', start_date=today - timedelta(days=7),
		end_date=today + timedelta(days=7), remote=True, assignment_details='details',
		assignment_status='Active', user_id=MEMBER_ID, emergency_id=1,
	)
	db.session.add(assignment)
	db.session.flush()

	checklist = Checklist(id=1, task_name='Set up Slack', task_description='desc')
	db.session.add(checklist)
	db.session.flush()
	subtask = SubTask(id=1, checklist_id=1, name='Create channel')
	assignment_checklist = AssignmentChecklist(id=1, emergency_id=1, checklist_id=1, task_completed=False)
	db.session.add_all([subtask, assignment_checklist])
	db.session.flush()

	db.session.add_all([
		AssignmentSubTask(id=1, assignment_checklist_id=1, sub_task_id=1, task_completed=False),
		Learning(id=1, overall_score=4, overall_exp='Good', assignment_id=1),
		Review(id=1, category='Coordination', type='Success', title='Test review', description='desc', status='Pending Approval', emergency_id=1),
		Story(id=1, entry='Story text', emergency_id=1),
		Portfolio(
			id=1, title='Test Map', type='Map', format='PDF', description='desc', product_status='Approved',
			local_file='test.pdf', image_file='test.png', creator_id=MEMBER_ID, assignment_id=1, emergency_id=1,
		),
		Availability(id=1, timeframe=str(today), dates='[]', user_id=MEMBER_ID, emergency_id=1),
		Alert(
			id=1, molnix_id=1, alert_record_created_at=now, event='Test Flood', role_profile='IM Coordinator',
			molnix_status='active', alert_status='Active', opens=now, start=now, end_time=now + timedelta(days=30),
			im_filter=True, iso3='TST', country_name='Testland', disaster_type_name='Flood', disaster_go_id=1,
			alert_id=1, region_id=1,
		),
		Acronym(id=1, acronym_eng='TST', def_eng='Test', expl_eng='Test acronym', added_by=MEMBER_ID, approved_by=ADMIN_ID, associated_ns=NS_GO_ID),
		RegionalFocalPoint(id=1, regional_id=1, focal_point_id=MEMBER_ID),
		Task(id=1, task_id=1, repo='test/repo', name='Test task', state='open', created_by_gh='octocat', url='https://example.org', created_at=now),
		Log(id=1, message='Seeded', user_id=ADMIN_ID),
	])
	db.session.flush()
	db.session.add(Documentation(id=1, article_name='Doc', url='https://example.org', category='Guide', summary='s', featured=True, author_id=ADMIN_ID, portfolio_id=1))
	db.session.commit()

	# rows were inserted with explicit IDs, so move each table's id sequence past them
	for table in db.metadata.sorted_tables:
		if 'id' in table.c and table.c.id.primary_key:
			db.session.execute(text(
				f"SELECT setval(pg_get_serial_sequence('\"{table.name}\"', 'id'), "
				f"COALESCE((SELECT MAX(id) FROM \"{table.name}\"), 0) + 1, false)"
			))
	db.session.commit()
