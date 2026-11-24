"""
Background jobs (APScheduler), run in production only.

Production runs gunicorn with several worker processes, and each one builds its
own app. Without coordination every worker started its own scheduler, so every
job (surge alert refresh, badge assignment, inactive-member Slack alerts) ran once
per worker. A non-blocking lock on SCHEDULER_LOCK_FILE makes sure exactly one
process per host runs the scheduler. When that worker exits (e.g. gunicorn's
--max-requests recycling), the lock is released and its replacement takes over.
"""
from flask_apscheduler import APScheduler

try:
	import fcntl
except ImportError:  # Windows: no flock; fall back to one scheduler per process
	fcntl = None

# open lock-file handles are kept here so the lock lives as long as the process
_held_locks = []


def _acquire_scheduler_lock(path):
	if fcntl is None:
		return True
	handle = open(path, 'w')
	try:
		fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
	except OSError:
		handle.close()
		return False
	_held_locks.append(handle)
	return True


def run_surge_alert_refresh():
	from SIMS_Portal.alerts.utils import refresh_open_alert_statuses, refresh_surge_alerts_latest, repair_missing_alert_statuses
	from SIMS_Portal.main.utils import heartbeats
	from flask import current_app

	latest_ok = refresh_surge_alerts_latest()
	repair_missing_alert_statuses()
	recheck_ok = refresh_open_alert_statuses()
	# only report healthy if GO was actually read, so a long GO outage shows up in
	# Better Stack as a missed heartbeat rather than a green check
	if latest_ok and recheck_ok:
		heartbeats('run_surge_alert_refresh', current_app.config['HEARTBEAT_URL_SURGE_ALERTS'])
	else:
		current_app.logger.warning('Surge alert refresh could not reach GO; skipping its heartbeat.')


def run_auto_badge_assigners():
	from flask import current_app
	from SIMS_Portal.main import utils

	for name in (
		'maiden_voyage', 'big_wig', 'self_promoter', 'polyglot', 'autobiographer', 'edward_tufte',
		'world_traveler', 'old_salt', 'eratosthenes', 'super_scholar', 'teaching_moment',
	):
		getattr(utils, f'auto_badge_assigner_{name}')()
	utils.heartbeats('run_auto_badge_assigners', current_app.config['HEARTBEAT_URL_BADGES'])


def run_alert_inactive_members():
	from SIMS_Portal.users.utils import alert_inactive_members
	alert_inactive_members()


def run_process_inactive_members():
	from SIMS_Portal.users.utils import process_inactive_members
	process_inactive_members()


# (job id, function, trigger arguments). Times use SCHEDULER_TIMEZONE unless set.
JOBS = [
	('run_surge_alert_refresh', run_surge_alert_refresh, {'trigger': 'cron', 'hour': '1,4,7,10,13,16'}),
	('run_auto_badge_assigners', run_auto_badge_assigners, {'trigger': 'cron', 'hour': '17'}),
	('run_set_user_inactive', run_alert_inactive_members, {'trigger': 'cron', 'day_of_week': 'thu', 'hour': 9, 'timezone': 'America/New_York'}),
	('run_process_inactive_members', run_process_inactive_members, {'trigger': 'cron', 'day_of_week': 'tue', 'hour': 9, 'timezone': 'America/New_York'}),
]


def init_scheduler(app):
	"""Start the scheduler if enabled and this process wins the lock. Returns it, or None."""
	if not app.config.get('SCHEDULER_ENABLED', not app.config['DEBUG']):
		return None
	if not _acquire_scheduler_lock(app.config['SCHEDULER_LOCK_FILE']):
		app.logger.info('Scheduler is running in another worker process; not starting one here.')
		return None

	scheduler = APScheduler()
	scheduler.init_app(app)

	def in_app_context(func):
		def job():
			with app.app_context():
				func()
		job.__name__ = func.__name__
		return job

	for job_id, func, trigger_args in JOBS:
		scheduler.add_job(id=job_id, func=in_app_context(func), **trigger_args)

	scheduler.start()
	app.logger.info('Scheduler started in this worker process.')
	return scheduler
