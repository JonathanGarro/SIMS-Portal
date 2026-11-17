"""
Surge alert jobs (SIMS_Portal/alerts/utils.py), with the GO API faked.

- refresh_open_alert_statuses() repairs alerts stored with no status (saved while
  the app read GO's deprecated status_display field) and skips closed ones
- refresh_surge_alerts_latest() updates existing alerts by alert_id, adds new ones,
  keeps going past a bad record, and logs a summary that names the failures
"""
import pytest

from SIMS_Portal import db
from SIMS_Portal.alerts import utils as alert_utils
from SIMS_Portal.models import Alert, Log


class FakeResponse:
	def __init__(self, payload, status=200):
		self.payload, self.status_code, self.text = payload, status, str(payload)

	def json(self):
		return self.payload

	def raise_for_status(self):
		if self.status_code >= 400:
			raise alert_utils.RequestException(f'HTTP {self.status_code}')


@pytest.fixture
def fake_go(monkeypatch):
	"""Route requests.get to canned GO API responses; record what was requested."""
	responses, requested = {}, []

	def fake_get(url, timeout=None):
		requested.append(url)
		return responses.get(url, FakeResponse({}, status=404))

	monkeypatch.setattr(alert_utils.requests, 'get', fake_get)
	monkeypatch.setattr(alert_utils.time, 'sleep', lambda seconds: None)
	monkeypatch.setattr(alert_utils, 'send_im_alert_to_slack', lambda alert: None)
	monkeypatch.setattr(alert_utils, 'send_error_message', lambda message: None)
	return responses, requested


def _detail_url(alert_id):
	return f'https://goadmin.ifrc.org/api/v2/surge_alert/{alert_id}/'


def test_open_status_refresh_repairs_alerts_with_no_status(fake_go):
	responses, requested = fake_go
	db.session.add_all([
		Alert(alert_id=9001, molnix_id=1, alert_status=None),
		Alert(alert_id=9002, molnix_id=2, alert_status='Open'),
		Alert(alert_id=9003, molnix_id=3, alert_status='Closed'),
		Alert(alert_id=9004, molnix_id=4, alert_status='Stood Down'),
		Alert(alert_id=9005, molnix_id=5, alert_status=None),  # deleted in GO: 404
	])
	db.session.commit()
	responses[_detail_url(9001)] = FakeResponse({'molnix_status_display': 'Closed', 'molnix_status': 'archived'})
	responses[_detail_url(9002)] = FakeResponse({'molnix_status_display': 'Stood Down', 'molnix_status': '2'})

	alert_utils.refresh_open_alert_statuses()

	ids = [9001, 9002, 9003, 9004, 9005]
	status = {a.alert_id: a.alert_status for a in db.session.query(Alert).filter(Alert.alert_id.in_(ids))}
	assert status == {9001: 'Closed', 9002: 'Stood Down', 9003: 'Closed', 9004: 'Stood Down', 9005: 'Removed'}
	# only open and status-less alerts are re-checked; closed and stood-down ones are final
	assert sorted(requested) == sorted([_detail_url(9001), _detail_url(9002), _detail_url(9005)])


def _api_alert(alert_id, molnix_id, status, sector='Health', **extra):
	return {
		'id': alert_id, 'molnix_id': molnix_id, 'created_at': '2026-11-01T12:00:00Z',
		'molnix_status': 'active', 'molnix_status_display': status,
		'opens': '2026-11-01T12:00:00Z', 'start': '2026-11-10T00:00:00Z', 'end': '2026-12-10T00:00:00Z',
		'molnix_tags': [{'name': sector, 'description': sector, 'groups': ['SECTOR'], 'tag_type': 'regular'}],
		'country': {'iso3': 'PAN', 'name': 'Panama'},
		'event': {'id': 1, 'name': 'Panama Earthquake', 'dtype': {'id': 2, 'name': 'Earthquake'}},
		**extra,
	}


def test_latest_refresh_updates_adds_and_summarizes_failures(fake_go):
	responses, _ = fake_go
	db.session.add(Alert(alert_id=500, molnix_id=50, alert_status='Open'))
	db.session.commit()
	broken = _api_alert(502, 52, 'Open')
	broken['molnix_tags'] = [None]  # a malformed record must not stop the run
	responses['https://goadmin.ifrc.org/api/v2/surge_alert/'] = FakeResponse({'results': [
		_api_alert(500, 50, 'Closed'),
		_api_alert(501, 51, 'Open', sector='Information Management'),
		broken,
	]})

	alert_utils.refresh_surge_alerts_latest()

	alerts = {a.alert_id: a for a in db.session.query(Alert).filter(Alert.alert_id.in_([500, 501, 502]))}
	assert alerts[500].alert_status == 'Closed'
	assert alerts[501].alert_status == 'Open' and alerts[501].im_filter is True
	assert 502 not in alerts
	summary = db.session.query(Log).filter(Log.message.like('%Surge Alert cron job has finished%')).order_by(Log.id.desc()).first()
	assert summary is not None
	assert 'Added 1 new records, updated 1 records, 1 failed (molnix_ids: 52)' in summary.message


def test_failure_summary_is_truncated():
	assert alert_utils._summarize_failures([]) == 'none'
	assert alert_utils._summarize_failures(list(range(12)), limit=3) == '0, 1, 2 and 9 more'


def test_missing_statuses_are_repaired_through_the_list_endpoint(fake_go):
	responses, requested = fake_go
	db.session.add_all([Alert(alert_id=700, molnix_id=70, alert_status=None), Alert(alert_id=701, molnix_id=71, alert_status=None)])
	db.session.commit()
	page_2 = 'https://goadmin.ifrc.org/api/v2/surge_alert/?limit=50&offset=50'
	responses['https://goadmin.ifrc.org/api/v2/surge_alert/'] = FakeResponse({'results': [_api_alert(700, 70, 'Closed')], 'next': page_2})
	responses[page_2] = FakeResponse({'results': [_api_alert(701, 71, 'Stood Down')], 'next': None})

	assert alert_utils.repair_missing_alert_statuses() == 2

	status = {a.alert_id: a.alert_status for a in db.session.query(Alert).filter(Alert.alert_id.in_([700, 701]))}
	assert status == {700: 'Closed', 701: 'Stood Down'}
	assert requested == ['https://goadmin.ifrc.org/api/v2/surge_alert/', page_2]  # two list pages, no per-alert calls


def test_missing_status_repair_does_nothing_when_every_alert_has_one(fake_go):
	_, requested = fake_go
	db.session.query(Alert).filter(Alert.alert_status.is_(None)).delete()
	db.session.commit()

	assert alert_utils.repair_missing_alert_statuses() == 0
	assert requested == []
