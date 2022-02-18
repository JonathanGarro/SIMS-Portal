from flask_app.config.mysqlconnection import connectToMySQL
from flask_app.models.member import Member
from flask_app.models.emergency import Emergency
from flask_app.models.emergency_type import Emergency_Type

class Assignment:
	db_name = "sims_network"
	
	def __init__(self, data):
		self.id = data['id']
		self.role = data['role']
		self.start_date = data['start_date']
		self.end_date = data['end_date']
		self.remote = data['remote']
		self.tor_file = data['tor_file']
		self.assignment_details = data['assignment_details']
		self.created_at = data['created_at']
		self.updated_at = data['updated_at']
		self.emergency = None
		self.member = None
	
	@classmethod
	def create_assignment(cls, data):
		query = "INSERT INTO assignments (role, start_date, end_date, assignment_details, created_at, updated_at, emergency_id, member_id) VALUES (%(role)s, %(start_date)s, %(end_date)s, %(assignment_details)s, NOW(), NOW(), %(emergency_id)s, %(member_id)s )"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results
	
	@classmethod
	def get_one_assignment(cls, data):
		query = "SELECT * FROM assignments WHERE id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results
	
	@classmethod
	def get_all_assignments_with_member_and_ns(cls):
		query = "SELECT * FROM assignments JOIN members ON member_id = members.id JOIN national_societies ON national_society_id = national_societies.id"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
	
	@classmethod
	def get_active_assignments(cls):
		query = "SELECT * FROM assignments WHERE end_date > CURDATE()"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
	
	@classmethod
	def get_active_assignment_count(cls):
		query = "SELECT COUNT(role) as AssignmentCount FROM assignments WHERE end_date > CURDATE() "
		results = connectToMySQL(cls.db_name).query_db(query)
		return results[0]

	@classmethod
	def get_assignment_with_member(cls, data):
		query = "SELECT * FROM assignments JOIN members ON members.id = assignments.member_id JOIN emergencies ON emergency_id = emergencies.id JOIN national_societies ON ns_go_id = emergency_location_id WHERE assignments.id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results[0]
	
	@classmethod
	def get_active_assignments_with_member(cls):
		query = "SELECT * FROM assignments JOIN members ON members.id = assignments.member_id JOIN emergencies ON emergency_id = emergencies.id WHERE end_date > CURDATE()"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
		
	@classmethod
	def get_all_assignments_by_member(cls, data):
		query = "SELECT * FROM assignments JOIN emergencies ON emergency_id = emergencies.id WHERE member_id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results
		
	@classmethod
	def get_all_assignments_by_emergency(cls, data):
		query = "SELECT * FROM assignments LEFT JOIN members ON member_id = members.id JOIN national_societies ON national_society_id = ns_go_id WHERE emergency_id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results
	
	@classmethod
	def count_assignment_days_remaining(cls, data):
		query = "SELECT DATEDIFF(end_date, CURDATE()) AS time_remaining FROM assignments WHERE id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results[0]
	
	@classmethod
	def get_assignment_length(cls, data):
		query = "SELECT DATEDIFF(end_date, start_date) AS assignment_length FROM assignments WHERE id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results[0]