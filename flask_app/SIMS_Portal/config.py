import os

class Config:
	DEBUG = True
	SECRET_KEY = os.environ.get('SECRET_KEY')
	SESSION_TYPE = 'filesystem'
	SESSION_PERMANENT = False
	SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
	CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
	CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
	ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
	ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SCHEDULER_API_ENABLED = True
	TRELLO_KEY = os.environ.get('TRELLO_KEY')
	TRELLO_TOKEN = os.environ.get('TRELLO_TOKEN')
	DATA_FOLDER = os.environ.get('DATA_FOLDER', '/SIMS_Portal/static/data/')
	SLACK_BOT_TOKEN_NEW_USER = os.environ.get('SLACK_BOT_TOKEN_NEW_USER')
	SIMS_PORTAL_SLACK_BOT = os.environ.get('SIMS_PORTAL_SLACK_BOT')
	ROOT_URL = 'http://rcrcsims.org'
	DROPBOX_BOT = os.environ.get('DROPBOX_BOT')
	DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
	DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
	DROPBOX_REFRESH_TOKEN = os.environ.get('DROPBOX_REFRESH_TOKEN')
	SCHEDULER_TIMEZONE = "America/New_York"
	LANGUAGES = ['en', 'es']
	UPLOAD_EXTENSIONS = ['.jpg', '.png', '.gif', '.jpeg', '.shp', '.py', '.doc', '.docx', '.xls', '.csv', '.dif', '.pdf', '.ppt', '.pptx', '.potx', '.zip', '.txt', '.ai', '.indd']
	PORTFOLIO_TYPES = ['Map', 'Infographic', 'Dashboard', 'Mobile Data Collection', 'Assessment', 'Internal Analysis', 'External Report', 'Code Snippet', 'Other']
	LOGTAIL_SOURCE_TOKEN = os.environ.get('LOGTAIL_SOURCE_TOKEN')
	POSITION_STACK_TOKEN = os.environ.get('POSITION_STACK_TOKEN')
	GOOGLE_MAPS_TOKEN = os.environ.get('GOOGLE_MAPS_TOKEN')
	WERKZEUG_DEBUG_PIN = '443-431-665'
	UPLOAD_BUCKET = 'sims-portal-uploads'
	CACHE_TYPE = 'simple'
	STATIC_FOLDER = 'static'
	RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
	RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')
	GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')