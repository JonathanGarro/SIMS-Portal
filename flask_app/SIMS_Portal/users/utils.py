from flask import url_for, current_app
import os
import secrets
import requests
from PIL import Image
from flask_mail import Message
from SIMS_Portal import mail, db
from SIMS_Portal.models import User, Assignment, Emergency
from slack_sdk import WebClient


def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	filename, file_ext = os.path.splitext(form_picture.filename)
	picture_filename = random_hex + file_ext
	picture_path = os.path.join(current_app.root_path, 'static/assets/img/avatars', picture_filename)
	
	output_size = (400, 400)
	resized_image = Image.open(form_picture)
	resized_image.thumbnail(output_size)
	resized_image.save(picture_path)
	
	return picture_filename
	
def send_reset_email(user):
	token = user.get_reset_token()
	msg = Message('Password reset request for SIMS', sender='sims_portal@dissolvingdata.com', recipients=[user.email])
	msg.body = f'''Login issues, huh? No sweat, it happens to the best of us. To reset your password, visit the following link:
{url_for("users.reset_token", token=token, _external=True)}
	
If you did not make this request, then simply ignore this email and no changes will be made.
'''
	mail.send(msg)

# send slack alert when new user signs up
def new_user_slack_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'C046A8T9ZJB',
			text = message
		)
	except:
		pass

# search for remote coordinators currently active
def rem_cos_search():
	with app.app_context():
		active_SIMS_cos = db.session.query(Assignment, User, Emergency).join(User, User.id == Assignment.user_id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.emergency_status == 'Active', Assignment.role == 'SIMS Remote Coordinator').all()
		print(active_SIMS_cos)

# general purpose DM messaging bot
def send_slack_dm(message, user):
	slack_token = current_app.config['SIMS_PORTAL_SLACK_BOT']
	data = {
			'token': slack_token,
			'channel': user,    # User's Slack ID
			'as_user': True,
			'text': message
	}
	requests.post(url='https://slack.com/api/chat.postMessage', data=data)