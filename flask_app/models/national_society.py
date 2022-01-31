from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash
from flask_app.models.member import Member

class National_Society:
	db_name = 'sims_network'
	
	def __init__(self, data):
		self.id = data['id']
		self.ns_name = data['ns_name']
		self.country = data['country']
		self.ns_go_id = data['ns_go_id']
		self.created_at = data['created_at']
		self.updated_at = data['updated_at']
		self.members = []
		
	@classmethod
	def get_all_national_societies(cls):
		query = "SELECT * FROM national_societies"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
	
	@classmethod
	def get_all_active_ns_count(cls):
		query = "SELECT COUNT(DISTINCT national_society_id) as DistinctNS FROM members WHERE status = 'Active'"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results[0]
	
	@classmethod
	def get_national_society_with_members(cls, data):
		query = "SELECT * FROM national_societies LEFT JOIN members ON ns_go_id = national_society_id WHERE national_societies.ns_go_id = %(id)s"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		# Instantiate member object and append to list of national societies
		this_ns = cls(results[0])

		for row in results:
			member_data = {
				"id": row['members.id'],
				"first_name": row['first_name'],
				"last_name": row['last_name'],
				"status": row['status'],
				"gender": row['gender'],
				"birthday": row['birthday'],
				"email": row['email'],
				"password": row['password'],
				"molnix_id": row['molnix_id'],
				"job_title": row['job_title'],
				"is_admin": row['is_admin'],
				"avatar": row['avatar'],
				"created_at": row['members.created_at'],
				"updated_at": row['members.updated_at'],
				"national_society_id": row['national_society_id']
			}
			# Make member object
			this_member = Member(member_data)
			this_ns.members.append(this_member)

		return this_ns