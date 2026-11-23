"""
Surge alert jobs (SIMS_Portal/alerts/utils.py), with the GO API faked.

- refresh_open_alert_statuses() repairs alerts stored with no status (saved while
  the app read GO's deprecated status_display field) and skips closed ones
- refresh_surge_alerts_latest() updates existing alerts by alert_id, adds new ones,
  keeps going past a bad record, and logs a summary that names the failures
"""
from datetime import datetime

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


# --- details GO fills in after an alert is first published ------------------------

LATEST_URL = 'https://goadmin.ifrc.org/api/v2/surge_alert/'


@pytest.fixture
def slack_notices(monkeypatch):
	sent = []
	monkeypatch.setattr(alert_utils, 'send_im_alert_to_slack', lambda alert: sent.append(alert.alert_id))
	return sent


def _early_copy(alert_id, molnix_id, status=None):
	"""An alert as first saved: before GO added its end date and sector tags."""
	return Alert(alert_id=alert_id, molnix_id=molnix_id, alert_status=status, im_filter=False, end_time=None, sectors='')


def test_latest_refresh_fills_in_details_added_after_the_alert_was_first_saved(fake_go, slack_notices):
	# production, 2026-11-23: alert 24209 (an IM analyst role) was saved an hour after
	# it opened, before GO had its end date or IM sector tag; only its status was ever
	# refreshed, so it stayed off the dashboard and never counted as an IM alert
	responses, _ = fake_go
	db.session.add(_early_copy(800, 80))
	db.session.commit()
	responses[LATEST_URL] = FakeResponse({'results': [_api_alert(800, 80, 'Open', sector='Information Management')]})

	alert_utils.refresh_surge_alerts_latest()

	alert = db.session.query(Alert).filter_by(alert_id=800).one()
	assert alert.alert_status == 'Open'
	assert alert.im_filter is True and alert.sectors == 'Information Management'
	assert alert.end_time == datetime(2026, 12, 10) and alert.start == datetime(2026, 11, 10)
	assert alert.country_name == 'Panama' and alert.event == 'Panama Earthquake'
	# it missed the IM notice when it was first saved, so it gets one now
	assert slack_notices == [800]


def test_unchanged_alerts_are_not_rewritten_or_renotified(fake_go, slack_notices):
	responses, _ = fake_go
	db.session.add(_early_copy(801, 81))
	db.session.commit()
	# real GO sends molnix_status as a number; the column stores text
	responses[LATEST_URL] = FakeResponse({'results': [_api_alert(801, 81, 'Open', sector='Information Management', molnix_status=0)]})

	alert_utils.refresh_surge_alerts_latest()
	alert_utils.refresh_surge_alerts_latest()

	assert slack_notices == [801]  # once, not on every run
	summary = db.session.query(Log).filter(Log.message.like('%Surge Alert cron job has finished%')).order_by(Log.id.desc()).first()
	# GO's ISO dates and numeric molnix_status compare equal to the stored values
	assert 'updated 0 records' in summary.message


def test_no_im_notice_for_alerts_that_are_no_longer_open(fake_go, slack_notices):
	responses, _ = fake_go
	db.session.add(_early_copy(802, 82, status='Open'))
	db.session.commit()
	responses[LATEST_URL] = FakeResponse({'results': [_api_alert(802, 82, 'Closed', sector='Information Management')]})

	alert_utils.refresh_surge_alerts_latest()

	alert = db.session.query(Alert).filter_by(alert_id=802).one()
	assert alert.im_filter is True and alert.alert_status == 'Closed'
	assert slack_notices == []


def test_blank_fields_from_go_never_erase_stored_details(fake_go, slack_notices):
	responses, _ = fake_go
	db.session.add(Alert(alert_id=803, molnix_id=83, alert_status='Open', end_time=datetime(2026, 12, 10),
	                     event='Panama Earthquake', im_filter=True))
	db.session.commit()
	incomplete = _api_alert(803, 83, 'Open', sector='Information Management', end=None)
	incomplete['event'] = None
	responses[LATEST_URL] = FakeResponse({'results': [incomplete]})

	alert_utils.refresh_surge_alerts_latest()

	alert = db.session.query(Alert).filter_by(alert_id=803).one()
	assert alert.end_time == datetime(2026, 12, 10) and alert.event == 'Panama Earthquake'


def test_full_refresh_fills_in_details_without_slack_notices(fake_go, slack_notices):
	responses, _ = fake_go
	db.session.add(_early_copy(804, 84))
	db.session.commit()
	responses[LATEST_URL] = FakeResponse({'results': [_api_alert(804, 84, 'Open', sector='Information Management')], 'next': None})

	alert_utils.refresh_surge_alerts()

	alert = db.session.query(Alert).filter_by(alert_id=804).one()
	assert alert.alert_status == 'Open' and alert.im_filter is True and alert.end_time == datetime(2026, 12, 10)
	assert slack_notices == []


def test_repaired_alerts_appear_on_the_dashboard(fake_go, slack_notices, admin_client):
	# end to end for the 2026-11-23 report: open in GO, but missing from the dashboard
	responses, _ = fake_go
	db.session.add(_early_copy(805, 85))
	db.session.commit()
	responses[LATEST_URL] = FakeResponse({'results': [_api_alert(805, 85, 'Open', sector='Information Management')]})
	db.session.query(Alert).filter_by(alert_id=805).update({'alert_record_created_at': datetime.now()})
	db.session.commit()
	assert 'Panama Earthquake' not in admin_client.get('/dashboard').get_data(as_text=True)

	alert_utils.refresh_surge_alerts_latest()

	assert 'Panama Earthquake' in admin_client.get('/dashboard').get_data(as_text=True)


# --- the IM Slack notice ----------------------------------------------------------

@pytest.fixture
def posted(monkeypatch):
	"""Capture IM notices and error messages instead of posting them to Slack."""
	sent = {'notices': [], 'errors': []}
	monkeypatch.setattr(alert_utils, 'new_surge_alert', sent['notices'].append)
	monkeypatch.setattr(alert_utils, 'send_error_message', sent['errors'].append)
	monkeypatch.setattr(alert_utils, 'get_slack_username', lambda slack_id: 'U123')
	return sent


def _im_alert(**overrides):
	fields = dict(
		alert_id=24209, molnix_id=99, role_profile='Humanitarian Information Analysis Officer', scope='Global',
		rotation='1st', language_required='English', modality='In Person', country_name='Afghanistan',
		start=datetime(2026, 11, 27), end_time=datetime(2027, 1, 27), region_id=3,
		event=None, disaster_go_id=None, ifrc_severity_level_display=None,
	)
	fields.update(overrides)
	return Alert(**fields)


def test_im_notice_is_sent_for_alerts_not_yet_linked_to_an_emergency(posted):
	# production: 7 IM notices since March 2025 were never sent, including 24209 on
	# 2026-11-23, because GO hadn't linked the alert to an emergency yet and the
	# severity lookup raised KeyError(None); the failure was only logged to the DB
	alert_utils.send_im_alert_to_slack(_im_alert())

	assert posted['errors'] == []
	(message,) = posted['notices']
	assert 'released for Afghanistan (not yet linked to an emergency in GO)' in message
	assert 'Humanitarian Information Analysis Officer' in message and 'rrms.ifrc.org/positions/show/99' in message
	assert 'None' not in message


def test_im_notice_for_a_linked_emergency_names_it_with_its_severity(posted):
	alert_utils.send_im_alert_to_slack(_im_alert(event='Panama Earthquake - 2026', disaster_go_id=8110, ifrc_severity_level_display='Yellow'))

	(message,) = posted['notices']
	assert 'released for the <https://go.ifrc.org/emergencies/8110|Panama Earthquake - 2026>, which is a :large_yellow_circle: yellow emergency' in message
	assert 'Standard role profile for this position' in message


def test_im_notice_leaves_out_missing_details_instead_of_printing_none(posted):
	alert_utils.send_im_alert_to_slack(_im_alert(role_profile='Some Other IM Role', event='Panama Earthquake - 2026',
	                                             disaster_go_id=8110, ifrc_severity_level_display=None))

	(message,) = posted['notices']
	# no severity: the emergency is named without a "which is ... emergency" clause
	assert '|Panama Earthquake - 2026>. ' in message and 'which is' not in message
	assert '• None' not in message and 'Standard role profile' not in message


def test_im_notice_without_a_scope_uses_the_global_wording(posted):
	alert_utils.send_im_alert_to_slack(_im_alert(scope=None))

	(message,) = posted['notices']
	assert 'New Global Information Management Surge Alert Released!' in message


def test_im_notice_failures_are_reported_not_just_logged(posted, monkeypatch):
	def broken(message):
		raise RuntimeError('slack is down')
	monkeypatch.setattr(alert_utils, 'new_surge_alert', broken)

	alert_utils.send_im_alert_to_slack(_im_alert())

	(error,) = posted['errors']
	assert 'alert_id 24209' in error and 'slack is down' in error


# --- the per-alert re-check fills in details too ----------------------------------

def _go_detail(alert_id, molnix_id, status='Open', sector='Information Management', event=None, **extra):
	record = _api_alert(alert_id, molnix_id, status, sector=sector, **extra)
	record['event'] = event
	record['molnix_tags'].append({'name': 'ASIAP', 'description': 'Asia Pacific Region', 'groups': ['REGION'], 'tag_type': 'regular'})
	return record


def test_recheck_fills_in_an_emergency_linked_after_the_alert_left_the_latest_50(fake_go, slack_notices):
	# an open alert GO links to an emergency weeks later, after it has scrolled out of
	# the latest refresh's ~50: only the per-alert re-check still looks at it
	responses, _ = fake_go
	db.session.add(Alert(alert_id=900, molnix_id=90, alert_status='Open', im_filter=True, event=None,
	                     ifrc_severity_level_display=None, end_time=datetime(2026, 12, 10)))
	db.session.commit()
	responses[_detail_url(900)] = FakeResponse(_go_detail(900, 90, event={
		'id': 8200, 'name': 'Afghanistan Drought - 2026', 'ifrc_severity_level_display': 'Orange',
		'dtype': {'id': 20, 'name': 'Drought'}}))

	alert_utils.refresh_open_alert_statuses()

	alert = db.session.query(Alert).filter_by(alert_id=900).one()
	assert (alert.event, alert.disaster_go_id, alert.ifrc_severity_level_display) == ('Afghanistan Drought - 2026', 8200, 'Orange')
	assert alert.disaster_type_name == 'Drought' and alert.region_id == 3
	assert slack_notices == []  # it was already IM, so it was already announced


def test_recheck_announces_an_open_alert_that_only_now_became_im(fake_go, slack_notices):
	responses, _ = fake_go
	db.session.add(_early_copy(901, 91, status='Open'))
	db.session.commit()
	responses[_detail_url(901)] = FakeResponse(_go_detail(901, 91))

	alert_utils.refresh_open_alert_statuses()
	alert_utils.refresh_open_alert_statuses()

	assert db.session.query(Alert).filter_by(alert_id=901).one().im_filter is True
	assert slack_notices == [901]  # once


def test_recheck_marks_deleted_alerts_removed_without_touching_their_details(fake_go, slack_notices):
	_, _ = fake_go  # no response registered: GO answers 404
	db.session.add(Alert(alert_id=902, molnix_id=92, alert_status='Open', im_filter=True,
	                     sectors='Information Management', event='Panama Earthquake'))
	db.session.commit()

	alert_utils.refresh_open_alert_statuses()

	alert = db.session.query(Alert).filter_by(alert_id=902).one()
	assert alert.alert_status == 'Removed'
	assert (alert.im_filter, alert.sectors, alert.event) == (True, 'Information Management', 'Panama Earthquake')


def test_full_refresh_records_regions_and_skips_malformed_records(fake_go, slack_notices):
	responses, _ = fake_go
	broken = _api_alert(904, 94, 'Open')
	broken['molnix_tags'] = [None]
	responses[LATEST_URL] = FakeResponse({'results': [_go_detail(903, 93), broken, _api_alert(905, 95, 'Closed')], 'next': None})

	alert_utils.refresh_surge_alerts()

	alerts = {a.alert_id: a for a in db.session.query(Alert).filter(Alert.alert_id.in_([903, 904, 905]))}
	assert alerts[903].region_id == 3  # the full refresh used to drop the region
	assert 904 not in alerts and alerts[905].alert_status == 'Closed'  # one bad record no longer aborts the run


def test_parse_go_alert_handles_alerts_with_no_emergency_or_tags():
	parsed = alert_utils.parse_go_alert({'id': 1, 'molnix_id': 2, 'molnix_status_display': 'Open', 'event': None,
	                                     'country': {'iso3': 'AFG', 'name': 'Afghanistan'}, 'molnix_tags': []})
	assert parsed['alert_status'] == 'Open' and parsed['country_name'] == 'Afghanistan'
	assert parsed['event'] is None and parsed['ifrc_severity_level_display'] is None
	assert parsed['sectors'] == '' and parsed['im_filter'] is False and parsed['region_id'] is None
