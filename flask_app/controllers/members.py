from flask_app import app
from flask import render_template,redirect,session,request, flash, url_for
from flask_app.models import member, emergency, national_society, assignment
from flask_app.models import alert
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import FileField, SubmitField
from wtforms.validators import InputRequired
from werkzeug.utils import secure_filename
import os
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

app.config['HEADSHOT_FOLDER'] = "flask_app/static/uploaded_files/headshots/"

@app.route('/layout')
def layout_preview():
	return render_template('layout.html')


@app.route('/index')
@app.route('/')
def index():
	# clear out the session cache to avoid member data issues on-load
	session.clear()

	active_member_count = member.Member.get_all_active_member_count()
	distinct_ns_count = national_society.National_Society.get_all_active_ns_count()
	return render_template('index.html', active_member_count = active_member_count, distinct_ns_count = distinct_ns_count)
	
@app.route('/members')
def member_page():
	active_members = member.Member.get_all_active_members()
	return render_template('members.html', active_members=active_members)
	
@app.route('/data')
def data_page():
	return render_template('data_viz.html')

@app.route('/portfolio')
def portfolio_page():
	return render_template('portfolio.html')
	
@app.route('/about')
def about_page():
	return render_template('about.html')

@app.route('/profile')
def profile_page():
	member_data = {
		'id': session['member_id']
	}
	if 'member_id' not in session:
		return redirect('/logout')
	
	this_member = member.Member.get_member_by_id_with_ns(member_data)
	countries = national_society.National_Society.get_all_national_societies()
	avatar = url_for('static', filename="uploaded_files/headshots/" + this_member.avatar)
	this_members_assignments = assignment.Assignment.get_all_assignments_by_member(member_data)
	return render_template('profile.html', member=this_member , countries=countries, avatar=avatar, assignments=this_members_assignments)

@app.route('/edit/profile/<int:id>', methods=['GET','POST'])
def edit_profile_page(id):
	member_data = {
		'id': session['member_id']
	}
	this_member = member.Member.get_member_by_id_with_ns(member_data)
	avatar = url_for('static', filename="uploaded_files/headshots/" + this_member.avatar)
	countries = national_society.National_Society.get_all_national_societies()
	
	return render_template('edit_profile.html', member=this_member, avatar=avatar, countries=countries)
	
@app.route('/update/profile', methods=['POST'])
def update_profile():
	member_data = {
		'id': session['member_id']
	}
	if not member.Member.validate_profile_update(request.form):
		return redirect(url_for('edit_profile_page', id=member_data['id']))
	
	data = {
		"id": request.form['mem_id'], # this is hidden data in the form
		"first_name": request.form['first_name'],
		"last_name": request.form['last_name'],
		"gender": request.form['gender'],
		"national_society_id": request.form['national_society_id'],
		"email": request.form['email'],
		"job_title": request.form['job_title'],
		"birthday": request.form['birthday']
	}

	member.Member.update_member_profile(data)
	member_data = {
			'id': session['member_id']
		}
	return redirect(url_for('profile_page'))

@app.route('/edit/avatar/<int:id>', methods=['GET','POST'])
def edit_avatar(id):
	member_data = {
		'id': session['member_id']
	}
	this_member = member.Member.get_member_by_id_with_ns(member_data)
	avatar = url_for('static', filename="uploaded_files/headshots/" + this_member.avatar)
	countries = national_society.National_Society.get_all_national_societies()
	return render_template('edit_profile_avatar.html', member=this_member, avatar=avatar, countries=countries)

@app.route('/edit/profile/upload_avatar', methods=['POST'])
def upload_avatar():
	uploaded_file = request.files['avatar']
	if uploaded_file.filename != '':
		filename = secure_filename(uploaded_file.filename)
		uploaded_file.save(os.path.join(app.config['HEADSHOT_FOLDER'], filename))
		data = {
			'filename': filename,
			'id': session['member_id']
		}
		member.Member.update_avatar_in_db(data)
		
		member_data = {
			'id': session['member_id']
		}
		this_member = member.Member.get_member_by_id_with_ns(member_data)
	return redirect(url_for('profile_page'))

@app.route('/register', methods=('GET','POST'))
def register():
	return render_template('register.html', countries = national_society.National_Society.get_all_national_societies())

@app.route('/new/member', methods=['POST'])
def create_new_member():
	print("Running registration validation")
	if not member.Member.validate_register(request.form):
		print("Registration validation failed")
		return redirect('/register')
	
	data = {
		"first_name": request.form['first_name'],
		"last_name": request.form['last_name'],
		"gender": request.form['gender'],
		"national_society_id": request.form['national_society_id'],
		"email": request.form['email'],
		"password": bcrypt.generate_password_hash(request.form['password'])
	}
	
	id = member.Member.register_new_member(data)
	session['member_id'] = id
	return redirect('/dashboard')
	
@app.route('/dashboard')
def dashboard():
	if 'member_id' not in session:
		return redirect('/logout')
	
	member_data = {
		'id': session['member_id']
	}
	active_assignments = assignment.Assignment.get_active_assignments_with_member()
	countries = national_society.National_Society.get_all_national_societies()
	latest_emergencies = emergency.Emergency.get_recent_emergencies()
	count_active_assignments = assignment.Assignment.get_active_assignment_count()
	current_member = member.Member.get_member_by_id(member_data)
	surge_alerts = alert.Alert.get_all_alerts()
	
	return render_template('dashboard.html', member=current_member, countries=countries, latest_emergencies=latest_emergencies, active_assignments=active_assignments, count_active_assignments=count_active_assignments, surge_alerts=surge_alerts)

@app.route('/login')
def login_page():
	return render_template('login.html')

@app.route('/login/member', methods=['POST'])
def login():
	user = member.Member.get_member_by_email(request.form)
	
	if not user:
		flash("Invalid Email","login")
		return redirect('/login')
	
	if not bcrypt.check_password_hash(user.password, request.form['password']):
		flash("Invalid Password","login")
		return redirect('/login')
	
	session['member_id'] = user.id
	flash(f"Welcome, ", "logged_in")
	return redirect('/dashboard')

@app.route('/logout')
def logout():
	session.clear()
	flash("You have been logged out.", "logout")
	return redirect('/login')
	
