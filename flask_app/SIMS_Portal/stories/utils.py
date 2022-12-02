from flask import url_for, current_app
from SIMS_Portal.models import User, Assignment, Emergency
from SIMS_Portal import db
from flask_login import current_user
import os
import secrets
from PIL import Image

def save_header(form_header):
	random_hex = secrets.token_hex(8)
	filename, file_ext = os.path.splitext(form_header.filename)
	picture_filename = random_hex + file_ext
	picture_path = os.path.join(current_app.root_path, 'static/assets/img/stories', picture_filename)
	
	output_size = (1300, 650)
	resized_image = Image.open(form_header)
	resized_image.thumbnail(output_size)
	resized_image.save(picture_path)
	
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