"""The site navigation: one menu on small screens, the two bars from lg up."""
import collections
import re

import pytest

SECTION_LINKS = ['About', 'Emergencies', 'Members', 'Portfolio', 'Documentation']


def _offcanvas(html):
	start = html.index('id="siteNav"')
	return html[start:html.index('</nav>', start)]


def test_single_hamburger(member_client):
	html = member_client.get('/dashboard').get_data(as_text=True)
	assert html.count('class="navbar-toggler"') == 1
	assert 'data-bs-toggle="offcanvas" data-bs-target="#siteNav"' in html


def test_second_bar_is_desktop_only(member_client):
	html = member_client.get('/dashboard').get_data(as_text=True)
	bar = re.search(r'<nav id="navbar_top_login" class="([^"]*)"', html).group(1).split()
	assert {'d-none', 'd-lg-flex'} <= set(bar)


def test_mobile_menu_has_every_link(member_client):
	menu = _offcanvas(member_client.get('/dashboard').get_data(as_text=True))
	for label in SECTION_LINKS + ['National Societies', 'Dashboard', 'Profile', 'Logout']:
		assert label in menu, label
	assert 'Admin' not in re.sub(r'<[^>]+>', ' ', menu).split()  # members don't get the admin link


def test_admins_get_the_admin_link(admin_client):
	assert '/admin/manage_profiles' in _offcanvas(admin_client.get('/dashboard').get_data(as_text=True))


@pytest.mark.parametrize('url,label', [('/emergencies/all', 'Emergencies'), ('/members/all', 'Members'), ('/documentation', 'Documentation')])
def test_current_section_is_marked(member_client, url, label):
	html = member_client.get(url).get_data(as_text=True)
	assert re.search(r'class="nav-link text-light nav-active" href="[^"]*" aria-current="page">%s<' % label, _offcanvas(html))
	assert f'aria-current="page">{label}</button>' in html  # desktop bar


def test_logged_out_menu(client):
	html = client.get('/about').get_data(as_text=True)
	menu = _offcanvas(html)
	for label in ['About', 'Portfolio', 'Members', 'Login']:
		assert f'>{label}</a>' in menu
	assert 'navbar_top_login' not in html  # no second bar
	assert 'nav-active" href="/about" aria-current="page"' in menu


@pytest.mark.parametrize('persona,url', [('member', '/dashboard'), ('admin', '/admin/view_logs'), ('anonymous', '/')])
def test_no_duplicate_element_ids(request, persona, url):
	client = request.getfixturevalue('client' if persona == 'anonymous' else f'{persona}_client')
	ids = re.findall(r'\sid="([^"{]+)"', client.get(url).get_data(as_text=True))
	dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
	assert not dupes, dupes
