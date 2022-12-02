from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint, current_app
from SIMS_Portal import db
from SIMS_Portal.config import Config
from SIMS_Portal.models import User, Assignment, Emergency, NationalSociety, EmergencyType, Alert, Portfolio, Story, Learning, Review
from SIMS_Portal.emergencies.forms import NewEmergencyForm, UpdateEmergencyForm
from SIMS_Portal.assignments.utils import aggregate_availability
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import login_user, logout_user, current_user, login_required
from collections import Counter
from datetime import datetime
import json

emergencies = Blueprint('emergencies', __name__)

@emergencies.route('/emergencies/all')
@login_required
def view_all_emergencies():
	emergencies = db.engine.execute("SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, e.created_at, a.end_date, COUNT(a.id) as count_assignments, n.country_name, t.emergency_type_name FROM emergency e LEFT JOIN assignment a ON a.emergency_id = e.id LEFT JOIN nationalsociety n ON e.emergency_location_id = n.ns_go_id LEFT JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE e.emergency_status <> 'Removed' GROUP BY e.emergency_name")
	return render_template('emergencies_all.html', emergencies=emergencies)

@emergencies.route('/emergency/new', methods=['GET', 'POST'])
@login_required
def new_emergency():
	form = NewEmergencyForm()
	if form.validate_on_submit():
		emergency = Emergency(emergency_name=form.emergency_name.data, emergency_location_id=form.emergency_location_id.data.ns_go_id, emergency_type_id=form.emergency_type_id.data.emergency_type_go_id, emergency_glide=form.emergency_glide.data, emergency_go_id=form.emergency_go_id.data, activation_details=form.activation_details.data, slack_channel=form.slack_channel.data, dropbox_url=form.dropbox_url.data, trello_url=form.trello_url.data)
		db.session.add(emergency)
		db.session.commit()
		flash('New emergency successfully created.', 'success')
		return redirect(url_for('main.dashboard'))
	latest_emergencies = Emergency.get_latest_go_emergencies()
	return render_template('create_emergency.html', title='Create New Emergency', form=form, latest_emergencies=latest_emergencies)

@emergencies.route('/emergency/<int:id>', methods=['GET', 'POST'])
@login_required
def view_emergency(id):
	# aggregate reported availability if data exists, otherwise return hide chart variable for jinja filtering
	try:
		func_call = aggregate_availability(id)
		values = func_call[0]
		labels = func_call[1]
		kill_chart = False
	except:
		values = []
		labels = []
		kill_chart = True
	# get IDs of all this emergency's sims remote coordinators
	sims_co_ids = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == id, Assignment.role == 'SIMS Remote Coordinator').all()

	# loop through IDs to see if current user is one of the coordinators
	sims_co_list = []
	for coordinator in sims_co_ids:
		sims_co_list.append(coordinator.User.id)
	if current_user.id in sims_co_list:
		user_is_sims_co = True
	else:
		user_is_sims_co = False
	
	pending_products = db.session.query(Portfolio).filter(Portfolio.emergency_id == id, Portfolio.product_status == 'Pending Approval').all()
	deployments = db.session.query(Assignment, Emergency, User, NationalSociety).join(Emergency, Emergency.id==Assignment.emergency_id).join(User, User.id==Assignment.user_id).join(NationalSociety, NationalSociety.ns_go_id==User.ns_id).filter(Emergency.id==id, Assignment.assignment_status=='Active').order_by(User.firstname).all()
	emergency_info = db.session.query(Emergency, EmergencyType, NationalSociety).join(EmergencyType, EmergencyType.emergency_type_go_id == Emergency.emergency_type_id).join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id).filter(Emergency.id == id).first()
	emergency_portfolio_size = len(db.session.query(Portfolio, Emergency).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Emergency.id == id, Portfolio.product_status == 'Approved').all())
	emergency_portfolio = db.session.query(Portfolio, Emergency).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Emergency.id == id, Portfolio.product_status == 'Approved').limit(3).all()
	check_for_story = db.session.query(Story, Emergency).join(Emergency, Emergency.id == Story.emergency_id).filter(Story.emergency_id == id).first()

	learning_count = db.session.query(Learning, Assignment, Emergency).join(Assignment, Assignment.id == Learning.assignment_id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == id).count()

	learning_data = db.engine.execute("SELECT AVG(overall_score) as 'Overall', AVG(got_support) as 'Support', AVG(internal_resource) as 'Internal Resources', AVG(external_resource) as 'External Resources', AVG(clear_tasks) as 'Task Clarity', AVG(field_communication) as 'Field Communication', AVG(clear_deadlines) as 'Deadlines', AVG(coordination_tools) as 'Coordination Tools' FROM learning JOIN assignment ON assignment.id = learning.assignment_id JOIN emergency ON emergency.id = assignment.emergency_id WHERE emergency.id = {}".format(id))
	
	data_dict_learnings = [x._asdict() for x in learning_data]
	learning_keys = []
	learning_values = []
	for k, v in data_dict_learnings[0].items():
		learning_keys.append(k)
		learning_values.append(v)
	
	avg_learning_data = db.engine.execute("SELECT AVG(overall_score) as 'Overall', AVG(got_support) as 'Support', AVG(internal_resource) as 'Internal Resources', AVG(external_resource) as 'External Resources', AVG(clear_tasks) as 'Task Clarity', AVG(field_communication) as 'Field Communication', AVG(clear_deadlines) as 'Deadlines', AVG(coordination_tools) as 'Coordination Tools' FROM learning")
	
	data_dict_avg_learnings = [x._asdict() for x in avg_learning_data]
	avg_learning_keys = []
	avg_learning_values = []
	for k, v in data_dict_avg_learnings[0].items():
		avg_learning_keys.append(k)
		avg_learning_values.append(v)

	existing_reviews = db.session.query(Review).filter(Review.emergency_id == id).all()
	
	deployment_history_count = len(deployments)
	
	return render_template('emergency.html', title='Emergency View', emergency_info=emergency_info, deployments=deployments, emergency_portfolio=emergency_portfolio, check_for_story=check_for_story, learning_data=learning_data, learning_keys=learning_keys, learning_values=learning_values, learning_count=learning_count, avg_learning_keys=avg_learning_keys, avg_learning_values=avg_learning_values, deployment_history_count=deployment_history_count, user_is_sims_co=user_is_sims_co, pending_products=pending_products, emergency_portfolio_size=emergency_portfolio_size, values=values, labels=labels, kill_chart=kill_chart, existing_reviews=existing_reviews)

@emergencies.route('/emergency/edit/<int:id>', methods=['GET', 'POST'])
def edit_emergency(id):
	form = UpdateEmergencyForm()
	emergency_info = db.session.query(Emergency).filter(Emergency.id == id).first()
	# emergency_info = db.session.query(Emergency, EmergencyType).join(EmergencyType, EmergencyType.emergency_type_go_id==Emergency.emergency_type_id).filter(Emergency.id==id).first()
	if form.validate_on_submit():
		emergency_info.emergency_name = form.emergency_name.data
		try: 
			emergency_info.emergency_location_id = form.emergency_location_id.data.ns_go_id
		except:
			pass
		try:
			selected_id = form.emergency_type_id.data.emergency_type_go_id
			db.session.query(Emergency).filter(Emergency.id==id).update({'emergency_type_id':selected_id})
		except:
			pass
		try: 
			emergency_info.emergency_go_id = form.emergency_go_id.data
		except:
			pass
		emergency_info.emergency_glide = form.emergency_glide.data
		emergency_info.activation_details = form.activation_details.data
		emergency_info.slack_channel = form.slack_channel.data
		emergency_info.dropbox_url = form.dropbox_url.data
		emergency_info.trello_url = form.trello_url.data
		db.session.commit()
		flash('Emergency record updated!', 'success')
		return redirect(url_for('main.dashboard'))
	elif request.method == 'GET':
		form.emergency_name.data = emergency_info.emergency_name
		form.emergency_glide.data = emergency_info.emergency_glide
		form.emergency_go_id.data = emergency_info.emergency_go_id
		form.activation_details.data = emergency_info.activation_details
		form.slack_channel.data = emergency_info.slack_channel
		form.dropbox_url.data = emergency_info.dropbox_url
		form.trello_url.data = emergency_info.trello_url
	return render_template('emergency_edit.html', form=form, emergency_info=emergency_info)

@emergencies.route('/emergency/gantt/<int:id>', methods=['GET', 'POST'])
@login_required
def emergency_gantt(id):
	emergency_info = db.session.query(Emergency).filter(Emergency.id == id).first()
	assignments = db.session.query(Assignment, Emergency, User).join(Emergency, Emergency.id == Assignment.emergency_id).join(User, User.id == Assignment.user_id).filter(Emergency.id == id).with_entities(Assignment.start_date, Assignment.end_date, User.fullname).all()
	start_end_dates = []
	for dates in assignments:
		start_end_dates.append([dates.start_date.strftime('%Y-%m-%d'), dates.end_date.strftime('%Y-%m-%d')])
	member_labels = []
	for member in assignments:
		member_labels.append(member.fullname)
	if start_end_dates:
		min_date = min(start_end_dates)
		min_date = min_date[0]
	else: 
		min_date = '2000-01-01'
	return render_template('emergency_gantt.html', start_end_dates=start_end_dates, member_labels=member_labels, min_date=min_date, emergency_info=emergency_info)

@emergencies.route('/emergency/closeout/<int:id>')
@login_required
def closeout_emergency(id):
	if current_user.is_admin == 1:
		try:
			db.session.query(Emergency).filter(Emergency.id==id).update({'emergency_status':'Closed'})
			db.session.commit()
			flash("Emergency closed out.", 'success')
		except:
			flash("Error closing emergency. Check that the emergency ID exists.")
		return redirect(url_for('main.dashboard'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@emergencies.route('/emergency/delete/<int:id>')
@login_required
def delete_emergency(id):
	if current_user.is_admin == 1:
		try:
			db.session.query(Emergency).filter(Emergency.id==id).update({'emergency_status':'Removed'})
			db.session.commit()
			flash("Emergency deleted.", 'success')
		except:
			flash("Error deleting emergency. Check that the emergency ID exists.")
		return redirect(url_for('main.dashboard'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403