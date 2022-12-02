from SIMS_Portal import db, login_manager
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from authlib.jose import jwt, JoseError
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
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

class Skill(db.Model):
	__tablename__ = 'skill'
	
	id = db.Column(db.Integer, primary_key=True)
	
	name = db.Column(db.String)
	category = db.Column(db.String)

class Language(db.Model):
	__tablename__ = 'language'
	
	id = db.Column(db.Integer, primary_key=True)
	
	name = db.Column(db.String)

class Badge(db.Model):
	__tablename__ = 'badge'
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	badge_url = db.Column(db.String)
	limited_edition = db.Column(db.Boolean, default=False)

class NationalSociety(db.Model):
	__tablename__ = 'nationalsociety'
	
	id = db.Column(db.Integer, primary_key=True)
	
	ns_name = db.Column(db.String(120), nullable=False)
	country_name = db.Column(db.String(120), nullable=False)
	ns_go_id = db.Column(db.Integer)
	iso2 = db.Column(db.String(2))
	iso3 = db.Column(db.String(3))
	
	users = db.relationship('User', backref='national_society', lazy=True)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

	def __repr__(self):
		return f"NationalSociety('{self.ns_name}','{self.country_name}','{self.ns_go_id}'"

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
	image_file = db.Column(db.String(20), nullable=False, default='default.png')
	twitter = db.Column(db.String(120))
	slack_id = db.Column(db.String(120))
	github = db.Column(db.String(120))
	linked_in = db.Column(db.String(120))
	messaging_number_country_code = db.Column(db.Integer)
	messaging_number = db.Column(db.Integer)
	
	ns_id = db.Column(db.Integer, db.ForeignKey('nationalsociety.ns_go_id'))
	
	assignments = db.relationship('Assignment', backref='assigned_member')
	products = db.relationship('Portfolio', backref='creator', lazy=True)
	skills = db.relationship('Skill', secondary='user_skill', backref='members_with_skill')
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
		return f"User('{self.id}, {self.firstname}','{self.lastname}','{self.email}','{self.image_file}', {self.ns_id})"

class Assignment(db.Model):
	__tablename__ = 'assignment'
	
	id = db.Column(db.Integer, primary_key=True)
	
	role = db.Column(db.String(100))
	start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
	end_date = db.Column(db.Date, nullable=False)
	remote = db.Column(db.Boolean)
	assignment_details = db.Column(db.String(1000))
	assignment_status = db.Column(db.String(100), default='Active')
	availability = db.Column(db.String)

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
	description = db.Column(db.Text)
	product_status = db.Column(db.String(100), default='Personal')
	final_file_location = db.Column(db.String(100), nullable=False)
	asset_file_location = db.Column(db.String(100))
	external = db.Column(db.Boolean, default=False)
	collaborator_ids = db.Column(db.String(200))
	approver_id = db.Column(db.Integer)
	approver_message = db.Column(db.Text)
	km_article = db.Column(db.Integer)
	
	assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
	creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	emergency_id = db.Column(db.Integer, db.ForeignKey('emergency.id'))
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())

	def __repr__(self):
		return f"Portfolio('{self.id}','{self.title}','{self.type}','{self.description}','{self.final_file_location}','{self.creator_id}','{self.collaborator_ids}')"

class Alert(db.Model):
	__tablename__ = 'alert'
	
	id = db.Column(db.Integer, primary_key=True)
	
	event_name = db.Column(db.String)
	event_go_id = db.Column(db.Integer)
	event_date = db.Column(db.DateTime)
	role_profile = db.Column(db.String)
	alert_date = db.Column(db.DateTime)
	alert_id = db.Column(db.Integer)
	alert_status = db.Column(db.String)
	location = db.Column(db.String)
	
	created_at = db.Column(db.DateTime, server_default=func.now())
	updated_at = db.Column(db.DateTime, onupdate=func.now())
	
	def __init__(self, role_profile, alert_date, alert_id, alert_status, event_name, event_go_id, event_date, location):
		self.role_profile = role_profile
		self.alert_date = datetime.strptime(alert_date, '%Y-%m-%dT%H:%M:%SZ')
		self.alert_id = alert_id
		self.alert_status = alert_status
		self.event_name = event_name
		self.event_go_id = event_go_id
		self.event_date = datetime.strptime(event_date, '%Y-%m-%dT%H:%M:%SZ')
		self.location = location
	
	@classmethod
	def save_go_alerts(cls, data):
		query = "INSERT INTO alerts (role_profile, alert_date, alert_id, alert_status, event_name, event_go_id, event_date, location) VALUES (%(role_profile)s, %(alert_date)s, %(alert_id)s, %(alert_status)s, %(event_name)s, %(event_go_id)s, %(event_date)s, %(location)s)"
		return query
	
	def __repr__(self):
		return f"Alert('{self.event_name}','{self.event_go_id}','{self.event_date}','{self.event_profile}','{self.alert_date}','{self.alert_id}','{self.alert_status}','{self.location}')"
