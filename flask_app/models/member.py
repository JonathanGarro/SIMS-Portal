from flask_app.config.mysqlconnection import connectToMySQL
import re
from flask_wtf import FlaskForm
# from flask_app.models import national_society
from wtforms import FileField, SubmitField
from flask_wtf.file import FileAllowed
from wtforms.validators import InputRequired
from werkzeug.utils import secure_filename
import os
from datetime import date
from flask import flash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

class Member:
	db_name = 'sims_network'
	
	def __init__(self, data):
		self.id = data['id']
		self.first_name = data['first_name']
		self.last_name = data['last_name']
		self.gender = data['gender']
		self.email = data['email']
		self.birthday = data['birthday']
		self.password = data['password']
		self.job_title = data['job_title']
		self.is_admin = data['is_admin']
		self.avatar = data['avatar']
		self.created_at = data['created_at']
		self.updated_at = data['updated_at']
		self.national_society_id = data['national_society_id']
		self.national_society = None
		self.emergencies = []
	
	@classmethod
	def get_all_active_member_count(cls):
		query = "SELECT COUNT(DISTINCT email) as DistinctActiveUsers FROM members WHERE status = 'Active' "
		results = connectToMySQL(cls.db_name).query_db(query)
		return results[0]
		
	@classmethod
	def get_all_active_members(cls):
		query = "SELECT * FROM members JOIN national_societies ON national_society_id = ns_go_id WHERE status = 'Active' "
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
	
	@classmethod
	def register_new_member(cls, data):
		print("Running register_new_member method")
		query = "INSERT INTO members (first_name, last_name, gender, email, password, national_society_id, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s,%(gender)s,%(email)s,%(password)s, %(national_society_id)s, NOW(), NOW() )"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results
	
	@classmethod
	def get_member_by_id(cls, data):
		print("GETTING MEMBER BY ID")
		query = "SELECT * FROM members WHERE id = %(id)s;"
		results = connectToMySQL(cls.db_name).query_db(query,data)
		if len(results) < 1:
			return False
		print(results[0])
		return cls(results[0])

	@classmethod
	def get_member_by_id_with_ns(cls, data):
		from flask_app.models import national_society
		query = "SELECT * FROM members JOIN national_societies ON national_society_id = ns_go_id WHERE members.id = %(id)s;"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		if len(results) < 1:
			return False
		this_member = cls(results[0])
		
		for row in results:
			ns_info = {
				"id": row['id'],
				"ns_name": row['ns_name'],
				"country": row['country'],
				"ns_go_id": row['ns_go_id'],
				"created_at": row['created_at'],
				"updated_at": row['updated_at']
			}
			this_ns = national_society.National_Society(ns_info)
			this_member.national_society=this_ns
		
		return this_member

	@classmethod
	def get_member_by_email(cls, data):
		query = "SELECT * FROM members WHERE email = %(email)s;"
		results = connectToMySQL(cls.db_name).query_db(query,data)
		if len(results) < 1:
			return False
		return cls(results[0])
	
	# @classmethod
	# def calc_member_age(cls, data):
	# 	today = date.today()
	# 	
	# 	query = "SELECT * FROM members WHERE id = %(id)s;"
	# 	results = connectToMySQL(cls.db_name).query_db(query,data)
	# 	
	# 	age = today.year - results['birthday'].year - ((today.month, today.day) < (results['birthday'].month, results['birthday'].day))
	# 	print(age)
	# 	return age

	@classmethod
	def update_avatar_in_db(cls, data):
		query = "UPDATE members SET avatar = %(filename)s WHERE id = %(id)s;"
		results = connectToMySQL(cls.db_name).query_db(query,data)
		return results
		
	@classmethod
	def update_member_profile(cls, data):
		query = "UPDATE members SET first_name = %(first_name)s, last_name = %(last_name)s, gender = %(gender)s, national_society_id = %(national_society_id)s, email = %(email)s, job_title = %(job_title)s, birthday = %(birthday)s WHERE id = %(id)s;"
		results = connectToMySQL(cls.db_name).query_db(query,data)
		return results

	@staticmethod
	def validate_register(member):
		is_valid = True
		
		query = "SELECT * FROM members WHERE email = %(email)s;"
		results = connectToMySQL(Member.db_name).query_db(query, member)
		
		if len(results) >= 1:
			is_valid = False
			flash("Email already taken.","register")
		if len(member['first_name']) < 2:
			is_valid=False
			flash("First name is required.","register")
		if len(member['last_name']) < 2:
			is_valid=False
			flash("Last name is required.","register")
		if not EMAIL_REGEX.match(member['email']):
			is_valid = False
			flash("Please enter a valid email address.", "register")
		if len(member['password']) < 6:
			is_valid=False
			flash("Password must be at least 6 characters.","register")
		if member['password'] != member['confirm']:
			is_valid=False
			flash("Passwords don't match.","register")

		return is_valid
	
	@staticmethod
	def validate_profile_update(member):
		is_valid = True
		
		query = "SELECT * FROM members WHERE email = %(email)s;"
		results = connectToMySQL(Member.db_name).query_db(query, member)
		
		if len(member['first_name']) < 2:
			is_valid=False
			flash("First name is required, initials not allowed.","update_profile")
		
		if len(member['last_name']) < 2:
			is_valid=False
			flash("Last name is required, initials not allowed","update_profile")
		
		if not EMAIL_REGEX.match(member['email']):
			is_valid = False
			flash("Please enter a valid email address.", "update_profile")
		
		return is_valid