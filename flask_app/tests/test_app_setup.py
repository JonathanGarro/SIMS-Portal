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


def _csp_directive(name):
	for directive in SECURITY_HEADERS['Content-Security-Policy'].rstrip(';').split('; '):
		parts = directive.split()
		if parts[0] == name:
			return set(parts[1:])
	raise AssertionError(f'no {name} directive')


def test_csp_allows_every_external_asset_in_templates():
	"""Adding a CDN script/stylesheet to a template without updating security.py breaks it in browsers."""
	import pathlib
	import re

	templates = pathlib.Path(__file__).parent.parent / 'SIMS_Portal' / 'templates'
	needed = {'script-src': set(), 'style-src': set()}
	for path in templates.rglob('*.html'):
		html = path.read_text()
		needed['script-src'] |= set(re.findall(r'<script[^>]*\ssrc=["\'](https://[^/"\']+)', html))
		needed['style-src'] |= set(re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\'](https://[^/"\']+)', html))
		needed['style-src'] |= set(re.findall(r'<link[^>]*href=["\'](https://[^/"\']+)[^>]*rel=["\']stylesheet["\']', html))
	assert needed['script-src'], 'expected to find CDN scripts'
	for directive, hosts in needed.items():
		missing = hosts - _csp_directive(directive)
		assert not missing, f'{directive} is missing {sorted(missing)}; add them in SIMS_Portal/security.py'


def test_layout_loads_a_single_bootstrap():
	import pathlib
	layout = (pathlib.Path(__file__).parent.parent / 'SIMS_Portal' / 'templates' / 'layout.html').read_text()
	assert layout.count('bootstrap.bundle.min.js') == 1
	assert 'bootstrap@5.3' in layout
	for gone in ('bootstrap/4.0.0', 'popper.js/1.', '@popperjs/core', 'recaptcha', '@^'):
		assert gone not in layout


def test_no_bootstrap4_data_attributes_left():
	import pathlib
	import re
	templates = pathlib.Path(__file__).parent.parent / 'SIMS_Portal' / 'templates'
	offenders = []
	for path in templates.rglob('*.html'):
		if path.parent.name == 'admin':  # Flask-Admin's own templates
			continue
		for m in re.finditer(r'(?<![\w-])data-(toggle|target|dismiss|placement|parent|spy|offset)=', path.read_text()):
			offenders.append(f'{path.name}: {m.group(0)}')
	assert not offenders, offenders


TEMPLATES_DIR = __import__('pathlib').Path(__file__).parent.parent / 'SIMS_Portal' / 'templates'

# a page that uses one of these must load it via partials/assets.html
PAGE_LIBRARIES = {
	'd3': (r'\bd3\.', 'assets.d3()'),
	'topojson': (r'\btopojson\.', 'assets.topojson()'),
	'Chart.js': (r'new Chart\(', 'assets.chartjs()'),
	'FullCalendar': (r'FullCalendar\.', 'assets.fullcalendar()'),
}


@pytest.mark.parametrize('library', PAGE_LIBRARIES)
def test_pages_load_the_libraries_they_use(library):
	import re
	usage, loader = PAGE_LIBRARIES[library]
	missing = [
		p.name for p in TEMPLATES_DIR.rglob('*.html')
		if p.parent.name not in ('admin', 'partials') and p.name != 'layout.html'
		and re.search(usage, p.read_text()) and loader not in p.read_text()
	]
	assert not missing, f'{library} used without {{{{ {loader} }}}}: {missing}'


def test_layout_does_not_load_page_specific_libraries():
	layout = (TEMPLATES_DIR / 'layout.html').read_text()
	for lib in ('d3', 'chart.js', 'fullcalendar', 'moment', 'feather-icons', 'fontawesome', 'topojson'):
		assert lib not in layout.lower(), lib


def test_single_icon_set():
	import re
	offenders = [p.name for p in TEMPLATES_DIR.rglob('*.html')
	             if p.parent.name != 'admin' and re.search(r'data-feather|\bfa-solid\b|\bfa-regular\b|\bfa fa-|feather\.replace', p.read_text())]
	assert not offenders, offenders


def test_nothing_rendered_before_extends():
	"""Markup before {% extends %} is emitted ahead of <!DOCTYPE>; use {% block head %} instead."""
	offenders = []
	for p in TEMPLATES_DIR.rglob('*.html'):
		text = p.read_text()
		if '{% extends' in text and not text.lstrip().startswith('{% extends'):
			offenders.append(p.name)
	assert not offenders, offenders


STATIC_DIR = TEMPLATES_DIR.parent / 'static'


def test_datatables_use_v2_layout_not_legacy_dom():
	"""The legacy `dom` option skips DataTables 2's .dt-layout-table wrapper, which the
	responsive CSS relies on to keep wide tables from overflowing phone screens."""
	import re
	scripts = (STATIC_DIR / 'js' / 'scripts.js').read_text()
	assert not re.search(r'^\s*dom\s*:', scripts, re.M)
	assert 'div.dt-container .dt-layout-table > div' in (STATIC_DIR / 'css' / 'main.css').read_text()


def test_no_fixed_widths_wider_than_a_phone_in_templates():
	import re
	offenders = []
	for p in TEMPLATES_DIR.rglob('*.html'):
		if p.parent.name == 'admin':
			continue
		for m in re.finditer(r'(?:min-)?width:\s*(\d{3,})px|\swidth=["\']?(\d{3,})', p.read_text()):
			if int(m.group(1) or m.group(2)) > 360:
				offenders.append(f'{p.name}: {m.group(0).strip()}')
	assert not offenders, offenders


def test_app_imports_without_pkg_resources():
	"""setuptools is removing pkg_resources; Flask-Admin 1.6.1, APScheduler 3.10 and
	dropbox 11 all imported it, so a fresh environment would fail to start the app."""
	import subprocess
	import sys
	code = (
		"import sys; sys.modules['pkg_resources'] = None\n"  # makes `import pkg_resources` raise
		"from SIMS_Portal import create_app\n"
		"import SIMS_Portal.portfolios.utils, SIMS_Portal.scheduler, SIMS_Portal.admin\n"
		"import flask_apscheduler, apscheduler.triggers.cron, dropbox, flask_admin.contrib.sqla\n"
		"print('ok')\n"
	)
	env = {**__import__('os').environ, 'SIMS_SKIP_DOTENV': '1'}
	result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, env=env,
	                        cwd=str(TEMPLATES_DIR.parent.parent))
	assert result.returncode == 0 and 'ok' in result.stdout, result.stderr[-2000:]


# Inline style="" attributes still in templates. This only goes down: put new styling
# in static/css/main.css (or a Bootstrap utility class) and lower the number when
# you remove one (#159).
MAX_INLINE_STYLES = 64


def test_inline_styles_do_not_increase():
	import re
	count = sum(len(re.findall(r'''\sstyle\s*=\s*["']''', p.read_text()))
	            for p in TEMPLATES_DIR.rglob('*.html') if p.parent.name != 'admin')
	assert count <= MAX_INLINE_STYLES, (
		f'{count} inline style attributes (limit {MAX_INLINE_STYLES}); move the new ones into static/css/main.css')
	if count < MAX_INLINE_STYLES:
		pytest.fail(f'Only {count} inline styles now: lower MAX_INLINE_STYLES in this file to {count}')


def test_static_assets_are_served_from_the_assets_folder(client):
	# SIMS_Portal/static/assets is a symlink to flask_app/assets/; it's the only way the
	# images get into the production image. A 2025 commit deleted it, which local dev
	# hid (docker-compose mounted the folder) but would have broken every image in prod.
	link = TEMPLATES_DIR.parent / 'static' / 'assets'
	assert link.is_symlink() and link.resolve() == (TEMPLATES_DIR.parent.parent / 'assets').resolve()
	response = client.get('/static/assets/img/pump-brakes.gif')
	assert response.status_code == 200 and response.mimetype == 'image/gif'
	response.close()
