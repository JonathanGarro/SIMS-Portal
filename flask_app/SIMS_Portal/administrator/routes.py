from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint
from SIMS_Portal import db, bcrypt
from SIMS_Portal.models import User
from SIMS_Portal.administrator.forms import AdminEditUserForm
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, login_required

administrator = Blueprint('administrator', __name__)

# Dev note: I've decided to implement the Flask-Admin library instead of rolling a custom admin portal. Leaving this in case we change our minds.
@administrator.route('/admin/', methods=['GET', 'POST'])
@administrator.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
	if current_user.is_admin == 1:
		form = AdminEditUserForm()
		all_users = db.session.query(User).all()
		return render_template('admin.html', all_users=all_users, form=form)
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

