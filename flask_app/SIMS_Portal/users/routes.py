import logging
from datetime import datetime, date

import pytz
from flask import (
	request, render_template, url_for, flash, redirect,
	jsonify, Blueprint, current_app, session
)
from flask_login import (
	login_user, logout_user, current_user, login_required
)
from flask_mail import Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, Integer, text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import flag_modified

from SIMS_Portal import db, bcrypt
from SIMS_Portal.models import (
	User, Assignment, Emergency, NationalSociety, Portfolio,
	EmergencyType, Skill, Language, user_skill, user_language,
	Badge, Alert, user_badge, Profile, user_profile, Log, user_language
)
from SIMS_Portal.users.forms import (
	RegistrationForm, LoginForm, UpdateAccountForm,
	RequestResetForm, ResetPasswordForm, AssignProfileTypesForm,
	UserLocationForm
)
from SIMS_Portal.users.utils import (
	save_picture, new_user_slack_alert, send_slack_dm,
	check_valid_slack_ids, send_reset_slack, search_location,
	update_member_locations, update_robots_txt, set_user_active
)
from SIMS_Portal.portfolios.utils import get_full_portfolio
from SIMS_Portal.users.utils import download_profile_photo, invite_user_to_github
from SIMS_Portal.main.utils import send_error_message

users = Blueprint('users', __name__)

@users.route('/members')
def members():
	page = request.args.get('page', 1, type = int)
	per_page = 24
	
	members_query = db.session.query(User).filter(
		and_(
			User.status == 'Active',
			or_(User.private_profile.is_(None), User.private_profile == False)
		)
	).order_by(User.id)
	
	members = members_query.paginate(page = page, per_page = per_page)
	return render_template('members.html', members=members)

@users.route('/members/inactive')
def inactive_members():
	page = request.args.get('page', 1, type = int)
	per_page = 24
	members_query = db.session.query(User).filter(
		and_(
			User.status == 'Inactive',
			or_(User.private_profile.is_(None), User.private_profile == False)
		)
	).order_by(User.id)
	members = members_query.paginate(page = page, per_page = per_page)
	return render_template('members_inactive.html', members=members)

@users.route('/members/all') 
@login_required
def members_all(): 
	language_alias = aliased(Language)
	skill_alias = aliased(Skill)
	profile_alias = aliased(Profile)
	
	members = db.session.query(
		User.id,
		User.firstname,
		User.lastname,
		User.status,
		User.email,
		User.job_title,
		User.slack_id,
		User.ns_id,
		User.image_file,
		NationalSociety.ns_name,
		func.string_agg(func.distinct(Language.name), ', ').label('languages'),
		func.string_agg(func.distinct(Skill.name), ', ').label('skills'),
		func.string_agg(func.distinct(Profile.name), ', ').label('profiles')
	).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id
	).outerjoin(user_language, user_language.c.user_id == User.id
	).outerjoin(Language, Language.id == user_language.c.language_id
	).outerjoin(user_profile, user_profile.c.user_id == User.id
	).outerjoin(Profile, Profile.id == user_profile.c.profile_id
	).outerjoin(user_skill, user_skill.c.user_id == User.id
	).outerjoin(Skill, Skill.id == user_skill.c.skill_id
	).filter(User.status.in_(['Active', 'Inactive'])
	).group_by(User.id, NationalSociety.ns_name
	).order_by(User.firstname
	).all()
	
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
			# check that slack id not already associated with an existing member
			existing_users_slack_ids = db.session.query(User).with_entities(User.slack_id).filter(User.slack_id != None).all()
			list_ids_to_check = []
			for id in existing_users_slack_ids:
				list_ids_to_check.append(id.slack_id)
			if form.slack_id.data in list_ids_to_check:
				flash('This Slack ID is already associated with a registered member.', 'danger')
				return render_template('register.html', title='Register for SIMS', form=form)
			
			# ping Slack API to get list of all members' ID, then compare form data to validate that user has entered valid ID
			try:
				slack_check = check_valid_slack_ids(form.slack_id.data)
			except:
				flash('Slack API is not responsive. Please contact a SIMS Portal administrator to complete registration.', 'danger')
				return render_template('register.html', title='Register for SIMS', form=form)
			if slack_check == False:
				flash('This Slack ID is not valid and does not belong to any existing SIMS Slack accounts.', 'danger')
				return render_template('register.html', title='Register for SIMS', form=form)
			else:
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				user = User(
					firstname=form.firstname.data, 
					lastname=form.lastname.data, 
					ns_id=form.ns_id.data.ns_go_id, 
					slack_id=form.slack_id.data, 
					email=form.email.data, 
					password=hashed_password)
				db.session.add(user)
				db.session.commit()
				message = "Thank you for registering for the SIMS Portal, {}. Your account has been placed into a queue, and will be approved by a SIMS Governance Committee member. You will be alerted here when that action is taken. In the meantime, you can log into the portal and explore the resources, but you will have limited permissions.".format(form.firstname.data)
				send_slack_dm(message, form.slack_id.data)
				new_user_slack_alert("A new user has registered on the SIMS Portal. Please review {}'s registration in the <{}/admin/approve_members|admin area>.".format(user.firstname, current_app.config['ROOT_URL']))
				flash('Your account has been created.', 'success')
				
				log_message = f"[INFO] A new user has registered for the Portal: {user.firstname} {user.lastname}."
				new_log = Log(message=log_message, user_id=0)
				db.session.add(new_log)
				db.session.commit()
				
				return redirect(url_for('users.login'))
		else:
			flash('Please correct the errors in the registration form.', 'danger')
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
			
			# reset user to active if they were previously inactive
			if user.status == 'Inactive':
				set_user_active(user.id)
				log_message = f"[INFO] User {user.id} was marked as active after logging back in."
				new_log = Log(message=log_message, user_id=user.id)
				db.session.add(new_log)
				db.session.commit()
				flash('Your account has been converted back to active!', 'success')
			
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			
			log_message = f"[INFO] User {current_user.id} logged in."
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			
			return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
		else:
			flash('Login failed. Please check email and password', 'danger')
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
	
	deployment_history_count = len(set(emergency.id for _, _, emergency in assignment_history))	
	
	user_portfolio = get_full_portfolio(current_user.id)
	user_portfolio_size = len(user_portfolio)
	
	user_products = db.session.query(User, Portfolio).join(Portfolio, Portfolio.creator_id==User.id).where(or_(User.id==current_user.id, Portfolio.collaborator_ids.like(str(user_info.id)))).filter(Portfolio.product_status != 'Removed').all()
	
	skills_list = db.engine.execute(text('SELECT * FROM "user" JOIN user_skill ON "user".id = user_skill.user_id JOIN skill ON skill.id = user_skill.skill_id WHERE "user".id=:current_user'), {'current_user': current_user.id})
	
	qualifying_profile_list_query = text("""
		SELECT profile.image, profile.name
		FROM user_profile
		JOIN profile ON profile.id = user_profile.profile_id
		JOIN (
			SELECT p.name AS name, MAX(up.tier) AS tier
			FROM user_profile up
			JOIN profile p ON p.id = up.profile_id
			WHERE up.user_id = :user_id
			GROUP BY p.name
		) highest_for_user ON profile.name = highest_for_user.name AND user_profile.tier = highest_for_user.tier
		WHERE user_profile.user_id = :user_id
	""")
	
	qualifying_profile_list = db.engine.execute(qualifying_profile_list_query, user_id=user_info.id).fetchall()
	qualifying_profile_count = db.engine.execute(qualifying_profile_list_query, user_id=user_info.id).scalar()
	
	languages_list = db.engine.execute(text('SELECT * FROM "user" JOIN user_language ON "user".id = user_language.user_id JOIN language ON language.id = user_language.language_id WHERE "user".id=:current_user'), {'current_user': current_user.id})
	
	profile_picture = '/uploads/' + current_user.image_file
	
	badges = db.engine.execute('SELECT * FROM "user" JOIN user_badge ON user_badge.user_id = "user".id JOIN badge ON badge.id = user_badge.badge_id WHERE "user".id={} ORDER BY name LIMIT 4'.format(current_user.id))
	
	count_badges = db.engine.execute(text("SELECT count(user_id) as count FROM user_badge WHERE user_id = :user_id"), {'user_id': current_user.id}).scalar()

	return render_template('profile.html', title='Profile', profile_picture=profile_picture, ns_association=ns_association, user_info=user_info, assignment_history=assignment_history, deployment_history_count=deployment_history_count, user_portfolio=user_portfolio[:3], skills_list=skills_list, languages_list=languages_list, badges=badges, user_portfolio_size=user_portfolio_size, count_badges=count_badges, qualifying_profile_list=qualifying_profile_list, qualifying_profile_count=qualifying_profile_count)
	
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
		
	deployment_history_count = len(set(emergency.id for _, _, emergency in assignment_history))	
	
	# show full portfolio if user is logged in
	if current_user.is_authenticated:
		user_portfolio = get_full_portfolio(id)
	# else show only products user has tagged as 'external'
	else:
		user_portfolio = get_full_portfolio(id)
	
	user_portfolio_size = len(user_portfolio)
	
	skills_list = db.engine.execute(text('SELECT * FROM "user" JOIN user_skill ON "user".id = user_skill.user_id JOIN skill ON skill.id = user_skill.skill_id WHERE "user".id = :member_id'), {'member_id': id})
	
	languages_list = db.engine.execute(text('SELECT * FROM "user" JOIN user_language ON "user".id = user_language.user_id JOIN language ON language.id = user_language.language_id WHERE "user".id=:member_id'), {'member_id': id})
	
	qualifying_profile_list_query = text("""
		SELECT profile.image, profile.name
		FROM user_profile
		JOIN profile ON profile.id = user_profile.profile_id
		JOIN (
			SELECT p.name AS name, MAX(up.tier) AS tier
			FROM user_profile up
			JOIN profile p ON p.id = up.profile_id
			WHERE up.user_id = :user_id
			GROUP BY p.name
		) highest_for_user ON profile.name = highest_for_user.name AND user_profile.tier = highest_for_user.tier
		WHERE user_profile.user_id = :user_id
	""")
	
	qualifying_profile_list = db.engine.execute(qualifying_profile_list_query, user_id=id).fetchall()
	qualifying_profile_count = db.engine.execute(qualifying_profile_list_query, user_id=id).scalar()
	
	profile_picture = '/uploads/' + user_info.image_file
	
	count_badges = db.engine.execute(text('SELECT count(*) as count FROM "user" JOIN user_badge ON user_badge.user_id = "user".id JOIN badge ON badge.id = user_badge.badge_id WHERE "user".id=:member_id'), {'member_id': id}).scalar()
	
	badges = db.engine.execute(text('SELECT * FROM "user" JOIN user_badge ON user_badge.user_id = "user".id JOIN badge ON badge.id = user_badge.badge_id WHERE "user".id=:member_id ORDER BY name LIMIT 4'), {'member_id': id})
	
	return render_template('profile_member.html', title='Member Profile', profile_picture=profile_picture, ns_association=ns_association, user_info=user_info, assignment_history=assignment_history, deployment_history_count=deployment_history_count, user_portfolio=user_portfolio[:3], user_portfolio_size=user_portfolio_size, skills_list=skills_list, languages_list=languages_list, count_badges=count_badges, badges=badges, qualifying_profile_list=qualifying_profile_list, qualifying_profile_count=qualifying_profile_count)

@users.route('/assign_profiles/<int:user_id>/<int:profile_id>/<int:tier>', methods=['GET', 'POST'])
@login_required
def assign_profiles(user_id, profile_id, tier):
	if current_user.is_admin == 1:
		try:
			# delete user's existing profiles at other tiers
			user_profile_table = db.Table('user_profile', db.metadata, autoload=True, autoload_with=db.engine)
			delete_condition = db.and_(
				user_profile_table.c.user_id == user_id,
				user_profile_table.c.profile_id == profile_id,
				user_profile_table.c.tier != tier
			)
			db.session.execute(user_profile_table.delete().where(delete_condition))
			db.session.commit()
		
			# insert the new profile for the user
			new_profile = user_profile_table.insert().values(user_id=user_id, profile_id=profile_id, tier=tier)
			db.session.execute(new_profile)
			db.session.commit()
			
			log_message = f"[INFO] A new profile has been assigned to {user_id} by {current_user.id}: Profile id: {profile_id} at tier {tier}."
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			
			flash('User has been assigned a new profile.', 'success')
			return redirect(url_for('main.admin_manage_profiles'))
		except Exception as e:
			log_message = f"[ERROR] Error assigning a new profile tier to user {user_id}: {e}."
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			send_error_message(log_message)
			
			return redirect(url_for('main.admin_manage_profiles'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@users.route('/badges_more/<int:user_id>')
@login_required
def view_all_user_badges(user_id):
	this_user = db.session.query(User).filter(User.id == user_id).first()
	
	all_user_badges = db.engine.execute(text('SELECT firstname, lastname, assigner_justify, b.id as badge_id, b.name as badge_name, b.badge_url as badge_url FROM "user" JOIN user_badge ON user_badge.user_id = "user".id JOIN badge b ON b.id = user_badge.badge_id WHERE "user".id=:user_id ORDER BY name'), {'user_id': user_id})
	
	list_badges = []
	for badge in all_user_badges:
		temp_dict = {}
		temp_dict['firstname'] = badge.firstname
		temp_dict['lastname'] = badge.lastname
		temp_dict['assigner_justify'] = badge.assigner_justify
		temp_dict['name'] = badge.badge_name
		temp_dict['badge_id'] = badge.badge_id
		temp_dict['badge_url'] = badge.badge_url
		list_badges.append(temp_dict)
	
	return render_template('badges_more.html', list_badges = list_badges, this_user = this_user)

@users.route('/support_profiles/<int:user_id>')
@login_required
def view_all_user_profiles(user_id):
	this_user = db.session.query(User).filter(User.id == user_id).first()
	
	qualifying_profile_list = db.engine.execute(text('SELECT profile.image, user_profile.tier FROM user_profile JOIN profile ON profile.id = user_profile.profile_id JOIN ('
		'SELECT p.name AS name, MAX(up.tier) AS tier FROM user_profile up JOIN profile p ON p.id = up.profile_id WHERE up.user_id = :user_id GROUP BY p.name'
	') highest_for_user ON profile.name = highest_for_user.name AND user_profile.tier = highest_for_user.tier WHERE user_profile.user_id = :user_id'), {'user_id': user_id})
	
	list_profiles = []
	for profile in qualifying_profile_list:
		temp_dict = {}
		temp_dict['image'] = profile.image
		temp_dict['tier'] = profile.tier
		list_profiles.append(temp_dict)
	
	return render_template('support_profile_details.html', list_profiles = list_profiles, this_user = this_user)

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
		current_user.linked_in = form.linked_in.data
		current_user.messaging_number_country_code = form.messaging_number_country_code.data
		current_user.messaging_number = form.messaging_number.data
		current_user.private_profile = form.private_profile.data
		
		# update robots.txt with user profile info if they want it to be private
		if form.private_profile.data: 
			update_robots_txt(current_user.id, disallow=True)
		else:
			update_robots_txt(current_user.id, disallow=False)
		
		# Check for GitHub username update before setting current_user.github
		if form.github.data != current_user.github:
			current_user.github = form.github.data
			invite_user_to_github(form.github.data)
		else:
			current_user.github = form.github.data

		# look for new skills added in the edit page
		for skill_name in form.skills.data:
			skill = Skill.query.filter(Skill.name == skill_name).first()
			if skill:
				current_user.skills.append(skill)
		
		# remove skills that are not in the updated list
		skills_to_remove = [skill for skill in current_user.skills if skill.name not in form.skills.data]
		for skill in skills_to_remove:
			current_user.skills.remove(skill)
			
		# look for new languages added in the edit page
		for language_name in form.languages.data:
			language = Language.query.filter(Language.name == language_name).first()
			if language:
				current_user.languages.append(language)
		
		# remove languages that are not in the updated list
		languages_to_remove = [language for language in current_user.languages if language.name not in form.languages.data]
		for language in languages_to_remove:
			current_user.languages.remove(language)

		db.session.commit()
		flash('Your account has been updated!', 'success')
		
		log_message = f"[INFO] User {current_user.id} successfully updated their their profile."
		new_log = Log(message=log_message, user_id=current_user.id)
		db.session.add(new_log)
		db.session.commit()
		
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
		form.private_profile.data = current_user.private_profile
		
		skill_names = [skill.name for skill in current_user.skills]
		language_names = [language.name for language in current_user.languages]
		
		selected_skill_names = [skill.name for skill in current_user.skills]
		selected_language_names = [language.name for language in current_user.languages]
		
		form.skills.data = skill_names
		form.languages.data = language_names

	profile_picture = '/uploads/' + current_user.image_file
	
	skills_list = db.engine.execute(text('SELECT * FROM "user" JOIN user_skill ON "user".id = user_skill.user_id JOIN skill ON skill.id = user_skill.skill_id WHERE "user".id=:current_user'), {'current_user': current_user.id})
	
	return render_template('profile_edit.html', title='Profile', profile_picture=profile_picture, form=form, ns_association=ns_association, skills_list=skills_list, selected_skill_names=selected_skill_names, selected_language_names=selected_language_names)

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
		profile_picture = '/uploads/' + this_user.image_file
		return render_template('profile_edit.html', title='Profile', profile_picture=profile_picture, form=form, ns_association=ns_association, current_user=this_user)
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@users.route('/delete_skill/<int:user_id>/<int:skill_id>', methods=['GET', 'POST'])
@login_required
def delete_skill(user_id, skill_id):
	if current_user.id == user_id:
		db.session.query(user_skill).filter(user_skill.c.user_id == user_id, user_skill.c.skill_id == skill_id).delete()
		db.session.commit()
		flash('Successfully removed skill.', 'success')
		return redirect(url_for('users.update_profile'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@users.route('/save_work_location/<int:user_id>', methods=['GET', 'POST'])
def save_user_location(user_id):
	form = UserLocationForm()
	if request.method == 'GET':
		return render_template('save_work_location.html', form=form)
	if request.method == 'POST':
		if form.validate_on_submit():
			if current_user.is_admin == 1 or current_user.id == user_id:
				location_query = form.location.data
				try:
					found_location = search_location(location_query)
					latitude = found_location[0]
					longitude = found_location[1]
					place_label = found_location[2]
					time_zone = found_location[3]
					# remove spaces for Google Maps API
					converted_location = location_query.replace(' ', '+')
					# put results into session to pass to /confirm_work_location/ route
					session['coordinates'] = [latitude, longitude]
					session['time_zone'] = time_zone
					session['place_label'] = place_label
					google_token = current_app.config['GOOGLE_MAPS_TOKEN']
					query_url = 'https://www.google.com/maps/embed/v1/place?key={}&q={}'.format(google_token, converted_location)
					return render_template('validate_location.html', query_url=query_url, user_id=user_id)
				except Exception as e:
					flash('The PositionStack API is not responsive. Please try again later.', 'warning')
					
					log_message = f"[ERROR] PositionStack API call failed: {e}."
					new_log = Log(message=log_message, user_id=current_user.id)
					db.session.add(new_log)
					db.session.commit()
					send_error_message(log_message)
					
					return redirect(url_for('users.profile'))
			else:
				flash("You are not allowed to edit other people's location.", "danger")
				return redirect(url_for('users.save_user_location', user_id = user_id))
		else:
			return redirect('users.save_user_location')

@users.route('/confirm_work_location/<int:user_id>', methods=['GET', 'POST'])
def confirm_user_location(user_id):
	user_info = db.session.query(User).filter(User.id == user_id).first()
	coordinates = session.get('coordinates', None)
	place_label = session.get('place_label', None)
	time_zone = session.get('time_zone', None)
	if current_user.is_admin == 1 or current_user.id == user_id:
		db.session.query(User).filter(User.id==user_id).update({'coordinates':str(coordinates), 'place_label':place_label, 'time_zone': time_zone})
		db.session.commit()
		flash("You've successfully saved your location!", "success")
		
		log_message = f"[INFO] User {user_info.id} has updated their location."
		new_log = Log(message=log_message, user_id=current_user.id)
		db.session.add(new_log)
		db.session.commit()
		
		update_member_locations()
		return redirect(url_for('users.profile'))
	else:
		flash('You are not allowed to edit other the locations of other users.', 'danger')
		return redirect('users.save_user_location', user_id = user_id)
		
@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
	form = RequestResetForm()
	valid_slack_ids = db.session.query(User).all()
	list_slack_ids = []
	for id in valid_slack_ids:
		list_slack_ids.append(id.slack_id)

	if form.validate_on_submit():
		user = User.query.filter(User.slack_id == form.slack_id.data).first()
		if user is None:
			# user not found, flash message and return
			flash("That Slack ID does not match any existing users. Contact a Portal administrator if you continue having issues locating your ID.", 'danger')
			return redirect('/reset_password')

		if user.is_active:  
			send_reset_slack(user) 
			log_message = f"[INFO] User {user.id} (Slack ID: {user.slack_id}) has requested a password reset."
			new_log = Log(message=log_message, user_id=user.id)
			db.session.add(new_log)
			db.session.commit()
			flash('A Slack message has been sent with instructions to reset your password.', 'info')
			return redirect(url_for('users.login'))
		else:
			# user account inactive, flash message and return
			flash('Your account is currently inactive. Please contact a Portal administrator to activate your account.', 'warning')
			return redirect('/reset_password')

	elif request.method == 'GET':
		if current_user.is_authenticated:
			form.slack_id.data = current_user.slack_id
		else:
			form.slack_id.data = ''
	return render_template('reset_request.html', title='Reset Password', form=form)

@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
	user = User.verify_reset_token(token)
	if user is None:
		flash('That is an invalid or expired token.', 'warning')
		return redirect(url_for('users.reset_request'))

	form = ResetPasswordForm()
	new_log = None 
	if form.validate_on_submit():
		try:
			hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
			user.password = hashed_password
			db.session.commit()
			
			flash('Your password has been reset. Please login with your new password.', 'success')
			return redirect(url_for('users.login'))
			
		except Exception as e:
			log_message = f"[Error] The reset_token() route failed: {e}"
			new_log = Log(message=log_message, user_id=63)
			db.session.rollback()
		finally:
			if new_log:  # check if new_log has been assigned a value
				db.session.add(new_log)
				db.session.commit()

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
			
			log_message = f"[INFO] The registration request for user {id} has been approved."
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			
			flash("Account approved.", 'success')
		except:
			flash("Error approving user. Check that the user ID exists.")
		return redirect(url_for('main.admin_approve_members'))
	elif current_user.is_admin == 1 and check_slack_id.slack_id is None:
		flash("User needs to have a Slack ID updated on their profile.","danger")
		return redirect(url_for('main.admin_approve_members'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@users.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
	if current_user.id == id:
		try:
			db.session.query(User).filter(User.id==id).update({'status':'Removed'})
			db.session.commit()
			flash("Account deleted.", 'success')
			
			log_message = f"[WARNING] User {current_user.id} deleted their profile."
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			send_error_message(log_message)
			
		except:
			flash("Error deleting user. Check that the user ID exists.")
		return redirect(url_for('users.logout'))
	elif current_user.is_admin == 1:
		try:
			db.session.query(User).filter(User.id==id).update({'status':'Removed'})
			db.session.commit()
			flash("Account deleted.", 'success')
			
			log_message = f"[WARNING] Admin user {current_user.id} deleted user {id}'s profile."
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			send_error_message(log_message)
			
		except:
			flash("Error deleting user. Check that the user ID exists.")
		return redirect(url_for('main.admin_approve_members'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@users.route('/user/save_slack_photo/<int:user_id>')
@login_required
def save_slack_photo_to_profile(user_id):
	if current_user.id == user_id or current_user.is_admin == 1:
		try:
			user_info = db.session.query(User).filter(User.id == user_id).first()
			download_profile_photo(user_info.slack_id)
			flash('Your profile has been updated with your Slack photo!', 'success')
			
			log_message = f"[INFO] User {current_user.id} successfully updated their their profile photo with their Slack photo."
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			
			return redirect(url_for("users.profile"))
		except Exception as e:
			
			log_message = f"[ERROR] User {current_user.id} tried to download their Slack photo but failed: {e}"
			new_log = Log(message=log_message, user_id=current_user.id)
			db.session.add(new_log)
			db.session.commit()
			send_error_message(log_message)
			
			flash('There was an error trying to download your photo. Please try again later or contact an administrator.', 'danger')
			return redirect(url_for("users.profile"))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
		
@users.route('/api/users', methods=['GET'])
def api_get_users():
	status_param = request.args.get('status')  
	
	if status_param:
		users = db.session.query(User).filter_by(status=status_param).order_by(User.id).all()
	else:
		users = db.session.query(User).order_by(User.id).all()
	
	result = [
		{
			'id': user.id, 
			'first_name': user.firstname, 
			'last_name': user.lastname, 
			'email': user.email, 
			'title': user.job_title, 
			'slack': user.slack_id, 
			'ns_id': user.ns_id, 
			'location': user.place_label, 
			'time_zone': user.time_zone, 
			'admin': user.is_admin, 
			'status': user.status} 
		for user in users
	]
	
	return jsonify(result)