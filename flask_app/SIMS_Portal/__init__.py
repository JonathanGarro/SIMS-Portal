from dotenv import load_dotenv
from flask import Flask, render_template
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_apscheduler import APScheduler
from flask_babel import Babel
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
from logging.handlers import RotatingFileHandler
from SIMS_Portal.config import Config
import logging
import os
from flask_wtf.csrf import CSRFProtect

load_dotenv()
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'danger'
cache = Cache()

from SIMS_Portal import models
from SIMS_Portal.main.utils import get_ns_list

# run utility to generate active NS list
def build_ns_dropdown():
	ns_list = get_ns_list()
	return {'ns_list': ns_list}

# AdminView inherits from ModelView to only show tables in the admin page if user is logged in AND is listed as an admin
class AdminView(ModelView):
	column_exclude_list = ('birthday', 'password', 'molnix_id', 'job_title', 'bio', 'roles', 'image_file', 'twitter', 'slack_id', 'github', 'created_at', 'updated_at', 'linked_in', 'messaging_number_country_code', 'messaging_number')
	column_hide_backrefs = False
	def is_accessible(self):
		try:
			if current_user.is_admin == 1:
				return current_user.is_authenticated
		except:
			pass
	
	def inaccessible_callback(self, name, **kwargs):
		return render_template('errors/403.html'), 403
	
def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(Config)
	app.config['MAX_CONTENT_LENGTH'] = 75 * 1000 * 1000
	
	db.init_app(app)
	migrate.init_app(app, db)
	
	# send build_ns_dropdown() data to context_processor for use in layout.html
	app.context_processor(build_ns_dropdown)
	
	bcrypt.init_app(app)
	login_manager.init_app(app)
	admin = Admin(app, name='SIMS Admin Portal', template_mode='bootstrap4', endpoint='admin')
	babel = Babel(app)
	Markdown(app)
	cache.init_app(app)
	
	csrf = CSRFProtect(app)
	
	# these headers are part of a compliance requirement for AmRC hosting on AWS
	# see https://learn-sims.org/portal-documentation/adding-and-updating-security-headers/
	@app.after_request
	def add_caching_headers(response):
		response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
		response.headers["X-Content-Type-Options"] = "nosniff"
		response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
		response.headers["X-Frame-Options"] = "DENY"
		response.headers["Content-Security-Policy"] = (
			"default-src 'self'; "
			"img-src 'self' data: https://www.google.com https://www.gstatic.com; "
			"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://d3js.org https://unpkg.com https://www.google.com https://www.googletagmanager.com https://cdnjs.cloudflare.com https://ajax.googleapis.com https://maxcdn.bootstrapcdn.com https://cdn.datatables.net https://www.gstatic.com; "
			"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdn.datatables.net https://maxcdn.bootstrapcdn.com; "
			"font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdn.jsdelivr.net https://maxcdn.bootstrapcdn.com data:; "
			"connect-src 'self' https://www.google-analytics.com https://www.gstatic.com"
			"frame-src 'self' https://www.google.com https://www.gstatic.com https://recaptcha.net; "
			"child-src 'self' https://www.google.com https://www.gstatic.com https://recaptcha.net; "
			"object-src 'none';"
		)
		return response
	
	@app.route('/health', methods=['GET'])
	def health_check():
		return 'OK', 200
	
	# logging
	if not app.debug:
		if not os.path.exists('logs'):
			os.mkdir('logs')
		file_handler = RotatingFileHandler('logs/sims-portal.log', maxBytes=1000000, backupCount=10)
		file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
		file_handler.setLevel(logging.INFO)
		app.logger.addHandler(file_handler)
		app.logger.setLevel(logging.INFO)
		app.logger.info('SIMS Portal Started Up')
	
	# only turn scheduled tasks on in production
	if app.config['DEBUG'] == False:
	
		scheduler = APScheduler()
		scheduler.init_app(app)
		scheduler.start()
		
		@scheduler.task('cron', id='run_surge_alert_refresh', hour='1,4,7,10,13,16')
		def run_surge_alert_refresh():
			with scheduler.app.app_context():
				from SIMS_Portal.alerts.utils import refresh_surge_alerts_latest
				from SIMS_Portal.main.utils import heartbeats
				refresh_surge_alerts_latest()
				heartbeats('run_surge_alert_refresh', 'https://uptime.betterstack.com/api/v1/heartbeat/7DQYkNR4cM96cKsY69xQah4k')
				
		@scheduler.task('cron', id='run_auto_badge_assigners', hour='17')
		def run_auto_badge_assigners():
			with scheduler.app.app_context():
				from SIMS_Portal.main.utils import heartbeats, auto_badge_assigner_big_wig, auto_badge_assigner_maiden_voyage, auto_badge_assigner_self_promoter, auto_badge_assigner_polyglot, auto_badge_assigner_autobiographer, auto_badge_assigner_world_traveler, auto_badge_assigner_edward_tufte, auto_badge_assigner_old_salt, auto_badge_assigner_eratosthenes, auto_badge_assigner_super_scholar, auto_badge_assigner_teaching_moment
				
				auto_badge_assigner_maiden_voyage()
				auto_badge_assigner_big_wig()
				auto_badge_assigner_self_promoter()
				auto_badge_assigner_polyglot()
				auto_badge_assigner_autobiographer()
				auto_badge_assigner_edward_tufte()
				auto_badge_assigner_world_traveler()
				auto_badge_assigner_old_salt()
				auto_badge_assigner_eratosthenes()
				auto_badge_assigner_super_scholar()
				auto_badge_assigner_teaching_moment()
				heartbeats('run_auto_badge_assigners', 'https://uptime.betterstack.com/api/v1/heartbeat/QWvz7BCEoLnpKeCFMFbK3d2a')
		
		@scheduler.task('cron', id='run_set_user_inactive', day_of_week='thu', hour=9, timezone='America/New_York')
		def run_alert_inactive_members():
			with scheduler.app.app_context():
				from SIMS_Portal.users.utils import alert_inactive_members
				
				alert_inactive_members()
		
		@scheduler.task('cron', id='run_process_inactive_members', day_of_week='tue', hour=9, timezone='America/New_York')
		def run_process_inactive_members():
			with scheduler.app.app_context():
				from SIMS_Portal.users.utils import process_inactive_members
				
				process_inactive_members()
	
	from SIMS_Portal.main.routes import main
	from SIMS_Portal.assignments.routes import assignments
	from SIMS_Portal.emergencies.routes import emergencies
	from SIMS_Portal.portfolios.routes import portfolios
	from SIMS_Portal.users.routes import users
	from SIMS_Portal.stories.routes import stories
	from SIMS_Portal.learnings.routes import learnings
	from SIMS_Portal.reviews.routes import reviews
	from SIMS_Portal.alerts.routes import alerts
	from SIMS_Portal.errors.handlers import errors
	from SIMS_Portal.availability.routes import availability
	from SIMS_Portal.acronym.routes import acronym

	app.register_blueprint(main)
	app.register_blueprint(assignments)
	app.register_blueprint(emergencies)
	app.register_blueprint(portfolios)
	app.register_blueprint(users)
	app.register_blueprint(stories)
	app.register_blueprint(learnings)
	app.register_blueprint(reviews)
	app.register_blueprint(alerts)
	app.register_blueprint(errors)
	app.register_blueprint(availability)
	app.register_blueprint(acronym)
	
	from SIMS_Portal.models import User, Assignment, Emergency, Portfolio, NationalSociety, Story, Learning, Review, Alert, Badge, Availability, Documentation
	admin.add_view(AdminView(User, db.session))
	admin.add_view(AdminView(Assignment, db.session))
	admin.add_view(AdminView(Emergency, db.session))
	admin.add_view(AdminView(Portfolio, db.session))
	admin.add_view(AdminView(Story, db.session))
	admin.add_view(AdminView(Learning, db.session))
	admin.add_view(AdminView(Review, db.session))
	admin.add_view(AdminView(Alert, db.session))
	admin.add_view(AdminView(NationalSociety, db.session))
	admin.add_view(AdminView(Badge, db.session))
	admin.add_view(AdminView(Documentation, db.session))
	
	# run function to populate globe animation each time the app spins up
	with app.app_context():
		from SIMS_Portal.users.utils import update_member_locations
		update_member_locations()
	
	return app