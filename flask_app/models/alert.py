from flask_app.config.mysqlconnection import connectToMySQL
from datetime import date
from flask import flash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from apscheduler.schedulers.background import BackgroundScheduler

class Alert: 
	db_name = 'sims_network'
	
	def __init__(self, data):
		self.id = data['id']
		self.role_profile = data['role_profile']
		self.alert_date = data['alert_date']
		self.alert_id = data['alert_id']
		self.alert_status = data['alert_status']
		self.event_name = data['event_name']
		self.event_go_id = data['event_id']
		self.event_date = data['event_date']
		self.location = data['location']
		self.created_at = data['created_at']
		self.updated_at = data['updated_at']
		
	@classmethod
	def clear_alert_table_before_update(cls):
		query = "DELETE FROM alerts"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results
	
	@classmethod
	def save_GO_alerts_from_API(cls, data):
		query = "INSERT INTO alerts (role_profile, alert_date, alert_id, alert_status, event_name, event_go_id, event_date, location) VALUES (%(role_profile)s, %(alert_date)s, %(alert_id)s, %(alert_status)s, %(event_name)s, %(event_go_id)s, %(event_date)s, %(location)s)"
		results = connectToMySQL(cls.db_name).query_db(query, data)
		return results
	
	@classmethod
	def get_all_alerts(cls):
		query = "SELECT * FROM alerts"
		results = connectToMySQL(cls.db_name).query_db(query)
		return results