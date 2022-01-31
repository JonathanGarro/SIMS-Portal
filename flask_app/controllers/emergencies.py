from flask import render_template,redirect,session,request, flash, url_for
from flask_app import app
from flask_app.models.emergency import Emergency
from flask_app.models.member import Member
from flask_app.models.national_society import National_Society
from flask_app.models.assignment import Assignment


@app.route('/new/emergency')
def create_emergency_page():
	if 'member_id' not in session:
		return redirect('/logout')
	member_data = {
		"id":session['member_id']
	}
	
	member = Member.get_member_by_id(member_data)
	countries = National_Society.get_all_national_societies()
	
	return render_template('create_emergency.html', member=member, countries=countries)

@app.route('/create/emergency', methods=['GET','POST'])
def new_emergency():
	if 'member_id' not in session:
		return redirect('/logout')
	
	member_data = {
		"id":session['member_id']
	}
	
	member = Member.get_member_by_id(member_data)
	
	data = {
		"emergency_name": request.form['emergency_name'],
		"emergency_type_id": request.form['emergency_type_id'],
		"emergency_glide": request.form['emergency_glide'],
		"emergency_go_id": request.form['emergency_go_id'],
		"emergency_location_id": request.form['emergency_location_id'],
		"activation_details": request.form['activation_details']
	}
	# 
	# if not member.is_admin == 1:
	# 	return redirect('/dashboard')
	
	id = Emergency.save_emergency(data)
	print(f"THIS NEW EMERGENCY'S ID IS: {id}")
	
	return redirect(url_for('view_emergency', id=id))

@app.route('/view/emergency/<int:id>')
def view_emergency(id):
	
	member_data = {
		"id": session['member_id']
	}
	member = Member.get_member_by_id(member_data)
	
	this_emergency = {
		'id': id
	}
	emergency = Emergency.get_one_emergency(this_emergency)
	countries = National_Society.get_all_national_societies()
	assignments = Assignment.get_all_assignments_by_emergency(this_emergency)
	return render_template('view_emergency.html', emergency=emergency, member=member, countries=countries, assignments=assignments)

@app.route('/edit/emergency/<int:id>')
def edit_emergency(id):
	member_data = {
		"id": session['member_id']
	}
	member = Member.get_member_by_id(member_data)
	
	this_emergency = {
		'id': id
	}
	emergency = Emergency.get_one_emergency(this_emergency)
	countries = National_Society.get_all_national_societies()
	
	return render_template('edit_emergency.html', emergency = emergency, member = member, countries = countries)