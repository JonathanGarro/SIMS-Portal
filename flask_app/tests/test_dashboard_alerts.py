"""Dashboard alerts: IM alerts counted and shown by default; every open alert available behind a switch."""
from datetime import datetime, timedelta

from SIMS_Portal import db
from SIMS_Portal.models import Alert


def test_dashboard_lists_every_open_alert_and_marks_im_ones(member_client):
	now = datetime.utcnow()
	common = dict(alert_record_created_at=now - timedelta(days=3), start=now + timedelta(days=5), end_time=now + timedelta(days=40))
	db.session.add_all([
		Alert(alert_id=8101, molnix_id=811, role_profile='IM Coordinator', alert_status='Open', im_filter=True, **common),
		Alert(alert_id=8102, molnix_id=812, role_profile='WASH Coordinator', alert_status='Open', im_filter=False, **common),
		Alert(alert_id=8103, molnix_id=813, role_profile='Closed Role', alert_status='Closed', im_filter=True, **common),
		Alert(alert_id=8104, molnix_id=814, role_profile='Old Role', alert_status='Open', im_filter=False,
			alert_record_created_at=now - timedelta(days=200), start=now, end_time=now + timedelta(days=5)),
	])
	db.session.commit()

	html = member_client.get('/dashboard').get_data(as_text=True)

	assert 'IM Coordinator' in html and 'WASH Coordinator' in html  # IM and non-IM open alerts both listed
	assert 'Closed Role' not in html and 'Old Role' not in html  # closed, or older than 90 days
	assert html.count('<tr data-im="1">') == 1 and html.count('<tr data-im="0">') == 1
	assert 'id="show-all-alerts"' in html
	assert 'Show all open alerts (2)' in html
	assert 'Open IM Alert<' in html  # the counter card counts IM alerts only (1)
