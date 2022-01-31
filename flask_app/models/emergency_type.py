from flask_app.config.mysqlconnection import connectToMySQL

class Emergency_Type:
	db_name = 'sims_network'
	
	def __init__(self, data):
		self.id = data['id']
		self.emergency_type_go_id = data['emergency_type_go_id']
		self.emergency_type_name = data['emergency_type_name']
		self.created_at = data['created_at']
		self.updated_at = data['updated_at']