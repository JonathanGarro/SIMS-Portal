import os

from flask import (
	request, render_template, url_for, flash, redirect,
	jsonify, Blueprint, current_app, send_file
)
from flask_login import (
	login_user, logout_user, current_user, login_required
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from SIMS_Portal import db
from SIMS_Portal.models import (
	User, Assignment, Emergency, NationalSociety, Portfolio,
	EmergencyType, Skill, Language, user_skill, user_language,
	Badge, Alert
)
from SIMS_Portal.portfolios.forms import PortfolioUploadForm
from SIMS_Portal.users.utils import send_slack_dm
from SIMS_Portal.portfolios.utils import (
	get_full_portfolio, save_portfolio_to_dropbox, save_cover_image
)
from func_timeout import func_timeout, FunctionTimedOut

portfolios = Blueprint('portfolios', __name__)

@portfolios.route('/portfolio')
def portfolio():
	type_search = ''
	# type_list = ['Map', 'Infographic', 'Dashboard', 'Mobile Data Collection', 'Assessment', 'Internal Analysis', 'External Report', 'Other']
	type_list = current_app.config['PORTFOLIO_TYPES']
	public_portfolio = db.session.query(Portfolio).filter(Portfolio.external==True, Portfolio.product_status=='Approved').all()
	return render_template('portfolio_public.html', title="SIMS Products", public_portfolio=public_portfolio, type_list=type_list, type_search=type_search)
	
@portfolios.route('/portfolio/filter/<type>', methods=['GET', 'POST'])
def filter_portfolio(type):
	type_list = current_app.config['PORTFOLIO_TYPES']
	type_search = "{}".format(type)
	public_portfolio = db.session.query(Portfolio).filter(Portfolio.external==True, Portfolio.product_status=='Approved', Portfolio.type == type_search).all()
	return render_template('portfolio_public.html', title="SIMS Products", public_portfolio=public_portfolio, type_search=type_search, type_list=type_list)
	
@portfolios.route('/all_products')
@login_required
def all_products():
	type_search = ''
	full_portfolio = db.session.query(Portfolio, User, Emergency).join(User, User.id == Portfolio.creator_id).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Portfolio.product_status != 'Removed').all()
	type_list = current_app.config['PORTFOLIO_TYPES']
	return render_template('portfolio_all.html', title="SIMS Products", full_portfolio=full_portfolio, type_list=type_list, type_search=type_search)

@portfolios.route('/portfolio_private/filter/<type>', methods=['GET', 'POST'])
@login_required
def filter_portfolio_private(type):
	type_list = current_app.config['PORTFOLIO_TYPES']
	type_search = "{}".format(type)
	full_portfolio = db.session.query(Portfolio, User, Emergency).join(User, User.id == Portfolio.creator_id).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Portfolio.product_status != 'Removed', Portfolio.type == type_search).all()
	return render_template('portfolio_all.html', title="SIMS Products", full_portfolio=full_portfolio, type_search=type_search, type_list=type_list)

@portfolios.route('/portfolio/new_from_assignment/<int:assignment_id>/<int:user_id>/<int:emergency_id>', methods=['GET', 'POST'])
@login_required
def new_portfolio_from_assignment(assignment_id, user_id, emergency_id):
	user_info = db.session.query(User).filter(User.id == user_id).first()
	form = PortfolioUploadForm()
	if form.validate_on_submit():
		if form.file.data:
			file = save_portfolio_to_dropbox(form.file.data, user_info.id, form.type.data)
		else:
			redirect_url = '/portfolio/new_from_assignment/{}/{}/{}'.format(assignment_id, user_id, emergency_id)
			flash('There was an error posting your product. Please make sure you have filled out all required fields and selected a compatible file.', 'danger')
			return redirect(redirect_url)
		if form.image_file.data:
			cover_image = save_cover_image(form.image_file.data, user_info.id, form.type.data)
		else:
			cover_image = form.format.data + '.png'
		if form.external.data == True:
			form.external.data = 1
			status = 'Pending Approval'
		else:
			form.external.data = 0
			status = 'Personal'
		product = Portfolio(
			local_file = file['file_filename'], title = form.title.data, creator_id = user_id, description = form.description.data, type = form.type.data, emergency_id = emergency_id, external = form.external.data, assignment_id = assignment_id, dropbox_file = file['share_link'], product_status = status, image_file = cover_image, format = form.format.data,
		)
		db.session.add(product)
		db.session.commit()
		if user_info.slack_id is not None:
			if form.external.data == True:
				message = 'You have successfully posted {} to the portal! Since you have requested that it be publicly visible, it has been added to the review queue for a SIMS Remote Coordinator. In the meantime, the product will be visible on your profile page to viewers that are logged in, and on your individual assignment page for this emergency.'.format(form.title.data)
			else:
				message = 'You have successfully posted {} to the portal! It has been marked as "Personal", and is now visible on your profile page to viewers that are logged in, and on your individual assignment page for this emergency.'.format(form.title.data)
			user = user_info.slack_id
			send_slack_dm(message, user)
		flash('New product successfully uploaded.', 'success')
		redirect_url = '/assignment/{}'.format(assignment_id)
		return redirect(redirect_url)
	return render_template('create_portfolio_from_assignment.html', title='Upload New SIMS Product', form=form)

@portfolios.route('/portfolio/view/<int:id>')
def view_portfolio(id):
	product = db.session.query(Portfolio, User, Emergency).join(User, User.id == Portfolio.creator_id).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Portfolio.id==id).first()
	if product is not None:
		# check if product already has collaborators assigned
		if product.Portfolio.collaborator_ids is not None:
			# strip out collaborator ids
			split_collaborators = product.Portfolio.collaborator_ids.split(',')
			# convert str to int
			list_collaborators = [eval(i) for i in split_collaborators]
			list_collaborators_user_info = []
			for user_id in list_collaborators:
				list_collaborators_user_info.append(db.session.query(User).filter(User.id == user_id).first())
			return render_template('portfolio_view.html', product=product, list_collaborators_user_info=list_collaborators_user_info)
		else:
			list_collaborators_user_info = None
			return render_template('portfolio_view.html', product=product, list_collaborators_user_info=list_collaborators_user_info)
	else:
		return redirect('error404')

@portfolios.route('/portfolio/download/<int:id>')
def download_portfolio(id):
	product = db.session.query(Portfolio).filter(Portfolio.id==id).first()
	path = os.path.join(current_app.root_path, 'static/assets/portfolio', product.local_file)
	return send_file(path, as_attachment=True)

@portfolios.route('/portfolio/delete/<int:id>')
@login_required
def delete_portfolio(id):
	if current_user.is_admin == 1 or current_user.id == id:
		try:
			db.session.query(Portfolio).filter(Portfolio.id==id).update({'product_status':'Removed'})
			db.session.commit()
			flash("Product deleted.", 'success')
		except:
			flash("Error deleting product. Check that the product ID exists.")
		return redirect(url_for('main.dashboard'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
		
@portfolios.route('/portfolio/review/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def review_portfolio(dis_id):
	emergency_info = db.session.query(Emergency, EmergencyType, NationalSociety).join(EmergencyType, EmergencyType.emergency_type_go_id == Emergency.emergency_type_id).join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id).filter(Emergency.id == dis_id).first()
	
	# get list of all SIMS coordinators for event
	disaster_coordinator_query = db.session.query(Emergency, Assignment, User).join(Assignment, Assignment.emergency_id == Emergency.id).join(User, User.id == Assignment.user_id).filter(Emergency.id == dis_id, Assignment.role == 'SIMS Remote Coordinator').all()
	# for loop gets the user id of query and appends to list
	disaster_coordinator_list = []
	for coordinator in disaster_coordinator_query:
		disaster_coordinator_list.append(coordinator.User.id)
	
	# check if current user is one of the event's coordinators
	if current_user.id in disaster_coordinator_list or current_user.is_admin == 1:
		pass
	else:
		event_name = db.session.query(Emergency).filter(Emergency.id == dis_id).first()
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins, disaster_coordinator_query=disaster_coordinator_query, event_name=event_name), 403
	# get pending products for this emergency	
	pending_list = db.session.query(Portfolio, Emergency, User).join(Emergency, Emergency.id == Portfolio.emergency_id).join(User, User.id == Portfolio.creator_id).filter(Portfolio.emergency_id == dis_id, Portfolio.product_status == 'Pending Approval').all()

	return render_template('portfolio_approve.html', pending_list=pending_list, emergency_info=emergency_info)
	
@portfolios.route('/portfolio/approve/<int:prod_id>/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def approve_portfolio(prod_id, dis_id):
	# get list of all SIMS coordinators for event
	disaster_coordinator_query = db.session.query(Emergency, Assignment, User).join(Assignment, Assignment.emergency_id == Emergency.id).join(User, User.id == Assignment.user_id).filter(Emergency.id == dis_id, Assignment.role == 'SIMS Remote Coordinator').all()
	
	# for loop gets the user id of query and appends to list
	disaster_coordinator_list = []
	for coordinator in disaster_coordinator_query:
		disaster_coordinator_list.append(coordinator.User.id)
	
	# check that product is associated with that disaster
	check_record = db.session.query(Portfolio, Emergency).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Portfolio.id == prod_id, Emergency.id == dis_id).first()
	
	# check if current user is one of the event's coordinators, and that the product passed the route is associated with the emergency
	if (current_user.id in disaster_coordinator_list or current_user.is_admin == 1) and check_record:
		try:
			db.session.query(Portfolio).filter(Portfolio.id == prod_id).update({'product_status':'Approved'})
			db.session.commit()
			flash('Product has been approved for external viewers.', 'success')
		except:
			flash('Error approving the product.', 'warning')
		redirect_url = '/portfolio/review/{}'.format(dis_id)
		return redirect(redirect_url)
	elif (current_user.id in disaster_coordinator_list or current_user.is_admin == 1) and not check_record:
		flash('Error approving the product. It looks like that product is not associated with this emergency, or an ID number is wrong. Contact a site administrator.', 'warning')
		redirect_url = '/portfolio/review/{}'.format(dis_id)
		return redirect(redirect_url)
	else:
		event_name = db.session.query(Emergency).filter(Emergency.id == dis_id).first()
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins, disaster_coordinator_query=disaster_coordinator_query, event_name=event_name), 403

@portfolios.route('/portfolio/reject/<int:prod_id>/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def reject_portfolio(prod_id, dis_id):
	# get list of all SIMS coordinators for event
	disaster_coordinator_query = db.session.query(Emergency, Assignment, User).join(Assignment, Assignment.emergency_id == Emergency.id).join(User, User.id == Assignment.user_id).filter(Emergency.id == dis_id, Assignment.role == 'SIMS Remote Coordinator').all()
	
	# for loop gets the user id of query and appends to list
	disaster_coordinator_list = []
	for coordinator in disaster_coordinator_query:
		disaster_coordinator_list.append(coordinator.User.id)
	
	# check that product is associated with that disaster
	check_record = db.session.query(Portfolio, Emergency).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Portfolio.id == prod_id, Emergency.id == dis_id).first()
	
	# check if current user is one of the event's coordinators, and that the product passed the route is associated with the emergency
	if (current_user.id in disaster_coordinator_list or current_user.is_admin == 1) and check_record:
		try:
			db.session.query(Portfolio).filter(Portfolio.id == prod_id).update({'product_status':'Personal'})
			db.session.commit()
			flash('Product has been rejected for public viewing.', 'success')
		except:
			flash('Error approving the product.', 'warning')
		redirect_url = '/portfolio/review/{}'.format(dis_id)
		return redirect(redirect_url)
	elif (current_user.id in disaster_coordinator_list or current_user.is_admin == 1) and not check_record:
		flash('Error approving the product. It looks like that product is not associated with this emergency, or an ID number is wrong. Contact a site administrator.', 'warning')
		redirect_url = '/portfolio/review/{}'.format(dis_id)
		return redirect(redirect_url)
	else:
		event_name = db.session.query(Emergency).filter(Emergency.id == dis_id).first()
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins, disaster_coordinator_query=disaster_coordinator_query, event_name=event_name), 403

@portfolios.route('/portfolio/emergency_more/<int:id>')
@login_required
def all_emergency_products(id):
	emergency_portfolio = db.session.query(Portfolio, Emergency).join(Emergency, Emergency.id == Portfolio.emergency_id).filter(Emergency.id == id, Portfolio.product_status == 'Approved').all()
	emergency_info = db.session.query(Emergency).filter(Emergency.id == id).first()
	return render_template('emergency_more.html', emergency_portfolio=emergency_portfolio, emergency_info=emergency_info)

@portfolios.route('/portfolio/profile_more/<int:id>')
@login_required
def all_user_products(id):
	user_info = db.session.query(User).filter(User.id == id).first()
	user_portfolio = get_full_portfolio(id)
	
	return render_template('profile_more.html', user_info=user_info, user_portfolio=user_portfolio)

@portfolios.route('/portfolio/add_supporter/<int:product_id>')
@login_required
def add_supporter_to_product(product_id):
	product = db.session.query(Portfolio).filter(Portfolio.id == product_id).first()
	product_owner = product.creator_id
	user_id = current_user.id
	collaborators = db.session.query(Portfolio).filter(Portfolio.id == product_id).first()
	# prevent product owner from also being collaborator
	if user_id == product_owner:
		flash('You are already listed as the owner of this product and cannot be added as a collaborator.','danger')
		return redirect(url_for('portfolios.view_portfolio', id=product_id))
	# check if collaborator column has data
	if collaborators.collaborator_ids is not None:
		# split the string by comma and convert to list
		split_collaborators = collaborators.collaborator_ids.split(',')
		# convert str to int
		list_collaborators = [eval(i) for i in split_collaborators]
		# check if user is already associated
		if user_id in list_collaborators:
			flash('You are already associated with this product.', 'danger')
			return redirect(url_for('portfolios.view_portfolio', id=product_id))
		else:
			# add user to list as collaborator
			list_collaborators.append(user_id)
			# convert list of ints back to single string
			string_of_collaborators = ','.join(str(x) for x in list_collaborators)
			# add new string back into db
			db.session.query(Portfolio).filter(Portfolio.id == product_id).update({'collaborator_ids':string_of_collaborators})
			db.session.commit()
			flash('You are now listed as a collaborator!', 'success')
			return redirect(url_for('portfolios.view_portfolio', id=product_id))
	# collaborator column is empty, so update with user id
	else:
		str(user_id)
		db.session.query(Portfolio).filter(Portfolio.id == product_id).update({'collaborator_ids':user_id})
		db.session.commit()
		flash('You are now listed as a collaborator!', 'success')
		return redirect(url_for('portfolios.view_portfolio', id=product_id))

@portfolios.route('/portfolio/remove_supporter/<int:product_id>')
@login_required
def remove_supporter_from_product(product_id):
	product = db.session.query(Portfolio).filter(Portfolio.id == product_id).first()
	product_owner = product.creator_id
	user_id = current_user.id
	collaborators = db.session.query(Portfolio).filter(Portfolio.id == product_id).first()
	if user_id == product_owner:
		flash('You are listed as the owner of this product and cannot untag yourself. You can delete the product if you wish to remove it from your profile.','danger')
		return redirect(url_for('portfolios.view_portfolio', id=product_id))
	if collaborators.collaborator_ids is not None:
		# split the string by comma and convert to list
		split_collaborators = collaborators.collaborator_ids.split(',')
		# convert str to int
		list_collaborators = [eval(i) for i in split_collaborators]
		
		if user_id in list_collaborators:
			list_collaborators.remove(user_id)
			string_of_collaborators = ','.join(str(x) for x in list_collaborators)
			db.session.query(Portfolio).filter(Portfolio.id == product_id).update({'collaborator_ids':string_of_collaborators})
			db.session.commit()
			
			# if removing supporter leaves blank column on collaborator_ids, replace text with "NULL"
			new_collaborators = db.session.query(Portfolio).filter(Portfolio.id == product_id).with_entities(Portfolio.collaborator_ids).first()
			if len(new_collaborators.collaborator_ids) < 1:
				db.session.query(Portfolio).filter(Portfolio.id == product_id).update({'collaborator_ids': 0 })
				db.session.commit()
			
			flash('You have removed yourself as a collaborator on this product.', 'success')
			return redirect(url_for('portfolios.view_portfolio', id=product_id))
		else: 
			flash('You are not listed as a collaborator on this product. If you think this error message is not correct, please contact a site administrator.', 'danger')
			return redirect(url_for('portfolios.view_portfolio', id=product_id))
	else:
		flash('This product has no collaborators listed that can be removed.', 'danger')
		return redirect(url_for('portfolios.view_portfolio', id=product_id))