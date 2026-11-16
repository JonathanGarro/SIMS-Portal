"""Syncing an emergency's GitHub issues into the Task table (tasks.utils.get_issues)."""
from datetime import datetime

import pytest
import requests

from SIMS_Portal import db
from SIMS_Portal.models import Emergency, Task
from SIMS_Portal.tasks import utils as task_utils
from SIMS_Portal.tasks.utils import GitHubSyncError, get_issues


def _issue(number, title='Issue'):
	return {
		'number': number, 'title': title, 'state': 'open', 'user': {'login': 'octocat'},
		'html_url': f'https://github.com/x/y/issues/{number}', 'assignees': [],
		'created_at': '2026-01-01T00:00:00Z',
	}


class _Response:
	def __init__(self, status_code=200, issues=()):
		self.status_code = status_code
		self._issues = list(issues)
		self.text = 'error body'

	def json(self):
		return self._issues


@pytest.fixture
def github(monkeypatch):
	"""Replace the GitHub API call; set github.response or github.error per test."""
	class Fake:
		response = _Response()
		error = None
	fake = Fake()

	def fake_get(url, headers=None, timeout=None):
		if fake.error:
			raise fake.error
		return fake.response
	monkeypatch.setattr(task_utils.requests, 'get', fake_get)
	return fake


def _tasks(repo):
	return {t.task_id: t.name for t in db.session.query(Task).filter(Task.repo == repo)}


def test_issue_numbers_are_scoped_to_their_repo(app, github):
	with app.app_context():
		db.session.add(Task(task_id=7, repo='repo-a', name='A7', state='open', created_at=datetime(2026, 1, 1)))
		db.session.commit()

		github.response = _Response(issues=[_issue(7, 'B7')])
		get_issues('repo-b')

		assert _tasks('repo-a') == {7: 'A7'}  # untouched, not moved to repo-b
		assert _tasks('repo-b') == {7: 'B7'}


def test_deletions_are_scoped_to_their_repo(app, github):
	with app.app_context():
		db.session.add_all([
			Task(task_id=3, repo='repo-a', name='A3', state='open', created_at=datetime(2026, 1, 1)),
			Task(task_id=3, repo='repo-b', name='B3', state='open', created_at=datetime(2026, 1, 1)),
		])
		db.session.commit()

		github.response = _Response(issues=[])  # issue 3 closed out of repo-b
		get_issues('repo-b')

		assert _tasks('repo-a') == {3: 'A3'}
		assert _tasks('repo-b') == {}


@pytest.mark.parametrize('setup', ['no_repo', 'unreachable', 'http_error'])
def test_failures_raise_github_sync_error(app, github, setup):
	repo = None if setup == 'no_repo' else 'repo-a'
	if setup == 'unreachable':
		github.error = requests.ConnectionError('down')
	if setup == 'http_error':
		github.response = _Response(status_code=404)
	with app.app_context(), pytest.raises(GitHubSyncError):
		get_issues(repo)


def test_refresh_route_reports_failure_instead_of_erroring(admin_client, github):
	github.error = requests.ConnectionError('down')
	response = admin_client.post('/emergency/refresh_github/1', follow_redirects=True)
	assert response.status_code == 200
	assert 'Could not sync GitHub issues' in response.get_data(as_text=True)


def test_refresh_route_syncs(admin_client, github):
	db.session.query(Emergency).filter(Emergency.id == 1).update({'github_repo': 'repo-a'})
	db.session.commit()
	github.response = _Response(issues=[_issue(1, 'First')])
	response = admin_client.post('/emergency/refresh_github/1', follow_redirects=True)
	assert 'Sync with GitHub issues for this emergency successful' in response.get_data(as_text=True)
	assert _tasks('repo-a') == {1: 'First'}
