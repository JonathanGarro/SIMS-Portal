import os
import secrets
from flask import current_app
from SIMS_Portal import db
from SIMS_Portal.models import Portfolio, User

def save_portfolio(form_file):
	random_hex = secrets.token_hex(8)
	filename, file_ext = os.path.splitext(form_file.filename)
	file_filename = random_hex + file_ext
	file_path = os.path.join(current_app.root_path, 'static/assets/portfolio', file_filename)
	form_file.save(file_path)
	
	return file_filename

def get_full_portfolio(id):
	"""Takes in a user's ID and gets all of their products, including those that they are listed as the creator (original poster to the portal) and those that they tagged themselves as a collaborator"""
	
	user_info = db.session.query(User).filter(User.id == id).first()
	all_collaborators_plus_creators = db.session.query(Portfolio.id, Portfolio.collaborator_ids, Portfolio.creator_id, Portfolio.product_status).filter(Portfolio.product_status != 'Removed').all()
	
	temp_list = []
	for item in all_collaborators_plus_creators:
		temp_dict = {}
		if item[1] is not None:
			temp_dict['product_id'] = item[0]
			temp_dict['user_ids'] = [int(item) for item in item[1].split(',') if item.isdigit()]
			temp_dict['user_ids'].append(item[2])
			temp_list.append(temp_dict)
		else:
			temp_dict['product_id'] = item[0]
			temp_dict['user_ids'] = [item[2]]
			temp_list.append(temp_dict)
	
	list_of_product_ids = []
	for item in temp_list:
		if id in item['user_ids']:
			list_of_product_ids.append(item['product_id'])
	
	temp_user_portfolio = []
	for this_product_id in list_of_product_ids:
		temp_user_portfolio.append(db.session.query(Portfolio).filter(Portfolio.id == this_product_id).all())

	user_portfolio = []
	for product in temp_user_portfolio:
		user_portfolio.append(product[0])

	return user_portfolio