import os
import tempfile
import secrets

import boto3
import dropbox
from flask import current_app
from SIMS_Portal import db
from SIMS_Portal.models import Portfolio, User
from PIL import Image
import logging


def save_portfolio_to_dropbox(form_file, user_id, type):
	"""
	Save a portfolio file to Dropbox and return the file details and shared link.
	
	Generates a unique filename for the uploaded file, saves it locally, uploads it to Dropbox,
	and returns the file name and a shared link to the file.
	
	Parameters:
	form_file (FileStorage): The file object to be uploaded.
	user_id (int): The ID of the user uploading the file.
	type (str): The type of file being uploaded.
	
	Returns:
	dict: A dictionary containing:
		- 'file_filename' (str): The name of the file saved in Dropbox.
		- 'share_link' (str): The shared link to the uploaded file in Dropbox.
	
	Side Effects:
	- Saves the file locally before uploading it to Dropbox.
	- Uploads the file to a specific folder in Dropbox.
	- Creates a shared link for the uploaded file in Dropbox.
	
	Raises:
	None
	"""
	
	# generate unique string to avoid filename conflicts
	random_hex = secrets.token_hex(8)
	
	# use an access token with ONLY individual scopes (don't select any team scopes)
	dropbox_access_token = current_app.config['DROPBOX_BOT']
	
	filename, file_ext = os.path.splitext(form_file.filename)
	file_filename = type + '-user'+ str(user_id) + '-' + random_hex + file_ext
	local_file_path = os.path.join(current_app.root_path, 'static/assets/portfolio', file_filename)
	dropbox_path = '/SIMS Portal/Portfolio/{}'.format(file_filename)
	form_file.save(local_file_path)
	
	client = dropbox.Dropbox(
		dropbox_access_token,
		app_key = current_app.config['DROPBOX_APP_KEY'],
		app_secret = current_app.config['DROPBOX_APP_SECRET'],
		oauth2_refresh_token = current_app.config['DROPBOX_REFRESH_TOKEN']
	)
	
	uploaded = client.files_upload(open(local_file_path, "rb").read(), dropbox_path)
	shared_link = client.sharing_create_shared_link(dropbox_path)
	
	share_link = shared_link.url
	
	output = {
		'file_filename': file_filename, 
		'share_link': share_link
	}
	
	return output

def save_cover_image(form_file, user_id, type):
	"""
	Save a cover image to an S3 bucket after resizing it.
	
	Generates a unique filename for the uploaded cover image, downscales the image to a maximum width of 850 pixels,
	saves it to a temporary file, uploads it to an S3 bucket, and returns the file path.
	
	Parameters:
	form_file (FileStorage): The image file to be uploaded.
	user_id (int): The ID of the user uploading the image.
	type (str): The type of image being uploaded.
	
	Returns:
	str: The file path where the image is saved in the S3 bucket.
	
	Side Effects:
	- Saves the resized image to a temporary file before uploading it to S3.
	- Uploads the image file to a specified S3 bucket.
	- Logs an error if resizing the image fails.
	
	Raises:
	None
	"""
	
	random_hex = secrets.token_hex(8)
	filename, file_ext = os.path.splitext(form_file.filename)
	file_filename = type + '-user'+ str(user_id) + '-' + random_hex + file_ext
	file_path = f"portfolio_cover_images/{file_filename}"
	
	# downscale image to max width of 850px
	try:
		with tempfile.NamedTemporaryFile(suffix=file_ext) as resized_image_file:
			basewidth = 850
			img = Image.open(form_file)
			wpercent = (basewidth/float(img.size[0]))
			hsize = int((float(img.size[1])*float(wpercent)))
			img = img.resize((basewidth,hsize), Image.Resampling.LANCZOS)
			img.save(resized_image_file.name)
			s3 = boto3.client("s3")
			s3.upload_file(resized_image_file.name, current_app.config["UPLOAD_BUCKET"], file_path)
	except Exception as e: 
		current_app.logger.error('Resize image on save_cover_image function failed: {}'.format(e))

	return file_path

def get_full_portfolio(id):
	"""
	Retrieve the full portfolio of a user by their ID.
	
	Queries the database to get all portfolio items associated with a specific user, either as a creator
	or as a collaborator. It returns a list of portfolio items that are not marked as 'Removed'.
	
	Parameters:
	id (int): The ID of the user for whom to retrieve the portfolio.
	
	Returns:
	list: A list of Portfolio objects associated with the user.
	
	Side Effects:
	None
	
	Raises:
	None
	"""
	
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
