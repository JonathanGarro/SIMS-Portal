from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint, current_app
from SIMS_Portal.models import Assignment, User, Emergency, Portfolio
from SIMS_Portal.users.utils import send_slack_dm
from SIMS_Portal import db, login_manager
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, current_user, logout_user, login_required
from SIMS_Portal.assignments.forms import NewAssignmentForm, UpdateAssignmentForm
from datetime import datetime
from datetime import date, timedelta
import pandas as pd

assignments = Blueprint('assignments', __name__)

@assignments.route('/assignment/new', methods=['GET', 'POST'])
@login_required
def new_assignment():
	form = NewAssignmentForm()
	if form.validate_on_submit():
		assignment = Assignment(user_id=form.user_id.data.id, emergency_id=form.emergency_id.data.id, start_date=form.start_date.data, end_date=form.end_date.data, role=form.role.data, assignment_details=form.assignment_details.data, remote=form.remote.data)
		db.session.add(assignment)
		db.session.commit()
		flash('New assignment successfully created.', 'success')
		return redirect(url_for('main.dashboard'))
	return render_template('create_assignment.html', title='New Assignment', form=form)

@assignments.route('/assignment/new/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def new_assignment_from_disaster(dis_id):
	form = NewAssignmentForm()
	emergency_info = db.session.query(Emergency).filter(Emergency.id == dis_id).first()
	if form.validate_on_submit():
		assignment = Assignment(user_id=form.user_id.data.id, emergency_id=dis_id, start_date=form.start_date.data, end_date=form.end_date.data, role=form.role.data, assignment_details=form.assignment_details.data, remote=form.remote.data)
		db.session.add(assignment)
		db.session.commit()
		# attempt to send slack message to user after successful assignment creation
		try:
			this_user = db.session.query(User).filter(User.id == form.user_id.data.id).first()
			message = 'Hi {}, you have been assigned to the {} response operation in the SIMS Portal. Be sure to use the <{}/assignment/{}|Report Availability feature on your assignment> to help the SIMS Remote Coordinator better plan for coverage of important tasks! '.format(this_user.firstname, emergency_info.emergency_name, current_app.config['ROOT_URL'], str(assignment.id))
			send_slack_dm(message, this_user.slack_id)
		# skip slack message if slack is down or user doesn't have slack ID filled in
		except:
			pass
		flash('New assignment successfully created.', 'success')
		return redirect(url_for('main.dashboard'))
	return render_template('create_assignment_from_disaster.html', title='New Assignment', form=form, emergency_info=emergency_info)

@assignments.route('/assignment/<int:id>')
@login_required
def view_assignment(id):
	assignment_info = db.session.query(Assignment, User, Emergency).join(User).join(Emergency).filter(Assignment.id == id).first()
	dict_assignment = assignment_info.Assignment.__dict__
	dict_start_date = str(dict_assignment['start_date'])
	dict_end_date = str(dict_assignment['end_date'])
	
	formatted_start_date = datetime.strptime(dict_start_date, '%Y-%m-%d').strftime('%d %b %Y')
	formatted_end_date = datetime.strptime(dict_end_date, '%Y-%m-%d').strftime('%d %b %Y')
	
	days_left = db.engine.execute("SELECT JULIANDAY(:end_date) - JULIANDAY(DATE('now')) AS days_remaining FROM Assignment WHERE id = :id", {'id': id, 'end_date': dict_end_date})
	days_left_dict = days_left.mappings().first()
	days_left_int = int(days_left_dict['days_remaining'])

	assingment_length = db.engine.execute("SELECT JULIANDAY(:end_date) - JULIANDAY(:start_date) AS length FROM Assignment WHERE id = :id", {'id': id, 'end_date': dict_end_date, 'start_date': dict_start_date})
	assignment_length_dict = assingment_length.mappings().first()
	assignment_length_int = int(assignment_length_dict['length'])
	
	assingment_portfolio = db.session.query(Portfolio).filter(Portfolio.assignment_id==id, Portfolio.product_status != 'Removed').all()
	count_assignment_portfolio = len(assingment_portfolio)
	
	# get availability if reported and convert to list, else return empty list
	if assignment_info.Assignment.availability:
		assignment_availability = assignment_info.Assignment.availability
		remove_brackets = assignment_availability.replace('[','').replace(']','').replace("'",'')
		available_dates = remove_brackets.split(', ')

		# available_dates = []
		# for date in dates:
		# 	available_dates.append(datetime.strptime(date,'%Y-%m-%d').strftime('%b %d'))
	else:
		available_dates = []
		
	return render_template('assignment_view.html', assignment_info=assignment_info, formatted_start_date=formatted_start_date, formatted_end_date=formatted_end_date, days_left_int=days_left_int, assignment_length_int=assignment_length_int, assingment_portfolio=assingment_portfolio, available_dates=available_dates, count_assignment_portfolio=count_assignment_portfolio)

@assignments.route('/assignment/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_assignment(id):
	assignment_info = db.session.query(Assignment, User, Emergency).join(User).join(Emergency).filter(Assignment.id == id).first()
	form = UpdateAssignmentForm(role=assignment_info.Assignment.role, start_date=assignment_info.Assignment.start_date, end_date=assignment_info.Assignment.end_date, assignment_details=assignment_info.Assignment.assignment_details)
	# get basic info about this assignment
	this_assignment = db.session.query(Assignment).filter(Assignment.id==id).first()
	if form.validate_on_submit():
		this_assignment.role = form.role.data
		this_assignment.start_date = form.start_date.data
		this_assignment.end_date = form.end_date.data
		this_assignment.assignment_details = form.assignment_details.data
		db.session.commit()
		flash('Assignment record updated!', 'success')
		return redirect(url_for('assignments.view_assignment', id=this_assignment.id))
	
	return render_template('assignment_edit.html', form=form, assignment_info=assignment_info)

@assignments.route('/assignment/delete/<int:id>')
@login_required
def delete_assignment(id):
	if current_user.is_admin == 1 or current_user.id == id:
		try:
			db.session.query(Assignment).filter(Assignment.id==id).update({'assignment_status':'Removed'})
			db.session.commit()
			flash("Assignment deleted.", 'success')
		except:
			flash("Error deleting assignment. Check that the assignment ID exists.")
		return redirect(url_for('main.dashboard'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
	
@assignments.route('/assignment/availability/<int:assignment_id>/<start>/<end>', methods=['GET', 'POST'])
@login_required
def assignment_availability(assignment_id, start, end):
	assignment_info = db.session.query(Assignment, User, Emergency).join(User).join(Emergency).filter(Assignment.id == assignment_id).first()
	
	dict_assignment = assignment_info.Assignment.__dict__
	dict_start_date = str(dict_assignment['start_date'])
	dict_end_date = str(dict_assignment['end_date'])
	
	formatted_start_date = datetime.strptime(dict_start_date, '%Y-%m-%d').strftime('%d %b %Y')
	formatted_end_date = datetime.strptime(dict_end_date, '%Y-%m-%d').strftime('%d %b %Y')
	
	days_left = db.engine.execute("SELECT JULIANDAY(:end_date) - JULIANDAY(DATE('now')) AS days_remaining FROM Assignment WHERE id = :id", {'id': assignment_id, 'end_date': dict_end_date})
	days_left_dict = days_left.mappings().first()
	days_left_int = int(days_left_dict['days_remaining'])
	
	assingment_length = db.engine.execute("SELECT JULIANDAY(:end_date) - JULIANDAY(:start_date) AS length FROM Assignment WHERE id = :id", {'id': assignment_id, 'end_date': dict_end_date, 'start_date': dict_start_date})
	assignment_length_dict = assingment_length.mappings().first()
	assignment_length_int = int(assignment_length_dict['length'])
	
	start_date = datetime.strptime(start, "%Y-%m-%d")
	end_date = datetime.strptime(end, "%Y-%m-%d")
	def daterange(start_date, end_date):
		for n in range(int((end_date - start_date).days)):
			yield start_date + timedelta(n)

	start_day_of_week = pd.Timestamp(start_date)
	
	date_list = []
	for single_date in daterange(start_date, end_date):
		date_list.append(single_date.strftime("%Y-%m-%d"))
		
	index_list = []
	index = len(date_list)
	for x in range(index):
		index_list.append(x)
	output = dict(list(enumerate(date_list, 1)))
	
	return render_template('/assignment_availability.html', date_list=date_list, assignment_id=assignment_id, assignment_info=assignment_info, days_left_int=days_left_int, assignment_length_int=assignment_length_int, formatted_start_date=formatted_start_date, formatted_end_date=formatted_end_date)

@assignments.route('/assignment/availability/result', methods=['GET', 'POST'])
@login_required
def assignment_availability_result():
	response = request.form.getlist('available')
	response_formatted = "{}".format(response)
	assignment_id = request.form.get('assignment_id')
	db.session.query(Assignment).filter(Assignment.id==assignment_id).update({'availability': response_formatted})
	db.session.commit()
	user_info = db.session.query(User).filter(User.id == current_user.id).first()
	# try sending message if user has slack ID filled in
	try:
		message = 'Hi {}, you have successfully updated your availability!'.format(user_info.firstname)
		send_slack_dm(message, user_info.slack_id)
	# skip slack message if slack is down or user doesn't have slack ID filled in
	except:
		pass
	return redirect(url_for('assignments.view_assignment', id=assignment_id))