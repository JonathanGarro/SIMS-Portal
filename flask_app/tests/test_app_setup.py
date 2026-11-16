"""App factory pieces: security headers, CLI, config, heartbeats."""
import importlib

import pytest
import requests

from SIMS_Portal.main.utils import heartbeats
from SIMS_Portal.security import SECURITY_HEADERS


def test_security_headers_on_every_response(client):
	for url in ('/', '/health', '/does-not-exist'):
		response = client.get(url)
		for header, value in SECURITY_HEADERS.items():
			assert response.headers[header] == value


def test_csp_blocks_plugins_and_framing():
	csp = SECURITY_HEADERS['Content-Security-Policy']
	assert "object-src 'none'" in csp and csp.startswith("default-src 'self'")
	assert SECURITY_HEADERS['X-Frame-Options'] == 'DENY'


def test_health_check(client):
	assert client.get('/health').get_data(as_text=True) == 'OK'


def test_update_member_locations_cli_command(app, monkeypatch):
	ran = []
	monkeypatch.setattr('SIMS_Portal.users.utils.update_member_locations', lambda: ran.append(True))
	result = app.test_cli_runner().invoke(args=['update-member-locations'])
	assert result.exit_code == 0, result.output
	assert ran == [True]


def test_no_secrets_or_removed_keys_in_config():
	from SIMS_Portal.config import Config
	for removed in ('WERKZEUG_DEBUG_PIN', 'CONSUMER_KEY', 'ACCESS_TOKEN', 'TRELLO_KEY', 'LOGTAIL_SOURCE_TOKEN'):
		assert not hasattr(Config, removed)
	assert Config.SCHEDULER_API_ENABLED is False


def test_root_url_defaults_to_https_and_can_be_overridden(monkeypatch):
	from SIMS_Portal import config
	monkeypatch.delenv('ROOT_URL', raising=False)
	assert importlib.reload(config).Config.ROOT_URL == 'https://rcrcsims.org'
	monkeypatch.setenv('ROOT_URL', 'http://localhost:5001')
	assert importlib.reload(config).Config.ROOT_URL == 'http://localhost:5001'
	monkeypatch.delenv('ROOT_URL')
	importlib.reload(config)


class TestHeartbeats:
	def test_skipped_without_url(self, app):
		with app.app_context():
			assert heartbeats('job', None) == 'Skipped'

	def test_network_failure_does_not_raise(self, app, monkeypatch):
		def fail(*args, **kwargs):
			raise requests.ConnectionError('down')
		monkeypatch.setattr('SIMS_Portal.main.utils.requests.get', fail)
		with app.app_context():
			assert heartbeats('job', 'https://example.invalid/hb') == 'Request failed'

	@pytest.mark.parametrize('status,result', [(200, 'Request successful'), (500, 'Request failed')])
	def test_pings_url(self, app, monkeypatch, status, result):
		calls = []
		def fake_get(url, timeout=None):
			calls.append((url, timeout))
			return type('R', (), {'status_code': status})()
		monkeypatch.setattr('SIMS_Portal.main.utils.requests.get', fake_get)
		with app.app_context():
			assert heartbeats('job', 'https://example.invalid/hb') == result
		assert calls == [('https://example.invalid/hb', 10)]
