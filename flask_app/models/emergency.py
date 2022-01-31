from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash
from flask_app.models.member import Member
from flask_app.models.emergency_type import Emergency_Type

class Emergency:
	db_name = 'sims_network'
	
	def __init__(self, data):
		self.id = data['id']
		self.emergency_name = data['emergency_name']
		self.emergency_type_id = data['emergency_type_id']
		self.emergency_glide = data['emergency_glide']
		self.emergency_go_id = data['emergency_go_id']
		self.emergency_location_id = data['emergency_location_id']
		self.activation_details = data['activation_details']
		self.created_at = data['created_at']
		self.updated_at = data['updated_at']
		self.emergency_type = None
		
	@classmethod
	def save_emergency(cls, data):
		print("Running save_emergency method")
		query = "INSERT INTO emergencies (emergency_name, emergency_glide, emergency_go_id, emergency_location_id, activation_details, created_at, updated_at, emergency_type_id, learnings_id) VALUES (%(emergency_name)s, %(emergency_glide)s, %(emergency_go_id)s, %(emergency_location_id)s, %(activation_details)s, NOW(), NOW(), %(emergency_type_id)s, 1  )"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results
		
	@classmethod
	def update_emergency(cls,data):
		pass
		
	@classmethod
	def destroy_emergency(cls, data):
		pass
	
	@classmethod
	def get_one_emergency(cls, data):
		query = "SELECT * FROM emergencies JOIN emergency_types ON emergency_type_id = emergency_type_go_id WHERE emergencies.id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		this_emergency = cls(results[0])
			
		for row in results:
			emergency_type_data = {
				"id": row['id'],
				"emergency_type_go_id": row['emergency_type_go_id'],
				"emergency_type_name": row['emergency_type_name'],
				"created_at": row['created_at'],
				"updated_at": row['updated_at']
			}
			# Make emergency_type object
			this_type = Emergency_Type(emergency_type_data)
			this_emergency.emergency_type=this_type
		
		return this_emergency
	
	@classmethod
	def get_all_emergencies(cls):
		query = "SELECT * FROM emergencies"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
	
	@classmethod
	def get_recent_emergencies(cls):
		print("GETTING RECENT EMERGENCIES")
		query = "SELECT * FROM emergencies ORDER BY created_at DESC LIMIT 5"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
	
	@staticmethod
	def validate_emergency(emergency):
		is_valid = True
		
		if len(emergency['emergency_name']) < 3:
			is_valid = False
			flash("An emergency name is required.", "emergency")
		
		if len(emergency['emergency_type']) < 1:
			is_valid = False
			flash("An emergency type is required.", "emergency")
		
		return is_valid