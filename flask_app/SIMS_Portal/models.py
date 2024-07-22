from SIMS_Portal import db, login_manager
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
from flask_login import UserMixin, current_user
from sqlalchemy.orm import declarative_base, relationship, column_property
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, ForeignKey, Integer, Table
import requests

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

user_profile = db.Table('user_profile',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('profile_id', db.Integer, db.ForeignKey('profile.id')),
	db.Column('tier', db.Integer)
)

user_skill = db.Table('user_skill', 
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'))
)

user_language = db.Table('user_language', 
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('language_id', db.Integer, db.ForeignKey('language.id'))
)

user_badge = db.Table('user_badge',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('badge_id', db.Integer, db.ForeignKey('badge.id')),
	db.Column('assigner_id', db.Integer),
	db.Column('assigner_justify', db.Text),
	db.Column('created_date', db.DateTime, server_default=func.now()),
	db.Column('updated_date', db.DateTime, onupdate=func.now())
)

user_workinggroup = db.Table('user_workinggroup',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('workinggroup_id', db.Integer, db.ForeignKey('workinggroup.id'))
)

class Task(db.Model):
	__tablename__ = 'task'
	
	id = db.Column(db.Integer, primary_key=True)
	task_id = db.Column(db.Integer) # github issue id
	repo = db.Column(db.String(100))
	name = db.Column(db.String(500))
	state = db.Column(db.String(10))
	created_by_gh = db.Column(db.String(100)) # github name of creator
	url = db.Column(db.String(500))
	assignees_gh = db.Column(db.String(500), nullable=True) # list of github names of people assigned
	created_at = db.Column(db.DateTime)
	
	date_added = db.Column(db.DateTime, server_default=func.now())
	date_modified = db.Column(db.DateTime, onupdate=func.now())
	
	def __repr__(self):
		return f"Task({self.id}, {self.name}, {self.state})"
	
class Log(db.Model):
	__tablename__ = 'log'
	
	id = db.Column(db.Integer, primary_key=True)
	message = db.Column(db.String(500))
	user_id = db.Column(db.Integer)
	timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
	
	def __repr__(self):
		return f"Log({self.timestamp}: {self.message}"

class Acronym(db.Model):
	__tablename__ = 'acronym'
	
	id = db.Column(db.Integer, primary_key=True)
	acronym_eng = db.Column(db.String(255), nullable=True)
	def_eng = db.Column(db.Text, nullable=True)
	expl_eng = db.Column(db.Text, nullable=True)
	acronym_esp = db.Column(db.String(255), nullable=True)
	def_esp = db.Column(db.Text, nullable=True)
	expl_esp = db.Column(db.Text, nullable=True)
	acronym_fra = db.Column(db.String(255), nullable=True)
	def_fra = db.Column(db.Text, nullable=True)
	expl_fra = db.Column(db.Text, nullable=True)
	relevant_link = db.Column(db.String(), nullable=True)
	anonymous_submitter_name = db.Column(db.String(), nullable=True)
	anonymous_submitter_email = db.Column(db.String(), nullable=True)
	scope = db.Column(db.Text, nullable=True)
	field = db.Column(db.Text, nullable=True)
	
	associated_ns = db.Column(db.Integer, db.ForeignKey('nationalsociety.ns_go_id'))
	added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
	
	date_added = db.Column(db.DateTime, server_default=func.now())
	date_modified = db.Column(db.DateTime, onupdate=func.now())
	
	def __repr__(self):
		return f"{self.acronym_eng} - {self.def_eng}"

class Documentation(db.Model):
	__tablename__ = 'documentation'
	
	id = db.Column(db.Integer, primary_key=True)
	article_name = db.Column(db.String)
	url = db.Column(db.String)
	category = db.Column(db.String)
	summary = db.Column(db.String)
	featured = db.Column(db.Boolean)
	
	author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'))
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class Profile(db.Model):
	__tablename__ = 'profile'
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	image = db.Column(db.String)
	
	def __repr__(self):
		return f"Profile('{self.name}')" 

class Skill(db.Model):
	__tablename__ = 'skill'
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	category = db.Column(db.String)
	
	def __repr__(self):
		return f"Skill('{self.name}','{self.category}')"
	
class Language(db.Model):
	__tablename__ = 'language'
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	
	def __repr__(self):
		return f"Language('{self.name}')"

class Badge(db.Model):
	__tablename__ = 'badge'
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	badge_url = db.Column(db.String)
	description = db.Column(db.String)
	limited_edition = db.Column(db.Boolean, default=False)
	
	def __repr__(self):
		return f"Badge('{self.name}')"
		

class NationalSociety(db.Model):
	__tablename__ = 'nationalsociety'
	
	id = db.Column(db.Integer, primary_key=True)
	ns_name = db.Column(db.String(120), nullable=False)
	country_name = db.Column(db.String(120), nullable=False)
	ns_go_id = db.Column(db.Integer, unique=True)
	iso2 = db.Column(db.String(2))
	iso3 = db.Column(db.String(3))
	
	users = db.relationship('User', backref='national_society', lazy=True)
	acronyms = db.relationship('Acronym', backref='national_society', lazy=True)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class User(db.Model, UserMixin):
	__tablename__ = 'user'
	
	id = db.Column(db.Integer, primary_key=True)
	firstname = db.Column(db.String(40), nullable=False)
	lastname = db.Column(db.String(40), nullable=False)
	status = db.Column(db.String(20), default='Pending')
	birthday = db.Column(db.Date)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	molnix_id = db.Column(db.Integer)
	job_title = db.Column(db.String(120))
	unit = db.Column(db.String(120))
	bio = db.Column(db.Text)
	is_admin = db.Column(db.Boolean, default=False)
	roles = db.Column(db.String(1000))
	languages = db.Column(db.String(1000))
	image_file = db.Column(db.String(200), nullable=False, default='default.png')
	twitter = db.Column(db.String(120))
	slack_id = db.Column(db.String(120))
	github = db.Column(db.String(120))
	linked_in = db.Column(db.String(120))
	messaging_number_country_code = db.Column(db.Integer)
	messaging_number = db.Column(db.BigInteger)
	coordinates = db.Column(db.String(120))
	time_zone = db.Column(db.String(120))
	place_label = db.Column(db.String(120))
	private_profile = db.Column(db.Boolean, default=False)
	
	ns_id = db.Column(db.Integer, db.ForeignKey('nationalsociety.ns_go_id'))
	
	assignments = db.relationship('Assignment', backref='assigned_member')
	products = db.relationship('Portfolio', backref='creator', lazy=True)
	skills = db.relationship('Skill', secondary='user_skill', backref='members_with_skill')
	profiles = db.relationship('Profile', secondary='user_profile', backref='members_with_profile')
	languages = db.relationship('Language', secondary='user_language', backref='members_with_language')
	badges = db.relationship('Badge', secondary='user_badge', backref='members_with_badge')
	working_groups = db.relationship('WorkingGroup', secondary='user_workinggroup', backref='members_with_workinggroup')
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())
	
	fullname = column_property(firstname + " " + lastname)
	
	def get_reset_token(self, expires_sec=1800):
		s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'user_id': self.id}).decode('utf-8')
	
	@staticmethod
	def verify_reset_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			user_id = s.loads(token)['user_id']
		except:
			return None
		return User.query.get(user_id)
	
	@hybrid_property
	def fullname(self):
		return self.firstname + " " + self.lastname
	
	def __repr__(self):
		return f"User({self.id}, {self.firstname} {self.lastname}, {self.email})"

class Assignment(db.Model):
	__tablename__ = 'assignment'
	
	id = db.Column(db.Integer, primary_key=True)
	role = db.Column(db.String(100))
	start_date = db.Column(db.Date, default=datetime.utcnow)
	end_date = db.Column(db.Date)
	remote = db.Column(db.Boolean)
	assignment_details = db.Column(db.String(1000))
	assignment_status = db.Column(db.String(100), default='Active')
	availability = db.Column(db.String)
	hours = db.Column(db.Integer, default=0)

	products = db.relationship('Portfolio', backref='assignment', lazy=True)
	learning = db.relationship('Learning', backref='assignment', uselist=False)
	
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	emergency_id = db.Column(db.Integer, db.ForeignKey('emergency.id'), default=0)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

	def __repr__(self):
		return f"Assignment('{self.role}','{self.start_date}','{self.end_date}','{self.remote}','{self.assignment_details}')"

class Learning(db.Model):
	__tablename__ = 'learning'
	
	id = db.Column(db.Integer, primary_key=True)
	overall_score = db.Column(db.Integer, nullable=False)
	overall_exp = db.Column(db.String, nullable=False)
	got_support = db.Column(db.Integer)
	internal_resource = db.Column(db.Integer)
	external_resource = db.Column(db.Integer)
	field_communication = db.Column(db.Integer)
	clear_tasks = db.Column(db.Integer)
	clear_deadlines = db.Column(db.Integer)
	coordination_tools = db.Column(db.Integer)
	
	assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), unique=True)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class Review(db.Model):
	__tablename__ = 'review'
	
	id = db.Column(db.Integer, primary_key=True)
	category = db.Column(db.String, nullable=False)
	type = db.Column(db.String, nullable=False)
	title = db.Column(db.String, nullable=False)
	description = db.Column(db.Text, nullable=False)
	recommended_action = db.Column(db.Text)
	follow_up = db.Column(db.Text)
	status = db.Column(db.String, nullable=False)
	
	emergency_id = db.Column(db.Integer, db.ForeignKey('emergency.id'), nullable=False)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class WorkingGroup(db.Model):
	__tablename__ = 'workinggroup'
	
	id = db.Column(db.Integer, primary_key=True)
	wg_name = db.Column(db.String, nullable=False)
	wg_description = db.Column(db.Text)
	wg_url = db.Column(db.String)
	wg_external = db.Column(db.Boolean)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class Story(db.Model):
	__tablename__ = 'story'
	
	id = db.Column(db.Integer, primary_key=True)
	header_image = db.Column(db.String, nullable=False, default='default-banner.jpg')
	header_caption = db.Column(db.String, nullable=False, default='default-banner.jpg')
	entry = db.Column(db.Text)
	
	emergency_id = db.Column(db.Integer, db.ForeignKey('emergency.id'), default=0)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class Emergency(db.Model):
	__tablename__ = 'emergency'
	
	id = db.Column(db.Integer, primary_key=True)
	emergency_name = db.Column(db.String(100), nullable=False)
	emergency_status = db.Column(db.String(100), nullable=False, default='Active')
	emergency_glide = db.Column(db.String(20))
	emergency_go_id = db.Column(db.Integer)
	emergency_location_id = db.Column(db.Integer)
	emergency_review_id = db.Column(db.Integer)
	activation_details = db.Column(db.String(1000))
	slack_channel = db.Column(db.String)
	dropbox_url = db.Column(db.String)
	trello_url = db.Column(db.String)
	github_repo = db.Column(db.String)
	
	emergency_type_id = db.Column(db.Integer, db.ForeignKey('emergencytype.id'))
	
	emergency_products = db.relationship('Portfolio', backref='emergency_response', lazy=True)
	reviews = db.relationship('Review', backref='related_operation', lazy=True)
	assigned_to = db.relationship('Assignment', backref='assigned_emergency', lazy=True)
	story_id = db.relationship('Story', backref='associated_story', lazy=True)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())
	
	@staticmethod
	def get_latest_go_emergencies():
		api_call = 'https://goadmin.ifrc.org/api/v2/event/'
		r = requests.get(api_call).json()
		
		output = []
		
		for x in r['results']:
			temp_dict = {}
			temp_dict['dis_id'] = x['id']
			temp_dict['dis_name'] = x['name']
			output.append(temp_dict)
		
		sorted_output = sorted(output, key=lambda d: d['dis_id'], reverse=True)[:11]
		
		return sorted_output
		
	def __repr__(self):
		return f"Emergency('{self.emergency_name}','{self.emergency_glide}','{self.emergency_go_id}','{self.emergency_location_id}','{self.emergency_type_id}','{self.emergency_review_id}','{self.activation_details}','{self.emergency_type_id}')"

class EmergencyType(db.Model):
	__tablename__ = 'emergencytype'
	
	id = db.Column(db.Integer, primary_key=True)
	emergency_type_go_id = db.Column(db.Integer)
	emergency_type_name = db.Column(db.String)
	
	emergencies = db.relationship('Emergency', backref='emergencies_of_type')
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class Portfolio(db.Model):
	__tablename__ = 'portfolio'
	
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	type = db.Column(db.String(100), nullable=False)
	format = db.Column(db.String(100))
	description = db.Column(db.Text)
	product_status = db.Column(db.String(100), default='Personal')
	local_file = db.Column(db.String(100), nullable=False)
	image_file = db.Column(db.String(200))
	dropbox_file = db.Column(db.String(300))
	external = db.Column(db.Boolean, default=False)
	collaborator_ids = db.Column(db.String(200))
	approver_id = db.Column(db.Integer)
	approver_message = db.Column(db.Text)
	km_article_id = db.Column(db.Integer) # this has been retired as we moved away from int for documentation ID
	learning_site_url = db.Column(db.String(1000)) # this has replaced the km_article_id
	
	assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
	creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	emergency_id = db.Column(db.Integer, db.ForeignKey('emergency.id'))
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

	def __repr__(self):
		return f"Portfolio('{self.id}','{self.title}','{self.type}','{self.description}','{self.image_file}','{self.creator_id}','{self.collaborator_ids}')"

class Alert(db.Model):
	__tablename__ = 'alert'
	
	id = db.Column(db.Integer, primary_key=True)
	molnix_id = db.Column(db.Integer)
	alert_record_created_at = db.Column(db.DateTime)
	event = db.Column(db.String)
	role_profile = db.Column(db.String)
	rotation = db.Column(db.String)
	modality = db.Column(db.String)
	language_required = db.Column(db.String)
	molnix_status = db.Column(db.String)
	alert_status = db.Column(db.String)
	opens = db.Column(db.DateTime)
	start = db.Column(db.DateTime)
	end_time = db.Column(db.DateTime)
	sectors = db.Column(db.String)
	role_tags = db.Column(db.String)
	scope = db.Column(db.String)
	im_filter = db.Column(db.Boolean)
	iso3 = db.Column(db.String)
	country_name = db.Column(db.String)
	disaster_type_id = db.Column(db.Integer)
	disaster_type_name = db.Column(db.String)
	disaster_go_id = db.Column(db.Integer)
	ifrc_severity_level_display = db.Column(db.String)
	alert_id = db.Column(db.Integer)
	region_id = db.Column(db.Integer)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())
	
	def __repr__(self):
		return f"Alert('{self.event}', '{self.event}')"
		
class Availability(db.Model):
	__tablename__ = 'availability'
	
	id = db.Column(db.Integer, primary_key=True)
	timeframe = db.Column(db.String)
	dates = db.Column(db.String)
	
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	emergency_id = db.Column(db.Integer, db.ForeignKey('emergency.id'), default=0)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

class Region(db.Model):
	__tablename__ = 'region'
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)

class RegionalFocalPoint(db.Model):
	__tablename__ = 'regional_focal_point'
	
	id = db.Column(db.Integer, primary_key=True)
	regional_id = db.Column(db.Integer, db.ForeignKey('region.id'), nullable=False)
	focal_point_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	
	