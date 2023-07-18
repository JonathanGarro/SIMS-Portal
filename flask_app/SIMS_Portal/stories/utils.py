from flask import url_for, current_app
from SIMS_Portal.models import User, Assignment, Emergency
from SIMS_Portal import db
from flask_login import current_user
import os
import secrets
import tempfile
import boto3
from PIL import Image
	
def save_header(form_header):
	random_hex = secrets.token_hex(8)
	filename, file_ext = os.path.splitext(form_header.filename)
	if file_ext.lower() == '.jpeg':
		file_ext = '.jpg'
	picture_filename = random_hex + file_ext
	picture_path = f"stories/{picture_filename}"
	
	with tempfile.NamedTemporaryFile(suffix=file_ext) as resized_image_file:
		output_size = (1300, 650)
		resized_image = Image.open(form_header)
		resized_image.thumbnail(output_size)
		resized_image.save(resized_image_file.name)
		s3 = boto3.client("s3")
		s3.upload_file(resized_image_file.name, current_app.config["UPLOAD_BUCKET"], picture_path)
	
	# prepend filename with s3 folder
	picture_filename = f"stories/{picture_filename}"
	
	return picture_filename

def check_sims_co(emergency_id):
	"""Takes in an emergency id record and verifies that the current user is listed as a SIMS Remove Coordinator for that record in order to allow additional permission sets."""
	sims_co_ids = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == emergency_id, Assignment.role == 'SIMS Remote Coordinator').all()
	sims_co_list = []
	for coordinator in sims_co_ids:
		sims_co_list.append(coordinator.User.id)
	if current_user.id in sims_co_list:
		user_is_sims_co = True
	else:
		user_is_sims_co = False
		
	return user_is_sims_co