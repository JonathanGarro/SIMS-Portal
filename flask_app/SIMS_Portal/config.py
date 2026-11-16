import os
import tempfile

from flask.cli import get_debug_flag

class Config:
	# Driven by the FLASK_DEBUG env var (Flask's own convention), defaulting to False.
	# This used to be hardcoded True, which meant it had to be hand-edited to False
	# before every production deploy - forget that step and the app still runs fine,
	# but the entire APScheduler block below (surge alerts, badge assignment,
	# inactive-member handling) silently never starts, since it's gated on
	# app.config['DEBUG'] == False. Set FLASK_DEBUG=1 in your local .env for dev.
	DEBUG = get_debug_flag()
	SECRET_KEY = os.environ.get('SECRET_KEY')
	MAX_CONTENT_LENGTH = 75 * 1000 * 1000  # upload size limit
	# In debug mode (local dev, e.g. via docker-compose's FLASK_DEBUG=1), prefer
	# DEV_SQLALCHEMY_DATABASE_URI over SQLALCHEMY_DATABASE_URI, so a dev and prod
	# credential can both sit in the same .env without one having to be commented
	# out for the other to take effect - a local run can no longer accidentally
	# point at the production database just because that line was left uncommented.
	# Production itself is unaffected: it doesn't set FLASK_DEBUG, and AWS injects
	# SQLALCHEMY_DATABASE_URI directly rather than through this file.
	if DEBUG:
		SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_SQLALCHEMY_DATABASE_URI') or os.environ.get('SQLALCHEMY_DATABASE_URI')
	else:
		SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
	SQLALCHEMY_ENGINE_OPTIONS = {
		'pool_pre_ping': True,
		'pool_recycle': 300,
		# TCP keepalives so the OS notices a silently-dropped connection (e.g. a NAT
		# gateway or firewall reaping an idle connection) instead of the app finding
		# out only when a query fails with "SSL SYSCALL error: EOF detected".
		'connect_args': {
			'keepalives': 1,
			'keepalives_idle': 30,
			'keepalives_interval': 10,
			'keepalives_count': 5,
		},
	}
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	# Must stay False: Flask-APScheduler's REST API (/scheduler/...) has no
	# authentication, and POST /scheduler/jobs can schedule any importable function
	# with arbitrary arguments. Nothing in the app uses it.
	SCHEDULER_API_ENABLED = False
	SCHEDULER_TIMEZONE = "America/New_York"
	# only one process per host runs the scheduler; see SIMS_Portal/scheduler.py
	SCHEDULER_LOCK_FILE = os.environ.get('SCHEDULER_LOCK_FILE', os.path.join(tempfile.gettempdir(), 'sims-portal-scheduler.lock'))
	# Better Stack uptime heartbeats pinged after scheduled jobs; skipped when unset
	HEARTBEAT_URL_SURGE_ALERTS = os.environ.get('HEARTBEAT_URL_SURGE_ALERTS')
	HEARTBEAT_URL_BADGES = os.environ.get('HEARTBEAT_URL_BADGES')
	SIMS_PORTAL_SLACK_BOT = os.environ.get('SIMS_PORTAL_SLACK_BOT')
	# base URL for links in Slack messages
	ROOT_URL = os.environ.get('ROOT_URL', 'https://rcrcsims.org')
	DROPBOX_BOT = os.environ.get('DROPBOX_BOT')
	DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
	DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
	DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')
	UPLOAD_EXTENSIONS = ['.jpg', '.png', '.gif', '.jpeg', '.shp', '.py', '.doc', '.docx', '.xls', '.csv', '.dif', '.pdf', '.ppt', '.pptx', '.potx', '.zip', '.txt', '.ai', '.indd']
	PORTFOLIO_TYPES = ['Map', 'Infographic', 'Dashboard', 'Mobile Data Collection', 'Assessment', 'Internal Analysis', 'External Report', 'Code Snippet', 'Other']
	POSITION_STACK_TOKEN = os.environ.get('POSITION_STACK_TOKEN')
	GOOGLE_MAPS_TOKEN = os.environ.get('GOOGLE_MAPS_TOKEN')
	UPLOAD_BUCKET = 'sims-portal-uploads'
	CACHE_TYPE = 'simple'
	RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
	RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')
	GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')