"""The production scheduler setup."""
import flask_apscheduler
import pytest

from SIMS_Portal import create_app
from tests.conftest import TestConfig


class ProductionLikeConfig(TestConfig):
	# what production runs with: DEBUG off, so the scheduler is enabled
	SCHEDULER_ENABLED = True


@pytest.fixture
def production_like_app(monkeypatch):
	# register the jobs and routes, but don't start the background thread
	monkeypatch.setattr(flask_apscheduler.APScheduler, 'start', lambda self, paused=False: None)
	return create_app(ProductionLikeConfig)


def test_scheduler_rest_api_is_not_exposed(production_like_app):
	exposed = [r.rule for r in production_like_app.url_map.iter_rules() if r.rule.startswith('/scheduler')]
	assert exposed == []


def test_scheduler_api_routes_return_404(production_like_app):
	client = production_like_app.test_client()
	assert client.get('/scheduler/jobs').status_code == 404
	assert client.post('/scheduler/jobs', json={'id': 'x', 'func': 'os:getcwd'}).status_code == 404


def test_scheduled_jobs_are_registered(production_like_app):
	job_ids = {job.id for job in production_like_app.apscheduler.get_jobs()}
	assert {'run_surge_alert_refresh', 'run_auto_badge_assigners', 'run_set_user_inactive', 'run_process_inactive_members'} <= job_ids
