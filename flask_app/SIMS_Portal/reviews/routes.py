from flask import (
	request, render_template, url_for, flash, redirect,
	jsonify, Blueprint, current_app
)
from flask_login import (
	login_user, logout_user, current_user, login_required
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

from SIMS_Portal import db
from SIMS_Portal.config import Config
from SIMS_Portal.models import Review, Emergency, User
from SIMS_Portal.reviews.forms import (
	NewEmergencyReviewForm, ProcessEmergencyReviewForm
)
from SIMS_Portal.users.utils import send_slack_dm
from SIMS_Portal.main.utils import check_sims_co

reviews = Blueprint('reviews', __name__)

@reviews.route('/operation_review/new/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def new_op_review(dis_id):
	form = NewEmergencyReviewForm()
	emergency_info = db.session.query(Emergency).filter(Emergency.id == dis_id).first()
	if request.method == 'GET' and check_sims_co(dis_id) == True:
		existing_reviews = db.session.query(Review).filter(Review.emergency_id == dis_id).all()
		return render_template('emergency_review.html', form=form, emergency_info=emergency_info, existing_reviews=existing_reviews)
	if request.method == 'POST' and check_sims_co(dis_id) == True:
		new_review = Review(
			category = form.category.data,
			type = form.type.data,
			title = form.title.data,
			description = form.description.data,
			recommended_action = form.recommendation.data,
			follow_up = 'Awaiting SIMS governance processing.',
			status = 'Open',
			emergency_id = emergency_info.id
		)
		db.session.add(new_review)
		db.session.commit()
		this_record_id = db.session.query(Review).filter(Review.emergency_id == emergency_info.id).order_by(Review.id.desc()).first()
		message = 'You have successfully created a new operational learning record for {}. You can <{}/operation_review/view/{}|view the record here>.'.format(emergency_info.emergency_name, current_app.config['ROOT_URL'], this_record_id.id)
		user = current_user.slack_id
		send_slack_dm(message, user)
		flash('New emergency review record created.', 'success')
		return redirect(url_for('reviews.new_op_review', dis_id=dis_id))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@reviews.route('/operation_review/view/<int:id>', methods=['GET'])
@login_required
def view_op_review(id):
	record = db.session.query(Review).filter(Review.id == id).first()
	emergency_info = db.session.query(Emergency, Review).join(Review, Review.emergency_id == Emergency.id).filter(Review.id == id).first()
	if record is None or emergency_info is None:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/404.html', list_of_admins=list_of_admins), 404
	return render_template('emergency_review_view.html', record=record, emergency_info=emergency_info)

@reviews.route('/operation_review/process/<int:id>', methods=['GET', 'POST'])
@login_required
def process_op_review(id):
	form = ProcessEmergencyReviewForm()
	record = db.session.query(Review).filter(Review.id == id).first()
	emergency_info = db.session.query(Emergency, Review).join(Review, Review.emergency_id == Emergency.id).filter(Review.id == id).first()
	if request.method == 'GET' and current_user.is_admin == 1:
		return render_template('emergency_review_processing.html', form=form, record=record, emergency_info=emergency_info)
	if request.method == 'POST' and current_user.is_admin == 1:
		follow_up = form.follow_up.data
		db.session.query(Review).filter(Review.id == id).update({'follow_up':follow_up, 'status':'Processed'})
		db.session.commit()
		return redirect(url_for('main.admin_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin == 1).all()
		return render_template('errors/404.html', list_of_admins=list_of_admins), 404
	if record is None or emergency_info is None:
		list_of_admins = db.session.query(User).filter(User.is_admin == 1).all()
		return render_template('errors/404.html', list_of_admins=list_of_admins), 404
	return render_template('emergency_review_processing.html', record=record, emergency_info=emergency_info)

@reviews.route('/operation_review/drop/<int:id>', methods=['GET', 'POST'])
@login_required
def drop_op_review(id):
	db.session.query(Review).filter(Review.id == id).update({'status': 'Dropped'})
	db.session.commit()
	return redirect(url_for('reviews.view_op_review', id=id))