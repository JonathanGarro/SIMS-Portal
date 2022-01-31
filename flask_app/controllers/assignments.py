from flask_app import app
from flask import render_template,redirect,session,request, flash, url_for
from flask_app.models import member, emergency, national_society, assignment, alert
from flask_wtf import FlaskForm
from datetime import datetime

@app.route('/new/assignment')
def new_assignment_page():
	countries = national_society.National_Society.get_all_national_societies()
	member_data = {
		'id': session['member_id']
	}
	this_member = member.Member.get_member_by_id_with_ns(member_data)
	active_members = member.Member.get_all_active_members()
	emergencies = emergency.Emergency.get_all_emergencies()
	return render_template('create_assignment.html', countries=countries, member=this_member, active_members=active_members, emergencies=emergencies)
	
@app.route('/create/assignment', methods=['POST'])
def create_assignment():
	if 'member_id' not in session:
		return redirect('/logout')
	
	data = {
		"role": request.form['role'],
		"start_date": request.form['start_date'],
		"end_date": request.form['end_date'],
		"emergency_id": request.form['emergency_id'],
		# "remote": request.form['remote'],
		"assignment_details": request.form['assignment_details'],
		"member_id": request.form['member_id']
	}
	id = assignment.Assignment.create_assignment(data)
	return redirect(url_for('view_assignment', id=id))
	
@app.route('/view/assignment/<int:id>')
def view_assignment(id):
	
	member_data = {
		"id": session['member_id']
	}
	# member = member.Member.get_member_by_id(member_data)
	
	this_assignment = {
		'id': id
	}
	this_member = member.Member.get_member_by_id(member_data)
	this_assignment_info = assignment.Assignment.get_assignment_with_member(this_assignment)
	countries = national_society.National_Society.get_all_national_societies()
	formatted_start_date = datetime.strptime(this_assignment_info['start_date'], '%Y-%m-%d').strftime('%d %b %Y')
	formatted_end_date = datetime.strptime(this_assignment_info['end_date'], '%Y-%m-%d').strftime('%d %b %Y')
	days_left = assignment.Assignment.count_assignment_days_remaining(this_assignment)
	assignment_length = assignment.Assignment.get_assignment_length(this_assignment)
	
	return render_template('view_assignment.html', countries=countries, assignment=this_assignment_info, member=this_member, formatted_start_date=formatted_start_date, formatted_end_date=formatted_end_date, days_left=days_left, assignment_length=assignment_length)