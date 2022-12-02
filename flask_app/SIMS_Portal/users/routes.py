from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint, current_app
from SIMS_Portal import db, bcrypt, mail
from SIMS_Portal.models import User, Assignment, Emergency, NationalSociety, Portfolio, EmergencyType, Skill, Language, user_skill, user_language, Badge, Alert, user_badge
from SIMS_Portal.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from SIMS_Portal.users.utils import save_picture, send_reset_email, new_user_slack_alert, send_slack_dm
from SIMS_Portal.portfolios.utils import get_full_portfolio
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from datetime import datetime, date

users = Blueprint('users', __name__)

@users.route('/members')
def members():
	members = db.engine.execute("SELECT user.id AS user_id, user.ns_id AS user_ns_id, user.firstname, user.lastname, nationalsociety.ns_go_id, user.image_file, user.job_title, nationalsociety.ns_name FROM user LEFT OUTER JOIN nationalsociety ON nationalsociety.ns_go_id = user.ns_id WHERE status = 'Active'")
	return render_template('members.html', members=members)

@users.route('/members/all') 
@login_required
def members_all(): 
	members = db.engine.execute("SELECT u.id, u.firstname, u.lastname, u.status, u.email, u.job_title, u.slack_id, u.ns_id, u.image_file, ns.ns_name, COUNT(a.id) as assignment_count FROM user u JOIN nationalsociety ns ON ns.ns_go_id = u.ns_id LEFT JOIN assignment a ON a.user_id = u.id WHERE u.status = 'Active' GROUP BY u.id ORDER BY u.firstname")
	return render_template('members_all.html', members=members)

@users.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('main.dashboard'))
	form = RegistrationForm()
	if request.method == 'GET':
		return render_template('register.html', title='Register for SIMS', form=form)
	else:
		if form.validate_on_submit():
			hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
			user = User(firstname=form.firstname.data, lastname=form.lastname.data, ns_id=form.ns_id.data.ns_go_id, email=form.email.data, password=hashed_password)
			db.session.add(user)
			db.session.commit()
			new_user_slack_alert("A new user has registered on the SIMS Portal. Please review {}'s registration in the <{}/admin_landing|admin area>.".format(user.firstname, current_app.config['ROOT_URL']))
			flash('Your account has been created.', 'success')
			return redirect(url_for('users.login'))
		else:
			flash('Please correct the errors in the registration form.', 'danger')
			return redirect(url_for('users.register'))
		return render_template('register.html', title='Register for SIMS', form=form)
	
@users.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if current_user.is_authenticated:
		return redirect(url_for('main.dashboard'))
	if request.method == 'GET':
		return render_template('login.html', title='Log into SIMS', form=form)
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
	else:
		flash('Login failed. Please check email and password', 'danger')
	return render_template('login.html', title='Log into SIMS', form=form)

@users.route('/logout')
def logout():
	logout_user()
	flash("You have been logged out.", "success")
	return redirect(url_for('users.login'))

@users.route('/profile')
@login_required
def profile():
	user_info = User.query.filter(User.id==current_user.id).first()
	try:
		ns_association = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.id==current_user.id).with_entities(NationalSociety.ns_name).first()[0]	
	except:
		ns_association = 'None' 
	try:
		assignment_history = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id==User.id).join(Emergency, Emergency.id==Assignment.emergency_id).filter(User.id==current_user.id, Emergency.emergency_status != 'Removed', Assignment.assignment_status != 'Removed').all()
		
	except:
		pass
	deployment_history_count = len(assignment_history)
	
	user_portfolio = get_full_portfolio(current_user.id)
	user_portfolio_size = len(user_portfolio)
	
	user_products = db.session.query(User, Portfolio).join(Portfolio, Portfolio.creator_id==User.id).where(or_(User.id==current_user.id, Portfolio.collaborator_ids.like(user_info.id))).filter(Portfolio.product_status != 'Removed').all()
	
	skills_list = db.engine.execute("SELECT * FROM user JOIN user_skill ON user.id = user_skill.user_id JOIN skill ON skill.id = user_skill.skill_id WHERE user.id=:current_user", {'current_user': current_user.id})
	
	languages_list = db.engine.execute("SELECT * FROM user JOIN user_language ON user.id = user_language.user_id JOIN language ON language.id = user_language.language_id WHERE user.id=:current_user", {'current_user': current_user.id})
	
	profile_picture = url_for('static', filename='assets/img/avatars/' + current_user.image_file)
	
	badges = db.engine.execute("SELECT * FROM user JOIN user_badge ON user_badge.user_id = user.id JOIN badge ON badge.id = user_badge.badge_id WHERE user.id=:current_user ORDER BY name", {'current_user': current_user.id})
	
	count_badges = db.engine.execute("SELECT count(*) as count FROM user JOIN user_badge ON user_badge.user_id = user.id JOIN badge ON badge.id = user_badge.badge_id WHERE user.id=:member_id ORDER BY name", {'member_id': current_user.id}).scalar()
	
	# highlight assignments for which end date has not passed (i.e. is active assignment)
	def convert_date_to_int(date):
		return 10000*date.year + 100*date.month + date.day
	today = date.today()
	today_int = convert_date_to_int(today)
	all_end_dates = []
	for end_date in assignment_history:
		all_end_dates.append(convert_date_to_int(end_date.Assignment.end_date))
	try:
		max_end = max(all_end_dates)
	except:
		pass

	return render_template('profile.html', title='Profile', profile_picture=profile_picture, ns_association=ns_association, user_info=user_info, assignment_history=assignment_history, deployment_history_count=deployment_history_count, user_portfolio=user_portfolio[:3], skills_list=skills_list, languages_list=languages_list, badges=badges, user_portfolio_size=user_portfolio_size, count_badges=count_badges)
	
@users.route('/profile/view/<int:id>')
def view_profile(id):
	user_info = User.query.filter(User.id==id).first()
	try:
		ns_association = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.id==id).with_entities(NationalSociety.ns_name).first()[0];
	except:
		ns_association = 'None' 
	try:
		assignment_history = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id==User.id).join(Emergency, Emergency.id==Assignment.emergency_id).filter(User.id==id, Emergency.emergency_status != 'Removed', Assignment.assignment_status != 'Removed').all()
	except:
		pass
	deployment_history_count = len(assignment_history)
	# show full portfolio if user is logged in
	if current_user.is_authenticated:
		user_portfolio = get_full_portfolio(id)
	# else show only products user has tagged as 'external'
	else:
		user_portfolio = get_full_portfolio(id)
	
	user_portfolio_size = len(user_portfolio)
	
	skills_list = db.engine.execute("SELECT * FROM user JOIN user_skill ON user.id = user_skill.user_id JOIN skill ON skill.id = user_skill.skill_id WHERE user.id=:member_id", {'member_id': id})
	
	languages_list = db.engine.execute("SELECT * FROM user JOIN user_language ON user.id = user_language.user_id JOIN language ON language.id = user_language.language_id WHERE user.id=:member_id", {'member_id': id})
	
	profile_picture = url_for('static', filename='assets/img/avatars/' + user_info.image_file)
	
	count_badges = db.engine.execute("SELECT count(*) as count FROM user JOIN user_badge ON user_badge.user_id = user.id JOIN badge ON badge.id = user_badge.badge_id WHERE user.id=:member_id ORDER BY name", {'member_id': id}).scalar()
	
	badges = db.engine.execute("SELECT * FROM user JOIN user_badge ON user_badge.user_id = user.id JOIN badge ON badge.id = user_badge.badge_id WHERE user.id=:member_id ORDER BY name", {'member_id': id})
	
	return render_template('profile_member.html', title='Member Profile', profile_picture=profile_picture, ns_association=ns_association, user_info=user_info, assignment_history=assignment_history, deployment_history_count=deployment_history_count, user_portfolio=user_portfolio[:3], user_portfolio_size=user_portfolio_size, skills_list=skills_list, languages_list=languages_list, count_badges=count_badges, badges=badges)

@users.route('/profile_edit', methods=['GET', 'POST'])
@login_required
def update_profile():
	form = UpdateAccountForm()
	try:
		ns_association = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.id==current_user.id).with_entities(NationalSociety.ns_name).first()[0]	
	except:
		ns_association = 'None'
	if form.validate_on_submit():
		if form.picture.data:
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file
		current_user.firstname = form.firstname.data
		current_user.lastname = form.lastname.data
		current_user.email = form.email.data
		current_user.job_title = form.job_title.data
		current_user.unit = form.unit.data
		try:
			current_user.ns_id = form.ns_id.data.ns_go_id
		except:
			pass
		current_user.bio = form.bio.data
		current_user.twitter = form.twitter.data
		current_user.slack_id = form.slack_id.data
		current_user.github = form.github.data
		current_user.linked_in = form.linked_in.data
		current_user.messaging_number_country_code = form.messaging_number_country_code.data
		current_user.messaging_number = form.messaging_number.data
		for skill in form.skills.data:
			current_user.skills.append(Skill.query.filter(Skill.name==skill).one())
		for language in form.languages.data:
			current_user.languages.append(Language.query.filter(Language.name==language).one())
		db.session.commit()
		flash('Your account has been updated!', 'success')
		return redirect(url_for('users.profile'))
	elif request.method == 'GET':
		form.firstname.data = current_user.firstname
		form.lastname.data = current_user.lastname
		form.email.data = current_user.email
		form.job_title.data = current_user.job_title
		form.unit.data = current_user.unit
		form.ns_id.data = current_user.ns_id
		form.bio.data = current_user.bio
		form.slack_id.data = current_user.slack_id
		form.github.data = current_user.github
		form.twitter.data = current_user.twitter
		form.linked_in.data = current_user.linked_in
		form.messaging_number_country_code.data = current_user.messaging_number_country_code
		form.messaging_number.data = current_user.messaging_number
	profile_picture = url_for('static', filename='assets/img/avatars/' + current_user.image_file)
	return render_template('profile_edit.html', title='Profile', profile_picture=profile_picture, form=form, ns_association=ns_association)

@users.route('/profile_edit/<int:id>', methods=['GET', 'POST'])
@login_required
def update_specified_profile(id):
	if current_user.is_admin == 1:
		form = UpdateAccountForm()
		this_user = db.session.query(User).filter(User.id==id).first()
		try:
			ns_association = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.id==id).with_entities(NationalSociety.ns_name).first()[0]	
		except:
			ns_association = 'None'
		if form.validate_on_submit():
			if form.picture.data:
				picture_file = save_picture(form.picture.data)
				this_user.image_file = picture_file
			this_user.firstname = form.firstname.data
			this_user.lastname = form.lastname.data
			this_user.email = form.email.data
			this_user.job_title = form.job_title.data
			try:
				this_user.ns_id = form.ns_id.data.ns_go_id
			except:
				pass
			this_user.bio = form.bio.data
			this_user.twitter = form.twitter.data
			this_user.github = form.github.data
			this_user.linked_in = form.linked_in.data
			this_user.slack_id = form.slack_id.data
			for skill in form.skills.data:
				this_user.skills.append(Skill.query.filter(Skill.name==skill).one())
			# this_user.roles = form.roles.data
			for language in form.languages.data:
				this_user.languages.append(Language.query.filter(Language.name==language).one())
			db.session.commit()
			flash("This user's account has been updated!", "success")
			return redirect(url_for('users.view_profile', id=id))
		elif request.method == 'GET':
			form.firstname.data = this_user.firstname
			form.lastname.data = this_user.lastname
			form.email.data = this_user.email
			form.job_title.data = this_user.job_title
			form.ns_id.data = this_user.ns_id
			form.bio.data = this_user.bio
			form.github.data = this_user.github
			form.twitter.data = this_user.twitter
			form.linked_in.data = this_user.linked_in
			form.slack_id.data = this_user.slack_id
		profile_picture = url_for('static', filename='assets/img/avatars/' + this_user.image_file)
		return render_template('profile_edit.html', title='Profile', profile_picture=profile_picture, form=form, ns_association=ns_association, current_user=this_user)
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
	
@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('main.dashboard'))
	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('An email has been sent with instructions to reset your password.', 'info')
		return redirect(url_for('users.login'))
	return render_template('reset_request.html', title='Reset Password', form=form)
	
@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.dashboard'))
	user = User.verify_reset_token(token)
	if user is None:
		flash('That is an invalid or expired token.', 'warning')
		return redirect(url_for('users.reset_request'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user.password = hashed_password
		db.session.commit()
		flash('Your password has been reset.', 'success')
		return redirect(url_for('users.login'))
	return render_template('reset_token.html', title='Reset Password', form=form)

@users.route('/user/approve/<int:id>', methods=['GET', 'POST'])
@login_required
def approve_user(id):
	approver_info = db.session.query(User).filter(User.id == current_user.id).first()
	check_slack_id = db.session.query(User).filter(User.id == id).first()
	if current_user.is_admin == 1 and check_slack_id.slack_id is not None:
		try:
			db.session.query(User).filter(User.id==id).update({'status':'Active'})
			db.session.commit()
			message = "Hi {}, your SIMS registration has been approved by {} {}. You now have full access to the SIMS Portal. I recommend logging in and updating your profile to help others learn more about you.".format(check_slack_id.firstname, approver_info.firstname, approver_info.lastname)
			user = check_slack_id.slack_id
			send_slack_dm(message, user)
			flash("Account approved.", 'success')
		except:
			flash("Error approving user. Check that the user ID exists.")
		return redirect(url_for('main.admin_landing'))
	elif current_user.is_admin == 1 and check_slack_id.slack_id is None:
		flash("User needs to have a Slack ID updated on their profile.","danger")
		return redirect(url_for('main.admin_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@users.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
	if current_user.id == id:
		try:
			db.session.query(User).filter(User.id==id).update({'status':'Removed'})
			db.session.commit()
			flash("Account deleted.", 'success')
		except:
			flash("Error deleting user. Check that the user ID exists.")
		return redirect(url_for('users.logout'))
	elif current_user.is_admin == 1:
		try:
			db.session.query(User).filter(User.id==id).update({'status':'Removed'})
			db.session.commit()
			flash("Account deleted.", 'success')
		except:
			flash("Error deleting user. Check that the user ID exists.")
		return redirect(url_for('main.admin_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403