from flask import Flask, redirect, url_for, request, render_template
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import datetime	
from SIMS_Portal.config import Config
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flaskext.markdown import Markdown

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login' # 'login' refers to the route to redirect to when user tries to access a page where @login_required but not currently logged in
login_manager.login_message_category = 'danger'
mail = Mail()

from SIMS_Portal import models

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
	
	db.init_app(app)
	bcrypt.init_app(app)
	login_manager.init_app(app)
	mail.init_app(app)
	admin = Admin(app, name='SIMS Admin Portal', template_mode='bootstrap4', endpoint='admin')
	Markdown(app)
	
	# # use this when migrating to new DB - will generate db file when running
	# with app.app_context():
	# 	db.create_all()
	# 
	# app.app_context().push()
	# db.create_all()
	
	from SIMS_Portal.main.routes import main
	from SIMS_Portal.assignments.routes import assignments
	from SIMS_Portal.emergencies.routes import emergencies
	from SIMS_Portal.portfolios.routes import portfolios
	from SIMS_Portal.users.routes import users
	from SIMS_Portal.stories.routes import stories
	from SIMS_Portal.learnings.routes import learnings
	from SIMS_Portal.reviews.routes import reviews
	from SIMS_Portal.errors.handlers import errors
	
	app.register_blueprint(main)
	app.register_blueprint(assignments)
	app.register_blueprint(emergencies)
	app.register_blueprint(portfolios)
	app.register_blueprint(users)
	app.register_blueprint(stories)
	app.register_blueprint(learnings)
	app.register_blueprint(reviews)
	app.register_blueprint(errors)
	
	from SIMS_Portal.models import User, Assignment, Emergency, Portfolio, NationalSociety, Story, Learning, Review
	admin.add_view(AdminView(User, db.session))
	admin.add_view(AdminView(Assignment, db.session))
	admin.add_view(AdminView(Emergency, db.session))
	admin.add_view(AdminView(Portfolio, db.session))
	admin.add_view(AdminView(Story, db.session))
	admin.add_view(AdminView(Learning, db.session))
	admin.add_view(AdminView(Review, db.session))
	admin.add_view(AdminView(NationalSociety, db.session))
	
	return app
