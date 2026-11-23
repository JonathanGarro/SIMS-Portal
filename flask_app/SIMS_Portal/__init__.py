import os

from dotenv import load_dotenv

# Load .env before anything below reads os.environ at import time (Config does, in
# its class body). `flask run` pre-loads .env itself, but gunicorn (Procfile,
# Dockerfile) does not, so without this every config value would be None there.
# The test suite sets SIMS_SKIP_DOTENV=1 so a developer's real .env (prod/dev DB
# URLs, Slack/Dropbox/GitHub tokens) can never leak into a test run.
if os.environ.get('SIMS_SKIP_DOTENV') != '1':
	load_dotenv()

import logging  # noqa: E402
from logging.handlers import RotatingFileHandler  # noqa: E402

import markdown as md  # noqa: E402
from flask import Flask  # noqa: E402
from flask_babel import Babel  # noqa: E402
from flask_bcrypt import Bcrypt  # noqa: E402
from flask_caching import Cache  # noqa: E402
from flask_limiter import Limiter  # noqa: E402
from flask_limiter.util import get_remote_address  # noqa: E402
from flask_login import LoginManager  # noqa: E402
from flask_migrate import Migrate  # noqa: E402
from flask_sqlalchemy import SQLAlchemy  # noqa: E402
from flask_wtf.csrf import CSRFProtect  # noqa: E402
from markupsafe import Markup  # noqa: E402
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402

from SIMS_Portal.config import Config  # noqa: E402

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'danger'
cache = Cache()
csrf = CSRFProtect()
babel = Babel()
# Per-route limits only (login, registration, password reset/change); see users/routes.py.
# Keyed on the client IP, so behind a reverse proxy set PROXY_FIX_HOPS (see config.py).
limiter = Limiter(key_func=get_remote_address)

from SIMS_Portal import models  # noqa: E402,F401  (registers the models with SQLAlchemy)


def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(config_class)

	# Trust X-Forwarded-For/-Proto from this many proxies in front of the app, so
	# request.remote_addr (and the rate limiter's per-IP key) is the real client
	# rather than the proxy. Only set it when such a proxy exists: with none, a
	# client could forge the header and dodge per-IP limits.
	if app.config['PROXY_FIX_HOPS']:
		hops = app.config['PROXY_FIX_HOPS']
		app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops)

	db.init_app(app)
	migrate.init_app(app, db)
	bcrypt.init_app(app)
	login_manager.init_app(app)
	cache.init_app(app)
	csrf.init_app(app)
	babel.init_app(app)
	limiter.init_app(app)

	_init_templating(app)
	_init_logging(app)

	from SIMS_Portal.admin import init_admin
	from SIMS_Portal.cli import init_cli
	from SIMS_Portal.password_policy import init_password_policy
	from SIMS_Portal.scheduler import init_scheduler
	from SIMS_Portal.security import init_security_headers

	init_security_headers(app)
	init_password_policy(app)
	_register_blueprints(app)
	init_admin(app, db)
	init_cli(app)
	init_scheduler(app)

	@app.route('/health', methods=['GET'])
	def health_check():
		return 'OK', 200

	return app


def _init_templating(app):
	from SIMS_Portal.main.utils import get_ns_list

	# national society list for the nav dropdown in layout.html
	@app.context_processor
	def inject_ns_list():
		return {'ns_list': get_ns_list()}

	# replaces Flask-Markdown, which is incompatible with Flask 3
	@app.template_filter('markdown')
	def markdown_filter(text):
		return Markup(md.markdown(text)) if text else ''


def _init_logging(app):
	if app.debug or app.testing:
		return
	os.makedirs('logs', exist_ok=True)
	file_handler = RotatingFileHandler('logs/sims-portal.log', maxBytes=1000000, backupCount=10)
	file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
	file_handler.setLevel(logging.INFO)
	app.logger.addHandler(file_handler)
	app.logger.setLevel(logging.INFO)
	app.logger.info('SIMS Portal Started Up')


def _register_blueprints(app):
	from SIMS_Portal.acronym.routes import acronym
	from SIMS_Portal.alerts.routes import alerts
	from SIMS_Portal.assignments.routes import assignments
	from SIMS_Portal.availability.routes import availability
	from SIMS_Portal.badges.routes import badges_bp
	from SIMS_Portal.checklists.routes import checklists
	from SIMS_Portal.emergencies.routes import emergencies
	from SIMS_Portal.errors.handlers import errors
	from SIMS_Portal.learnings.routes import learnings
	from SIMS_Portal.main.routes import main
	from SIMS_Portal.portal_admin.routes import portal_admin
	from SIMS_Portal.portfolios.routes import portfolios
	from SIMS_Portal.reviews.routes import reviews
	from SIMS_Portal.stories.routes import stories
	from SIMS_Portal.users.routes import users

	for blueprint in (main, portal_admin, badges_bp, checklists, assignments, emergencies, portfolios, users, stories, learnings, reviews, alerts, errors, availability, acronym):
		app.register_blueprint(blueprint)
