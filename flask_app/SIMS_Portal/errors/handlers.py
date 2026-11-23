from flask import Blueprint, render_template
from SIMS_Portal import db
from SIMS_Portal.models import User

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def error_404(error):
	return render_template('errors/404.html'), 404
	
@errors.app_errorhandler(403)
def error_403(error):
	list_of_admins = db.session.query(User).filter(User.is_admin == True, User.status == 'Active').all()
	return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@errors.app_errorhandler(413)
def error_413(error):
	return render_template('errors/413.html'), 413

@errors.app_errorhandler(429)
def error_429(error):
	# raised by Flask-Limiter (see the limits in users/routes.py)
	return render_template('errors/429.html'), 429

@errors.app_errorhandler(500)
def error_500(error):
	return render_template('errors/500.html'), 500