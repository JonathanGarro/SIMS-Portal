"""Reporting availability for an emergency."""
import pytest

from SIMS_Portal import db
from SIMS_Portal.models import Availability, User
from tests.seed import MEMBER_ID

RESULT_URLS = ['/availability/result/1', '/availability/result/next_week/1']


@pytest.fixture
def sent_dms(monkeypatch):
	sent = []
	monkeypatch.setattr('SIMS_Portal.availability.routes.send_slack_dm', lambda message, user: sent.append((user, message)))
	return sent


def _set_slack_id(value):
	db.session.query(User).filter(User.id == MEMBER_ID).update({'slack_id': value})
	db.session.commit()


@pytest.mark.parametrize('url', RESULT_URLS)
def test_report_saves_and_sends_confirmation_dm(member_client, sent_dms, url):
	_set_slack_id('U123')
	response = member_client.post(url, data={'available': ['Monday, January 05']})
	assert response.status_code == 302
	assert sent_dms == [('U123', 'Hi Max, you have successfully updated your availability!')]
	saved = db.session.query(Availability).filter(Availability.user_id == MEMBER_ID).order_by(Availability.id.desc()).first()
	assert saved.dates == "['Monday, January 05']"


@pytest.mark.parametrize('url', RESULT_URLS)
def test_no_dm_without_slack_id(member_client, sent_dms, url):
	_set_slack_id(None)
	assert member_client.post(url, data={'available': ['Monday, January 05']}).status_code == 302
	assert sent_dms == []


def test_slack_failure_does_not_break_the_save(member_client, monkeypatch):
	_set_slack_id('U123')
	def boom(message, user):
		raise RuntimeError('slack down')
	monkeypatch.setattr('SIMS_Portal.availability.routes.send_slack_dm', boom)
	assert member_client.post(RESULT_URLS[0], data={'available': ['Monday, January 05']}).status_code == 302
