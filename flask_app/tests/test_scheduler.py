"""The production scheduler setup."""
import flask_apscheduler
import pytest

from SIMS_Portal import create_app, scheduler as scheduler_module
from tests.conftest import TestConfig

EXPECTED_JOBS = {
	'run_surge_alert_refresh', 'run_auto_badge_assigners', 'run_set_user_inactive',
	'run_process_inactive_members', 'run_update_member_locations',
}


@pytest.fixture
def make_production_like_app(monkeypatch, tmp_path):
	"""Build apps the way production does (scheduler enabled), sharing one lock file."""
	# register the jobs and routes, but don't start the background thread
	monkeypatch.setattr(flask_apscheduler.APScheduler, 'start', lambda self, paused=False: None)
	monkeypatch.setattr(scheduler_module, '_held_locks', [])

	class ProductionLikeConfig(TestConfig):
		SCHEDULER_ENABLED = True
		SCHEDULER_LOCK_FILE = str(tmp_path / 'scheduler.lock')

	created = []

	def make():
		app = create_app(ProductionLikeConfig)
		created.append(app)
		return app

	yield make
	for handle in scheduler_module._held_locks:
		handle.close()


def test_scheduler_rest_api_is_not_exposed(make_production_like_app):
	app = make_production_like_app()
	assert [r.rule for r in app.url_map.iter_rules() if r.rule.startswith('/scheduler')] == []
	client = app.test_client()
	assert client.get('/scheduler/jobs').status_code == 404
	assert client.post('/scheduler/jobs', json={'id': 'x', 'func': 'os:getcwd'}).status_code == 404


def test_all_jobs_are_registered(make_production_like_app):
	app = make_production_like_app()
	assert {job.id for job in app.apscheduler.get_jobs()} == EXPECTED_JOBS


def test_only_one_worker_runs_the_scheduler(make_production_like_app):
	# simulates gunicorn workers: each builds an app, but only the first gets the lock
	first, second, third = make_production_like_app(), make_production_like_app(), make_production_like_app()
	assert hasattr(first, 'apscheduler')
	assert not hasattr(second, 'apscheduler')
	assert not hasattr(third, 'apscheduler')


def test_lock_is_released_when_the_holder_exits(make_production_like_app):
	make_production_like_app()
	for handle in scheduler_module._held_locks:
		handle.close()  # what happens when the worker process exits
	assert hasattr(make_production_like_app(), 'apscheduler')


def test_member_locations_job_runs_at_startup(make_production_like_app):
	job = make_production_like_app().apscheduler.get_job('run_update_member_locations')
	assert job.next_run_time is not None and job.next_run_time.tzinfo is not None


def test_scheduler_disabled_in_tests_and_debug(app):
	assert not hasattr(app, 'apscheduler')


def test_jobs_run_inside_an_app_context(make_production_like_app, monkeypatch):
	ran = []
	monkeypatch.setattr('SIMS_Portal.users.utils.update_member_locations', lambda: ran.append(__import__('flask').current_app.name))
	job = make_production_like_app().apscheduler.get_job('run_update_member_locations')
	job.func()
	assert ran == ['SIMS_Portal']
