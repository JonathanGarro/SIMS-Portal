import os

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY')
	SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
	CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
	CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
	ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
	ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAIL_SERVER = 'smtp.dreamhost.com'
	MAIL_PORT = 465
	MAIL_USE_TLS = False
	MAIL_USE_SSL = True
	MAIL_USERNAME = 'sims_portal@dissolvingdata.com'
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	MAIL_DEBUG = True
	SCHEDULER_API_ENABLED = True
	TRELLO_KEY = os.environ.get('TRELLO_KEY')
	TRELLO_TOKEN = os.environ.get('TRELLO_TOKEN')
	DATA_FOLDER = '/SIMS_Portal/static/data/'
	SLACK_BOT_TOKEN_NEW_USER = os.environ.get('SLACK_BOT_TOKEN_NEW_USER')
	SIMS_PORTAL_SLACK_BOT = os.environ.get('SIMS_PORTAL_SLACK_BOT')
	ROOT_URL = 'http://127.0.0.1:5000'